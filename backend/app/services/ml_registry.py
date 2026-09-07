"""Process-wide singletons for the trained ML/physics artifacts.

Loaded once at API startup (see `main.py`'s lifespan) so requests don't pay
model-load cost per call. If artifacts are missing, raises a clear error
telling the operator to run `python ml/train.py` first -- the app should
never silently fall back to an untrained model.
"""

from __future__ import annotations

import json
from functools import lru_cache

import numpy as np
import torch

from coolgrid_ml.detection.model import HeatDetectionModel
from coolgrid_ml.explain.shap_explainer import HeatExplainer
from coolgrid_ml.optimization.optimizer import InterventionOptimizer
from coolgrid_ml.physics.pinn import PhysicsInformedLSTNet, FEATURE_ORDER as PINN_FEATURE_ORDER
from coolgrid_ml.prediction.forecaster import HeatForecaster
from coolgrid_ml.providers.factory import get_provider_registry
from coolgrid_ml.simulation.engine import SimulationEngine

from ..core.config import get_settings

DETECTION_MODEL_VERSION = "xgboost-v1"
PINN_MODEL_VERSION = "pinn-v1"


class MLRegistry:
    def __init__(self):
        settings = get_settings()
        detection_dir = settings.ml_artifacts_dir / "heat_detection"
        pinn_dir = settings.ml_artifacts_dir / "pinn"

        if not detection_dir.exists():
            raise RuntimeError(
                f"Heat detection model not found at {detection_dir}. "
                "Run `python train.py` from the ml/ directory first."
            )

        self.detection_model = HeatDetectionModel.load(detection_dir)
        self.explainer = HeatExplainer(self.detection_model)
        self.forecaster = HeatForecaster(self.detection_model)
        self.simulation_engine = SimulationEngine(self.detection_model)
        self.optimizer = InterventionOptimizer(self.detection_model)
        self.providers = get_provider_registry()

        self.pinn: PhysicsInformedLSTNet | None = None
        self.pinn_meta: dict | None = None
        if pinn_dir.exists():
            with open(pinn_dir / "meta.json") as f:
                self.pinn_meta = json.load(f)
            model = PhysicsInformedLSTNet(n_features=len(self.pinn_meta["feature_order"]))
            model.load_state_dict(torch.load(pinn_dir / "pinn.pt", weights_only=True))
            model.set_normalization(np.array(self.pinn_meta["mean"]), np.array(self.pinn_meta["std"]))
            model.eval()
            self.pinn = model

    def pinn_predict_one(self, feature_row: dict) -> float | None:
        if self.pinn is None:
            return None
        ordered = np.array([[feature_row[k] for k in PINN_FEATURE_ORDER]], dtype=np.float32)
        return float(self.pinn.predict(ordered)[0])


@lru_cache
def get_ml_registry() -> MLRegistry:
    return MLRegistry()
