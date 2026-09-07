"""Intervention definitions and modular per-intervention physical effect
models.

Each intervention is parameterized by a `coverage_pct` (0-100), meaning the
percentage of the ward's built/available surface converted to that
intervention. Effects are expressed as deltas to the same attributes the
energy balance model consumes (albedo, green_space_pct, water_body_pct),
so the simulation engine can re-run `physics.energy_balance.estimate_lst`
under "what-if" conditions -- the cooling estimate is a genuine physics
recomputation, not a lookup table.

Unit costs / land / water figures are illustrative, planning-level
placeholders (documented) calibrated to be directionally reasonable
(trees and green roofs cost more and need more water than reflective
paint), NOT sourced from a validated costing database.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class InterventionType(str, Enum):
    URBAN_TREES = "urban_trees"
    COOL_ROOFS = "cool_roofs"
    GREEN_ROOFS = "green_roofs"
    VEGETATION_CORRIDORS = "vegetation_corridors"
    BLUE_INFRASTRUCTURE = "blue_infrastructure"
    REFLECTIVE_SURFACES = "reflective_surfaces"


@dataclass(frozen=True)
class InterventionMeta:
    label: str
    description: str
    unit_cost_usd_per_pct_per_km2: float
    land_fraction_of_coverage: float  # fraction of covered % that requires new/converted land
    water_m3_per_year_per_pct_per_km2: float
    max_coverage_pct: float


INTERVENTION_METADATA: dict[InterventionType, InterventionMeta] = {
    InterventionType.URBAN_TREES: InterventionMeta(
        label="Urban Trees",
        description="Street and park tree planting increasing canopy cover.",
        unit_cost_usd_per_pct_per_km2=60_000,
        land_fraction_of_coverage=0.9,
        water_m3_per_year_per_pct_per_km2=150,
        max_coverage_pct=40,
    ),
    InterventionType.COOL_ROOFS: InterventionMeta(
        label="Cool Roofs",
        description="High-albedo reflective roof coatings on existing buildings.",
        unit_cost_usd_per_pct_per_km2=45_000,
        land_fraction_of_coverage=0.0,
        water_m3_per_year_per_pct_per_km2=0,
        max_coverage_pct=80,
    ),
    InterventionType.GREEN_ROOFS: InterventionMeta(
        label="Green Roofs",
        description="Vegetated rooftop systems adding evapotranspirative cooling.",
        unit_cost_usd_per_pct_per_km2=400_000,
        land_fraction_of_coverage=0.0,
        water_m3_per_year_per_pct_per_km2=80,
        max_coverage_pct=60,
    ),
    InterventionType.VEGETATION_CORRIDORS: InterventionMeta(
        label="Vegetation Corridors",
        description="Connected linear green corridors along roads/waterways.",
        unit_cost_usd_per_pct_per_km2=75_000,
        land_fraction_of_coverage=0.85,
        water_m3_per_year_per_pct_per_km2=130,
        max_coverage_pct=30,
    ),
    InterventionType.BLUE_INFRASTRUCTURE: InterventionMeta(
        label="Blue Infrastructure",
        description="Ponds, wetlands and daylighted waterways for evaporative cooling.",
        unit_cost_usd_per_pct_per_km2=220_000,
        land_fraction_of_coverage=0.95,
        water_m3_per_year_per_pct_per_km2=0,
        max_coverage_pct=15,
    ),
    InterventionType.REFLECTIVE_SURFACES: InterventionMeta(
        label="Reflective Surfaces",
        description="High-albedo pavement/road surface treatments.",
        unit_cost_usd_per_pct_per_km2=55_000,
        land_fraction_of_coverage=0.0,
        water_m3_per_year_per_pct_per_km2=0,
        max_coverage_pct=70,
    ),
}


@dataclass
class InterventionConfig:
    type: InterventionType
    coverage_pct: float  # 0-100

    def clamp(self) -> "InterventionConfig":
        meta = INTERVENTION_METADATA[self.type]
        return InterventionConfig(self.type, max(0.0, min(self.coverage_pct, meta.max_coverage_pct)))


def apply_intervention_deltas(
    base_attrs: dict, interventions: list[InterventionConfig]
) -> dict:
    """Returns a new attrs dict (albedo, green_space_pct, water_body_pct,
    built_up_density) reflecting the combined effect of all interventions."""
    attrs = dict(base_attrs)
    for cfg in interventions:
        cfg = cfg.clamp()
        frac = cfg.coverage_pct / 100.0
        if cfg.type == InterventionType.URBAN_TREES:
            attrs["green_space_pct"] = min(100.0, attrs["green_space_pct"] + frac * 35.0)
        elif cfg.type == InterventionType.COOL_ROOFS:
            roof_area_frac = frac * attrs["built_up_density"] * 0.55
            attrs["albedo"] = min(0.85, attrs["albedo"] + roof_area_frac * 0.45)
        elif cfg.type == InterventionType.GREEN_ROOFS:
            roof_area_frac = frac * attrs["built_up_density"] * 0.55
            attrs["green_space_pct"] = min(100.0, attrs["green_space_pct"] + roof_area_frac * 55.0)
            attrs["albedo"] = min(0.85, attrs["albedo"] + roof_area_frac * 0.06)
        elif cfg.type == InterventionType.VEGETATION_CORRIDORS:
            attrs["green_space_pct"] = min(100.0, attrs["green_space_pct"] + frac * 22.0)
            attrs["built_up_density"] = max(0.0, attrs["built_up_density"] - frac * 0.04)
        elif cfg.type == InterventionType.BLUE_INFRASTRUCTURE:
            attrs["water_body_pct"] = min(60.0, attrs["water_body_pct"] + frac * 18.0)
        elif cfg.type == InterventionType.REFLECTIVE_SURFACES:
            road_area_frac = frac * 0.5
            attrs["albedo"] = min(0.85, attrs["albedo"] + road_area_frac * 0.35)
    return attrs


def estimate_resource_needs(interventions: list[InterventionConfig], area_km2: float) -> dict:
    total_cost = 0.0
    total_land_km2 = 0.0
    total_water_m3 = 0.0
    breakdown = []
    for cfg in interventions:
        cfg = cfg.clamp()
        meta = INTERVENTION_METADATA[cfg.type]
        cost = meta.unit_cost_usd_per_pct_per_km2 * cfg.coverage_pct * area_km2
        land = meta.land_fraction_of_coverage * (cfg.coverage_pct / 100.0) * area_km2
        water = meta.water_m3_per_year_per_pct_per_km2 * cfg.coverage_pct * area_km2
        total_cost += cost
        total_land_km2 += land
        total_water_m3 += water
        breakdown.append(
            {
                "type": cfg.type.value,
                "label": meta.label,
                "coverage_pct": cfg.coverage_pct,
                "cost_usd": round(cost, 0),
                "land_km2": round(land, 4),
                "water_m3_per_year": round(water, 0),
            }
        )
    return {
        "total_cost_usd": round(total_cost, 0),
        "total_land_km2": round(total_land_km2, 4),
        "total_water_m3_per_year": round(total_water_m3, 0),
        "breakdown": breakdown,
    }
