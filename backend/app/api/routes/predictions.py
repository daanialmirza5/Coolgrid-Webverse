import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.city import Ward
from ...schemas.heat import PredictionResponse
from ...services import prediction_service

router = APIRouter(tags=["predictions"], dependencies=[Depends(get_current_user)])


@router.get("/wards/{ward_id}/predictions", response_model=PredictionResponse)
def get_ward_predictions(ward_id: uuid.UUID, db: Session = Depends(get_db)):
    ward = db.get(Ward, ward_id)
    if ward is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ward not found")
    return prediction_service.predict_for_ward(db, ward)
