import enum
import uuid

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base
from .mixins import TimestampMixin, UUIDPk


class WardArchetype(str, enum.Enum):
    DENSE_CORE = "dense_core"
    RESIDENTIAL = "residential"
    INDUSTRIAL = "industrial"
    GREEN_BELT = "green_belt"
    RIVERSIDE = "riverside"
    PERI_URBAN = "peri_urban"


class City(UUIDPk, TimestampMixin, Base):
    __tablename__ = "cities"

    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(128), default="India")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    bbox_min_lon: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_min_lat: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_max_lon: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_max_lat: Mapped[float] = mapped_column(Float, nullable=False)

    wards: Mapped[list["Ward"]] = relationship(back_populates="city", cascade="all, delete-orphan")


class Ward(UUIDPk, TimestampMixin, Base):
    __tablename__ = "wards"
    # Geometry(..., spatial_index=True) below already manages the GIST index
    # via GeoAlchemy2's DDL events -- an explicit Index() here would collide.

    city_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True)
    ward_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    archetype: Mapped[WardArchetype] = mapped_column(Enum(WardArchetype, name="ward_archetype"), nullable=False)
    geom = mapped_column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)
    centroid_lon: Mapped[float] = mapped_column(Float, nullable=False)
    centroid_lat: Mapped[float] = mapped_column(Float, nullable=False)
    area_km2: Mapped[float] = mapped_column(Float, nullable=False)

    built_up_density: Mapped[float] = mapped_column(Float, nullable=False)
    green_space_pct: Mapped[float] = mapped_column(Float, nullable=False)
    water_body_pct: Mapped[float] = mapped_column(Float, nullable=False)
    road_density_km_per_km2: Mapped[float] = mapped_column(Float, nullable=False)
    building_height_mean_m: Mapped[float] = mapped_column(Float, nullable=False)
    albedo_base: Mapped[float] = mapped_column(Float, nullable=False)
    population_density_per_km2: Mapped[float] = mapped_column(Float, nullable=False)
    population_total: Mapped[int] = mapped_column(Integer, nullable=False)
    vulnerable_population_pct: Mapped[float] = mapped_column(Float, nullable=False)

    city: Mapped["City"] = relationship(back_populates="wards")
    locations: Mapped[list["Location"]] = relationship(back_populates="ward", cascade="all, delete-orphan")


class Location(UUIDPk, TimestampMixin, Base):
    """A point-level reference within a ward (e.g. a specific hotspot pin)."""

    __tablename__ = "locations"

    ward_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    geom = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    location_type: Mapped[str] = mapped_column(String(64), default="poi")

    ward: Mapped["Ward | None"] = relationship(back_populates="locations")
