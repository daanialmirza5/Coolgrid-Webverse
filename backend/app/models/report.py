import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base
from .mixins import TimestampMixin, UUIDPk


class ReportStatus(str, enum.Enum):
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class Report(UUIDPk, TimestampMixin, Base):
    __tablename__ = "reports"

    city_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("cities.id", ondelete="CASCADE"), nullable=True, index=True)
    ward_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus, name="report_status"), default=ReportStatus.GENERATING, nullable=False)
    sections_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class ModelRun(UUIDPk, TimestampMixin, Base):
    __tablename__ = "model_runs"

    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    metrics_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    artifact_path: Mapped[str] = mapped_column(String(512), nullable=False)


class AuditLog(UUIDPk, Base):
    __tablename__ = "audit_logs"

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
