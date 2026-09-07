import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.audit import log_audit
from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.city import Ward
from ...models.user import User
from ...schemas.simulation import InterventionCatalogItem, SimulationRequest, SimulationResultOut
from ...services import simulation_service
from coolgrid_ml.simulation.interventions import INTERVENTION_METADATA

router = APIRouter(tags=["simulation"], dependencies=[Depends(get_current_user)])


@router.get("/interventions/catalog", response_model=list[InterventionCatalogItem])
def intervention_catalog():
    return [
        InterventionCatalogItem(
            type=t.value, label=m.label, description=m.description,
            unit_cost_usd_per_pct_per_km2=m.unit_cost_usd_per_pct_per_km2,
            land_fraction_of_coverage=m.land_fraction_of_coverage,
            water_m3_per_year_per_pct_per_km2=m.water_m3_per_year_per_pct_per_km2,
            max_coverage_pct=m.max_coverage_pct,
        )
        for t, m in INTERVENTION_METADATA.items()
    ]


@router.post("/simulations", response_model=SimulationResultOut, status_code=status.HTTP_201_CREATED)
def run_simulation(payload: SimulationRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ward = db.get(Ward, payload.ward_id)
    if ward is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ward not found")
    result = simulation_service.run_simulation(db, ward, payload.interventions, user)
    log_audit(db, action="run_simulation", resource_type="simulation", user_id=user.id, resource_id=str(result.id))
    return result


@router.get("/simulations/{simulation_id}", response_model=SimulationResultOut)
def get_simulation(simulation_id: uuid.UUID, db: Session = Depends(get_db)):
    record = simulation_service.get_simulation(db, simulation_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation not found")
    ward = db.get(Ward, record.ward_id)
    from ...schemas.simulation import InterventionInput, ResourceBreakdownItem

    return SimulationResultOut(
        id=record.id, ward_id=ward.id, ward_name=ward.name,
        interventions=[InterventionInput(**i) for i in record.interventions_json],
        baseline_lst=record.baseline_lst, simulated_lst=record.simulated_lst,
        expected_cooling_c=record.expected_cooling_c, cooling_ci_low=record.cooling_ci_low,
        cooling_ci_high=record.cooling_ci_high, confidence=record.confidence,
        baseline_risk=record.baseline_risk, simulated_risk=record.simulated_risk,
        risk_reduction_pct=record.risk_reduction_pct, cost_usd=record.cost_usd,
        land_km2=record.land_km2, water_m3_per_year=record.water_m3_per_year,
        population_benefited=record.population_benefited,
        resource_breakdown=[ResourceBreakdownItem(**b) for b in record.resource_breakdown_json],
    )
