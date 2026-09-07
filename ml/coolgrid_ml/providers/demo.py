"""Demo data providers.

Every value returned here is synthetic. Generation follows rules so the
downstream ML actually has something meaningful to learn and explain:

 1. Static urban/population attributes come from `data.city_grid` (seeded,
    archetype-driven).
 2. Time-varying weather is sampled once per (ward, date) from a seasonal
    climatology (loosely shaped on Pune's hot/monsoon/winter pattern) plus
    Gaussian noise -- and that *exact same* sampled weather is what both
    `DemoWeatherProvider` reports AND what `DemoSatelliteProvider` feeds into
    the surface energy balance to generate LST. If these two providers used
    independently-random weather (as an earlier version of this module did),
    the "weather" feature columns in the training set would not actually
    match the conditions that produced the LST label, and a model trained on
    that data would see mostly noise. Sharing one weather sample per
    (ward, date) is what makes the built-up/vegetation/albedo -> LST
    relationship genuinely learnable (and explainable via SHAP) rather than
    hardcoded.
 3. All RNG seeding uses a stable hash (sha256-based, not Python's
    per-process-randomized `hash()`) so the same (seed, ward, date) always
    produces the same values across processes -- e.g. so the ML training
    script and the live backend agree on "today's" observation for a ward.

`is_demo=True` is set on every provider and observation; the API/UI must
surface this to users (see backend `datasources` endpoints).
"""

from __future__ import annotations

import hashlib
from datetime import date

import numpy as np

from ..data.city_grid import generate_city
from ..data.climatology import (
    seasonal_air_temp,
    seasonal_humidity,
    seasonal_radiation,
    seasonal_wind,
)
from ..physics.energy_balance import estimate_lst
from .base import (
    PopulationDataProvider,
    PopulationFeatureSet,
    SatelliteDataProvider,
    SatelliteObservation,
    UrbanDataProvider,
    UrbanFeatureSet,
    WeatherDataProvider,
    WeatherObservation,
)

_SEED = 42


def _stable_seed(*parts: object) -> int:
    key = "|".join(str(p) for p in parts).encode("utf-8")
    digest = hashlib.sha256(key).digest()
    return int.from_bytes(digest[:4], "big")


def _ward_lookup(seed: int = _SEED) -> dict:
    return {w.ward_id: w for w in generate_city(seed)}


def _sample_daily_weather(seed: int, ward_id: str, as_of: date) -> dict:
    """The single source of truth for a (ward, date)'s weather -- shared by
    the weather and satellite providers so features and labels stay consistent."""
    doy = as_of.timetuple().tm_yday
    rng = np.random.default_rng(_stable_seed(seed, "weather", ward_id, as_of.isoformat()))
    air_temp = seasonal_air_temp(doy) + rng.normal(0, 0.8)
    radiation = max(0.0, seasonal_radiation(doy) + rng.normal(0, 15))
    humidity = float(np.clip(seasonal_humidity(doy) + rng.normal(0, 4), 15, 98))
    wind = max(0.4, seasonal_wind(doy) + rng.normal(0, 0.6))
    return {"air_temp": air_temp, "radiation": radiation, "humidity": humidity, "wind": wind}


