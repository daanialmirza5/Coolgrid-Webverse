"""CoolGrid ML/physics pipeline package.

Layers:
  providers   -- data source abstractions (satellite/weather/urban/population), demo + real
  data        -- demo city generation (synthetic Pune-like grid) and feature schemas
  detection   -- XGBoost-based heat/LST detection and risk classification
  explain     -- SHAP-based driver explainability
  physics     -- surface energy balance constraints + lightweight physics-informed NN (PINN)
  prediction  -- short/medium term LST forecasting with confidence intervals
  simulation  -- intervention effect models (trees, cool roofs, green roofs, blue infra, reflective surfaces)
  optimization-- constraint-aware intervention portfolio optimizer

All synthetic data generated here is DEMO DATA and is labeled as such end-to-end;
it approximates plausible physical relationships but is not derived from real
satellite observations.
"""

__version__ = "0.1.0"
