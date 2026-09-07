import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base
from .heat import RiskLevel
from .mixins import TimestampMixin, UUIDPk


class InterventionType(str, enum.Enum):
    URBAN_TREES = "urban_trees"
    COOL_ROOFS = "cool_roofs"
    GREEN_ROOFS = "green_roofs"
    VEGETATION_CORRIDORS = "vegetation_corridors"
    BLUE_INFRASTRUCTURE = "blue_infrastructure"
    REFLECTIVE_SURFACES = "reflective_surfaces"


class Intervention(UUIDPk, TimestampMixin, Base):
    """Static reference catalog of intervention types (seeded once)."""

    __tablename__ = "interventions"

    type: Mapped[InterventionType] = mapped_column(Enum(InterventionType, name="intervention_type"), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    unit_cost_usd_per_pct_per_km2: Mapped[float] = mapped_column(Float, nullable=False)
    land_fraction_of_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    water_m3_per_year_per_pct_per_km2: Mapped[float] = mapped_column(Float, nullable=False)
    max_coverage_pct: Mapped[float] = mapped_column(Float, nullable=False)


class Simulation(UUIDPk, TimestampMixin, Base):
    __tablename__ = "simulations"

    ward_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    interventions_json: Mapped[list] = mapped_column(JSON, nullable=False)
    baseline_lst: Mapped[float] = mapped_column(Float, nullable=False)
    simulated_lst: Mapped[float] = mapped_column(Float, nullable=False)
    expected_cooling_c: Mapped[float] = mapped_column(Float, nullable=False)
    cooling_ci_low: Mapped[float] = mapped_column(Float, nullable=False)
    cooling_ci_high: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_risk: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel, name="risk_level"), nullable=False)
    simulated_risk: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel, name="risk_level"), nullable=False)
    risk_reduction_pct: Mapped[float] = mapped_column(Float, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False)
    land_km2: Mapped[float] = mapped_column(Float, nullable=False)
    water_m3_per_year: Mapped[float] = mapped_column(Float, nullable=False)
    population_benefited: Mapped[int] = mapped_column(Integer, nullable=False)
    resource_breakdown_json: Mapped[list] = mapped_column(JSON, nullable=False)


class OptimizationRun(UUIDPk, TimestampMixin, Base):
    __tablename__ = "optimization_runs"

    ward_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    constraints_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    results_json: Mapped[list] = mapped_column(JSON, nullable=False)

    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="optimization_run", cascade="all, delete-orphan")


class Recommendation(UUIDPk, TimestampMixin, Base):
    __tablename__ = "recommendations"

    ward_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)
    optimization_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=True, index=True)
    simulation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("simulations.id", ondelete="SET NULL"), nullable=True)

    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    narrative_text: Mapped[str] = mapped_column(Text, nullable=False)
    metrics_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    optimization_run: Mapped["OptimizationRun | None"] = relationship(back_populates="recommendations")
