from __future__ import annotations

import uuid

from coolgrid_ml.simulation.interventions import InterventionConfig, InterventionType as MLInterventionType
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..models.city import Ward
from ..models.heat import RiskLevel as DBRiskLevel
from ..models.intervention import Simulation
from ..models.user import User
from ..schemas.simulation import InterventionInput, ResourceBreakdownItem, SimulationResultOut
from .detection_service import build_current_features
from .ml_registry import get_ml_registry
from .ward_adapter import to_ward_base


def run_simulation(db: Session, ward: Ward, interventions: list[InterventionInput], user: User | None) -> SimulationResultOut:
    registry = get_ml_registry()
    ward_base = to_ward_base(ward)
    as_of = get_settings().effective_today()

    current_features = build_current_features(registry, [ward], as_of).drop(columns=["ward_pk", "ward_code"])
    [current_detection] = registry.detection_model.predict(current_features)

    ml_interventions = [InterventionConfig(MLInterventionType(i.type.value), i.coverage_pct) for i in interventions]
    result = registry.simulation_engine.simulate(
        ward_base, ml_interventions, as_of=as_of, current_lst_anchor=current_detection.lst_celsius
    )

    record = Simulation(
        ward_id=ward.id,
        user_id=user.id if user else None,
        interventions_json=[i.model_dump(mode="json") for i in interventions],
        baseline_lst=result.baseline_lst,
        simulated_lst=result.simulated_lst,
        expected_cooling_c=result.expected_cooling_c,
        cooling_ci_low=result.cooling_ci_low,
        cooling_ci_high=result.cooling_ci_high,
        confidence=result.confidence,
        baseline_risk=DBRiskLevel(result.baseline_risk.value),
        simulated_risk=DBRiskLevel(result.simulated_risk.value),
        risk_reduction_pct=result.risk_reduction_pct,
        cost_usd=result.cost_usd,
        land_km2=result.land_km2,
        water_m3_per_year=result.water_m3_per_year,
        population_benefited=result.population_benefited,
        resource_breakdown_json=result.resource_breakdown,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return SimulationResultOut(
        id=record.id,
        ward_id=ward.id,
        ward_name=ward.name,
        interventions=interventions,
        baseline_lst=result.baseline_lst,
        simulated_lst=result.simulated_lst,
        expected_cooling_c=result.expected_cooling_c,
        cooling_ci_low=result.cooling_ci_low,
        cooling_ci_high=result.cooling_ci_high,
        confidence=result.confidence,
        baseline_risk=result.baseline_risk,
        simulated_risk=result.simulated_risk,
        risk_reduction_pct=result.risk_reduction_pct,
        cost_usd=result.cost_usd,
        land_km2=result.land_km2,
        water_m3_per_year=result.water_m3_per_year,
        population_benefited=result.population_benefited,
        resource_breakdown=[ResourceBreakdownItem(**b) for b in result.resource_breakdown],
    )


def get_simulation(db: Session, simulation_id: uuid.UUID) -> Simulation | None:
    return db.get(Simulation, simulation_id)
