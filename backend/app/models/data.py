import enum
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Enum, Float, ForeignKey, Index, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base
from .mixins import TimestampMixin, UUIDPk


class DataDomain(str, enum.Enum):
    SATELLITE = "satellite"
    WEATHER = "weather"
    URBAN = "urban"
    POPULATION = "population"


class Dataset(UUIDPk, TimestampMixin, Base):
    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[DataDomain] = mapped_column(Enum(DataDomain, name="data_domain"), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[str] = mapped_column(String(32), default="v1")
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class Observation(UUIDPk, TimestampMixin, Base):
    __tablename__ = "observations"
    __table_args__ = (Index("ix_observations_ward_date", "ward_id", "observed_on"),)

    ward_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    observed_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    lst_celsius: Mapped[float] = mapped_column(Float, nullable=False)
    ndvi: Mapped[float] = mapped_column(Float, nullable=False)
    ndbi: Mapped[float] = mapped_column(Float, nullable=False)
    albedo: Mapped[float] = mapped_column(Float, nullable=False)
    air_temp_celsius: Mapped[float] = mapped_column(Float, nullable=False)
    humidity_pct: Mapped[float] = mapped_column(Float, nullable=False)
    wind_speed_ms: Mapped[float] = mapped_column(Float, nullable=False)
    shortwave_wm2: Mapped[float] = mapped_column(Float, nullable=False)
    cloud_cover_pct: Mapped[float] = mapped_column(Float, default=0.0)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False)


class Feature(UUIDPk, TimestampMixin, Base):
    """Snapshot of the exact feature vector fed to the detection model, kept
    for reproducibility/audit of explainability results."""

    __tablename__ = "features"

    ward_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)
    computed_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    feature_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
