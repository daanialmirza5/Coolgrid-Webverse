from __future__ import annotations

from datetime import date

from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..models.city import City, Ward
from ..models.heat import Hotspot
from ..schemas.geo import WardGeoJSONCollection, WardGeoJSONFeature
from ..schemas.heat import DashboardSummaryOut, DriverAnalysisOut, DriverContributionOut, HotspotOut, WardComparisonRow
from .detection_service import build_current_features, get_or_create_daily_heatmap, record_feature_snapshot
from .ml_registry import get_ml_registry


def get_demo_city(db: Session) -> City:
    city = db.execute(select(City).where(City.is_demo.is_(True))).scalars().first()
    if city is None:
        raise ValueError("No demo city seeded. Run `python -m app.seed` in backend/.")
    return city


def get_ward_or_404(db: Session, ward_id) -> Ward | None:
    return db.get(Ward, ward_id)


def wards_geojson(db: Session, city: City) -> WardGeoJSONCollection:
    wards = db.execute(select(Ward).where(Ward.city_id == city.id)).scalars().all()
    features = []
    for w in wards:
        shape = to_shape(w.geom)
        features.append(
            WardGeoJSONFeature(
                geometry=mapping(shape),
                properties={
                    "id": str(w.id),
                    "ward_code": w.ward_code,
                    "name": w.name,
                    "archetype": w.archetype.value,
                    "built_up_density": w.built_up_density,
                    "green_space_pct": w.green_space_pct,
                    "water_body_pct": w.water_body_pct,
                    "population_total": w.population_total,
                },
            )
        )
    return WardGeoJSONCollection(features=features)


def dashboard_summary(db: Session, city: City) -> DashboardSummaryOut:
    heat_map = get_or_create_daily_heatmap(db, city)
    return DashboardSummaryOut(
        city_id=city.id,
        city_name=city.name,
        generated_at=heat_map.generated_at.isoformat(),
        avg_lst=round(heat_map.avg_lst, 1),
        max_lst=round(heat_map.max_lst, 1),
        hotspot_count=heat_map.hotspot_count,
        population_exposed=heat_map.population_exposed,
        high_risk_ward_count=heat_map.hotspot_count,
        avg_vegetation_pct=round(heat_map.summary_json["avg_vegetation_pct"], 1),
        avg_built_up_pct=round(heat_map.summary_json["avg_built_up_pct"], 1),
        is_demo=city.is_demo,
        model_version=heat_map.model_version,
    )


def list_hotspots(db: Session, city: City, risk_filter: str | None = None) -> list[HotspotOut]:
    heat_map = get_or_create_daily_heatmap(db, city)
    query = select(Hotspot, Ward).join(Ward, Hotspot.ward_id == Ward.id).where(Hotspot.heat_map_id == heat_map.id)
    rows = db.execute(query).all()
    out = []
    for hotspot, ward in rows:
        if risk_filter and hotspot.risk_level.value != risk_filter.upper():
            continue
        out.append(
            HotspotOut(
                id=hotspot.id,
                ward_id=ward.id,
                ward_name=ward.name,
                detected_on=hotspot.detected_on,
                lst_celsius=hotspot.lst_celsius,
                lst_lower=hotspot.lst_lower,
                lst_upper=hotspot.lst_upper,
                heat_score=hotspot.heat_score,
                risk_level=hotspot.risk_level,
                confidence=hotspot.confidence,
                rank_in_city=hotspot.rank_in_city,
                centroid_lon=ward.centroid_lon,
                centroid_lat=ward.centroid_lat,
            )
        )
    out.sort(key=lambda h: h.rank_in_city or 999)
    return out


def get_hotspot_for_ward(db: Session, ward: Ward, city: City) -> HotspotOut | None:
    heat_map = get_or_create_daily_heatmap(db, city)
    row = db.execute(
        select(Hotspot).where(Hotspot.heat_map_id == heat_map.id, Hotspot.ward_id == ward.id)
    ).scalars().first()
    if row is None:
        return None
    return HotspotOut(
        id=row.id, ward_id=ward.id, ward_name=ward.name, detected_on=row.detected_on,
        lst_celsius=row.lst_celsius, lst_lower=row.lst_lower, lst_upper=row.lst_upper,
        heat_score=row.heat_score, risk_level=row.risk_level, confidence=row.confidence,
        rank_in_city=row.rank_in_city, centroid_lon=ward.centroid_lon, centroid_lat=ward.centroid_lat,
    )


_NARRATIVE_TEMPLATES = {
    "increases_heat": "{label} is pushing temperatures up",
    "decreases_heat": "{label} is helping keep this area cooler",
}


def driver_analysis(db: Session, ward: Ward, as_of: date | None = None) -> DriverAnalysisOut:
    as_of = as_of or get_settings().effective_today()
    registry = get_ml_registry()
    df = build_current_features(registry, [ward], as_of)
    feature_row = df.drop(columns=["ward_pk", "ward_code"])

    [detection] = registry.detection_model.predict(feature_row)
    contributions = registry.explainer.explain_grouped(feature_row)
    base_value = registry.explainer.base_value()

    record_feature_snapshot(db, ward.id, as_of, feature_row.iloc[0].to_dict())
    db.commit()

    top_positive = [c for c in contributions if c.direction == "increases_heat"][:3]
    top_negative = [c for c in contributions if c.direction == "decreases_heat"][:2]

    parts = []
    if top_positive:
        drivers_txt = ", ".join(c.label.lower() for c in top_positive)
        parts.append(f"{ward.name} is hot primarily due to {drivers_txt}")
    if top_negative:
        mitigators_txt = " and ".join(c.label.lower() for c in top_negative)
        parts.append(f"partially offset by {mitigators_txt}")
    narrative = ("; ".join(parts) + ".") if parts else "Heat drivers are balanced for this ward."

    return DriverAnalysisOut(
        ward_id=ward.id,
        ward_name=ward.name,
        lst_celsius=detection.lst_celsius,
        base_value=round(base_value, 2),
        drivers=[
            DriverContributionOut(
                feature=c.feature, label=c.label, value=c.value, shap_value=c.shap_value,
                direction=c.direction, relative_contribution_pct=c.relative_contribution_pct,
            )
            for c in contributions
        ],
        narrative=narrative,
    )


def ward_comparison(db: Session, city: City) -> list[WardComparisonRow]:
    heat_map = get_or_create_daily_heatmap(db, city)
    rows = db.execute(
        select(Hotspot, Ward).join(Ward, Hotspot.ward_id == Ward.id).where(Hotspot.heat_map_id == heat_map.id)
    ).all()
    return [
        WardComparisonRow(
            ward_id=ward.id, ward_name=ward.name, archetype=ward.archetype.value,
            lst_celsius=hotspot.lst_celsius, heat_score=hotspot.heat_score, risk_level=hotspot.risk_level,
            green_space_pct=ward.green_space_pct, built_up_density=ward.built_up_density,
            population_total=ward.population_total,
        )
        for hotspot, ward in rows
    ]
