"""SHAP-based driver explainability for the heat detection model.

Wraps `shap.TreeExplainer` around the trained XGBoost median model to
answer "why is this area hot?" with ranked, signed feature contributions
(Lundberg & Lee, 2017).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import shap

from ..detection.features import build_feature_frame
from ..detection.model import HeatDetectionModel

WEATHER_FEATURES = {"humidity_pct", "wind_speed_ms", "shortwave_wm2", "air_temp_c"}

# Direction-aware labels: a SHAP value's sign says whether *this ward's*
# value of a feature pushed its prediction up or down relative to the
# model's baseline -- e.g. "increases_heat" for green_space_pct usually
# means the ward has BELOW-AVERAGE vegetation, not that vegetation itself
# heats things up. Labeling by direction avoids that confusion and matches
# how the product spec itself phrases drivers ("Low vegetation", "Low
# albedo") rather than naming the raw feature.
FRIENDLY_NAMES: dict[str, dict[str, str]] = {
    "ndvi": {"increases_heat": "Low vegetation index (NDVI)", "decreases_heat": "Healthy vegetation index (NDVI)"},
    "ndbi": {"increases_heat": "High built-up index (NDBI)", "decreases_heat": "Low built-up index (NDBI)"},
    "albedo": {"increases_heat": "Low surface albedo", "decreases_heat": "High surface albedo (reflective surfaces)"},
    "built_up_density": {"increases_heat": "High built-up density", "decreases_heat": "Low built-up density"},
    "green_space_pct": {"increases_heat": "Low vegetation / green cover", "decreases_heat": "Ample vegetation / green cover"},
    "water_body_pct": {"increases_heat": "Limited water body coverage", "decreases_heat": "Water body cooling effect"},
    "road_density_km_per_km2": {"increases_heat": "High road density", "decreases_heat": "Low road density"},
    "population_density_per_km2": {"increases_heat": "High population density", "decreases_heat": "Low population density"},
    "humidity_pct": {"increases_heat": "Low humidity", "decreases_heat": "High humidity"},
    "wind_speed_ms": {"increases_heat": "Low wind speed", "decreases_heat": "High wind speed"},
    "shortwave_wm2": {"increases_heat": "High solar radiation", "decreases_heat": "Low solar radiation"},
    "air_temp_c": {"increases_heat": "High ambient air temperature", "decreases_heat": "Low ambient air temperature"},
}


def _label_for(feature: str, direction: str) -> str:
    entry = FRIENDLY_NAMES.get(feature)
    if entry is None:
        return feature
    return entry[direction]


@dataclass
class DriverContribution:
    feature: str
    label: str
    value: float
    shap_value: float
    direction: str  # "increases_heat" | "decreases_heat"
    relative_contribution_pct: float


class HeatExplainer:
    def __init__(self, model: HeatDetectionModel):
        self.model = model
        self._explainer = shap.TreeExplainer(model.median_model)

    def explain(self, df_row: pd.DataFrame) -> list[DriverContribution]:
        X = build_feature_frame(df_row)
        shap_values = self._explainer.shap_values(X)
        row_shap = shap_values[0]
        row_vals = X.iloc[0]

        total_abs = float(np.sum(np.abs(row_shap))) or 1e-9
        contributions = []
        for feat, sv, val in zip(X.columns, row_shap, row_vals):
            direction = "increases_heat" if sv > 0 else "decreases_heat"
            contributions.append(
                DriverContribution(
                    feature=feat,
                    label=_label_for(feat, direction),
                    value=round(float(val), 3),
                    shap_value=round(float(sv), 4),
                    direction=direction,
                    relative_contribution_pct=round(abs(float(sv)) / total_abs * 100, 1),
                )
            )
        contributions.sort(key=lambda c: abs(c.shap_value), reverse=True)
        return contributions

    def explain_grouped(self, df_row: pd.DataFrame) -> list[DriverContribution]:
        """Same as `explain()`, but collapses the four weather covariates
        (which are identical across every ward on a given day) into one
        "Weather conditions" driver. Presenting them separately would let a
        transient weather condition (e.g. today's wind speed) dominate the
        ranking and crowd out the ward-specific urban-form drivers
        (built-up density, vegetation, albedo, ...) that a city planner can
        actually act on -- and that matches how the product spec itself
        groups drivers ("Built-up density, Low vegetation, ..., Weather")."""
        raw = self.explain(df_row)
        weather = [c for c in raw if c.feature in WEATHER_FEATURES]
        other = [c for c in raw if c.feature not in WEATHER_FEATURES]

        weather_shap = sum(c.shap_value for c in weather)
        total_abs = sum(abs(c.shap_value) for c in other) + abs(weather_shap)
        total_abs = total_abs or 1e-9

        grouped = [
            DriverContribution(
                feature=c.feature, label=c.label, value=c.value, shap_value=c.shap_value,
                direction=c.direction, relative_contribution_pct=round(abs(c.shap_value) / total_abs * 100, 1),
            )
            for c in other
        ]
        if weather:
            weather_direction = "increases_heat" if weather_shap > 0 else "decreases_heat"
            weather_label = (
                "Hot weather conditions (temperature, radiation, humidity, wind)"
                if weather_direction == "increases_heat"
                else "Mild weather conditions (temperature, radiation, humidity, wind)"
            )
            grouped.append(
                DriverContribution(
                    feature="weather", label=weather_label,
                    value=0.0, shap_value=round(weather_shap, 4),
                    direction=weather_direction,
                    relative_contribution_pct=round(abs(weather_shap) / total_abs * 100, 1),
                )
            )
        grouped.sort(key=lambda c: abs(c.shap_value), reverse=True)
        return grouped

    def base_value(self) -> float:
        return float(self._explainer.expected_value)
