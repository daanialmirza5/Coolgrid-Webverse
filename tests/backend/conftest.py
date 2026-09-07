"""Pytest fixtures for CoolGrid backend API tests.

Runs against a dedicated `coolgrid_test` Postgres/PostGIS database (created
once via `docker exec coolgrid-db psql ... CREATE DATABASE coolgrid_test`,
documented in docs/DEMO.md / README setup steps) so tests never touch the
dev database's seeded demo data. Schema is created directly from the
SQLAlchemy models (no Alembic) and truncated between tests for isolation.

The trained ML artifacts under data/demo/models/ are loaded read-only and
shared with the dev server -- they don't need a database.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

os.environ["DATABASE_URL"] = "postgresql+psycopg://coolgrid:coolgrid_dev_password@localhost:5432/coolgrid_test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.city import City, Ward, WardArchetype
from app.models.intervention import Intervention, InterventionType
from app.models.user import User, UserRole

get_settings.cache_clear()
settings = get_settings()

engine = create_engine(settings.database_url, future=True)
TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with engine.begin() as conn:
        tables = [t.name for t in reversed(Base.metadata.sorted_tables)]
        conn.execute(text(f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db_session():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    from app.main import app

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def demo_city_and_ward(db_session):
    city = City(
        slug="test-city", name="Test City (Demo)", country="India", is_demo=True,
        bbox_min_lon=73.0, bbox_min_lat=18.0, bbox_max_lon=74.0, bbox_max_lat=19.0,
    )
    db_session.add(city)
    db_session.flush()

    ward = Ward(
        city_id=city.id, ward_code="ward-01", name="Test Ward", archetype=WardArchetype.DENSE_CORE,
        geom="SRID=4326;POLYGON((73.0 18.0, 73.1 18.0, 73.1 18.1, 73.0 18.1, 73.0 18.0))",
        centroid_lon=73.05, centroid_lat=18.05, area_km2=10.0,
        built_up_density=0.7, green_space_pct=10.0, water_body_pct=1.0,
        road_density_km_per_km2=12.0, building_height_mean_m=15.0, albedo_base=0.14,
        population_density_per_km2=20000, population_total=200000, vulnerable_population_pct=20.0,
    )
    db_session.add(ward)

    for t in InterventionType:
        db_session.add(Intervention(
            type=t, label=t.value.replace("_", " ").title(), description="test",
            unit_cost_usd_per_pct_per_km2=50000, land_fraction_of_coverage=0.5,
            water_m3_per_year_per_pct_per_km2=100, max_coverage_pct=50,
        ))
    db_session.commit()
    db_session.refresh(city)
    db_session.refresh(ward)
    return city, ward


@pytest.fixture
def demo_user(db_session):
    user = User(
        email="test@coolgrid.app", hashed_password=hash_password("TestPass123"),
        full_name="Test User", role=UserRole.ANALYST, is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    user = User(
        email="admin-test@coolgrid.app", hashed_password=hash_password("AdminPass123"),
        full_name="Test Admin", role=UserRole.ADMIN, is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, demo_user):
    resp = client.post("/api/auth/login", json={"email": demo_user.email, "password": "TestPass123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client, admin_user):
    resp = client.post("/api/auth/login", json={"email": admin_user.email, "password": "AdminPass123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
