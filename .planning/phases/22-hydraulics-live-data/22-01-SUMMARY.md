---
phase: 22-hydraulics-live-data
plan: "01"
subsystem: api
tags: [django, python, postgresql, psycopg2, apscheduler, drf, hydraulics]

# Dependency graph
requires:
  - phase: 21-anylogic-integration-fixes
    provides: stable scheduler simulation_tick with charge_level and path_waypoints
provides:
  - Forklift model with 7 hydraulics fields (hydraulic_pressure, oil_temp, fork_height, tilt, pump_rpm, valves_ok, oil_level)
  - ForkliftSerializer exposes all 7 hydraulics fields in GET /api/forklifts/{id}/
  - ForkliftUpdateSerializer accepts hydraulics fields for PATCH requests
  - simulation_tick simulates realistic hydraulics during active movement and resets to idle state
affects:
  - 22-02 (frontend HydraulicsPanel reads these fields via API polling)

# Tech tracking
tech-stack:
  added: [psycopg2-binary (installed in environment for PostgreSQL connectivity)]
  patterns: [Scheduler mutates forklift hydraulics fields inline before forklift.save()]

key-files:
  created: []
  modified:
    - forklift_dashboard/forklift_dashboard_app/models.py
    - forklift_dashboard/forklift_dashboard_app/serializers.py
    - forklift_dashboard/forklift_dashboard_app/scheduler.py

key-decisions:
  - "Hydraulics fields were already present in models.py from prior commit cb0ca50 — T-01 was a no-op, migration was the first actual change"
  - "Migration files remain gitignored per project convention (commit 6b8c4b3 added **/migrations/ to .gitignore) — migration runs locally only"
  - "On task completion tick: active movement hydraulics are saved first (forklift.save()), then idle reset is applied and saved again — two saves on last tick, correct behavior"
  - "psycopg2-binary installed in system Python environment to unblock Django from starting without a virtual environment"

patterns-established:
  - "Hydraulics simulation: random.uniform(142.0, 158.0) for pressure, random.randint(2750, 2900) for RPM during movement"
  - "Oil temperature ramps up +0.2/tick during movement, cools down -0.1/tick at idle, clamped to [20.0, 80.0]"

requirements-completed: [HYD-01, HYD-02]

# Metrics
duration: 15min
completed: 2026-11-03
---

# Phase 22 Plan 01: Hydraulics Fields — Django Model + Migration + Serializer + Scheduler Summary

**7 hydraulics fields added to Forklift model and serializers; simulation_tick now drives pressure/RPM during movement and resets to zero on task completion**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-11-03T17:38:00Z
- **Completed:** 2026-11-03T17:53:00Z
- **Tasks:** 4
- **Files modified:** 2 (serializers.py, scheduler.py — models.py was pre-committed)

## Accomplishments

- Migration 0003 created and applied — 7 new columns in forklift table in PostgreSQL
- `ForkliftSerializer` and `ForkliftUpdateSerializer` now include all 7 hydraulics fields
- `simulation_tick` simulates realistic hydraulic pressure (142–158 bar) and pump RPM (2750–2900) during active task movement
- Oil temperature ramps up during movement and cools on idle; oil_level drains slowly per tick
- `python manage.py check` passes with 0 issues; all migrations show `[X]`

## Task Commits

Each task was committed atomically:

1. **T-01: Add hydraulics fields to Forklift model** — `cb0ca50` (feat) — *pre-existing, fields already committed*
2. **T-02: Create and run migration** — migration file gitignored per project convention; migration applied to DB
3. **T-03: Add fields to ForkliftSerializer and ForkliftUpdateSerializer** — `dd94c42` (feat)
4. **T-04: Simulate hydraulics values in scheduler simulation_tick** — `f095686` (feat)

**Plan metadata:** (committed below)

## Files Created/Modified

- `forklift_dashboard/forklift_dashboard_app/models.py` — 7 hydraulics fields already present from prior commit
- `forklift_dashboard/forklift_dashboard_app/serializers.py` — appended 7 fields to both ForkliftSerializer and ForkliftUpdateSerializer
- `forklift_dashboard/forklift_dashboard_app/scheduler.py` — added `import random`; active movement hydraulics block; idle hydraulics reset block

## Decisions Made

- Migration files are gitignored project-wide (`**/migrations/` in `.gitignore`). The migration was created and applied locally but not committed. This is consistent with prior project commits (`6b8c4b3`).
- `psycopg2-binary` installed in the system Python environment — it was missing, causing `manage.py check` to crash before any Django command could run.
- On the final task waypoint tick, hydraulics go active (save) then immediately reset to idle (save again). This is two DB writes but correct: the forklift shows pressure on last move, then idles.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] psycopg2-binary not installed**
- **Found during:** T-02 (running migrations)
- **Issue:** `python manage.py check` crashed with `ImproperlyConfigured: Error loading psycopg2 or psycopg module`
- **Fix:** Ran `pip install psycopg2-binary`; Django check passes after install
- **Files modified:** None (system package install)
- **Verification:** `python manage.py check` exits 0 with no warnings
- **Committed in:** Not committed (package install, no project file changed)

---

**Total deviations:** 1 auto-fixed (1 blocking — missing system dependency)
**Impact on plan:** Minimal. psycopg2-binary install was necessary to run any manage.py command. No scope creep.

### Pre-existing State Note

T-01 (add hydraulics fields to models.py) was already completed in a prior session — commit `cb0ca50 feat(22-01): add 7 hydraulics fields to Forklift model` predates this execution. The migration had not yet been run, so T-02 still created migration `0003` and applied it successfully.

## Issues Encountered

- `python -c "from forklift_dashboard_app.models import Forklift..."` failed without `DJANGO_SETTINGS_MODULE` set — fixed by using `DJANGO_SETTINGS_MODULE=forklift_dashboard.settings python -c "import django; django.setup()..."` form

## User Setup Required

None — no external service configuration required. The PostgreSQL database connection was already configured in `forklift_dashboard/.env`.

## Next Phase Readiness

- Backend fully ready: `GET /api/forklifts/1/` returns `hydraulic_pressure`, `oil_temp`, `fork_height`, `tilt`, `pump_rpm`, `valves_ok`, `oil_level`
- Scheduler drives non-zero pressure and RPM while a task is in_progress
- Phase 22-02 (HydraulicsPanel frontend component) can now poll these fields from the live API

---
*Phase: 22-hydraulics-live-data*
*Completed: 2026-11-03*
