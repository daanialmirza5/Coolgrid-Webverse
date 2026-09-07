"""Synthetic demonstration city generator.

Generates a labeled DEMO city loosely shaped on Pune, India's bounding box
(the hackathon team's home city) purely for a geographically plausible map
extent. Ward geometry is a regular grid (NOT real administrative boundaries)
and every attribute is synthetically generated with a fixed random seed for
reproducibility. Nothing here originates from Landsat, Sentinel, census, or
any other real data source.
"""

from __future__ import annotations

import numpy as np

from .schema import WardArchetype, WardBase

DEMO_CITY_ID = "pune-demo"
DEMO_CITY_NAME = "Pune (Demo Dataset)"

# Approximate Pune metro bounding box (lon_min, lat_min, lon_max, lat_max).
BBOX = (73.755, 18.440, 73.955, 18.620)
GRID_COLS = 6
GRID_ROWS = 4

_ARCHETYPE_WEIGHTS = {
    WardArchetype.DENSE_CORE: 0.20,
    WardArchetype.RESIDENTIAL: 0.30,
    WardArchetype.INDUSTRIAL: 0.15,
    WardArchetype.GREEN_BELT: 0.15,
    WardArchetype.RIVERSIDE: 0.10,
    WardArchetype.PERI_URBAN: 0.10,
}

# archetype -> (built_up, green_pct, water_pct, road_density, bldg_height, albedo, pop_density, vulnerable_pct)
_ARCHETYPE_PROFILE = {
    WardArchetype.DENSE_CORE: dict(built_up=(0.75, 0.90), green=(2, 8), water=(0, 2), road=(14, 20), height=(15, 35), albedo=(0.10, 0.16), pop=(18000, 32000), vuln=(18, 28)),
    WardArchetype.RESIDENTIAL: dict(built_up=(0.45, 0.65), green=(10, 22), water=(0, 3), road=(8, 13), height=(8, 16), albedo=(0.14, 0.20), pop=(9000, 18000), vuln=(15, 24)),
    WardArchetype.INDUSTRIAL: dict(built_up=(0.60, 0.80), green=(3, 10), water=(0, 2), road=(6, 11), height=(6, 12), albedo=(0.09, 0.14), pop=(2000, 6000), vuln=(10, 16)),
    WardArchetype.GREEN_BELT: dict(built_up=(0.10, 0.25), green=(45, 70), water=(1, 5), road=(2, 5), height=(4, 8), albedo=(0.18, 0.24), pop=(1500, 5000), vuln=(12, 20)),
    WardArchetype.RIVERSIDE: dict(built_up=(0.30, 0.50), green=(15, 30), water=(15, 35), road=(5, 9), height=(6, 14), albedo=(0.15, 0.22), pop=(6000, 12000), vuln=(16, 24)),
    WardArchetype.PERI_URBAN: dict(built_up=(0.20, 0.40), green=(25, 45), water=(0, 4), road=(3, 6), height=(4, 9), albedo=(0.17, 0.23), pop=(2500, 7000), vuln=(14, 22)),
}


def _pick_archetype(rng: np.random.Generator) -> WardArchetype:
    keys = list(_ARCHETYPE_WEIGHTS.keys())
    probs = list(_ARCHETYPE_WEIGHTS.values())
    idx = rng.choice(len(keys), p=probs)
    return keys[idx]


def generate_city(seed: int = 42) -> list[WardBase]:
    rng = np.random.default_rng(seed)
    lon_min, lat_min, lon_max, lat_max = BBOX
    dlon = (lon_max - lon_min) / GRID_COLS
    dlat = (lat_max - lat_min) / GRID_ROWS

    # Distance-to-center weighting nudges dense_core toward the middle of the
    # grid and green/peri-urban toward the edges, which keeps the map visually
    # coherent (a plausible city shape) without hand-placing every ward.
    center_col, center_row = (GRID_COLS - 1) / 2, (GRID_ROWS - 1) / 2
    max_dist = np.hypot(center_col, center_row)

    wards: list[WardBase] = []
    idx = 1
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            dist = np.hypot(col - center_col, row - center_row) / max_dist
            archetype = _archetype_for_position(rng, dist)

            lon0 = lon_min + col * dlon
            lat0 = lat_min + row * dlat
            lon1, lat1 = lon0 + dlon, lat0 + dlat
            ring = [[lon0, lat0], [lon1, lat0], [lon1, lat1], [lon0, lat1], [lon0, lat0]]
            centroid = (round((lon0 + lon1) / 2, 5), round((lat0 + lat1) / 2, 5))

            # km^2 approx at this latitude (WGS84 quick approximation).
            km_per_deg_lat = 111.0
            km_per_deg_lon = 111.0 * np.cos(np.radians((lat0 + lat1) / 2))
            area_km2 = round(dlon * km_per_deg_lon * dlat * km_per_deg_lat, 2)

            profile = _ARCHETYPE_PROFILE[archetype]
            built_up = round(float(rng.uniform(*profile["built_up"])), 3)
            green_pct = round(float(rng.uniform(*profile["green"])), 1)
            water_pct = round(float(rng.uniform(*profile["water"])), 1)
            road_density = round(float(rng.uniform(*profile["road"])), 2)
            height = round(float(rng.uniform(*profile["height"])), 1)
            albedo = round(float(rng.uniform(*profile["albedo"])), 3)
            pop_density = round(float(rng.uniform(*profile["pop"])), 0)
            vuln_pct = round(float(rng.uniform(*profile["vuln"])), 1)
            population_total = int(pop_density * area_km2)

            ward_id = f"ward-{idx:02d}"
            wards.append(
                WardBase(
                    ward_id=ward_id,
                    name=f"Ward {idx}",
                    archetype=archetype,
                    polygon=ring,
                    centroid=centroid,
                    area_km2=area_km2,
                    built_up_density=built_up,
                    green_space_pct=green_pct,
                    water_body_pct=water_pct,
                    road_density_km_per_km2=road_density,
                    building_height_mean_m=height,
                    albedo_base=albedo,
                    population_density_per_km2=pop_density,
                    population_total=population_total,
                    vulnerable_population_pct=vuln_pct,
                )
            )
            idx += 1
    return wards


def _archetype_for_position(rng: np.random.Generator, normalized_dist: float) -> WardArchetype:
    """Bias archetype choice by distance-from-center, then sample."""
    if normalized_dist < 0.35:
        weights = {
            WardArchetype.DENSE_CORE: 0.55,
            WardArchetype.RESIDENTIAL: 0.30,
            WardArchetype.INDUSTRIAL: 0.15,
        }
    elif normalized_dist < 0.7:
        weights = {
            WardArchetype.RESIDENTIAL: 0.40,
            WardArchetype.INDUSTRIAL: 0.20,
            WardArchetype.RIVERSIDE: 0.20,
            WardArchetype.GREEN_BELT: 0.10,
            WardArchetype.PERI_URBAN: 0.10,
        }
    else:
        weights = {
            WardArchetype.GREEN_BELT: 0.35,
            WardArchetype.PERI_URBAN: 0.35,
            WardArchetype.RESIDENTIAL: 0.15,
            WardArchetype.RIVERSIDE: 0.15,
        }
    keys = list(weights.keys())
    probs = np.array(list(weights.values()))
    probs = probs / probs.sum()
    idx = rng.choice(len(keys), p=probs)
    return keys[idx]


def city_bounds() -> tuple[float, float, float, float]:
    return BBOX
