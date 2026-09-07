import uuid
from datetime import date

from pydantic import BaseModel

from ..models.heat import RiskLevel


class HotspotOut(BaseModel):
    id: uuid.UUID
    ward_id: uuid.UUID
    ward_name: str
    detected_on: date
    lst_celsius: float
    lst_lower: float
    lst_upper: float
    heat_score: float
    risk_level: RiskLevel
    confidence: float
    rank_in_city: int | None
    centroid_lon: float
    centroid_lat: float

    model_config = {"from_attributes": True}


class DriverContributionOut(BaseModel):
    feature: str
    label: str
    value: float
    shap_value: float
    direction: str
    relative_contribution_pct: float


class DriverAnalysisOut(BaseModel):
    ward_id: uuid.UUID
    ward_name: str
    lst_celsius: float
    base_value: float
    drivers: list[DriverContributionOut]
    narrative: str


class PredictionPointOut(BaseModel):
    horizon_days: int
    target_date: date
    predicted_lst: float
    predicted_lst_lower: float
    predicted_lst_upper: float
    change_from_current_c: float
    risk_level: RiskLevel
    confidence: float
    physics_estimate_lst: float
    disclaimer: str


class PredictionResponse(BaseModel):
    ward_id: uuid.UUID
    ward_name: str
    as_of: date
    current_lst: float
    points: list[PredictionPointOut]


class DashboardSummaryOut(BaseModel):
    city_id: uuid.UUID
    city_name: str
    generated_at: str
    avg_lst: float
    max_lst: float
    hotspot_count: int
    population_exposed: int
    high_risk_ward_count: int
    avg_vegetation_pct: float
    avg_built_up_pct: float
    is_demo: bool
    model_version: str


class WardComparisonRow(BaseModel):
    ward_id: uuid.UUID
    ward_name: str
    archetype: str
    lst_celsius: float
    heat_score: float
    risk_level: RiskLevel
    green_space_pct: float
    built_up_density: float
    population_total: int
