"""Short/medium-term LST forecasting.

For each horizon (1 / 7 / 30 days by default) the forecaster:
  1. Projects expected weather deterministically from the seasonal
     climatology (no real forecast feed is available in demo mode).
  2. Builds a feature row from the ward's static attributes (optionally
     overridden by a simulation scenario -- see `simulation/`) plus the
     projected weather.
  3. Runs the XGBoost detector's median/lower/upper quantile models.
  4. Blends the ML median with the simplified physics energy-balance
     estimate for the same projected conditions -- this is the "physics
     layer influencing predictions" requirement, not decorative.
  5. Widens the confidence interval and lowers confidence with horizon
     length, since longer-range projections rely more on climatology and
     less on observed conditions.

Every result is returned with an explicit confidence value and is never
framed as a guaranteed outcome.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from ..data.climatology import (
    seasonal_air_temp,
    seasonal_humidity,
    seasonal_radiation,
    seasonal_wind,
)
from ..data.schema import WardBase
from ..detection.model import HeatDetectionModel, RiskLevel
from ..physics.energy_balance import estimate_lst

PHYSICS_BLEND_WEIGHT = 0.35  # fraction of final prediction attributed to the physics estimate

DEFAULT_HORIZONS = (1, 7, 30)


@dataclass
class ForecastPoint:
    horizon_days: int
    target_date: str
    predicted_lst: float
    predicted_lst_lower: float
    predicted_lst_upper: float
    change_from_current_c: float
    risk_level: RiskLevel
    confidence: float
    physics_estimate_lst: float
    disclaimer: str = "Modeled projection with uncertainty -- not a guaranteed outcome."


class HeatForecaster:
    def __init__(self, model: HeatDetectionModel):
        self.model = model

    def _feature_row(
        self,
        ward: WardBase,
        target_date: date,
        overrides: dict | None = None,
    ) -> tuple[pd.DataFrame, dict]:
        doy = target_date.timetuple().tm_yday
        air_temp = seasonal_air_temp(doy)
        radiation = seasonal_radiation(doy)
        humidity = seasonal_humidity(doy)
        wind = seasonal_wind(doy)

        attrs = {
            "albedo": ward.albedo_base,
            "green_space_pct": ward.green_space_pct,
            "water_body_pct": ward.water_body_pct,
            "built_up_density": ward.built_up_density,
        }
        if overrides:
            attrs.update({k: v for k, v in overrides.items() if k in attrs})

        ndvi = float(np.clip(0.75 * (attrs["green_space_pct"] / 100) + 0.05 * (attrs["water_body_pct"] / 100) - 0.35 * attrs["built_up_density"], -0.1, 0.9))
        ndbi = float(np.clip(0.65 * attrs["built_up_density"] - 0.3 * (attrs["green_space_pct"] / 100), -0.3, 0.8))

        row = {
            "ndvi": ndvi,
            "ndbi": ndbi,
            "albedo": attrs["albedo"],
            "built_up_density": attrs["built_up_density"],
            "green_space_pct": attrs["green_space_pct"],
            "water_body_pct": attrs["water_body_pct"],
            "road_density_km_per_km2": ward.road_density_km_per_km2,
            "population_density_per_km2": ward.population_density_per_km2,
            "humidity_pct": humidity,
            "wind_speed_ms": wind,
            "shortwave_wm2": radiation,
            "air_temp_c": air_temp,
        }
        weather_ctx = {"air_temp": air_temp, "radiation": radiation, "humidity": humidity, "wind": wind}
        return pd.DataFrame([row]), {**attrs, **weather_ctx}

    def forecast(
        self,
        ward: WardBase,
        current_lst: float,
        as_of: date | None = None,
        horizons: tuple[int, ...] = DEFAULT_HORIZONS,
        scenario_overrides: dict | None = None,
    ) -> list[ForecastPoint]:
        as_of = as_of or date.today()
        points: list[ForecastPoint] = []

        # `current_lst` is a single noisy observation (real satellite passes
        # are noisy too), while every horizon's feature row below is built
        # from smooth, noise-free seasonal climatology. Jumping straight to
        # the climatology value at h=1 would make "tomorrow" look
        # implausibly different from "today" whenever today happened to be
        # an anomalously hot/cool reading. Instead, treat
        # (current_lst - today's climatology) as today's anomaly and persist
        # it into the forecast with exponential decay toward climatology --
        # a standard, simple baseline technique in short-range forecasting
        # (persistence forecasting), not just a display smoothing trick.
        today_feature_df, today_ctx = self._feature_row(ward, as_of, scenario_overrides)
        [today_detection] = self.model.predict(today_feature_df)
        today_physics = estimate_lst(
            air_temp_c=today_ctx["air_temp"], shortwave_wm2=today_ctx["radiation"], albedo=today_ctx["albedo"],
            green_space_pct=today_ctx["green_space_pct"], water_body_pct=today_ctx["water_body_pct"],
            built_up_density=today_ctx["built_up_density"], humidity_pct=today_ctx["humidity"], wind_speed_ms=today_ctx["wind"],
        )
        today_climatology = (1 - PHYSICS_BLEND_WEIGHT) * today_detection.lst_celsius + PHYSICS_BLEND_WEIGHT * today_physics.lst_celsius
        anomaly = current_lst - today_climatology
        ANOMALY_DECAY_TAU_DAYS = 10.0

        for h in horizons:
            target_date = as_of + timedelta(days=h)
            feature_df, ctx = self._feature_row(ward, target_date, scenario_overrides)
            [detection] = self.model.predict(feature_df)

            physics = estimate_lst(
                air_temp_c=ctx["air_temp"],
                shortwave_wm2=ctx["radiation"],
                albedo=ctx["albedo"],
                green_space_pct=ctx["green_space_pct"],
                water_body_pct=ctx["water_body_pct"],
                built_up_density=ctx["built_up_density"],
                humidity_pct=ctx["humidity"],
                wind_speed_ms=ctx["wind"],
            )

            climatology_blend = (1 - PHYSICS_BLEND_WEIGHT) * detection.lst_celsius + PHYSICS_BLEND_WEIGHT * physics.lst_celsius
            decay = np.exp(-h / ANOMALY_DECAY_TAU_DAYS)
            blended = climatology_blend + decay * anomaly

            horizon_widen = 1.0 + 0.22 * np.sqrt(h)
            half_width = max((detection.lst_upper - detection.lst_lower) / 2, 0.5) * horizon_widen
            lower = blended - half_width
            upper = blended + half_width
            confidence = float(np.clip(detection.confidence - 0.015 * np.sqrt(h) * 5, 0.3, 0.95))

            points.append(
                ForecastPoint(
                    horizon_days=h,
                    target_date=target_date.isoformat(),
                    predicted_lst=round(blended, 2),
                    predicted_lst_lower=round(lower, 2),
                    predicted_lst_upper=round(upper, 2),
                    change_from_current_c=round(blended - current_lst, 2),
                    risk_level=self.model._risk_level(blended),
                    confidence=round(confidence, 3),
                    physics_estimate_lst=physics.lst_celsius,
                )
            )
        return points
