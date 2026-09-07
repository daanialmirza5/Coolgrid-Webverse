"""Converts a DB `Ward` row into the ML package's plain `WardBase` dataclass
so `coolgrid_ml` stays independent of SQLAlchemy."""

from coolgrid_ml.data.schema import WardArchetype as MLWardArchetype
from coolgrid_ml.data.schema import WardBase

from ..models.city import Ward


def to_ward_base(ward: Ward) -> WardBase:
    return WardBase(
        ward_id=ward.ward_code,
        name=ward.name,
        archetype=MLWardArchetype(ward.archetype.value),
        polygon=[],
        centroid=(ward.centroid_lon, ward.centroid_lat),
        area_km2=ward.area_km2,
        built_up_density=ward.built_up_density,
        green_space_pct=ward.green_space_pct,
        water_body_pct=ward.water_body_pct,
        road_density_km_per_km2=ward.road_density_km_per_km2,
        building_height_mean_m=ward.building_height_mean_m,
        albedo_base=ward.albedo_base,
        population_density_per_km2=ward.population_density_per_km2,
        population_total=ward.population_total,
        vulnerable_population_pct=ward.vulnerable_population_pct,
    )
