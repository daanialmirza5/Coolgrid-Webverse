import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.city import City
from ...schemas.heat import DashboardSummaryOut, HotspotOut, WardComparisonRow
from ...services import heat_service

router = APIRouter(tags=["heatmap"], dependencies=[Depends(get_current_user)])


def _get_city(db: Session, city_id: uuid.UUID | None) -> City:
    if city_id is not None:
        city = db.get(City, city_id)
        if city is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")
        return city
    return heat_service.get_demo_city(db)


@router.get("/dashboard/summary", response_model=DashboardSummaryOut)
def dashboard_summary(city_id: uuid.UUID | None = None, db: Session = Depends(get_db)):
    city = _get_city(db, city_id)
    return heat_service.dashboard_summary(db, city)


@router.get("/hotspots", response_model=list[HotspotOut])
def list_hotspots(
    city_id: uuid.UUID | None = None,
    risk: str | None = Query(default=None, description="Filter by LOW/MODERATE/HIGH/CRITICAL"),
    db: Session = Depends(get_db),
):
    city = _get_city(db, city_id)
    return heat_service.list_hotspots(db, city, risk_filter=risk)


@router.get("/comparison/wards", response_model=list[WardComparisonRow])
def ward_comparison(city_id: uuid.UUID | None = None, db: Session = Depends(get_db)):
    city = _get_city(db, city_id)
    return heat_service.ward_comparison(db, city)
