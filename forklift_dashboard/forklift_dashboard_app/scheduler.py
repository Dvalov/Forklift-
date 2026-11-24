import atexit
import logging
import os
import random
from datetime import timedelta
from http import HTTPStatus

import requests as http_requests
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

ANYLOGIC_URL = os.environ.get('ANYLOGIC_URL', 'http://127.0.0.1:8080')
WAREHOUSE_URL = os.environ.get('WAREHOUSE_URL', 'http://localhost:8001')
CONVERTER_URL = os.environ.get('CONVERTER_URL', 'http://localhost:8002')

ANYLOGIC_ORDER_TIMEOUT_SECONDS = 0.5
ANYLOGIC_STATE_TIMEOUT_SECONDS = 0.3
CONVERTER_COORDS_TIMEOUT_SECONDS = 0.5
CONVERTER_PATH_TIMEOUT_SECONDS = 3
HTTP_PROXIES = {'http': None, 'https': None}

SIMULATION_JOB_ID = 'forklift_simulation'
SIMULATION_INTERVAL_SECONDS = 0.5
ROUTE_PREVIEW_DURATION = timedelta(seconds=0.75)

DISCHARGE_RATE = 0.5  # charge_level units lost per tick of movement
MOVING_SPEED = 1.0
RAISED_FORK_HEIGHT = 1.0
HYDRAULIC_PRESSURE_RANGE = (142.0, 158.0)
PUMP_RPM_RANGE = (2750, 2900)
MIN_OIL_TEMP = 20.0
MAX_OIL_TEMP = 80.0
OIL_TEMP_RISE_PER_TICK = 0.2
OIL_TEMP_DROP_ON_STOP = 0.1
OIL_LEVEL_DROP_PER_TICK = 0.01

_TASK_PENDING = 'pending'
_TASK_IN_PROGRESS = 'in_progress'
_TASK_COMPLETED = 'completed'
_FORKLIFT_IDLE = 'idle'
_FORKLIFT_MOVING = 'moving'

_AL_DEFAULT_STATE = 'Idle'
_AL_FORK_RAISED_STATES = frozenset({'PickUp', 'PutDown'})
_AL_TASK_WORKING_STATES = _AL_FORK_RAISED_STATES | {'GoToSource', 'GoToDest'}
_AL_TASK_FINISH_STATES = frozenset({_AL_DEFAULT_STATE, 'Complete', 'ReturnToBase'})
_AL_MOVING_STATES = _AL_TASK_WORKING_STATES | {'GoToCharger', 'ReturnToBase'}
_AL_STATE_TO_DJANGO: dict[str, str] = {
    _AL_DEFAULT_STATE: _FORKLIFT_IDLE,
    'GoToSource': _FORKLIFT_MOVING,
    'PickUp': _FORKLIFT_MOVING,
    'GoToDest': _FORKLIFT_MOVING,
    'PutDown': _FORKLIFT_MOVING,
    'Complete': _FORKLIFT_IDLE,
    'Charging': 'charging',
    'GoToCharger': _FORKLIFT_MOVING,
    'ReturnToBase': _FORKLIFT_MOVING,
}

_scheduler = None
_last_dispatched_task_id: int | None = None


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        simulation_tick,
        trigger='interval',
        seconds=SIMULATION_INTERVAL_SECONDS,
        id=SIMULATION_JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    atexit.register(lambda: _scheduler.shutdown(wait=False))
    logger.info("APScheduler started — simulation_tick running every %gs", SIMULATION_INTERVAL_SECONDS)


