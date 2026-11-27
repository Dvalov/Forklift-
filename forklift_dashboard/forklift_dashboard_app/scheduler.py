import atexit
import logging
import os
import random
from contextlib import contextmanager
from datetime import timedelta
from http import HTTPStatus
from threading import Lock

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
_dispatch_lock = Lock()


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

        with anylogic_dispatch_state() as anylogic_state:
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
    from .models import Task

    #recover_missing_anylogic_orders(forklift.pk, anylogic_state)

    forklifts = anylogic_state.get('forklifts', [])
    al_fl = forklifts[0] if forklifts else {}
    reported_state = al_fl.get('state')
    al_state = reported_state or _AL_DEFAULT_STATE
    django_status = _AL_STATE_TO_DJANGO.get(al_state, _FORKLIFT_IDLE)

    active_tasks = Task.objects.filter(
        forklift=forklift, status__in=(_TASK_PENDING, _TASK_IN_PROGRESS),
    )
    done = anylogic_state.get('done')
    if type(done) is int and done >= 0:
        accepted = active_tasks.filter(anylogic_order_number__gt=0)
        accepted.filter(anylogic_order_number__lte=done).update(
            status=_TASK_COMPLETED, updated_at=timezone.now(),
        )
        if reported_state in _AL_TASK_WORKING_STATES:
            accepted.filter(status=_TASK_PENDING, anylogic_order_number=done + 1).update(
                status=_TASK_IN_PROGRESS, updated_at=timezone.now(),
            )

    # Tasks already in flight before the upgrade lack an AnyLogic order number.
    if reported_state in _AL_TASK_FINISH_STATES:
        legacy_task = active_tasks.filter(
            status=_TASK_IN_PROGRESS, anylogic_order_number__isnull=True, path_waypoints=[],
        ).first()
        if legacy_task:
            legacy_task.status = _TASK_COMPLETED
            legacy_task.save(update_fields=['status', 'updated_at'])

    dispatch_next_task(anylogic_state, forklift)

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

    tasks = Task.objects.filter(forklift=forklift)
    if tasks.filter(
        status__in=(_TASK_PENDING, _TASK_IN_PROGRESS), anylogic_order_number__isnull=False,
    ).exists():
        return

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


@contextmanager
def anylogic_dispatch_state():
    with _dispatch_lock:
        yield _fetch_anylogic_state()


def _empty_anylogic_queue(anylogic_state):
    forklifts = anylogic_state.get('forklifts', [])
    return anylogic_state.get('pending') == 0 and bool(forklifts) and all(
        forklift.get('state') == _AL_DEFAULT_STATE and forklift.get('busy') is False
        for forklift in forklifts
    )


def recover_missing_anylogic_orders(forklift_id, anylogic_state):
    from .models import Task

    done = anylogic_state.get('done')
    if type(done) is not int or done < 0 or not _empty_anylogic_queue(anylogic_state):
        return 0

    pending = Task.objects.filter(forklift_id=forklift_id, status=_TASK_PENDING)
    missing = pending.filter(anylogic_order_number__gt=done)
    if not missing.exists():
        return 0

    # A single empty snapshot can be taken while the model is changing states.
    confirmation = _fetch_anylogic_state()
    if confirmation is None or confirmation.get('done') != done or not _empty_anylogic_queue(confirmation):
        return 0

    if done == 0:
        missing = missing | pending.filter(anylogic_order_number=0)
    recovered = missing.update(anylogic_order_number=None, updated_at=timezone.now())
    if recovered:
        logger.info("Restored %s pending tasks missing from the AnyLogic queue", recovered)
    return recovered


def dispatch_next_task(anylogic_state, forklift):
    from .models import Task

    cell_names = [cell['name'] for cell in anylogic_state.get('cells', [])]
    task_id = Task.objects.filter(
        forklift=forklift, status=_TASK_PENDING, anylogic_order_number__isnull=True,
        source_cell_name__in=cell_names, dest_cell_name__in=cell_names,
    ).values_list('pk', flat=True).first()
    if task_id is not None:
        dispatch_task(task_id, anylogic_state)


@transaction.atomic
def dispatch_task(task_id, anylogic_state):
    from .models import Task

    done = anylogic_state.get('done')
    pending = anylogic_state.get('pending')
    forklifts = anylogic_state.get('forklifts', [])
    if type(done) is not int or type(pending) is not int or min(done, pending) < 0 or not forklifts:
        return

    task = Task.objects.select_for_update().filter(
        pk=task_id, status=_TASK_PENDING, anylogic_order_number__isnull=True,
    ).first()
    if task is None:
        return

    cells = {cell['name']: cell['id'] for cell in anylogic_state.get('cells', [])}
    if task.source_cell_name not in cells or task.dest_cell_name not in cells:
        logger.warning("AnyLogic cells missing for task %s", task_id)
        return

    # /order returns only ok. Use the current FIFO position and the model's completion counter.
    active = sum(
        forklift.get('state') in _AL_TASK_WORKING_STATES
        or (forklift.get('state') == _AL_DEFAULT_STATE and forklift.get('busy') is True)
        for forklift in forklifts
    )
    order_number = done + pending + active + 1
    try:
        response = http_requests.post(
            f'{ANYLOGIC_URL}/order',
            json={
                'sourceCellId': cells[task.source_cell_name],
                'destCellId': cells[task.dest_cell_name],
            },
            timeout=ANYLOGIC_ORDER_TIMEOUT_SECONDS,
            proxies=HTTP_PROXIES,
        )
    except http_requests.ConnectTimeout:
        logger.warning("Could not connect to AnyLogic to send task %s", task_id)
        return
    except http_requests.RequestException as exc:
        # The server may have accepted the POST before the response was lost.
        logger.warning("Unknown AnyLogic dispatch outcome for task %s: %s", task_id, exc)
        order_number = 0
    else:
        try:
            result = response.json()
        except ValueError:
            result = None
        if response.ok and isinstance(result, dict) and result.get('ok') is True:
            logger.info("AnyLogic accepted task %s as order %s", task_id, order_number)
        elif isinstance(result, dict) and result.get('ok') is False:
            logger.warning("AnyLogic rejected task %s: %s", task_id, result.get('error'))
            return
        else:
            logger.warning("Unknown AnyLogic response for task %s: HTTP %s", task_id, response.status_code)
            order_number = 0

    task.anylogic_order_number = order_number
    task.save(update_fields=['anylogic_order_number', 'updated_at'])


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
