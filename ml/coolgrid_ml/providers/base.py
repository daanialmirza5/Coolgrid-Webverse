"""Abstract data provider interfaces.

CoolGrid's ML/physics pipeline is decoupled from where its inputs come from.
Every provider below defines the contract a real integration (Google Earth
Engine / Landsat / Sentinel-2 / ERA5 / OSM / census APIs) must satisfy. Until
credentials for those services are configured, CoolGrid runs entirely on the
Demo* implementations in `demo.py`, which produce clearly-labeled synthetic
data with physically plausible relationships (e.g. more vegetation -> lower
LST). No demo output is ever presented as real satellite/weather data.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class SatelliteObservation:
    ward_id: str
    observed_on: date
    lst_celsius: float
    ndvi: float
    ndbi: float
    albedo: float
    cloud_cover_pct: float
    source: str
    is_demo: bool


@dataclass
class WeatherObservation:
    ward_id: str
    observed_on: date
    air_temp_celsius: float
    humidity_pct: float
    wind_speed_ms: float
    shortwave_radiation_wm2: float
    source: str
    is_demo: bool


@dataclass
class UrbanFeatureSet:
    ward_id: str
    built_up_density: float  # 0-1 fraction of impervious/built surface
    road_density_km_per_km2: float
    green_space_pct: float
    water_body_pct: float
    building_height_mean_m: float
    source: str
    is_demo: bool


@dataclass
class PopulationFeatureSet:
    ward_id: str
    population_density_per_km2: float
    population_total: int
    vulnerable_population_pct: float
    source: str
    is_demo: bool


class SatelliteDataProvider(ABC):
    """LST / NDVI / NDBI / albedo from thermal + optical satellite bands."""

    name: str = "abstract-satellite"
    is_demo: bool = True

    @abstractmethod
    def get_observations(self, ward_ids: list[str], as_of: date) -> list[SatelliteObservation]:
        ...


class WeatherDataProvider(ABC):
    """Near-surface meteorology (ERA5-equivalent)."""

    name: str = "abstract-weather"
    is_demo: bool = True

    @abstractmethod
    def get_observations(self, ward_ids: list[str], as_of: date) -> list[WeatherObservation]:
        ...


class UrbanDataProvider(ABC):
    """Built environment features (OSM-equivalent)."""

    name: str = "abstract-urban"
    is_demo: bool = True

    @abstractmethod
    def get_features(self, ward_ids: list[str]) -> list[UrbanFeatureSet]:
        ...


class PopulationDataProvider(ABC):
    """Population / demographic density (census-equivalent)."""

    name: str = "abstract-population"
    is_demo: bool = True

    @abstractmethod
    def get_features(self, ward_ids: list[str]) -> list[PopulationFeatureSet]:
        ...


@dataclass
class ProviderRegistry:
    """Bundle of active providers, with a flag summarizing whether any is live."""

    satellite: SatelliteDataProvider
    weather: WeatherDataProvider
    urban: UrbanDataProvider
    population: PopulationDataProvider
    notes: list[str] = field(default_factory=list)

    @property
    def all_demo(self) -> bool:
        return all(
            p.is_demo
            for p in (self.satellite, self.weather, self.urban, self.population)
        )

    def status(self) -> dict[str, Any]:
        return {
            "satellite": {"provider": self.satellite.name, "is_demo": self.satellite.is_demo},
            "weather": {"provider": self.weather.name, "is_demo": self.weather.is_demo},
            "urban": {"provider": self.urban.name, "is_demo": self.urban.is_demo},
            "population": {"provider": self.population.name, "is_demo": self.population.is_demo},
            "all_demo": self.all_demo,
            "notes": self.notes,
        }
