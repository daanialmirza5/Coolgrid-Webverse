# Demo Mode & Judging Flow

## Demo Mode

CoolGrid runs entirely on synthetic DEMO DATA (see [DATA.md](DATA.md)) — no paid API keys, no external data credentials, no internet access required for the core detect→explain→predict→simulate→optimize flow (the map even avoids depending on an external basemap host — see [ARCHITECTURE.md](ARCHITECTURE.md)). Every screen that surfaces demo-derived numbers carries a visible "DEMO DATA" badge or note.

The app's internal "today" is pinned to a fixed pre-monsoon peak-heat date (`2026-04-20`, see `backend/app/core/config.py`'s `demo_reference_date`) rather than the real calendar date, specifically so the demo **reliably** shows a dramatic, hotspot-rich scenario regardless of what day it's actually run on — CoolGrid's demo climatology has a real seasonal cycle (including a cooler monsoon season), and without this pin the dashboard could show zero hotspots if run in September.

Demo accounts (seeded by `backend/app/seed.py`):

| Role | Email | Password |
|---|---|---|
| Analyst | `demo@coolgrid.app` | `CoolGrid#Demo2026` |
| Admin | `admin@coolgrid.app` | `CoolGrid#Admin2026` |

## Recommended Judging Flow (5–10 minutes)

This is the flow the app is optimized for — every step below has been verified against a real headless-browser run of the actual app.

1. **Landing → Sign in** as the demo analyst. *"This is CoolGrid — detect, explain, predict, simulate, and optimize urban heat interventions."*
2. **Dashboard**: *"Here's the city heat situation"* — average/max LST, high/critical ward count, population exposed, vegetation/built-up %, a live map preview, and top hotspots.
3. **Heat Map**: *"Here are the hotspots"* — toggle between LST, Risk Level, Vegetation, Built-up, and Population layers; click a ward to jump into its detail.
4. **Hotspot Detail**: current LST + range, heat score, city rank, confidence, top-3 driver preview, ward profile (built-up density, vegetation, albedo, road density, population).
5. **Driver Analysis**: *"Here's why this hotspot is hot"* — full SHAP-ranked driver chart, color-coded warms/cools, with a plain-English narrative.
6. **Predictions**: *"Here's what we predict"* — 1/7/30-day LST forecast chart with widening confidence error bars, explicit "not a guaranteed outcome" disclaimer.
7. **Simulation**: *"Now let's test interventions"* — adjust the 6 intervention sliders (e.g. 30% urban trees + 40% cool roofs), run the simulation, see baseline→simulated cooling, cost, land, water, population benefited, and risk-level change.
8. **Optimization**: *"Now let CoolGrid optimize the plan"* — set budget/land/water/priority constraints, run the optimizer, see the top 5 ranked strategies with natural-language reasons.
9. **Recommendations**: the persisted, ranked recommendations for this ward, generated directly from the optimization results.
10. **Ward Comparison**: the full city ranked by LST, colored by risk, with a sortable detail table.
11. **Reports**: generate a city-wide or ward-scoped PDF (executive summary → heat situation → drivers → predictions → optimization → recommended actions → data sources → methodology) and download it.
12. **Data Sources**: confirm every domain is running in DEMO mode, see the detection model's live metrics and PINN training status.
13. **Admin** (if signed in as admin): system status, user management, audit log.
14. **Logout** → confirm the dashboard now redirects back to `/login`.

## What to Say About the Physics

CoolGrid isn't just calling an LLM or drawing from a lookup table — the cooling numbers in Simulation and Optimization come from re-solving a real (simplified, documented) surface energy balance under the intervention's perturbed surface attributes, with Monte Carlo weather sampling for genuine confidence intervals. See the Physics section of [ML.md](ML.md) for exactly what's modeled and what's a documented simplification.
