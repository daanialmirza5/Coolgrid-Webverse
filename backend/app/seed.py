"""Seeds the database with CoolGrid's demo city, wards, historical
observations, the intervention catalog, demo users, and an initial
detection run.

Prerequisites: `python ml/train.py` (from ml/) must have been run at least
once so data/demo/seed/{wards.json,observations.csv} and the trained models
under data/demo/models/ exist.

Run from backend/: `python -m app.seed`
"""

from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from .core.config import get_settings
from .core.database import Base, SessionLocal, engine
from .core.security import hash_password
from .models.city import City, Location, Ward, WardArchetype
from .models.data import Dataset, DataDomain, Observation
from .models.heat import HeatMap
from .models.intervention import Intervention, InterventionType
from .models.report import ModelRun
from .models.user import User, UserRole
from .services.ml_registry import get_ml_registry

settings = get_settings()

DEMO_CITY_SLUG = "pune-demo"
DEMO_CITY_NAME = "Pune (Demo Dataset)"


def seed_city_and_wards(db: Session) -> tuple[City, dict[str, Ward]]:
    city = db.query(City).filter_by(slug=DEMO_CITY_SLUG).one_or_none()
    if city is None:
        with open(settings.seed_dir / "wards.json") as f:
            wards_raw = json.load(f)
        lons = [pt[0] for w in wards_raw for pt in w["polygon"]]
        lats = [pt[1] for w in wards_raw for pt in w["polygon"]]

        city = City(
            slug=DEMO_CITY_SLUG,
            name=DEMO_CITY_NAME,
            country="India",
            is_demo=True,
            bbox_min_lon=min(lons),
            bbox_min_lat=min(lats),
            bbox_max_lon=max(lons),
            bbox_max_lat=max(lats),
        )
        db.add(city)
        db.flush()

        for w in wards_raw:
            ring_wkt = ", ".join(f"{lon} {lat}" for lon, lat in w["polygon"])
            ward = Ward(
                city_id=city.id,
                ward_code=w["ward_id"],
                name=w["name"],
                archetype=WardArchetype(w["archetype"]),
                geom=f"SRID=4326;POLYGON(({ring_wkt}))",
                centroid_lon=w["centroid"][0],
                centroid_lat=w["centroid"][1],
                area_km2=w["area_km2"],
                built_up_density=w["built_up_density"],
                green_space_pct=w["green_space_pct"],
                water_body_pct=w["water_body_pct"],
                road_density_km_per_km2=w["road_density_km_per_km2"],
                building_height_mean_m=w["building_height_mean_m"],
                albedo_base=w["albedo_base"],
                population_density_per_km2=w["population_density_per_km2"],
                population_total=w["population_total"],
                vulnerable_population_pct=w["vulnerable_population_pct"],
            )
            db.add(ward)
        db.commit()
        print(f"  seeded city '{DEMO_CITY_NAME}' with {len(wards_raw)} wards")
    else:
        print(f"  city '{DEMO_CITY_NAME}' already present, skipping")

    wards = {w.ward_code: w for w in db.query(Ward).filter_by(city_id=city.id).all()}
    return city, wards


def seed_ward_locations(db: Session, wards: dict[str, Ward]) -> None:
    """One `Location` point per ward (its centroid), seeded so the table
    the schema defines for point-level references actually has real,
    reproducible content instead of sitting empty forever. A real
    deployment would add more location types here (e.g. a cooling
    center, a monitoring station) as they're introduced."""
    if db.query(Location).first() is not None:
        print("  ward locations already present, skipping")
        return

    for ward in wards.values():
        db.add(
            Location(
                ward_id=ward.id,
                name=f"{ward.name} centroid",
                lat=ward.centroid_lat,
                lon=ward.centroid_lon,
                geom=f"SRID=4326;POINT({ward.centroid_lon} {ward.centroid_lat})",
                location_type="ward_centroid",
            )
        )
    db.commit()
    print(f"  seeded {len(wards)} ward centroid locations")


