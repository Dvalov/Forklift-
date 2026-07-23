import atexit
import logging

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
        seconds=1,
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
        from .models import Forklift, Task

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

        in_progress = Task.objects.filter(forklift=forklift, status='in_progress').first()

        if not in_progress:
            pending = Task.objects.filter(forklift=forklift, status='pending').first()
            if pending:
                path = _fetch_path(
                    forklift_id=forklift_id, warehouse_id=warehouse_id,
                    from_x=forklift.cell_x, from_y=forklift.cell_y, from_z=forklift.cell_z,
                    dest_x=pending.dest_cell_x, dest_y=pending.dest_cell_y, dest_z=pending.dest_cell_z,
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
            waypoints = list(in_progress.path_waypoints)
            next_wp = waypoints.pop(0)

            forklift.cell_x = round(next_wp['x'])
            forklift.cell_y = round(next_wp.get('y', forklift.cell_y))
            forklift.cell_z = round(next_wp['z'])
            forklift.charge_level = max(0.0, forklift.charge_level - DISCHARGE_RATE)

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
                forklift.save()
                logger.info(
                    "Task %s completed; forklift now idle at cell (%s, %s)",
                    in_progress.pk, forklift.cell_x, forklift.cell_z,
                )
            else:
                in_progress.save()

    except Exception:
        logger.exception("Unhandled error in simulation_tick")


def _fetch_real_coords(warehouse_id, cell_x, cell_y, cell_z):
    """Call Converter convert_cell_address and return {"x", "y", "z"} in metres, or None on error."""
    try:
        url = f"http://localhost:8002/api/converter/{warehouse_id}/cells/convert/"
        resp = http_requests.get(url, params={'x': cell_x, 'y': cell_y, 'z': cell_z},
                                 timeout=0.5, proxies={'http': None, 'https': None})
        resp.raise_for_status()
        data = resp.json()
        return {'x': data['x'], 'y': data['y'], 'z': data['z']}
    except Exception:
        logger.warning("Could not convert cell (%s,%s,%s) to real coords", cell_x, cell_y, cell_z)
        return None


def _fetch_path(forklift_id, warehouse_id, from_x, from_y, from_z, dest_x, dest_y, dest_z):
    """Call Converter get_cell_path and return list of {"x", "y", "z"} waypoints, or None on error."""
    try:
        url = f"http://localhost:8002/api/converter/{warehouse_id}/cells/get_path/"
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
        logger.exception("Failed to fetch path from Converter at %s", url)
        return None
