import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.audit import log_audit
from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.city import Ward
from ...models.user import User
from ...schemas.simulation import OptimizationConstraintsIn, OptimizationRunOut, RecommendationOut
from ...services import optimization_service

router = APIRouter(tags=["optimization"], dependencies=[Depends(get_current_user)])


@router.post("/optimizations", response_model=OptimizationRunOut, status_code=status.HTTP_201_CREATED)
def run_optimization(payload: OptimizationConstraintsIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ward = db.get(Ward, payload.ward_id)
    if ward is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ward not found")
    result = optimization_service.run_optimization(db, ward, payload, user)
    log_audit(db, action="run_optimization", resource_type="optimization_run", user_id=user.id, resource_id=str(result.id))
    return result


@router.get("/wards/{ward_id}/recommendations", response_model=list[RecommendationOut])
def get_recommendations(ward_id: uuid.UUID, db: Session = Depends(get_db)):
    ward = db.get(Ward, ward_id)
    if ward is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ward not found")
    return optimization_service.list_recommendations(db, ward)
