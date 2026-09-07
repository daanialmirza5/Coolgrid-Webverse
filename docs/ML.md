# ML & Physics Pipeline

Package: `ml/coolgrid_ml/`. Zero dependency on FastAPI/SQLAlchemy — plain dataclasses and pandas DataFrames throughout, so it's independently testable and reusable.

## Pipeline Stages

```
providers → data → detection → explain → physics → prediction → simulation → optimization
```

### 1. Providers (`providers/`)

Abstract interfaces: `SatelliteDataProvider`, `WeatherDataProvider`, `UrbanDataProvider`, `PopulationDataProvider` (`base.py`). `Demo*` implementations (`demo.py`) are active by default; `factory.py` documents exactly where a real `GoogleEarthEngineSatelliteProvider`/ERA5/OSM/census provider would be wired in, gated by env-var presence, with zero other application changes required.

**Design note that mattered**: the demo satellite and weather providers must sample the *same* weather for a given (ward, date) — `demo.py`'s `_sample_daily_weather()` is the single source of truth both providers call into. An earlier version sampled weather independently for each, which meant the "weather" feature columns in the training set didn't actually match the conditions that produced the LST label — the model could only learn noise (R²≈0.53, MAE≈8°C). After the fix: **R²=0.99, MAE=0.6°C**. All RNG seeding uses a stable SHA-256-based hash (not Python's per-process-randomized `hash()`), so the same (seed, ward, date) always produces the same values across processes — training and the live backend agree on "today's" observation.

### 2. Data (`data/`)

`city_grid.py` generates a synthetic 6×4 grid of 24 wards over Pune's approximate bounding box (not real administrative boundaries), with archetype-driven (dense_core/residential/industrial/green_belt/riverside/peri_urban) static attributes: built-up density, vegetation %, water %, road density, building height, albedo, population density/total, vulnerable population %. `climatology.py` is a shared seasonal weather model (hot Mar–Jun, monsoon Jun–Sep, mild winter) used by both the demo providers and the forecaster. `dataset.py` samples the providers across many historical dates to build the supervised training table.

### 3. Detection (`detection/model.py`)

XGBoost regressor predicting LST from 12 features (NDVI, NDBI, albedo, built-up density, vegetation %, water %, road density, population density, humidity, wind, solar radiation, air temperature). Two additional XGBoost models trained with `reg:quantileerror` (α=0.1, 0.9) give data-driven confidence intervals — wards with atypical feature combinations get wider intervals, not a fixed ± band. Risk level (LOW/MODERATE/HIGH/CRITICAL) and a 0–100 heat score are derived from the predicted LST's percentile within the training distribution.

Current metrics (`data/demo/models/heat_detection/meta.json`): **MAE 0.61°C, RMSE 0.82°C, R² 0.99** on a held-out 20% split.

### 4. Explainability (`explain/shap_explainer.py`)

`shap.TreeExplainer` on the median XGBoost model. Two important design choices:

- **Direction-aware labels**: a positive SHAP value for `green_space_pct` usually means the ward has *below-average* vegetation, not that vegetation itself heats things up. `FRIENDLY_NAMES` maps each feature to a `{increases_heat, decreases_heat}` pair of labels ("Low vegetation / green cover" vs. "Ample vegetation / green cover") so the UI never phrases a driver misleadingly.
- **Weather grouping** (`explain_grouped()`): the four weather features are identical across every ward on a given day, so ungrouped they can dominate the ranking (75%+ of the explanation) and crowd out the ward-specific, actionable urban-form drivers a city planner can do something about. `explain_grouped()` collapses them into one "Weather conditions" driver, matching how the product spec itself phrases the example driver list ("Built-up density, Low vegetation, Low albedo, Road density, Population density, Weather").

### 5. Physics (`physics/`)

**`energy_balance.py`** — a simplified, documented surface energy balance (Rn = H + LE + G, after Oke 1982):

- Net radiation from shortwave input and albedo.
- Latent heat flux (evapotranspirative cooling) from vegetation/water cover and humidity (Priestley-Taylor-style).
- Ground heat storage computed as a diagnostic (built-up density, albedo) but **not** subtracted from daytime sensible heat — an earlier version did subtract it, which made higher built-up density *lower* daytime LST (backwards for a skin-temperature estimate; G represents energy banked for nighttime release, not a same-day sink). See the code comment for the physical reasoning.
- Surface-air temperature offset via a bulk aerodynamic formula, with built-up density independently reducing near-surface wind mixing (urban canyon/building drag effect) — this is what gives built-up density its own LST effect distinct from albedo/vegetation.
- The offset is clamped to a documented realistic band (−3°C to +26°C) because the bulk formula is unstable (divides by wind speed) at very low wind — a real bug caught during testing produced a 225°C LST before this clamp was added.

**`pinn.py`** — a lightweight PyTorch MLP trained with a combined loss (`(1-w)·MSE(pred, observed) + w·MSE(pred, energy_balance_estimate)`, w=0.35): a constraint-style physics-informed neural network (a soft physical prior via the loss function) rather than a PDE-residual PINN over spatiotemporal coordinates — an appropriate scope for ward-level tabular features. Exposed via the data sources page (`pinn_trained: true/false`) and recorded as a `ModelRun`.

### 6. Prediction (`prediction/forecaster.py`)

For each horizon (1/7/30 days): projects deterministic seasonal climatology, runs the XGBoost detector + energy balance on the projected conditions, blends them (65% detector / 35% physics), then **persists today's observed anomaly with exponential decay** (τ=10 days) toward that climatology blend. This matters: without it, a 1-day-ahead forecast built purely from smooth climatology could look implausibly different from today's actual (noisy) reading whenever today happened to be anomalous — a real issue caught during testing (a ward showing 60.2°C "today" but 55.5°C "tomorrow" with no explanation). Persistence forecasting (today's anomaly decaying toward the seasonal normal) is a standard, simple short-range forecasting baseline technique, not just a display smoothing trick.

### 7. Simulation (`simulation/`)

Each of the 6 intervention types (`interventions.py`) has a documented effect on albedo/vegetation/water/built-up-density, plus illustrative unit cost/land/water metadata. `engine.py` re-solves the energy balance under baseline vs. perturbed attributes, Monte Carlo-sampling weather noise (60 samples) for a genuine confidence interval on the cooling estimate — not a fixed percentage. `current_lst_anchor` (see [ARCHITECTURE.md](ARCHITECTURE.md)) re-bases the result onto the ward's actual detected LST so it's consistent with what's shown elsewhere in the UI for the same ward.

### 8. Optimization (`optimization/optimizer.py`)

Discretized grid search: 4 coverage levels (0%, 33%, 66%, 100% of each intervention's max) × 6 intervention types = up to 4,095 candidate portfolios, filtered by budget/land/water feasibility, scored by a weighted multi-objective function (cooling, population benefit, risk reduction vs. cost, land, water — weights tunable via `population_priority`/`risk_priority`), returning the top 5 with a natural-language reason generated from the actual simulation numbers.

## Training

```powershell
cd ml
..\.venv\Scripts\python train.py
```

Exports: `data/demo/seed/{wards.json,wards.geojson,observations.csv}`, `data/demo/models/heat_detection/{median,lower,upper}_model.joblib` + `meta.json`, `data/demo/models/pinn/pinn.pt` + `meta.json`.

## Tests

`ml/tests/` (21 tests): physics relationships (vegetation/albedo cool, built-up heats, low-wind stays bounded), city grid determinism, dataset schema, detection model fit quality + save/load roundtrip, SHAP ranking + grouping, forecast confidence widening + anomaly persistence, simulation anchoring + zero-coverage no-op, optimizer budget constraint + ranking order.