def simulation_tick():
    try:
        from .models import Forklift

        forklift_id = getattr(settings, 'FORKLIFT_ID', None)
        warehouse_id = getattr(settings, 'WAREHOUSE_ID', None)

        if not forklift_id:
            logger.warning("Tick skipped: FORKLIFT_ID not set, anylogic_state=not_polled")
            return

        try:
            forklift = Forklift.objects.get(pk=forklift_id)
        except Forklift.DoesNotExist:
            logger.error("Tick skipped: forklift=%s not found in Django, anylogic_state=not_polled", forklift_id)
            return

        anylogic_state = _fetch_anylogic_state()
        if anylogic_state is not None:
            _tick_anylogic_mode(forklift, anylogic_state)
        else:
            _tick_django_mode(forklift, forklift_id, warehouse_id)

    except Exception:
        logger.exception("Unhandled error in simulation_tick")


# ---------------------------------------------------------------------------
# AnyLogic mode — AnyLogic owns movement; Django only syncs status/hydraulics
# ---------------------------------------------------------------------------

def _tick_anylogic_mode(forklift, anylogic_state):
    global _last_dispatched_task_id
    from .models import Task

    forklifts = anylogic_state.get('forklifts', [])
    al_fl = forklifts[0] if forklifts else None
    reported_state = al_fl.get('state') if al_fl else None
    al_busy = al_fl.get('busy') if al_fl else None
    al_state = al_fl.get('state', _AL_DEFAULT_STATE) if al_fl else _AL_DEFAULT_STATE
    django_status = _AL_STATE_TO_DJANGO.get(al_state, _FORKLIFT_IDLE)

    in_progress = Task.objects.filter(forklift=forklift, status=_TASK_IN_PROGRESS).first()
    logger.info(
        "Tick: forklift=%s anylogic_state=%s busy=%s anylogic_pending=%s anylogic_done=%s "
        "django_task=%s django_status=%s awaiting_start_task=%s",
        forklift.pk, reported_state, al_busy,
        anylogic_state.get('pending'), anylogic_state.get('done'),
        in_progress.pk if in_progress else None, in_progress.status if in_progress else None,
        _last_dispatched_task_id,
    )

    # 1. Task Lifecycle Management
    if al_state in _AL_TASK_WORKING_STATES:
        if _last_dispatched_task_id is not None:
            logger.info(
                "AnyLogic entered working state %s: clearing start wait for task=%s",
                al_state, _last_dispatched_task_id,
            )
        _last_dispatched_task_id = None

    elif in_progress:
        if reported_state in _AL_TASK_FINISH_STATES and in_progress.pk != _last_dispatched_task_id:
            in_progress.status = _TASK_COMPLETED
            in_progress.save()
            logger.info(
                "Task %s status: in_progress -> completed (forklift=%s anylogic_state=%s)",
                in_progress.pk, forklift.pk, reported_state,
            )
            in_progress = None
            _last_dispatched_task_id = None
        else:
            reason = 'awaiting_working_state' if in_progress.pk == _last_dispatched_task_id else 'awaiting_finish_state'
            logger.info(
                "Queue waiting: forklift=%s task=%s status=in_progress anylogic_state=%s reason=%s",
                forklift.pk, in_progress.pk, reported_state, reason,
            )

    if in_progress is None and reported_state == _AL_DEFAULT_STATE and al_busy is False:
        _last_dispatched_task_id = None
        _dispatch_next_task(anylogic_state, forklift)

    # 2. Forklift Status & Telemetry Sync
    if al_state in _AL_MOVING_STATES:
        forklift.status = django_status
        forklift.speed = MOVING_SPEED
        forklift.charge_level = al_fl.get('charge', forklift.charge_level) if al_fl else forklift.charge_level
        forklift.fork_height = RAISED_FORK_HEIGHT if al_state in _AL_FORK_RAISED_STATES else 0.0
        forklift.hydraulic_pressure = round(random.uniform(*HYDRAULIC_PRESSURE_RANGE), 1)
        forklift.oil_temp = round(min(MAX_OIL_TEMP, forklift.oil_temp + OIL_TEMP_RISE_PER_TICK), 1)
        forklift.pump_rpm = random.randint(*PUMP_RPM_RANGE)
        forklift.valves_ok = True
        forklift.oil_level = round(max(0.0, forklift.oil_level - OIL_LEVEL_DROP_PER_TICK), 2)
        forklift.save()

    else:
        new_charge = al_fl.get('charge', forklift.charge_level) if al_fl else forklift.charge_level
        if (forklift.status != django_status or
                forklift.charge_level != new_charge or
                forklift.speed != 0.0 or
                forklift.fork_height != 0.0):
            forklift.status = django_status
            forklift.charge_level = new_charge
            forklift.speed = 0.0
            forklift.fork_height = 0.0
            forklift.hydraulic_pressure = 0.0
            forklift.pump_rpm = 0
            forklift.oil_temp = round(max(MIN_OIL_TEMP, forklift.oil_temp - OIL_TEMP_DROP_ON_STOP), 1)
            forklift.save()


