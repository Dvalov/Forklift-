import atexit
import logging
import os
import random

import requests as http_requests
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings

logger = logging.getLogger(__name__)

DISCHARGE_RATE = 0.5  # charge_level units lost per tick of movement

_scheduler = None


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        simulation_tick,
        trigger='interval',
        seconds=0.5,
        id='forklift_simulation',
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    atexit.register(lambda: _scheduler.shutdown(wait=False))
    logger.info("APScheduler started — simulation_tick running every 1s")


def simulation_tick():
    try:
        from .models import Forklift

        forklift_id = getattr(settings, 'FORKLIFT_ID', None)
        warehouse_id = getattr(settings, 'WAREHOUSE_ID', None)

        if not forklift_id:
            logger.warning("FORKLIFT_ID not set in settings; simulation_tick skipped")
            return

        try:
            forklift = Forklift.objects.get(pk=forklift_id)
        except Forklift.DoesNotExist:
            logger.error("Forklift pk=%s not found in DB", forklift_id)
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

_AL_TASK_WORKING_STATES = {'GoToSource', 'PickUp', 'GoToDest', 'PutDown'}  # если одно из этих состояний, задача остается pending
_AL_START_NEW_TASK_STATES = {'ReturnToBase', 'Idle', 'Complete'}  # если Complete, Idle или ReturnToBase — переводим in_progress в completed и пулим pending
# в каком бы состоянии ни был погрузчик, задача всегда добавляется в статусе pending
_AL_SERVICE_MOVING_STATES = {'GoToCharger'}
_AL_MOVING_STATES = _AL_TASK_WORKING_STATES | _AL_SERVICE_MOVING_STATES | {'ReturnToBase'}
_AL_IDLE_STATES = {'Idle', 'Complete', 'Charging'}

_AL_STATE_TO_DJANGO: dict[str, str] = {
    'Idle':         'idle',
    'GoToSource':   'moving',
    'PickUp':       'moving',
    'GoToDest':     'moving',
    'PutDown':      'moving',
    'Complete':     'idle',
    'Charging':     'charging',
    'GoToCharger':  'moving',
    'ReturnToBase': 'moving',
}

_last_dispatched_task_id: int | None = None


def _tick_anylogic_mode(forklift, anylogic_state):
    global _last_dispatched_task_id
    from .models import Task

    forklifts = anylogic_state.get('forklifts', [])
    al_fl = forklifts[0] if forklifts else None
    al_state = al_fl.get('state', 'Idle') if al_fl else 'Idle'
    django_status = _AL_STATE_TO_DJANGO.get(al_state, 'idle')

    in_progress = Task.objects.filter(forklift=forklift, status='in_progress').first()

    # 1. Task Lifecycle Management
    if al_state in _AL_TASK_WORKING_STATES:
        # Forklift actively executing a task in AnyLogic; reset dispatched tracker
        _last_dispatched_task_id = None
        # Если одно из этих состояний, задача остается pending

    elif al_state in _AL_START_NEW_TASK_STATES:
        # Если статус Complete, Idle или ReturnToBase:
        # Случай 1: есть текущая задача in_progress -> переводим в completed
        if in_progress:
            if in_progress.pk != _last_dispatched_task_id:
                in_progress.status = 'completed'
                in_progress.save()
                logger.info("Task %s completed (AnyLogic mode, state=%s)", in_progress.pk, al_state)
                in_progress = None
                _last_dispatched_task_id = None
            else:
                # Задача только что отправлена в AnyLogic и ожидает перехода в рабочее состояние
                return

        # Случай 2: нету текущей задачи в статусе in_progress (или только что завершили)
        # -> просто берем задачу pending и переводим ее в in_progress
        _last_dispatched_task_id = None
        _dispatch_next_task(anylogic_state, forklift)

    # 2. Forklift Status & Telemetry Sync
    if al_state in _AL_MOVING_STATES:
        forklift.status = django_status
        forklift.speed = 1.0
        forklift.charge_level = al_fl.get('charge', forklift.charge_level) if al_fl else forklift.charge_level
        forklift.fork_height = 1.0 if al_state in ('PickUp', 'PutDown') else 0.0
        forklift.hydraulic_pressure = round(random.uniform(142.0, 158.0), 1)
        forklift.oil_temp = round(min(80.0, forklift.oil_temp + 0.2), 1)
        forklift.pump_rpm = random.randint(2750, 2900)
        forklift.valves_ok = True
        forklift.oil_level = round(max(0.0, forklift.oil_level - 0.01), 2)
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
            forklift.oil_temp = round(max(20.0, forklift.oil_temp - 0.1), 1)
            forklift.save()


# ---------------------------------------------------------------------------
# Django mode — full A* simulation when AnyLogic is unavailable
# ---------------------------------------------------------------------------

