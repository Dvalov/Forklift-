---
phase: 22-hydraulics-live-data
plan: "02"
subsystem: frontend
tags: [react, typescript, tanstack-query, hydraulics, live-data]

# Dependency graph
requires:
  - phase: 22-01
    provides: Forklift model + serializer with 7 hydraulics fields via GET /api/forklifts/{id}/
provides:
  - Forklift TypeScript interface extended with 7 hydraulics fields
  - InstrumentPanel.HydraulicsPanel wired to live forklift polling (useForkliftQuery)
  - MOCK.hydraulics removed — no more static hydraulics data in InstrumentPanel
affects:
  - Instruments tab: HydraulicsPanel now shows real-time values from backend

# Tech tracking
tech-stack:
  added: []
  patterns:
    - forklift?.field ?? defaultValue — optional chaining with fallback for live API data before first poll

key-files:
  created: []
  modified:
    - frontend/src/types/api.ts
    - frontend/src/components/Instruments/InstrumentPanel.tsx

key-decisions:
  - "node_modules symlink (junction) created in worktree frontend/ -> main repo frontend/node_modules — standard git worktree pattern when node_modules are gitignored"
  - "HydraulicsPanel status prop: forklift?.status === 'moving' ? 'Работает' : 'Стоит' — covers idle/loading/error/stopped as non-moving"
  - "Default fallback values: pressure=0, oilTemp=20, forkHeight=0, tilt=0, pumpRpm=0, valvesOk=true, oilLevel=100 — safe display before first API response"

requirements-completed: [HYD-03]

# Metrics
duration: 7min
completed: 2026-11-03
---

# Phase 22 Plan 02: Hydraulics Live Data — TypeScript types + InstrumentPanel wiring Summary

**TypeScript Forklift interface extended with 7 hydraulics fields; HydraulicsPanel wired to live useForkliftQuery data, MOCK.hydraulics removed**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-11-03T18:18:00Z
- **Completed:** 2026-11-03T18:25:30Z
- **Tasks:** 2
- **Files modified:** 2 (api.ts, InstrumentPanel.tsx)

## Accomplishments

- `Forklift` interface in `api.ts` now includes all 7 hydraulics fields: `hydraulic_pressure`, `oil_temp`, `fork_height`, `tilt`, `pump_rpm`, `valves_ok`, `oil_level`
- `InstrumentPanel.tsx`: `<HydraulicsPanel>` now receives live props from `forklift` data returned by `useForkliftQuery()`
- `MOCK.hydraulics` object removed from `InstrumentPanel` — hydraulics values no longer static
- `npx tsc --noEmit` exits 0 in both tasks
- Status derivation: `'moving'` -> `'Работает'`, any other status -> `'Стоит'`

## Task Commits

Each task was committed atomically:

1. **T-01: Extend Forklift TypeScript interface** — `f0d4da9` (feat) — `frontend/src/types/api.ts`
2. **T-02: Wire HydraulicsPanel to live forklift data** — `4eb90fc` (feat) — `frontend/src/components/Instruments/InstrumentPanel.tsx`

## Files Created/Modified

- `frontend/src/types/api.ts` — added 7 hydraulics fields after `speed` in `interface Forklift`
- `frontend/src/components/Instruments/InstrumentPanel.tsx` — replaced `<HydraulicsPanel {...MOCK.hydraulics} />` with live props; removed `hydraulics` key from MOCK object

## Decisions Made

- `node_modules` junction created in worktree `frontend/` pointing to main repo `frontend/node_modules` — git worktrees don't replicate gitignored directories; junction is the standard workaround to run `tsc` in the worktree context
- Default fallback values for `??` operators: pressure=0, oilTemp=20 (ambient), forkHeight=0, tilt=0, pumpRpm=0, valvesOk=true, oilLevel=100 — these show safe neutral state before first API poll completes

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] node_modules missing in git worktree**
- **Found during:** T-01 (running `npx tsc --noEmit`)
- **Issue:** `npx tsc` resolved to an npm shim that refused to run without local TypeScript install; worktree has no `node_modules` (gitignored directories not linked by git worktree)
- **Fix:** Created Windows junction `frontend/node_modules` -> main repo `frontend/node_modules`; verified `./node_modules/.bin/tsc --noEmit` exits 0
- **Files modified:** None (junction is a filesystem artifact, not tracked by git)
- **Committed in:** Not committed (filesystem junction, no project file changed)

---

**Total deviations:** 1 auto-fixed (1 blocking — missing node_modules in worktree)
**Impact on plan:** Minimal. Junction creation was a one-liner; TypeScript verification ran correctly after.

## Known Stubs

None — hydraulics values now come directly from live API data via `useForkliftQuery()`.

## Threat Flags

None — this plan is frontend-only (TypeScript interface extension + component re-wiring). No new network endpoints, auth paths, or schema changes introduced.

## Self-Check

- [x] `frontend/src/types/api.ts` — hydraulics fields present
- [x] `frontend/src/components/Instruments/InstrumentPanel.tsx` — live props wired
- [x] Commit f0d4da9 exists (T-01)
- [x] Commit 4eb90fc exists (T-02)
- [x] `MOCK.hydraulics` removed from InstrumentPanel
- [x] `npx tsc --noEmit` exits 0

## Self-Check: PASSED

## Next Phase Readiness

- Phase 22 complete: backend (22-01) + frontend (22-02) both done
- HydraulicsPanel shows live pressure, RPM, oil temp on every poll cycle (~3–5 s)
- No further hydraulics work planned in v8.0 milestone
