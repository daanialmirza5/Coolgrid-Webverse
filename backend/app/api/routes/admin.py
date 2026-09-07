import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...core.audit import log_audit
from ...core.database import get_db
from ...core.deps import require_admin
from ...models.city import City, Ward
from ...models.heat import HeatMap
from ...models.intervention import OptimizationRun, Simulation
from ...models.report import AuditLog, ModelRun
from ...models.user import User, UserRole
from ...schemas.auth import UserOut
from ...services import datasource_service

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


class SystemStatusOut(BaseModel):
    database_connected: bool
    city_count: int
    ward_count: int
    user_count: int
    simulation_count: int
    optimization_run_count: int
    heat_map_count: int
    model_runs: list[dict]
    data_sources: dict


class UpdateUserRoleRequest(BaseModel):
    role: UserRole
    is_active: bool | None = None


class AuditLogOut(BaseModel):
    id: uuid.UUID
    created_at: str
    user_id: uuid.UUID | None
    action: str
    resource_type: str
    resource_id: str | None

    model_config = {"from_attributes": True}


@router.get("/system-status", response_model=SystemStatusOut)
def system_status(db: Session = Depends(get_db)):
    try:
        db.execute(select(func.now()))
        connected = True
    except Exception:
        connected = False

    model_runs = db.execute(select(ModelRun).order_by(ModelRun.trained_at.desc())).scalars().all()

    return SystemStatusOut(
        database_connected=connected,
        city_count=db.scalar(select(func.count()).select_from(City)) or 0,
        ward_count=db.scalar(select(func.count()).select_from(Ward)) or 0,
        user_count=db.scalar(select(func.count()).select_from(User)) or 0,
        simulation_count=db.scalar(select(func.count()).select_from(Simulation)) or 0,
        optimization_run_count=db.scalar(select(func.count()).select_from(OptimizationRun)) or 0,
        heat_map_count=db.scalar(select(func.count()).select_from(HeatMap)) or 0,
        model_runs=[{"model_name": m.model_name, "version": m.version, "metrics": m.metrics_json} for m in model_runs],
        data_sources=datasource_service.get_status().model_dump(mode="json"),
    )


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.execute(select(User).order_by(User.created_at.desc())).scalars().all()


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user_role(user_id: uuid.UUID, payload: UpdateUserRoleRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    log_audit(
        db, action="update_user_role", resource_type="user", user_id=admin.id, resource_id=str(user.id),
        metadata={"new_role": payload.role.value, "is_active": payload.is_active},
    )
    return user


@router.get("/audit-logs", response_model=list[AuditLogOut])
def audit_logs(db: Session = Depends(get_db), limit: int = 100):
    rows = db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 500))).scalars().all()
    return [
        AuditLogOut(
            id=r.id, created_at=r.created_at.isoformat(), user_id=r.user_id,
            action=r.action, resource_type=r.resource_type, resource_id=r.resource_id,
        )
        for r in rows
    ]
