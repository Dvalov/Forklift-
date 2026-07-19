---
phase: 9
plan: "09-02"
subsystem: backend-django
tags: [models, migrations, serializers, django, a-star, simulation]
dependency_graph:
  requires: [09-01]
  provides: [Forklift.speed field, Task.path_waypoints field, migration-0005, serializer-speed, serializer-path-waypoints]
  affects: [forklift_dashboard API, Wave 2 scheduler, Wave 2 A* engine, Phase 10 frontend live data]
tech_stack:
  added: []
  patterns: [Django JSONField with callable default, DRF read_only_fields for API write protection]
key_files:
  created:
    - forklift_dashboard/forklift_dashboard_app/migrations/0005_task_path_waypoints_forklift_speed.py
  modified:
    - forklift_dashboard/forklift_dashboard_app/models.py
    - forklift_dashboard/forklift_dashboard_app/serializers.py
decisions:
  - "Migration 0005 created manually (not via makemigrations) to match exact field order in plan"
  - "path_waypoints marked read_only in TaskSerializer — only the scheduler writes waypoints, not API clients"
  - "default=list (callable) used for path_waypoints JSONField to avoid shared mutable default across instances"
metrics:
  duration: "~10 minutes"
  completed: "2026-07-09"
  tasks_completed: 2
  tasks_total: 2
---

# Phase 9 Plan 02: Model Fields + Migration 0005 + Serializer Updates Summary

Added two database fields required by the Wave 2 A* scheduler and simulation engine: `Forklift.speed` for movement velocity and `Task.path_waypoints` for storing computed route waypoints.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add speed to Forklift model and path_waypoints to Task model | b0d8e9b | models.py |
| 2 | Create migration 0005 and update both serializers | 40926ae | migrations/0005_..., serializers.py |

## What Was Built

**Forklift.speed (FloatField, default=1.0)** — movement speed in tiles per second. Wave 2 A* scheduler uses this to calculate ETA and simulation step timing.

**Task.path_waypoints (JSONField, default=list)** — stores the computed A* path as a list of `{"x": int, "z": int}` dicts. The scheduler writes waypoints after computing the route; the frontend (Phase 10) reads them for live route visualization.

**Migration 0005** — manually created file depending on `0004_forklift_charge_level`. Applies `AddField` for both new columns. All 5 forklift_dashboard_app migrations verified applied (`[X]`).

**Serializer updates:**
- `ForkliftSerializer.Meta.fields`: added `'speed'` after `'position_z'`
- `TaskSerializer.Meta.fields`: added `'path_waypoints'` after `'dest_cell_z'`
- `TaskSerializer.Meta.read_only_fields`: added `'path_waypoints'` — DRF ignores client-supplied values on write (STRIDE threat T-09-02-01 mitigated)

## Deviations from Plan

None — plan executed exactly as written.

## Threat Surface Scan

No new network endpoints, auth paths, or trust boundaries introduced. The `path_waypoints` field is read-only in `TaskSerializer` as required by threat T-09-02-01 (Tampering mitigation). No threat flags.

## Known Stubs

None — no placeholder data, no hardcoded empty values flowing to UI.

## Self-Check: PASSED

- [X] `forklift_dashboard/forklift_dashboard_app/models.py` — Forklift.speed and Task.path_waypoints present
- [X] `forklift_dashboard/forklift_dashboard_app/migrations/0005_task_path_waypoints_forklift_speed.py` — created and applied
- [X] `forklift_dashboard/forklift_dashboard_app/serializers.py` — speed and path_waypoints in correct serializers
- [X] Commit b0d8e9b exists (Task 1)
- [X] Commit 40926ae exists (Task 2)
- [X] All 5 forklift_dashboard_app migrations applied
- [X] `Forklift().speed == 1.0` verified
- [X] `Task().path_waypoints == []` verified
- [X] `path_waypoints` in `TaskSerializer.Meta.read_only_fields`
- [X] `path_waypoints` default is `list` callable (not mutable `[]`)
