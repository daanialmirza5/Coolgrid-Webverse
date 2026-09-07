import uuid

from pydantic import BaseModel

from ..models.report import ReportStatus


class ReportRequest(BaseModel):
    ward_id: uuid.UUID | None = None
    city_id: uuid.UUID | None = None
    title: str | None = None
    simulation_id: uuid.UUID | None = None
    optimization_run_id: uuid.UUID | None = None


class ReportOut(BaseModel):
    id: uuid.UUID
    title: str
    status: ReportStatus
    ward_id: uuid.UUID | None
    city_id: uuid.UUID | None
    created_at: str
    download_url: str | None

    model_config = {"from_attributes": True}
