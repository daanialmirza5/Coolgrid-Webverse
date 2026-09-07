# API Reference

Base URL: `http://localhost:8000`. All routes except `/health` and `/api/auth/*` require `Authorization: Bearer <access_token>`. Interactive docs at `/docs` (Swagger) and `/redoc`.

## Auth (`/api/auth`)

| Method | Path | Description |
|---|---|---|
| POST | `/register` | Create account (starts as `viewer` role). Returns tokens + user. |
| POST | `/login` | Returns access + refresh tokens + user. |
| POST | `/refresh` | Exchange a refresh token for a new token pair. |
| POST | `/logout` | Audit-logs the logout. Stateless JWTs — client discards tokens. |
| POST | `/forgot-password` | Issues a reset token. **Demo mode**: returned directly in the response (no email provider configured) instead of emailed. |
| POST | `/reset-password` | Consumes a reset token, sets a new password. |
| GET | `/me` | Current user. |

## Users (`/api/users`)

| Method | Path | Description |
|---|---|---|
| PATCH | `/me` | Update full name / organization. |
| POST | `/me/change-password` | Requires current password. |

## Geo (`/api`)

| Method | Path | Description |
|---|---|---|
| GET | `/cities` | List cities (one demo city). |
| GET | `/cities/{id}` | City detail (name, bbox, is_demo). |
| GET | `/cities/{id}/wards` | All wards for a city. |
| GET | `/cities/{id}/wards.geojson` | Ward polygons as a GeoJSON FeatureCollection. |
| GET | `/wards/{id}` | Single ward. |

## Heat / Hotspots / Drivers / Predictions (`/api`)

| Method | Path | Description |
|---|---|---|
| GET | `/dashboard/summary?city_id=` | Avg/max LST, hotspot count, population exposed, vegetation/built-up %. |
| GET | `/hotspots?city_id=&risk=` | Ranked hotspot list, optional `risk` filter (LOW/MODERATE/HIGH/CRITICAL). |
| GET | `/wards/{id}/hotspot` | Today's hotspot record for one ward. |
| GET | `/wards/{id}/drivers` | SHAP driver attribution + narrative for one ward. |
| GET | `/wards/{id}/predictions` | 1/7/30-day LST forecast with confidence ranges. |
| GET | `/comparison/wards?city_id=` | Full comparison table across all wards. |

## Simulation (`/api`)

| Method | Path | Description |
|---|---|---|
| GET | `/interventions/catalog` | The 6 intervention types with cost/land/water/max-coverage metadata. |
| POST | `/simulations` | Body: `{ward_id, interventions: [{type, coverage_pct}]}`. Runs the physics simulation, persists and returns the result. |
| GET | `/simulations/{id}` | Fetch a past simulation result. |

## Optimization / Recommendations (`/api`)

| Method | Path | Description |
|---|---|---|
| POST | `/optimizations` | Body: `{ward_id, budget_usd, land_km2, water_m3_per_year, target_cooling_c?, population_priority?, risk_priority?}`. Returns up to 5 ranked strategies; also persists `Recommendation` rows. |
| GET | `/wards/{id}/recommendations` | Recommendations generated from the most recent optimization runs for this ward. |

## Reports (`/api`)

| Method | Path | Description |
|---|---|---|
| POST | `/reports` | Body: any of `{ward_id, city_id, simulation_id, optimization_run_id, title}`. Generates a PDF synchronously and returns its status. |
| GET | `/reports` | Reports created by the current user. |
| GET | `/reports/{id}` | Single report metadata. |
| GET | `/reports/{id}/download` | The PDF file (requires the `Authorization` header — the frontend fetches it as a blob rather than a plain link, since a plain `<a href>` navigation never attaches a Bearer token). |

## Data Sources (`/api/datasources`)

| Method | Path | Description |
|---|---|---|
| GET | `/status` | Per-domain provider status (all `is_demo: true` in this deployment), detection model version/metrics, whether the PINN is trained. |

## Admin (`/api/admin`, admin role required)

| Method | Path | Description |
|---|---|---|
| GET | `/system-status` | DB connectivity, table counts, model run history, data source status. |
| GET | `/users` | All users. |
| PATCH | `/users/{id}` | Change a user's role / active status. |
| GET | `/audit-logs?limit=` | Recent audit log entries (login, register, run_simulation, run_optimization, etc.). |

## Error Format

Errors return `{"detail": "<message>"}` with an appropriate status code (400/401/403/404/409/422/500). 422 responses (FastAPI/Pydantic validation errors) return the standard `{"detail": [{"loc": ..., "msg": ..., "type": ...}]}` array format.
