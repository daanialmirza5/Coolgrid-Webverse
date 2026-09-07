import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.city import Ward
from ...schemas.heat import DriverAnalysisOut, HotspotOut
from ...services import heat_service

router = APIRouter(tags=["hotspots"], dependencies=[Depends(get_current_user)])


@router.get("/wards/{ward_id}/hotspot", response_model=HotspotOut)
def get_ward_hotspot(ward_id: uuid.UUID, db: Session = Depends(get_db)):
    ward = db.get(Ward, ward_id)
    if ward is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ward not found")
    city = heat_service.get_demo_city(db)
    hotspot = heat_service.get_hotspot_for_ward(db, ward, city)
    if hotspot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No hotspot record for this ward yet")
    return hotspot


@router.get("/wards/{ward_id}/drivers", response_model=DriverAnalysisOut)
def get_ward_drivers(ward_id: uuid.UUID, db: Session = Depends(get_db)):
    ward = db.get(Ward, ward_id)
    if ward is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ward not found")
    return heat_service.driver_analysis(db, ward)
