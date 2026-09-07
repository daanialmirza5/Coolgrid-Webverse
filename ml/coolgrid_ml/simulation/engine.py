"""What-if intervention simulation engine.

Runs the simplified surface energy balance twice -- once with the ward's
baseline attributes, once with attributes perturbed by the requested
interventions -- holding weather constant so the isolated cooling effect of
the intervention portfolio is what's measured. A small Monte Carlo
perturbation of weather inputs turns that into a confidence interval,
reflecting the documented reality that real-world cooling depends on
execution, season, and local conditions (not a fixed guaranteed delta).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np

from ..data.climatology import (
    seasonal_air_temp,
    seasonal_humidity,
    seasonal_radiation,
    seasonal_wind,
)
from ..data.schema import WardBase
from ..detection.model import HeatDetectionModel, RiskLevel
from ..physics.energy_balance import estimate_lst
from .interventions import (
    InterventionConfig,
    apply_intervention_deltas,
    estimate_resource_needs,
)

N_MONTE_CARLO = 60


@dataclass
class SimulationResult:
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
    resource_breakdown: list[dict] = field(default_factory=list)


class SimulationEngine:
    def __init__(self, model: HeatDetectionModel):
        self.model = model

    def simulate_deterministic_lst(
        self,
        ward: WardBase,
        interventions: list[InterventionConfig],
        as_of: date | None = None,
    ) -> tuple[float, float]:
        """Fast, noise-free (baseline, simulated) LST pair -- used by the
        optimizer's combinatorial search, where hundreds of candidate
        portfolios must be scored cheaply. Full `simulate()` (with Monte
        Carlo confidence intervals) is then only run for the finalists."""
        as_of = as_of or date.today()
        doy = as_of.timetuple().tm_yday
        wx = dict(
            air_temp_c=seasonal_air_temp(doy),
            shortwave_wm2=seasonal_radiation(doy),
            humidity_pct=seasonal_humidity(doy),
            wind_speed_ms=seasonal_wind(doy),
        )
        base_attrs = dict(
            albedo=ward.albedo_base,
            green_space_pct=ward.green_space_pct,
            water_body_pct=ward.water_body_pct,
            built_up_density=ward.built_up_density,
        )
        sim_attrs = apply_intervention_deltas(base_attrs, interventions)
        baseline_lst = estimate_lst(built_up_density=base_attrs["built_up_density"], **base_attrs_no_bud(base_attrs), **wx).lst_celsius
        simulated_lst = estimate_lst(built_up_density=sim_attrs["built_up_density"], **base_attrs_no_bud(sim_attrs), **wx).lst_celsius
        return baseline_lst, simulated_lst

    def simulate(
        self,
        ward: WardBase,
        interventions: list[InterventionConfig],
        as_of: date | None = None,
        current_lst_anchor: float | None = None,
    ) -> SimulationResult:
        """`current_lst_anchor`, when given, re-bases baseline/simulated LST
        (and their CI) onto the ward's actual currently-detected LST (from
        the XGBoost detector on today's real/noisy observation) rather than
        this engine's own pure-physics baseline for a "typical" day.
        Otherwise the simulator's "baseline" and the dashboard's "current
        LST" for the same ward on the same day could legitimately differ
        (different models, and physics uses smooth climatology while the
        detector sees today's noisy reading) in a way that looks like a bug.
        The cooling *delta* itself is always the genuine physics
        recomputation under the intervention; only the anchor point shifts."""
        as_of = as_of or date.today()
        doy = as_of.timetuple().tm_yday
        base_weather = dict(
            air_temp_c=seasonal_air_temp(doy),
            shortwave_wm2=seasonal_radiation(doy),
            humidity_pct=seasonal_humidity(doy),
            wind_speed_ms=seasonal_wind(doy),
        )

        base_attrs = dict(
            albedo=ward.albedo_base,
            green_space_pct=ward.green_space_pct,
            water_body_pct=ward.water_body_pct,
            built_up_density=ward.built_up_density,
        )
        sim_attrs = apply_intervention_deltas(base_attrs, interventions)

        rng = np.random.default_rng(hash((ward.ward_id, as_of.isoformat())) % (2**32))
        baseline_samples = []
        simulated_samples = []
        for _ in range(N_MONTE_CARLO):
            wx = {
                "air_temp_c": base_weather["air_temp_c"] + rng.normal(0, 1.0),
                "shortwave_wm2": max(0, base_weather["shortwave_wm2"] + rng.normal(0, 25)),
                "humidity_pct": np.clip(base_weather["humidity_pct"] + rng.normal(0, 5), 10, 100),
                "wind_speed_ms": max(0.3, base_weather["wind_speed_ms"] + rng.normal(0, 0.6)),
            }
            baseline_samples.append(
                estimate_lst(built_up_density=base_attrs["built_up_density"], **base_attrs_no_bud(base_attrs), **wx).lst_celsius
            )
            simulated_samples.append(
                estimate_lst(built_up_density=sim_attrs["built_up_density"], **base_attrs_no_bud(sim_attrs), **wx).lst_celsius
            )

        baseline_samples = np.array(baseline_samples)
        simulated_samples = np.array(simulated_samples)
        cooling_samples = baseline_samples - simulated_samples

        baseline_lst = float(baseline_samples.mean())
        simulated_lst = float(simulated_samples.mean())
        expected_cooling = float(cooling_samples.mean())
        ci_low = float(np.percentile(cooling_samples, 10))
        ci_high = float(np.percentile(cooling_samples, 90))

        if current_lst_anchor is not None:
            baseline_lst = current_lst_anchor
            simulated_lst = current_lst_anchor - expected_cooling

        total_coverage = sum(c.clamp().coverage_pct for c in interventions) or 0.0
        confidence = float(np.clip(0.85 - 0.0025 * total_coverage, 0.4, 0.9))

        baseline_risk = self.model._risk_level(baseline_lst)
        simulated_risk = self.model._risk_level(simulated_lst)
        baseline_score = self.model._heat_score(baseline_lst)
        simulated_score = self.model._heat_score(simulated_lst)
        risk_reduction_pct = float(
            np.clip((baseline_score - simulated_score) / max(baseline_score, 1e-6) * 100, -100, 100)
        )

        resources = estimate_resource_needs(interventions, ward.area_km2)

        coverage_fraction_avg = np.clip(total_coverage / 100.0, 0, 1)
        population_benefited = int(round(ward.population_total * (0.3 + 0.7 * coverage_fraction_avg)))

        return SimulationResult(
            baseline_lst=round(baseline_lst, 2),
            simulated_lst=round(simulated_lst, 2),
            expected_cooling_c=round(expected_cooling, 2),
            cooling_ci_low=round(ci_low, 2),
            cooling_ci_high=round(ci_high, 2),
            confidence=round(confidence, 3),
            baseline_risk=baseline_risk,
            simulated_risk=simulated_risk,
            risk_reduction_pct=round(risk_reduction_pct, 1),
            cost_usd=resources["total_cost_usd"],
            land_km2=resources["total_land_km2"],
            water_m3_per_year=resources["total_water_m3_per_year"],
            population_benefited=population_benefited,
            resource_breakdown=resources["breakdown"],
        )


def base_attrs_no_bud(attrs: dict) -> dict:
    return {k: v for k, v in attrs.items() if k != "built_up_density"}
