from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum


class WardArchetype(str, Enum):
    DENSE_CORE = "dense_core"
    RESIDENTIAL = "residential"
    INDUSTRIAL = "industrial"
    GREEN_BELT = "green_belt"
    RIVERSIDE = "riverside"
    PERI_URBAN = "peri_urban"


@dataclass
class WardBase:
    """Static (slowly-changing) ward attributes that seed all synthetic layers."""

    ward_id: str
    name: str
    archetype: WardArchetype
    polygon: list[list[float]]  # ring of [lon, lat]
    centroid: tuple[float, float]  # (lon, lat)
    area_km2: float
    built_up_density: float  # 0-1
    green_space_pct: float  # 0-100
    water_body_pct: float  # 0-100
    road_density_km_per_km2: float
    building_height_mean_m: float
    albedo_base: float  # 0-1 surface reflectivity
    population_density_per_km2: float
    population_total: int
    vulnerable_population_pct: float  # 0-100 (elderly/children/outdoor-worker proxy)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["archetype"] = self.archetype.value
        return d

    def to_geojson_feature(self) -> dict:
        return {
            "type": "Feature",
            "properties": {
                "ward_id": self.ward_id,
                "name": self.name,
                "archetype": self.archetype.value,
                "area_km2": self.area_km2,
                "built_up_density": self.built_up_density,
                "green_space_pct": self.green_space_pct,
                "water_body_pct": self.water_body_pct,
                "population_density_per_km2": self.population_density_per_km2,
                "population_total": self.population_total,
            },
            "geometry": {"type": "Polygon", "coordinates": [self.polygon]},
        }
