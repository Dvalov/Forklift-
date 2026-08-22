# Forklift Dashboard — Project Guide

## Project Context

React industrial dashboard for warehouse forklift operators. See `.planning/PROJECT.md` for full context.

**Core value:** Оператор видит состояние погрузчика и ставит задачи выбором ячейки — всё в одном экране.

## Architecture

Three Django services + React frontend:
- `forklift_dashboard` (port 8000) — main API: forklifts + tasks
- `Warehouse` (port 8001) — warehouse cells
- `Converter` (port 8002) — cell address → real coordinates

Frontend: `frontend/` — React 19 + TypeScript + Vite

## GSD Workflow

This project uses the GSD (Get Shit Done) workflow. Planning artifacts are in `.planning/` (gitignored).

**Current state:** See `.planning/STATE.md`
**Roadmap:** See `.planning/ROADMAP.md`
**Requirements:** See `.planning/REQUIREMENTS.md`

### Phase commands

```
/gsd:plan-phase N      — plan phase N
/gsd:execute-phase N   — execute phase N
/gsd:discuss-phase N   — discuss approach before planning
/gsd:progress          — see project status
```

### Rules

- Read `.planning/STATE.md` at the start of every session
- Never hardcode `FORKLIFT_ID` or `WAREHOUSE_ID` — use `.env` vars
- Never commit `.planning/` — it is gitignored
- Fix backend bugs (Phase 1) before any frontend API work
- All fetch calls go through `src/api/client.ts` — never call `fetch` directly in components

## Key Decisions

- Polling every 3–5s (not WebSocket) — DRF backend, no Django Channels
- Converter called from frontend during task creation — backend TaskViewSet.create() is broken
- Dark theme always-on — industrial display style
- Native fetch (no axios) — thin wrapper in `src/api/client.ts`
- TanStack Query v5 for server state, Zustand v5 for UI state

## Known Backend Bugs (Phase 1 must fix)

1. CORS absent on all 3 services → every browser request blocked
2. `TaskViewSet.create()` crashes with KeyError + IntegrityError
3. `ForkliftSerializer` missing `charge_level`
4. `TaskSerializer` missing `dest_cell_x/y/z`
5. `Task.forklift_id` ForeignKey generates `forklift_id_id` column