def seed_datasets_and_observations(db: Session, wards: dict[str, Ward]) -> None:
    if db.query(Observation).first() is not None:
        print("  observations already present, skipping")
        return

    datasets = {}
    for domain, provider_name in [
        (DataDomain.SATELLITE, "demo-satellite-v1"),
        (DataDomain.WEATHER, "demo-weather-v1"),
        (DataDomain.URBAN, "demo-urban-v1"),
        (DataDomain.POPULATION, "demo-population-v1"),
    ]:
        ds = Dataset(name=f"CoolGrid Demo {domain.value.title()}", domain=domain, provider_name=provider_name, is_demo=True)
        db.add(ds)
        datasets[domain] = ds
    db.flush()

    df = pd.read_csv(settings.seed_dir / "observations.csv")
    count = 0
    for row in df.itertuples():
        ward = wards.get(row.ward_id)
        if ward is None:
            continue
        db.add(
            Observation(
                ward_id=ward.id,
                dataset_id=datasets[DataDomain.SATELLITE].id,
                observed_on=datetime.strptime(row.observed_on, "%Y-%m-%d").date(),
                lst_celsius=row.lst_celsius,
                ndvi=row.ndvi,
                ndbi=row.ndbi,
                albedo=row.albedo,
                air_temp_celsius=row.air_temp_c,
                humidity_pct=row.humidity_pct,
                wind_speed_ms=row.wind_speed_ms,
                shortwave_wm2=row.shortwave_wm2,
                is_demo=True,
                source="demo-satellite-v1",
            )
        )
        count += 1
        if count % 500 == 0:
            db.flush()
    db.commit()
    print(f"  seeded {count} historical observations")


def seed_interventions(db: Session) -> None:
    if db.query(Intervention).first() is not None:
        print("  intervention catalog already present, skipping")
        return

    from coolgrid_ml.simulation.interventions import INTERVENTION_METADATA

    for itype, meta in INTERVENTION_METADATA.items():
        db.add(
            Intervention(
                type=InterventionType(itype.value),
                label=meta.label,
                description=meta.description,
                unit_cost_usd_per_pct_per_km2=meta.unit_cost_usd_per_pct_per_km2,
                land_fraction_of_coverage=meta.land_fraction_of_coverage,
                water_m3_per_year_per_pct_per_km2=meta.water_m3_per_year_per_pct_per_km2,
                max_coverage_pct=meta.max_coverage_pct,
            )
        )
    db.commit()
    print(f"  seeded {len(INTERVENTION_METADATA)} intervention types")


def seed_users(db: Session) -> None:
    if db.query(User).first() is not None:
        print("  users already present, skipping")
        return

    db.add(
        User(
            email=settings.demo_admin_email,
            hashed_password=hash_password(settings.demo_admin_password),
            full_name="CoolGrid Admin",
            role=UserRole.ADMIN,
            organization="CoolGrid",
        )
    )
    db.add(
        User(
            email=settings.demo_user_email,
            hashed_password=hash_password(settings.demo_user_password),
            full_name="Demo City Planner",
            role=UserRole.ANALYST,
            organization="Pune Municipal Corporation (Demo)",
        )
    )
    db.commit()
    print(f"  seeded demo users: {settings.demo_admin_email} (admin), {settings.demo_user_email} (analyst)")


def seed_model_run_record(db: Session) -> None:
    if db.query(ModelRun).first() is not None:
        return
    registry = get_ml_registry()
    db.add(
        ModelRun(
            model_name="heat_detection_xgboost",
            version="xgboost-v1",
            metrics_json=registry.detection_model.metrics,
            artifact_path=str(settings.ml_artifacts_dir / "heat_detection"),
        )
    )
    if registry.pinn_meta is not None:
        db.add(
            ModelRun(
                model_name="physics_informed_pinn",
                version="pinn-v1",
                metrics_json=registry.pinn_meta.get("train_result", {}),
                artifact_path=str(settings.ml_artifacts_dir / "pinn"),
            )
        )
    db.commit()
    print("  recorded model run metadata")


def seed_initial_heatmap(db: Session, city: City, wards: dict[str, Ward]) -> None:
    if db.query(HeatMap).first() is not None:
        print("  initial heat map already present, skipping")
        return
    from .services.detection_service import get_or_create_daily_heatmap

    heat_map = get_or_create_daily_heatmap(db, city)
    print(f"  seeded initial heat map with {heat_map.hotspot_count} hotspots flagged (of {len(wards)} wards)")


def main():
    Base.metadata.create_all(bind=engine, checkfirst=True)  # no-op if alembic already applied; safe otherwise
    db = SessionLocal()
    try:
        print("Seeding CoolGrid demo data...")
        city, wards = seed_city_and_wards(db)
        seed_ward_locations(db, wards)
        seed_datasets_and_observations(db, wards)
        seed_interventions(db)
        seed_users(db)
        seed_model_run_record(db)
        seed_initial_heatmap(db, city, wards)
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