# ---------------------------------------------------------------------------
# Django mode — full A* simulation when AnyLogic is unavailable
# ---------------------------------------------------------------------------

def _tick_django_mode(forklift, forklift_id, warehouse_id):
    from .models import Task

    in_progress = Task.objects.filter(forklift=forklift, status=_TASK_IN_PROGRESS).first()
    logger.info(
        "Tick: forklift=%s anylogic_state=unavailable mode=django "
        "django_task=%s django_status=%s waypoints=%s",
        forklift_id, in_progress.pk if in_progress else None,
        in_progress.status if in_progress else None,
        len(in_progress.path_waypoints) if in_progress else None,
    )

    if not in_progress:
        pending = Task.objects.filter(forklift=forklift, status=_TASK_PENDING).first()
        if pending:
            logger.info(
                "Next task selected: task=%s forklift=%s status=%s mode=django",
                pending.pk, forklift_id, pending.status,
            )
            path = _fetch_task_path(forklift, warehouse_id, pending)
            if path is None:
                return

            if path == []:
                pending.status = _TASK_COMPLETED
                pending.path_waypoints = []
                pending.save()
                forklift.status = _FORKLIFT_IDLE
                forklift.speed = 0.0
                forklift.save()
                logger.info(
                    "Task %s status: pending -> completed (forklift=%s already at destination)",
                    pending.pk, forklift_id,
                )
                return

            pending.path_waypoints = path
            pending.status = _TASK_IN_PROGRESS
            with transaction.atomic():
                pending.save()
                if forklift.status != _FORKLIFT_IDLE or forklift.speed != 0:
                    forklift.status = _FORKLIFT_IDLE
                    forklift.speed = 0.0
                    forklift.save()
            logger.info(
                "Task %s status: pending -> in_progress (forklift=%s mode=django route_preview=%d)",
                pending.pk, forklift_id, len(path),
            )
            return
        else:
            logger.info("No pending tasks: forklift=%s mode=django", forklift_id)

    if in_progress and in_progress.path_waypoints:
        if forklift.status == _FORKLIFT_IDLE and timezone.now() - in_progress.updated_at < ROUTE_PREVIEW_DURATION:
            return

        waypoints = list(in_progress.path_waypoints)
        next_wp = waypoints.pop(0)

        forklift.status = _FORKLIFT_MOVING
        forklift.speed = MOVING_SPEED
        forklift.cell_x = round(next_wp['x'])
        forklift.cell_y = round(next_wp.get('y', forklift.cell_y))
        forklift.cell_z = round(next_wp['z'])

        forklift.charge_level = max(0.0, forklift.charge_level - DISCHARGE_RATE)
        forklift.hydraulic_pressure = round(random.uniform(*HYDRAULIC_PRESSURE_RANGE), 1)
        forklift.oil_temp = round(min(MAX_OIL_TEMP, forklift.oil_temp + OIL_TEMP_RISE_PER_TICK), 1)
        forklift.pump_rpm = random.randint(*PUMP_RPM_RANGE)
        forklift.valves_ok = True
        forklift.oil_level = round(max(0.0, forklift.oil_level - OIL_LEVEL_DROP_PER_TICK), 2)

        real = _fetch_real_coords(warehouse_id, forklift.cell_x, forklift.cell_y, forklift.cell_z)
        if real:
            forklift.position_x = real['x']
            forklift.position_y = real['y']
            forklift.position_z = real['z']

        in_progress.path_waypoints = waypoints
        if not waypoints:
            in_progress.status = _TASK_COMPLETED
            forklift.status = _FORKLIFT_IDLE
            forklift.speed = 0.0
            forklift.hydraulic_pressure = 0.0
            forklift.pump_rpm = 0
            forklift.oil_temp = round(max(MIN_OIL_TEMP, forklift.oil_temp - OIL_TEMP_DROP_ON_STOP), 1)

        with transaction.atomic():
            forklift.save()
            in_progress.save()

        if not waypoints:
            logger.info(
                "Task %s status: in_progress -> completed (forklift=%s mode=django cell=%s,%s)",
                in_progress.pk, forklift_id, forklift.cell_x, forklift.cell_z,
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dispatch_next_task(anylogic_state, forklift):
    """Send the next pending task to AnyLogic /order if one exists and not yet dispatched."""
    global _last_dispatched_task_id
    from .models import Task
    next_task = Task.objects.filter(forklift=forklift, status=_TASK_PENDING).first()
    if not next_task:
        logger.info("No pending tasks: forklift=%s mode=anylogic", forklift.pk)
        return
    if next_task.pk == _last_dispatched_task_id:
        logger.info("Task %s already dispatched: forklift=%s mode=anylogic", next_task.pk, forklift.pk)
        return

    logger.info(
        "Next task selected: task=%s forklift=%s status=%s mode=anylogic source=%s dest=%s",
        next_task.pk, forklift.pk, next_task.status, next_task.source_cell_name, next_task.dest_cell_name,
    )
    al_cells = anylogic_state.get('cells', [])
    al_source = next(
        (c for c in al_cells if c.get('name') == next_task.source_cell_name), None
    )
    al_dest = next(
        (c for c in al_cells if c.get('name') == next_task.dest_cell_name), None
    )
    if al_source is None or al_dest is None:
        logger.warning(
            "Next task %s: AnyLogic cell not found (source=%s, dest=%s)",
            next_task.pk, next_task.source_cell_name, next_task.dest_cell_name,
        )
        return

    try:
        resp = http_requests.post(
            f'{ANYLOGIC_URL}/order',
            json={'sourceCellId': al_source['id'], 'destCellId': al_dest['id']},
            timeout=ANYLOGIC_ORDER_TIMEOUT_SECONDS,
            proxies=HTTP_PROXIES,
        )
        try:
            response_data = resp.json()
        except ValueError:
            response_data = None
        logger.info(
            "AnyLogic /order response: task=%s http_status=%s order_ok=%s",
            next_task.pk, resp.status_code,
            response_data.get('ok') if isinstance(response_data, dict) else None,
        )
        if resp.ok:
            _last_dispatched_task_id = next_task.pk
            next_task.status = _TASK_IN_PROGRESS
            next_task.path_waypoints = []
            next_task.save()
            logger.info(
                "Task %s status: pending -> in_progress (forklift=%s mode=anylogic source_id=%s dest_id=%s)",
                next_task.pk, forklift.pk, al_source['id'], al_dest['id'],
            )
        else:
            logger.warning(
                "Failed to dispatch task %s to AnyLogic (source=%s→%s, dest=%s→%s), status=%s",
                next_task.pk, next_task.source_cell_name, al_source['id'],
                next_task.dest_cell_name, al_dest['id'], resp.status_code,
            )
    except Exception as exc:
        logger.warning("Failed to dispatch task %s to AnyLogic: %s", next_task.pk, exc)


def _fetch_anylogic_state():
    """Return AnyLogic /state JSON via Warehouse proxy, or None if unavailable."""
    try:
        resp = http_requests.get(
            f'{WAREHOUSE_URL}/api/anylogic/state',
            timeout=ANYLOGIC_STATE_TIMEOUT_SECONDS,
            proxies=HTTP_PROXIES,
        )
        if resp.status_code == HTTPStatus.OK:
            return resp.json()
        logger.warning("AnyLogic /state read failed: http_status=%s", resp.status_code)
    except Exception as exc:
        logger.warning("AnyLogic /state read failed: error=%s", type(exc).__name__)
    return None


def _fetch_real_coords(warehouse_id, cell_x, cell_y, cell_z):
    """Call Converter universal convert and return {"x", "y", "z"} in metres, or None on error."""
    try:
        resp = http_requests.get(
            f'{CONVERTER_URL}/api/converter/convert/',
            params={'x': cell_x, 'y': cell_y, 'z': cell_z},
            timeout=CONVERTER_COORDS_TIMEOUT_SECONDS,
            proxies=HTTP_PROXIES,
        )
        resp.raise_for_status()
        data = resp.json()
        return {'x': data['x'], 'y': data['y'], 'z': data['z']}
    except Exception:
        logger.warning("Could not convert cell (%s,%s,%s) to real coords", cell_x, cell_y, cell_z)
        return None


def _fetch_task_path(forklift, warehouse_id, task):
    from_x, from_y, from_z = forklift.cell_x, forklift.cell_y, forklift.cell_z
    pickup_path = []
    # Tasks created without a pickup address retain their destination-only route.
    if task.source_cell_x > 0 and task.source_cell_z > 0:
        pickup_path = _fetch_path(
            forklift.pk, warehouse_id, from_x, from_y, from_z,
            2 * task.source_cell_x - 1, task.source_cell_y, task.source_cell_z,
        )
        if pickup_path is None:
            logger.warning("Could not plan pickup for task %s", task.pk)
            return None
        if pickup_path:
            pickup_approach = pickup_path[-1]
            from_x, from_y, from_z = pickup_approach['x'], pickup_approach.get('y', from_y), pickup_approach['z']

    delivery_path = _fetch_path(
        forklift.pk, warehouse_id, from_x, from_y, from_z,
        2 * task.dest_cell_x - 1, task.dest_cell_y, task.dest_cell_z,
    )
    if delivery_path is None:
        logger.warning("Could not plan delivery for task %s", task.pk)
        return None

    logger.info(
        "Task %s route planned: pickup_waypoints=%s delivery_waypoints=%s",
        task.pk, len(pickup_path), len(delivery_path),
    )
    return pickup_path + delivery_path


def _fetch_path(forklift_id, warehouse_id, from_x, from_y, from_z, dest_x, dest_y, dest_z):
    """Call Converter get_cell_path and return list of {"x", "z"} waypoints, or None on error."""
    try:
        url = f'{CONVERTER_URL}/api/converter/{warehouse_id}/cells/get_path/'
        resp = http_requests.get(url, params={
            'forklift_id': forklift_id,
            'warehouse_id': warehouse_id,
            'from_x': from_x, 'from_y': from_y, 'from_z': from_z,
            'dest_x': dest_x, 'dest_y': dest_y, 'dest_z': dest_z,
        }, timeout=CONVERTER_PATH_TIMEOUT_SECONDS, proxies=HTTP_PROXIES)
        resp.raise_for_status()
        data = resp.json()
        path = data.get('path')
        if data.get('error') or not isinstance(path, list):
            logger.warning(
                "Converter could not route (%s,%s)->(%s,%s): %s",
                from_x, from_z, dest_x, dest_z, data.get('error') or 'invalid path',
            )
            return None
        return path
    except Exception:
        logger.warning("Converter unavailable, path fetch skipped")
        return None
