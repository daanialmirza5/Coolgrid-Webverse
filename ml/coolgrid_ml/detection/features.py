"""Feature engineering for the heat detection model.

Combines the covariates required by the spec: NDVI, NDBI/built-up, albedo,
population density, road density, humidity, wind, radiation, historical LST
(via air temperature + season as its proxy driver here, since the model
predicts *current* LST rather than reusing it as an input feature -- that
would be circular).
"""

from __future__ import annotations

import pandas as pd

from ..data.dataset import FEATURE_COLUMNS

__all__ = ["FEATURE_COLUMNS", "build_feature_frame"]


def build_feature_frame(raw: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in FEATURE_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"Missing required feature columns: {missing}")
    frame = raw[FEATURE_COLUMNS].copy()
    return frame.astype(float)
