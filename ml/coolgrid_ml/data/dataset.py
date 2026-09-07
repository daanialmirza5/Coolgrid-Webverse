"""Builds a supervised training table by sampling the demo providers across
many historical dates and all wards -- this is the "historical observations"
CoolGrid trains its heat-detection model and PINN on."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from ..providers.demo import (
    DemoPopulationProvider,
    DemoSatelliteProvider,
    DemoUrbanProvider,
    DemoWeatherProvider,
)
from .city_grid import generate_city

FEATURE_COLUMNS = [
    "ndvi",
    "ndbi",
    "albedo",
    "built_up_density",
    "green_space_pct",
    "water_body_pct",
    "road_density_km_per_km2",
    "population_density_per_km2",
    "humidity_pct",
    "wind_speed_ms",
    "shortwave_wm2",
    "air_temp_c",
]


def build_training_dataset(
    n_days: int = 240,
    end_date: date | None = None,
    seed: int = 42,
    sample_stride: int = 3,
) -> pd.DataFrame:
    """Returns one row per (ward, sampled date) with features + target lst_celsius."""
    end_date = end_date or date.today()
    wards = generate_city(seed)
    ward_ids = [w.ward_id for w in wards]
    ward_by_id = {w.ward_id: w for w in wards}

    satellite = DemoSatelliteProvider(seed)
    weather = DemoWeatherProvider(seed)
    urban = DemoUrbanProvider(seed)
    population = DemoPopulationProvider(seed)

    urban_by_id = {f.ward_id: f for f in urban.get_features(ward_ids)}
    pop_by_id = {f.ward_id: f for f in population.get_features(ward_ids)}

    rows = []
    for day_offset in range(0, n_days, sample_stride):
        as_of = end_date - timedelta(days=day_offset)
        sat_obs = {o.ward_id: o for o in satellite.get_observations(ward_ids, as_of)}
        wx_obs = {o.ward_id: o for o in weather.get_observations(ward_ids, as_of)}
        for ward_id in ward_ids:
            ward = ward_by_id[ward_id]
            sat = sat_obs[ward_id]
            wx = wx_obs[ward_id]
            u = urban_by_id[ward_id]
            p = pop_by_id[ward_id]
            rows.append(
                {
                    "ward_id": ward_id,
                    "archetype": ward.archetype.value,
                    "observed_on": as_of.isoformat(),
                    "ndvi": sat.ndvi,
                    "ndbi": sat.ndbi,
                    "albedo": sat.albedo,
                    "built_up_density": u.built_up_density,
                    "green_space_pct": u.green_space_pct,
                    "water_body_pct": u.water_body_pct,
                    "road_density_km_per_km2": u.road_density_km_per_km2,
                    "population_density_per_km2": p.population_density_per_km2,
                    "humidity_pct": wx.humidity_pct,
                    "wind_speed_ms": wx.wind_speed_ms,
                    "shortwave_wm2": wx.shortwave_radiation_wm2,
                    "air_temp_c": wx.air_temp_celsius,
                    "lst_celsius": sat.lst_celsius,
                }
            )
    return pd.DataFrame(rows)
