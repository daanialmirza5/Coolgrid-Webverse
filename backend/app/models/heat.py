import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Index, Integer, JSON, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base
from .mixins import TimestampMixin, UUIDPk


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class HeatMap(UUIDPk, TimestampMixin, Base):
    """One city-wide detection run: every ward's hotspot record for that run
    links back here, so the dashboard/map can show a consistent snapshot."""

    __tablename__ = "heat_maps"

    city_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    avg_lst: Mapped[float] = mapped_column(Float, nullable=False)
    max_lst: Mapped[float] = mapped_column(Float, nullable=False)
    hotspot_count: Mapped[int] = mapped_column(Integer, nullable=False)
    population_exposed: Mapped[int] = mapped_column(Integer, nullable=False)
    summary_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    hotspots: Mapped[list["Hotspot"]] = relationship(back_populates="heat_map", cascade="all, delete-orphan")


class Hotspot(UUIDPk, TimestampMixin, Base):
    __tablename__ = "hotspots"
    __table_args__ = (Index("ix_hotspots_ward_date", "ward_id", "detected_on"),)

    ward_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)
    heat_map_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("heat_maps.id", ondelete="CASCADE"), nullable=True, index=True)
    detected_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    lst_celsius: Mapped[float] = mapped_column(Float, nullable=False)
    lst_lower: Mapped[float] = mapped_column(Float, nullable=False)
    lst_upper: Mapped[float] = mapped_column(Float, nullable=False)
    heat_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel, name="risk_level"), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    rank_in_city: Mapped[int | None] = mapped_column(Integer, nullable=True)
    top_drivers_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    heat_map: Mapped["HeatMap | None"] = relationship(back_populates="hotspots")


class Prediction(UUIDPk, TimestampMixin, Base):
    __tablename__ = "predictions"
    __table_args__ = (Index("ix_predictions_ward_asof", "ward_id", "as_of"),)

    ward_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)
    as_of: Mapped[date] = mapped_column(Date, nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_lst: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_lst_lower: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_lst_upper: Mapped[float] = mapped_column(Float, nullable=False)
    change_from_current_c: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel, name="risk_level"), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    physics_estimate_lst: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