class DemoSatelliteProvider(SatelliteDataProvider):
    name = "demo-satellite-v1"
    is_demo = True

    def __init__(self, seed: int = _SEED):
        self.seed = seed
        self._wards = _ward_lookup(seed)

    def get_observations(self, ward_ids: list[str], as_of: date) -> list[SatelliteObservation]:
        out = []
        doy = as_of.timetuple().tm_yday
        for ward_id in ward_ids:
            ward = self._wards.get(ward_id)
            if ward is None:
                continue
            wx = _sample_daily_weather(self.seed, ward_id, as_of)
            rng = np.random.default_rng(_stable_seed(self.seed, "sat", ward_id, as_of.isoformat()))

            est = estimate_lst(
                air_temp_c=wx["air_temp"],
                shortwave_wm2=wx["radiation"],
                albedo=ward.albedo_base,
                green_space_pct=ward.green_space_pct,
                water_body_pct=ward.water_body_pct,
                built_up_density=ward.built_up_density,
                humidity_pct=wx["humidity"],
                wind_speed_ms=wx["wind"],
            )
            lst = est.lst_celsius + rng.normal(0, 0.4)

            ndvi = float(np.clip(0.75 * (ward.green_space_pct / 100) + 0.05 * (ward.water_body_pct / 100) - 0.35 * ward.built_up_density + rng.normal(0, 0.03), -0.1, 0.9))
            ndbi = float(np.clip(0.65 * ward.built_up_density - 0.3 * (ward.green_space_pct / 100) + rng.normal(0, 0.03), -0.3, 0.8))
            cloud_cover = float(np.clip(rng.uniform(0, 15) + (25 if 152 <= doy <= 273 else 0), 0, 95))

            out.append(
                SatelliteObservation(
                    ward_id=ward_id,
                    observed_on=as_of,
                    lst_celsius=round(lst, 2),
                    ndvi=round(ndvi, 3),
                    ndbi=round(ndbi, 3),
                    albedo=round(float(np.clip(ward.albedo_base + rng.normal(0, 0.01), 0.02, 0.5)), 3),
                    cloud_cover_pct=round(cloud_cover, 1),
                    source=self.name,
                    is_demo=True,
                )
            )
        return out


class DemoWeatherProvider(WeatherDataProvider):
    name = "demo-weather-v1"
    is_demo = True

    def __init__(self, seed: int = _SEED):
        self.seed = seed

    def get_observations(self, ward_ids: list[str], as_of: date) -> list[WeatherObservation]:
        out = []
        for ward_id in ward_ids:
            wx = _sample_daily_weather(self.seed, ward_id, as_of)
            out.append(
                WeatherObservation(
                    ward_id=ward_id,
                    observed_on=as_of,
                    air_temp_celsius=round(wx["air_temp"], 2),
                    humidity_pct=round(wx["humidity"], 1),
                    wind_speed_ms=round(wx["wind"], 2),
                    shortwave_radiation_wm2=round(wx["radiation"], 1),
                    source=self.name,
                    is_demo=True,
                )
            )
        return out


class DemoUrbanProvider(UrbanDataProvider):
    name = "demo-urban-v1"
    is_demo = True

    def __init__(self, seed: int = _SEED):
        self._wards = _ward_lookup(seed)

    def get_features(self, ward_ids: list[str]) -> list[UrbanFeatureSet]:
        out = []
        for ward_id in ward_ids:
            ward = self._wards.get(ward_id)
            if ward is None:
                continue
            out.append(
                UrbanFeatureSet(
                    ward_id=ward_id,
                    built_up_density=ward.built_up_density,
                    road_density_km_per_km2=ward.road_density_km_per_km2,
                    green_space_pct=ward.green_space_pct,
                    water_body_pct=ward.water_body_pct,
                    building_height_mean_m=ward.building_height_mean_m,
                    source=self.name,
                    is_demo=True,
                )
            )
        return out


class DemoPopulationProvider(PopulationDataProvider):
    name = "demo-population-v1"
    is_demo = True

    def __init__(self, seed: int = _SEED):
        self._wards = _ward_lookup(seed)

    def get_features(self, ward_ids: list[str]) -> list[PopulationFeatureSet]:
        out = []
        for ward_id in ward_ids:
            ward = self._wards.get(ward_id)
            if ward is None:
                continue
            out.append(
                PopulationFeatureSet(
                    ward_id=ward_id,
                    population_density_per_km2=ward.population_density_per_km2,
                    population_total=ward.population_total,
                    vulnerable_population_pct=ward.vulnerable_population_pct,
                    source=self.name,
                    is_demo=True,
                )
            )
        return out
