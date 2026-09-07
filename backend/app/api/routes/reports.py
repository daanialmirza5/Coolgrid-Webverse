import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ...core.audit import log_audit
from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.user import User
from ...schemas.report import ReportOut, ReportRequest
from ...services import report_service

router = APIRouter(tags=["reports"], dependencies=[Depends(get_current_user)])


def _report_out(report) -> ReportOut:
    return ReportOut(
        id=report.id, title=report.title, status=report.status,
        ward_id=report.ward_id, city_id=report.city_id,
        created_at=report.created_at.isoformat(),
        download_url=f"/api/reports/{report.id}/download" if report.status.value == "ready" else None,
    )


@router.post("/reports", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def create_report(payload: ReportRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = report_service.create_report(db, payload, user)
    log_audit(db, action="generate_report", resource_type="report", user_id=user.id, resource_id=str(report.id))
    return _report_out(report)


@router.get("/reports", response_model=list[ReportOut])
def list_reports(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [_report_out(r) for r in report_service.list_reports(db, user)]


@router.get("/reports/{report_id}", response_model=ReportOut)
def get_report(report_id: uuid.UUID, db: Session = Depends(get_db)):
    report = report_service.get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return _report_out(report)


@router.get("/reports/{report_id}/download")
def download_report(report_id: uuid.UUID, db: Session = Depends(get_db)):
    report = report_service.get_report(db, report_id)
    if report is None or report.file_path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file not available")
    return FileResponse(report.file_path, media_type="application/pdf", filename=f"{report.title}.pdf")
