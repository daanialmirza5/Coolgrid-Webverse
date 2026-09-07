import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.city import City, Ward
from ...schemas.geo import CityOut, WardGeoJSONCollection, WardOut
from ...services import heat_service

router = APIRouter(tags=["geo"], dependencies=[Depends(get_current_user)])


def _city_out(city: City) -> CityOut:
    return CityOut(
        id=city.id, slug=city.slug, name=city.name, country=city.country, is_demo=city.is_demo,
        bbox=[city.bbox_min_lon, city.bbox_min_lat, city.bbox_max_lon, city.bbox_max_lat],
    )


@router.get("/cities", response_model=list[CityOut])
def list_cities(db: Session = Depends(get_db)):
    cities = db.execute(select(City)).scalars().all()
    return [_city_out(c) for c in cities]


@router.get("/cities/{city_id}", response_model=CityOut)
def get_city(city_id: uuid.UUID, db: Session = Depends(get_db)):
    city = db.get(City, city_id)
    if city is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")
    return _city_out(city)


@router.get("/cities/{city_id}/wards", response_model=list[WardOut])
def list_wards(city_id: uuid.UUID, db: Session = Depends(get_db)):
    city = db.get(City, city_id)
    if city is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")
    wards = db.execute(select(Ward).where(Ward.city_id == city_id).order_by(Ward.ward_code)).scalars().all()
    return wards


@router.get("/cities/{city_id}/wards.geojson", response_model=WardGeoJSONCollection)
def wards_geojson(city_id: uuid.UUID, db: Session = Depends(get_db)):
    city = db.get(City, city_id)
    if city is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")
    return heat_service.wards_geojson(db, city)


@router.get("/wards/{ward_id}", response_model=WardOut)
def get_ward(ward_id: uuid.UUID, db: Session = Depends(get_db)):
    ward = db.get(Ward, ward_id)
    if ward is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ward not found")
    return ward
