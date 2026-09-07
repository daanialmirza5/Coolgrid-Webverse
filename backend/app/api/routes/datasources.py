from fastapi import APIRouter, Depends

from ...core.deps import get_current_user
from ...schemas.datasource import DataSourceStatusOut
from ...services import datasource_service

router = APIRouter(prefix="/datasources", tags=["datasources"], dependencies=[Depends(get_current_user)])


@router.get("/status", response_model=DataSourceStatusOut)
def datasource_status():
    return datasource_service.get_status()
