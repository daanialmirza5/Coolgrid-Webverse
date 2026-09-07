from __future__ import annotations

import uuid

from coolgrid_ml.optimization.optimizer import OptimizationConstraints as MLConstraints
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..models.city import Ward
from ..models.intervention import OptimizationRun, Recommendation
from ..models.user import User
from ..schemas.simulation import (
    OptimizationConstraintsIn,
    OptimizationRunOut,
    RankedInterventionItem,
    RankedStrategyOut,
    RecommendationOut,
)
from .ml_registry import get_ml_registry
from .ward_adapter import to_ward_base


def run_optimization(db: Session, ward: Ward, constraints: OptimizationConstraintsIn, user: User | None) -> OptimizationRunOut:
    registry = get_ml_registry()
    ward_base = to_ward_base(ward)

    ml_constraints = MLConstraints(
        budget_usd=constraints.budget_usd,
        land_km2=constraints.land_km2,
        water_m3_per_year=constraints.water_m3_per_year,
        target_cooling_c=constraints.target_cooling_c,
        population_priority=constraints.population_priority,
        risk_priority=constraints.risk_priority,
    )
    strategies = registry.optimizer.optimize(ward_base, ml_constraints, as_of=get_settings().effective_today(), top_k=5)

    results_json = [
        {
            "rank": s.rank,
            "interventions": s.interventions,
            "score": s.score,
            "expected_cooling_c": s.expected_cooling_c,
            "cooling_ci_low": s.cooling_ci_low,
            "cooling_ci_high": s.cooling_ci_high,
            "cost_usd": s.cost_usd,
            "population_benefited": s.population_benefited,
            "land_km2": s.land_km2,
            "water_m3_per_year": s.water_m3_per_year,
            "risk_reduction_pct": s.risk_reduction_pct,
            "confidence": s.confidence,
            "reason": s.reason,
        }
        for s in strategies
    ]

    run = OptimizationRun(
        ward_id=ward.id,
        user_id=user.id if user else None,
        constraints_json=constraints.model_dump(mode="json"),
        results_json=results_json,
    )
    db.add(run)
    db.flush()

    for s in strategies:
        top_type = s.interventions[0]["label"] if s.interventions else "Intervention"
        title = f"#{s.rank}: {top_type}" + (f" + {len(s.interventions) - 1} more" if len(s.interventions) > 1 else "")
        db.add(
            Recommendation(
                ward_id=ward.id,
                optimization_run_id=run.id,
                rank=s.rank,
                title=title,
                narrative_text=s.reason,
                metrics_json={
                    "expected_cooling_c": s.expected_cooling_c,
                    "cost_usd": s.cost_usd,
                    "population_benefited": s.population_benefited,
                    "risk_reduction_pct": s.risk_reduction_pct,
                    "confidence": s.confidence,
                },
            )
        )
    db.commit()
    db.refresh(run)

    return OptimizationRunOut(
        id=run.id,
        ward_id=ward.id,
        ward_name=ward.name,
        constraints=constraints,
        strategies=[
            RankedStrategyOut(
                rank=s.rank,
                interventions=[RankedInterventionItem(**i) for i in s.interventions],
                score=s.score,
                expected_cooling_c=s.expected_cooling_c,
                cooling_ci_low=s.cooling_ci_low,
                cooling_ci_high=s.cooling_ci_high,
                cost_usd=s.cost_usd,
                population_benefited=s.population_benefited,
                land_km2=s.land_km2,
                water_m3_per_year=s.water_m3_per_year,
                risk_reduction_pct=s.risk_reduction_pct,
                confidence=s.confidence,
                reason=s.reason,
            )
            for s in strategies
        ],
    )


def list_recommendations(db: Session, ward: Ward) -> list[RecommendationOut]:
    rows = (
        db.query(Recommendation)
        .filter(Recommendation.ward_id == ward.id)
        .order_by(Recommendation.created_at.desc(), Recommendation.rank.asc())
        .limit(20)
        .all()
    )
    return [
        RecommendationOut(
            id=r.id, ward_id=ward.id, ward_name=ward.name, rank=r.rank,
            title=r.title, narrative_text=r.narrative_text, metrics=r.metrics_json,
        )
        for r in rows
    ]


def get_optimization_run(db: Session, run_id: uuid.UUID) -> OptimizationRun | None:
    return db.get(OptimizationRun, run_id)
