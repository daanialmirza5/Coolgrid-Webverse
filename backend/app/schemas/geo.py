import uuid

from pydantic import BaseModel

from ..models.city import WardArchetype


class CityOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    country: str
    is_demo: bool
    bbox: list[float]

    model_config = {"from_attributes": True}


class WardOut(BaseModel):
    id: uuid.UUID
    city_id: uuid.UUID
    ward_code: str
    name: str
    archetype: WardArchetype
    centroid_lon: float
    centroid_lat: float
    area_km2: float
    built_up_density: float
    green_space_pct: float
    water_body_pct: float
    road_density_km_per_km2: float
    building_height_mean_m: float
    albedo_base: float
    population_density_per_km2: float
    population_total: int
    vulnerable_population_pct: float

    model_config = {"from_attributes": True}


class WardGeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: dict
    properties: dict


class WardGeoJSONCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[WardGeoJSONFeature]
