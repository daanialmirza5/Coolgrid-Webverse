import uuid

from pydantic import BaseModel, Field

from ..models.heat import RiskLevel
from ..models.intervention import InterventionType


class InterventionInput(BaseModel):
    type: InterventionType
    coverage_pct: float = Field(ge=0, le=100)


class InterventionCatalogItem(BaseModel):
    type: InterventionType
    label: str
    description: str
    unit_cost_usd_per_pct_per_km2: float
    land_fraction_of_coverage: float
    water_m3_per_year_per_pct_per_km2: float
    max_coverage_pct: float


class SimulationRequest(BaseModel):
    ward_id: uuid.UUID
    interventions: list[InterventionInput] = Field(min_length=1)


class ResourceBreakdownItem(BaseModel):
    type: str
    label: str
    coverage_pct: float
    cost_usd: float
    land_km2: float
    water_m3_per_year: float


class SimulationResultOut(BaseModel):
    id: uuid.UUID
    ward_id: uuid.UUID
    ward_name: str
    interventions: list[InterventionInput]
    baseline_lst: float
    simulated_lst: float
    expected_cooling_c: float
    cooling_ci_low: float
    cooling_ci_high: float
    confidence: float
    baseline_risk: RiskLevel
    simulated_risk: RiskLevel
    risk_reduction_pct: float
    cost_usd: float
    land_km2: float
    water_m3_per_year: float
    population_benefited: int
    resource_breakdown: list[ResourceBreakdownItem]


class OptimizationConstraintsIn(BaseModel):
    ward_id: uuid.UUID
    budget_usd: float = Field(gt=0)
    land_km2: float = Field(gt=0)
    water_m3_per_year: float = Field(gt=0)
    target_cooling_c: float | None = None
    population_priority: float = Field(default=1.0, ge=0, le=2)
    risk_priority: float = Field(default=1.0, ge=0, le=2)


class RankedInterventionItem(BaseModel):
    type: str
    label: str
    coverage_pct: float


class RankedStrategyOut(BaseModel):
    rank: int
    interventions: list[RankedInterventionItem]
    score: float
    expected_cooling_c: float
    cooling_ci_low: float
    cooling_ci_high: float
    cost_usd: float
    population_benefited: int
    land_km2: float
    water_m3_per_year: float
    risk_reduction_pct: float
    confidence: float
    reason: str


class OptimizationRunOut(BaseModel):
    id: uuid.UUID
    ward_id: uuid.UUID
    ward_name: str
    constraints: OptimizationConstraintsIn
    strategies: list[RankedStrategyOut]


class RecommendationOut(BaseModel):
    id: uuid.UUID
    ward_id: uuid.UUID
    ward_name: str
    rank: int
    title: str
    narrative_text: str
    metrics: dict
