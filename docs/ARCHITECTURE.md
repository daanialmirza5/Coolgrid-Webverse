# Architecture

## Overview

CoolGrid is a three-tier application: a Next.js SPA-style frontend, a FastAPI backend, and an in-process ML/physics package (`coolgrid_ml`) that the backend imports directly — there is no separate ML microservice or HTTP hop between backend and ML code.

```
┌─────────────────┐        HTTPS/JSON         ┌──────────────────────────────┐
│  Next.js 16      │ ────────────────────────▶ │  FastAPI backend              │
│  (App Router)    │ ◀──────────────────────── │  app/api/routes/*             │
│  client-rendered │        JWT bearer          │  app/services/*  (business    │
│  pages, fetch()  │                            │    logic bridging DB + ML)    │
└─────────────────┘                            │  app/models/*    (SQLAlchemy) │
                                                 └───────────┬──────────────────┘
                                                             │ import (in-process)
                                                 ┌───────────▼──────────────────┐
                                                 │  coolgrid_ml package          │
                                                 │  providers / data / detection │
                                                 │  explain / physics /          │
                                                 │  prediction / simulation /    │
                                                 │  optimization                 │
                                                 └───────────┬──────────────────┘
                                                             │
                                                 ┌───────────▼──────────────────┐
                                                 │  PostgreSQL + PostGIS         │
                                                 │  (Docker)                     │
                                                 └────────────────────────────────┘
```

## Frontend

Every page under `frontend/app/(app)/` is a Client Component (`"use client"`) that fetches directly from the FastAPI backend via `lib/api-client.ts` — this is deliberately a "strict SPA" pattern (per Next.js's own guidance for apps whose data lives entirely behind an external REST API), not server-rendered data fetching. Auth state lives in `lib/auth-context.tsx` (React context + `localStorage` JWTs); `components/layout/auth-guard.tsx` redirects unauthenticated users to `/login` client-side. `lib/use-api.ts` is a small generic hook giving every page consistent loading/success/error/retry states.

The map (`components/map/city-map.tsx`) uses MapLibre GL JS with a **self-contained inline style** (no remote basemap tiles) so the map never depends on a third-party host being reachable — ward polygons, colors, borders, and tooltips carry all the information a city planner needs. See the comment in that file and in `frontend/scripts/copy-maplibre-worker.js` for a real bug this project hit and fixed: maplibre-gl's automatic worker-script-URL detection resolves to an empty string when the library is loaded via Next.js's code-split dynamic imports, silently breaking every map source. The fix copies maplibre-gl's worker bundle into `public/` and calls `setWorkerUrl()` explicitly.

## Backend

- `app/main.py` — FastAPI app construction, CORS, global exception handlers, router registration under `/api`, and a `lifespan` hook that loads the ML registry once at startup (failing fast with a clear error if `ml/train.py` hasn't been run).
- `app/core/` — settings (`config.py`, pydantic-settings from `.env`), JWT + bcrypt (`security.py`), DB session (`database.py`), auth dependency (`deps.py`), audit logging helper (`audit.py`).
- `app/models/` — 17 SQLAlchemy tables (see README). `Ward`/`Location` use GeoAlchemy2 `Geometry` columns with GIST indexes.
- `app/schemas/` — Pydantic request/response models, one file per domain.
- `app/services/` — the actual business logic. Notably `ml_registry.py` (process-wide singleton loading trained artifacts), `detection_service.py` (builds today's feature table from providers, runs the detector, persists one HeatMap+Hotspot snapshot per demo-calendar-day, idempotently), `ward_adapter.py` (converts a DB `Ward` row into the ML package's plain `WardBase` dataclass, keeping `coolgrid_ml` free of any SQLAlchemy dependency).
- `app/api/routes/` — thin FastAPI routers; each endpoint validates input, delegates to a service, and returns a Pydantic response model.

### The demo clock

`Settings.demo_reference_date` (`backend/app/core/config.py`) pins "today" for detection/prediction/simulation purposes to a fixed pre-monsoon peak-heat date (`2026-04-20`) rather than the real system date. CoolGrid's demo climatology has a genuine Pune-like seasonal cycle (hot Mar–Jun, cooler monsoon Jun–Sep, mild winter), so anchoring to the real calendar date would mean the demo looks dramatically different (and sometimes has *zero* hotspots) depending on what day it happens to be run — a real reliability risk for a judged demo. This only changes which synthetic date's weather is sampled; it is not a fake system clock and doesn't affect timestamps elsewhere (audit logs, report generation times, etc. use the real clock).

### Detection caching

`detection_service.get_or_create_daily_heatmap()` reuses an existing `HeatMap` + `Hotspot` snapshot if one already exists for the demo reference date (checked via `Hotspot.detected_on`, not the row's real creation timestamp — see the comment in that function for why), and computes a fresh one otherwise. This keeps repeated dashboard/hotspot-list/map loads fast without re-running the detector on every request, while still being correct if the underlying ML artifacts or reference date ever change (stale snapshots are naturally superseded).

## ML/Physics Package (`coolgrid_ml`)

See [ML.md](ML.md) for the full pipeline. In one line: `providers` (demo data generation) → `data` (city grid + training dataset) → `detection` (XGBoost) → `explain` (SHAP) → `physics` (energy balance + PINN) → `prediction` (forecaster blending detection+physics) → `simulation` (intervention effect models) → `optimization` (constraint-aware portfolio ranking).

The package has zero dependency on FastAPI or SQLAlchemy — it operates on plain dataclasses (`WardBase`, etc.) and pandas DataFrames, so it's independently testable (see `ml/tests/`) and could be reused outside this backend (a CLI, a notebook, a different API).

## Database

PostgreSQL 16 + PostGIS 3.4, schema managed by Alembic. See the README's [Database](../README.md#database) section for the tiger_geocoder-filtering gotcha in `alembic/env.py` and the GeoAlchemy2 auto-index gotcha in the initial migration.

## Request Lifecycle Example: "Run a Simulation"

1. Frontend `Simulation` page collects intervention coverage sliders, calls `api.simulations.run(wardId, interventions)`.
2. `POST /api/simulations` → `simulation_service.run_simulation()`:
   - Fetches the `Ward` row, converts to `WardBase` via `ward_adapter`.
   - Builds today's feature row via `detection_service.build_current_features()` and runs the XGBoost detector to get the ward's actual current LST (the "anchor").
   - Calls `registry.simulation_engine.simulate(ward, interventions, as_of=demo_reference_date, current_lst_anchor=...)` — this re-solves the energy balance under baseline vs. perturbed surface attributes, Monte Carlo-sampling weather noise for a genuine confidence interval, then re-bases the result onto the anchor LST so it's consistent with what the dashboard/hotspot pages show for the same ward (see the docstring on `SimulationEngine.simulate` for why this re-basing exists).
   - Persists a `Simulation` row, returns the result.
3. Frontend renders baseline→simulated bar chart, cooling/cost/land/water/population metrics, and risk-level change.
