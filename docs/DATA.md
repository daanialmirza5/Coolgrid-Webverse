# Data

## This is DEMO DATA

Every observation, ward polygon, and derived value in this deployment is synthetically generated. **None of it is real Landsat, Sentinel-2, ERA5, OpenStreetMap, or census data.** The UI labels this everywhere it's relevant (dashboard badge, data sources page, PDF reports).

## Why Pune-shaped

The demo city (`DEMO_CITY_NAME = "Pune (Demo Dataset)"`) uses Pune, India's approximate bounding box purely for a geographically plausible, recognizable map extent. Ward geometry is a regular 6×4 grid — **not real administrative ward boundaries** — and every attribute is generated from a fixed random seed (42) for full reproducibility.

## Generation Pipeline

1. **`ml/coolgrid_ml/data/city_grid.py`** assigns each grid cell an archetype (dense_core, residential, industrial, green_belt, riverside, peri_urban) biased by distance from the grid center (dense archetypes cluster centrally, green/peri-urban toward the edges — for a visually coherent city shape, not because it's derived from any real data). Each archetype has a profile of plausible ranges (e.g. dense_core: 75–90% built-up, 2–8% vegetation) that static attributes are sampled from.
2. **`ml/coolgrid_ml/data/climatology.py`** defines a simplified seasonal cycle for Pune (hot Mar–Jun peaking ~day 110, monsoon cooling Jun–Sep, mild winter) — a sinusoidal approximation, not a calibrated meteorological model.
3. **`ml/coolgrid_ml/providers/demo.py`** samples one shared weather draw per (ward, date) from that climatology plus Gaussian noise, then runs it through the physics energy balance (`physics/energy_balance.py`) to produce a physically-grounded "true" LST, plus NDVI/NDBI computed from the same vegetation/built-up attributes plus noise. This is what makes the built-up/vegetation/albedo → LST relationship in the training data *real* (recoverable by a model fit on it, explainable via SHAP) rather than hardcoded.
4. **`ml/coolgrid_ml/data/dataset.py`** samples this across ~80 dates × 24 wards (stride 3 over 240 days) to build the training table.
5. **`ml/train.py`** orchestrates all of the above, trains the models, and exports everything to `data/demo/`.
6. **`backend/app/seed.py`** loads the exported city/wards/observations into PostgreSQL, seeds the intervention catalog and demo users, and triggers an initial detection run.

## What a Real Deployment Would Replace

| Domain | Demo provider | Real replacement |
|---|---|---|
| Satellite (LST, NDVI, NDBI, albedo) | `DemoSatelliteProvider` | Google Earth Engine: Landsat 8/9 thermal bands, Sentinel-2 optical, ECOSTRESS where available |
| Weather | `DemoWeatherProvider` | ERA5 reanalysis (Copernicus CDS) |
| Urban form | `DemoUrbanProvider` | OpenStreetMap (building footprints, road network, land use) |
| Population | `DemoPopulationProvider` | Census / gridded population datasets (e.g. WorldPop) |

Each would implement the corresponding abstract base class in `ml/coolgrid_ml/providers/base.py` and be registered in `providers/factory.py` guarded by the presence of its required credentials (e.g. `GEE_SERVICE_ACCOUNT_JSON`) — no other application code would need to change, since detection/prediction/simulation/optimization all consume the provider *interfaces*, never a concrete class.

## Historical Observations

240 days × 24 wards, sampled every 3 days (1,920 rows), exported to `data/demo/seed/observations.csv` and loaded into the `observations` table by the seed script. LST ranges ~25–55°C across the dataset, matching plausible extremes for a hot pre-monsoon Indian city (dry, low-vegetation, low-wind conditions push the upper end; the physics model's documented clamp keeps it from diverging further — see [ML.md](ML.md)).
