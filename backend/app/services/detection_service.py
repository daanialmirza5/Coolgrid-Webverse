"""Heat detection: builds today's feature table for a city's wards, runs it
through the trained XGBoost model, and persists one HeatMap + per-ward
Hotspot snapshot per calendar day (idempotent -- repeated calls the same day
reuse the existing snapshot instead of re-detecting)."""

from __future__ import annotations

from datetime import date

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..models.city import City, Ward
from ..models.data import Feature
from ..models.heat import HeatMap, Hotspot, RiskLevel
from .ml_registry import MLRegistry, get_ml_registry

DETECTION_MODEL_VERSION = "xgboost-v1"


def build_current_features(registry: MLRegistry, wards: list[Ward], as_of: date) -> pd.DataFrame:
    ward_ids = [w.ward_code for w in wards]
    sat_obs = {o.ward_id: o for o in registry.providers.satellite.get_observations(ward_ids, as_of)}
    urban = {f.ward_id: f for f in registry.providers.urban.get_features(ward_ids)}
    pop = {f.ward_id: f for f in registry.providers.population.get_features(ward_ids)}
    wx = {o.ward_id: o for o in registry.providers.weather.get_observations(ward_ids, as_of)}

    rows = []
    for ward in wards:
        s, u, p, w = sat_obs[ward.ward_code], urban[ward.ward_code], pop[ward.ward_code], wx[ward.ward_code]
        rows.append(
            {
                "ward_pk": ward.id,
                "ward_code": ward.ward_code,
                "ndvi": s.ndvi, "ndbi": s.ndbi, "albedo": s.albedo,
                "built_up_density": u.built_up_density, "green_space_pct": u.green_space_pct,
                "water_body_pct": u.water_body_pct, "road_density_km_per_km2": u.road_density_km_per_km2,
                "population_density_per_km2": p.population_density_per_km2,
                "humidity_pct": w.humidity_pct, "wind_speed_ms": w.wind_speed_ms,
                "shortwave_wm2": w.shortwave_radiation_wm2, "air_temp_c": w.air_temp_celsius,
            }
        )
    return pd.DataFrame(rows)


def record_feature_snapshot(db: Session, ward_id, computed_on: date, feature_row: dict, model_version: str = DETECTION_MODEL_VERSION) -> None:
    """Persists the exact feature vector fed to the detection model for one
    (ward, date), for later audit/reproducibility of a hotspot or driver
    explanation. Idempotent per (ward, date, model_version) -- repeated
    detection runs or driver-analysis calls the same day don't pile up
    duplicate snapshots."""
    existing = db.execute(
        select(Feature).where(
            Feature.ward_id == ward_id,
            Feature.computed_on == computed_on,
            Feature.model_version == model_version,
        )
    ).scalars().first()
    if existing is not None:
        return
    db.add(
        Feature(
            ward_id=ward_id,
            computed_on=computed_on,
            feature_json={k: (float(v) if isinstance(v, (int, float)) else v) for k, v in feature_row.items()},
            model_version=model_version,
        )
    )


def get_or_create_daily_heatmap(db: Session, city: City, as_of: date | None = None) -> HeatMap:
    as_of = as_of or get_settings().effective_today()

    latest = db.execute(
        select(HeatMap).where(HeatMap.city_id == city.id).order_by(HeatMap.generated_at.desc())
    ).scalars().first()
    if latest is not None:
        sample_hotspot = db.execute(
            select(Hotspot).where(Hotspot.heat_map_id == latest.id).limit(1)
        ).scalars().first()
        # Cache key is the simulated "as_of" date the detection run covers
        # (Hotspot.detected_on), not the row's real wall-clock creation time
        # -- CoolGrid's demo clock is pinned to `demo_reference_date`, so once
        # a run exists for that date it's reused indefinitely.
        if sample_hotspot is not None and sample_hotspot.detected_on == as_of:
            return latest

    registry = get_ml_registry()
    wards = db.execute(select(Ward).where(Ward.city_id == city.id)).scalars().all()
    df = build_current_features(registry, wards, as_of)
    results = registry.detection_model.predict(df)

    ward_by_code = {w.ward_code: w for w in wards}
    heat_map = HeatMap(
        city_id=city.id,
        model_version="xgboost-v1",
        avg_lst=sum(r.lst_celsius for r in results) / len(results),
        max_lst=max(r.lst_celsius for r in results),
        hotspot_count=sum(1 for r in results if r.risk_level.value in ("HIGH", "CRITICAL")),
        population_exposed=sum(
            ward_by_code[row.ward_code].population_total
            for row, r in zip(df.itertuples(), results)
            if r.risk_level.value in ("HIGH", "CRITICAL")
        ),
        summary_json={
            "avg_vegetation_pct": sum(w.green_space_pct for w in wards) / len(wards),
            "avg_built_up_pct": sum(w.built_up_density for w in wards) / len(wards) * 100,
        },
    )
    db.add(heat_map)
    db.flush()

    ranked = sorted(zip(df.itertuples(), results), key=lambda rr: rr[1].lst_celsius, reverse=True)
    for rank, (row, r) in enumerate(ranked, start=1):
        ward = ward_by_code[row.ward_code]
        driver_row = df[df["ward_code"] == row.ward_code]
        top_drivers = [
            {"label": c.label, "direction": c.direction, "relative_contribution_pct": c.relative_contribution_pct}
            for c in registry.explainer.explain_grouped(driver_row)[:3]
        ]
        record_feature_snapshot(
            db, ward.id, as_of,
            driver_row.drop(columns=["ward_pk", "ward_code"]).iloc[0].to_dict(),
        )
        db.add(
            Hotspot(
                ward_id=ward.id,
                heat_map_id=heat_map.id,
                detected_on=as_of,
                lst_celsius=r.lst_celsius,
                lst_lower=r.lst_lower,
                lst_upper=r.lst_upper,
                heat_score=r.heat_score,
                risk_level=RiskLevel(r.risk_level.value),
                confidence=r.confidence,
                rank_in_city=rank,
                top_drivers_json=top_drivers,
            )
        )
    db.commit()
    db.refresh(heat_map)
    return heat_map
