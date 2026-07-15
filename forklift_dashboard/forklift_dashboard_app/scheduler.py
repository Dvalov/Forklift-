import atexit
import logging
import os

import requests as http_requests
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings

logger = logging.getLogger(__name__)

DISCHARGE_RATE = 0.5  # charge_level units lost per tick of movement

_scheduler = None


def _find_stop_cell(dest_x: int, dest_z: int, obstacles: set, forklift_x: float, forklift_z: float) -> tuple:
    """Find the best free cell adjacent to dest to stop the forklift.

    Checks all 4 cardinal neighbors; picks the one not in obstacles that is
    closest to the forklift's current position. Falls back to dest itself
    (with dest removed from obstacles) if all neighbors are blocked.
    """
    candidates = []
    for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        neighbor = (dest_x + dx, dest_z + dz)
        if neighbor not in obstacles:
            dist = abs(neighbor[0] - forklift_x) + abs(neighbor[1] - forklift_z)
            candidates.append((dist, neighbor))

    if candidates:
        candidates.sort(key=lambda t: t[0])
        return candidates[0][1]

    return (dest_x, dest_z)  # all neighbors blocked — fall back to cell itself


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
        from .pathfinding import astar

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

        # Recovery: in_progress task with empty waypoints — run A* now
        if in_progress and not in_progress.path_waypoints:
            obstacles = _fetch_obstacles(warehouse_id)
            if obstacles is None:
                logger.error("Could not fetch warehouse cells; skipping recovery for task %s", in_progress.pk)
                return
            start = (forklift.position_x, forklift.position_z)
            goal = _find_stop_cell(
                in_progress.dest_cell_x, in_progress.dest_cell_z,
                obstacles, forklift.position_x, forklift.position_z,
            )
            path = astar(start, goal, obstacles)
            if path is None:
                logger.warning("No path for in_progress task %s; marking failed", in_progress.pk)
                in_progress.status = 'failed'
                in_progress.save()
                forklift.status = 'idle'
                forklift.speed = 0.0
                forklift.save()
                in_progress = None
            elif path == []:
                in_progress.status = 'completed'
                in_progress.save()
                forklift.status = 'idle'
                forklift.speed = 0.0
                forklift.save()
                logger.info("Task %s recovered: already at destination", in_progress.pk)
                in_progress = None
            else:
                in_progress.path_waypoints = path
                in_progress.save()
                forklift.status = 'moving'
                forklift.speed = 1.0
                forklift.save()
                logger.info("Task %s recovered; A* found %d waypoints", in_progress.pk, len(path))

        if not in_progress:
            pending = Task.objects.filter(forklift=forklift, status='pending').order_by('created_at').first()
            if pending:
                obstacles = _fetch_obstacles(warehouse_id)
                if obstacles is None:
                    logger.error("Could not fetch warehouse cells; skipping task pickup for task %s", pending.pk)
                    return

                start = (forklift.position_x, forklift.position_z)
                goal = _find_stop_cell(
                    pending.dest_cell_x, pending.dest_cell_z,
                    obstacles, forklift.position_x, forklift.position_z,
                )

                path = astar(start, goal, obstacles)

                if path is None:
                    logger.warning(
                        "No path from %s to %s for task %s; task remains pending",
                        start, goal, pending.pk
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
                logger.info("Task %s picked up; path has %d waypoints", pending.pk, len(path))
                return  # advance waypoints on the next tick so in_progress is always visible

        if in_progress and in_progress.path_waypoints:
            waypoints = list(in_progress.path_waypoints)
            next_wp = waypoints.pop(0)

            forklift.position_x = float(next_wp['x'])
            forklift.position_z = float(next_wp['z'])
            forklift.charge_level = max(0.0, forklift.charge_level - DISCHARGE_RATE)
            forklift.save()

            in_progress.path_waypoints = waypoints
            if not waypoints:
                in_progress.status = 'completed'
                in_progress.save()
                forklift.status = 'idle'
                forklift.speed = 0.0
                forklift.save()
                logger.info("Task %s completed; forklift stopped at (%s, %s)",
                            in_progress.pk, next_wp['x'], next_wp['z'])
            else:
                in_progress.save()

    except Exception:
        logger.exception("Unhandled error in simulation_tick")


def _fetch_obstacles(warehouse_id) -> set | None:
    try:
        url = f"http://localhost:8001/api/warehouse/{warehouse_id}/cells/"
        # trust_env=False bypasses Windows system proxy which returns 503 for localhost
        session = http_requests.Session()
        session.trust_env = False
        resp = session.get(url, timeout=3)
        resp.raise_for_status()
        cells = resp.json()
        return {(int(c['x']), int(c['z'])) for c in cells}
    except Exception:
        logger.exception("Failed to fetch obstacles from Warehouse API at %s", url)
        return None