def _tick_django_mode(forklift, forklift_id, warehouse_id):
    from .models import Task

    in_progress = Task.objects.filter(forklift=forklift, status='in_progress').first()

    if not in_progress:
        pending = Task.objects.filter(forklift=forklift, status='pending').first()
        if pending:
            path = _fetch_path(
                forklift_id=forklift_id, warehouse_id=warehouse_id,
                from_x=forklift.cell_x, from_y=forklift.cell_y, from_z=forklift.cell_z,
                dest_x=2 * pending.dest_cell_x - 1, dest_y=pending.dest_cell_y, dest_z=pending.dest_cell_z,
            )
            if path is None:
                logger.error(
                    "Could not fetch path for task %s (%s,%s,%s)->(%s,%s,%s)",
                    pending.pk,
                    forklift.cell_x, forklift.cell_y, forklift.cell_z,
                    pending.dest_cell_x, pending.dest_cell_y, pending.dest_cell_z,
                )
                return

            if path == []:
                pending.status = 'completed'
                pending.path_waypoints = []
                pending.save()
                forklift.status = 'idle'
                forklift.speed = 0.0
                forklift.save()
                logger.info("Task %s completed immediately (forklift already at destination)", pending.pk)
                return

            pending.path_waypoints = path
            pending.status = 'in_progress'
            pending.save()
            forklift.status = 'moving'
            forklift.speed = 1.0
            forklift.save()
            in_progress = pending
            logger.info("Task %s picked up; path has %d waypoints", pending.pk, len(path))

    if in_progress and in_progress.path_waypoints:
        from django.utils import timezone
        from datetime import timedelta
        if (in_progress.frontend_advanced_at and
                timezone.now() - in_progress.frontend_advanced_at < timedelta(seconds=2)):
            logger.debug("Task %s: frontend driving, skipping backend tick", in_progress.pk)
            return

        waypoints = list(in_progress.path_waypoints)
        next_wp = waypoints.pop(0)

        forklift.cell_x = round(next_wp['x'])
        forklift.cell_y = round(next_wp.get('y', forklift.cell_y))
        forklift.cell_z = round(next_wp['z'])

        forklift.charge_level = max(0.0, forklift.charge_level - DISCHARGE_RATE)
        forklift.hydraulic_pressure = round(random.uniform(142.0, 158.0), 1)
        forklift.oil_temp = round(min(80.0, forklift.oil_temp + 0.2), 1)
        forklift.pump_rpm = random.randint(2750, 2900)
        forklift.valves_ok = True
        forklift.oil_level = round(max(0.0, forklift.oil_level - 0.01), 2)

        real = _fetch_real_coords(warehouse_id, forklift.cell_x, forklift.cell_y, forklift.cell_z)
        if real:
            forklift.position_x = real['x']
            forklift.position_y = real['y']
            forklift.position_z = real['z']

        forklift.save()

        in_progress.path_waypoints = waypoints
        if not waypoints:
            in_progress.status = 'completed'
            in_progress.save()
            forklift.status = 'idle'
            forklift.speed = 0.0
            forklift.hydraulic_pressure = 0.0
            forklift.pump_rpm = 0
            forklift.oil_temp = round(max(20.0, forklift.oil_temp - 0.1), 1)
            forklift.save()
            logger.info(
                "Task %s completed; forklift now idle at cell (%s, %s)",
                in_progress.pk, forklift.cell_x, forklift.cell_z,
            )
        else:
            in_progress.save()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dispatch_next_task(anylogic_state, forklift):
    """Send the next pending task to AnyLogic /order if one exists and not yet dispatched."""
    global _last_dispatched_task_id
    from .models import Task
    next_task = Task.objects.filter(forklift=forklift, status='pending').first()
    if not next_task or next_task.pk == _last_dispatched_task_id:
        return

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
        anylogic_url = os.environ.get('ANYLOGIC_URL', 'http://127.0.0.1:8080')
        resp = http_requests.post(
            f'{anylogic_url}/order',
            json={'sourceCellId': al_source['id'], 'destCellId': al_dest['id']},
            timeout=0.5,
            proxies={'http': None, 'https': None},
        )
        if resp.ok:
            _last_dispatched_task_id = next_task.pk
            next_task.status = 'in_progress'
            next_task.path_waypoints = []
            next_task.save()
            logger.info(
                "Dispatched task %s to AnyLogic (source=%s→%s, dest=%s→%s), status set to in_progress",
                next_task.pk, next_task.source_cell_name, al_source['id'],
                next_task.dest_cell_name, al_dest['id'],
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
        warehouse_url = os.environ.get('WAREHOUSE_URL', 'http://localhost:8001')
        resp = http_requests.get(
            f"{warehouse_url}/api/anylogic/state",
            timeout=0.3,
            proxies={'http': None, 'https': None},
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def _fetch_real_coords(warehouse_id, cell_x, cell_y, cell_z):
    """Call Converter universal convert and return {"x", "y", "z"} in metres, or None on error."""
    try:
        converter_url = os.environ.get('CONVERTER_URL', 'http://localhost:8002')
        resp = http_requests.get(
            f"{converter_url}/api/converter/convert/",
            params={'x': cell_x, 'y': cell_y, 'z': cell_z},
            timeout=0.5, proxies={'http': None, 'https': None},
        )
        resp.raise_for_status()
        data = resp.json()
        return {'x': data['x'], 'y': data['y'], 'z': data['z']}
    except Exception:
        logger.warning("Could not convert cell (%s,%s,%s) to real coords", cell_x, cell_y, cell_z)
        return None


def _fetch_path(forklift_id, warehouse_id, from_x, from_y, from_z, dest_x, dest_y, dest_z):
    """Call Converter get_cell_path and return list of {"x", "z"} waypoints, or None on error."""
    try:
        converter_url = os.environ.get('CONVERTER_URL', 'http://localhost:8002')
        url = f"{converter_url}/api/converter/{warehouse_id}/cells/get_path/"
        resp = http_requests.get(url, params={
            'forklift_id': forklift_id,
            'warehouse_id': warehouse_id,
            'from_x': from_x, 'from_y': from_y, 'from_z': from_z,
            'dest_x': dest_x, 'dest_y': dest_y, 'dest_z': dest_z,
        }, timeout=3, proxies={'http': None, 'https': None})
        resp.raise_for_status()
        data = resp.json()
        return data.get('path', [])
    except Exception:
        logger.warning("Converter unavailable, path fetch skipped")
        return None
