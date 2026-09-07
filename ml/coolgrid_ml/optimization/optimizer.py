"""Constraint-aware intervention portfolio optimizer.

Performs a discretized grid search over coverage levels for every
intervention type, filters candidates that respect the user's budget/land/
water constraints, scores the feasible set on a weighted multi-objective
function (maximize cooling, population benefit, risk reduction; minimize
cost, land, water), and returns the top-ranked portfolios with a natural-
language reason.

This is a combinatorial search over a discretized action space, not a full
integer/linear program -- appropriate for six intervention types with a
handful of coverage levels each, and simple to reason about and extend.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from datetime import date

import numpy as np

from ..data.schema import WardBase
from ..detection.model import HeatDetectionModel
from ..simulation.engine import SimulationEngine
from ..simulation.interventions import (
    INTERVENTION_METADATA,
    InterventionConfig,
    InterventionType,
    estimate_resource_needs,
)

COVERAGE_LEVELS_FRACTIONS = (0.0, 0.33, 0.66, 1.0)  # fraction of each intervention's max_coverage_pct


@dataclass
class OptimizationConstraints:
    budget_usd: float
    land_km2: float
    water_m3_per_year: float
    target_cooling_c: float | None = None
    population_priority: float = 1.0  # 0-2, scales population-benefit weight
    risk_priority: float = 1.0  # 0-2, scales risk-reduction weight


@dataclass
class RankedStrategy:
    rank: int
    interventions: list[dict]
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


class InterventionOptimizer:
    def __init__(self, model: HeatDetectionModel):
        self.model = model
        self.engine = SimulationEngine(model)

    def _candidate_portfolios(self) -> list[list[InterventionConfig]]:
        types = list(InterventionType)
        level_grids = [
            [frac * INTERVENTION_METADATA[t].max_coverage_pct for frac in COVERAGE_LEVELS_FRACTIONS]
            for t in types
        ]
        portfolios = []
        for combo in itertools.product(*level_grids):
            if all(c == 0 for c in combo):
                continue
            portfolios.append(
                [InterventionConfig(t, cov) for t, cov in zip(types, combo) if cov > 0]
            )
        return portfolios

    def optimize(
        self,
        ward: WardBase,
        constraints: OptimizationConstraints,
        as_of: date | None = None,
        top_k: int = 5,
    ) -> list[RankedStrategy]:
        as_of = as_of or date.today()
        candidates = self._candidate_portfolios()

        scored = []
        for portfolio in candidates:
            resources = estimate_resource_needs(portfolio, ward.area_km2)
            if resources["total_cost_usd"] > constraints.budget_usd:
                continue
            if resources["total_land_km2"] > constraints.land_km2:
                continue
            if resources["total_water_m3_per_year"] > constraints.water_m3_per_year:
                continue

            baseline_lst, simulated_lst = self.engine.simulate_deterministic_lst(ward, portfolio, as_of)
            cooling = baseline_lst - simulated_lst
            if constraints.target_cooling_c is not None and cooling < constraints.target_cooling_c * 0.5:
                # Keep near-target candidates in the pool but drop clearly insufficient ones.
                continue

            baseline_score = self.model._heat_score(baseline_lst)
            simulated_score = self.model._heat_score(simulated_lst)
            risk_reduction_pct = (baseline_score - simulated_score) / max(baseline_score, 1e-6) * 100

            total_coverage = sum(c.coverage_pct for c in portfolio)
            coverage_fraction_avg = np.clip(total_coverage / 100.0, 0, 1)
            population_benefited = ward.population_total * (0.3 + 0.7 * coverage_fraction_avg)

            scored.append(
                {
                    "portfolio": portfolio,
                    "cooling": cooling,
                    "cost": resources["total_cost_usd"],
                    "land": resources["total_land_km2"],
                    "water": resources["total_water_m3_per_year"],
                    "population_benefited": population_benefited,
                    "risk_reduction_pct": risk_reduction_pct,
                }
            )

        if not scored:
            return []

        cooling_max = max(s["cooling"] for s in scored) or 1e-6
        cost_max = max(s["cost"] for s in scored) or 1e-6
        land_max = max(s["land"] for s in scored) or 1e-6
        water_max = max(s["water"] for s in scored) or 1e-6
        pop_max = max(s["population_benefited"] for s in scored) or 1e-6
        risk_max = max(s["risk_reduction_pct"] for s in scored) or 1e-6

        w_cooling = 1.0
        w_population = 0.8 * constraints.population_priority
        w_risk = 0.8 * constraints.risk_priority
        w_cost = 0.5
        w_land = 0.3
        w_water = 0.2

        for s in scored:
            norm_cooling = s["cooling"] / cooling_max
            norm_pop = s["population_benefited"] / pop_max
            norm_risk = s["risk_reduction_pct"] / risk_max if risk_max > 0 else 0
            norm_cost = s["cost"] / cost_max
            norm_land = s["land"] / land_max if land_max > 0 else 0
            norm_water = s["water"] / water_max if water_max > 0 else 0

            score = (
                w_cooling * norm_cooling
                + w_population * norm_pop
                + w_risk * norm_risk
                - w_cost * norm_cost
                - w_land * norm_land
                - w_water * norm_water
            )
            s["score"] = score

        scored.sort(key=lambda s: s["score"], reverse=True)

        results: list[RankedStrategy] = []
        for i, s in enumerate(scored[:top_k], start=1):
            full = self.engine.simulate(ward, s["portfolio"], as_of)
            reason = self._build_reason(ward, s["portfolio"], full, constraints)
            results.append(
                RankedStrategy(
                    rank=i,
                    interventions=[
                        {
                            "type": c.type.value,
                            "label": INTERVENTION_METADATA[c.type].label,
                            "coverage_pct": round(c.coverage_pct, 1),
                        }
                        for c in s["portfolio"]
                    ],
                    score=round(float(s["score"]), 4),
                    expected_cooling_c=full.expected_cooling_c,
                    cooling_ci_low=full.cooling_ci_low,
                    cooling_ci_high=full.cooling_ci_high,
                    cost_usd=full.cost_usd,
                    population_benefited=full.population_benefited,
                    land_km2=full.land_km2,
                    water_m3_per_year=full.water_m3_per_year,
                    risk_reduction_pct=full.risk_reduction_pct,
                    confidence=full.confidence,
                    reason=reason,
                )
            )
        return results

    def _build_reason(self, ward: WardBase, portfolio, full, constraints: OptimizationConstraints) -> str:
        labels = [INTERVENTION_METADATA[c.type].label for c in portfolio]
        if len(labels) == 1:
            combo_txt = labels[0]
        else:
            combo_txt = ", ".join(labels[:-1]) + " combined with " + labels[-1]
        return (
            f"{combo_txt} in {ward.name} is projected to cool the area by "
            f"{full.expected_cooling_c:.1f}°C (range {full.cooling_ci_low:.1f}–{full.cooling_ci_high:.1f}°C), "
            f"reducing heat risk by {full.risk_reduction_pct:.0f}% and benefiting "
            f"~{full.population_benefited:,} residents, within the ${constraints.budget_usd:,.0f} budget "
            f"and available land/water constraints."
        )
