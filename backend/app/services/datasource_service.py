from ..schemas.datasource import DataSourceStatusOut, ProviderStatusOut
from .ml_registry import get_ml_registry


def get_status() -> DataSourceStatusOut:
    registry = get_ml_registry()
    status = registry.providers.status()
    return DataSourceStatusOut(
        satellite=ProviderStatusOut(**status["satellite"]),
        weather=ProviderStatusOut(**status["weather"]),
        urban=ProviderStatusOut(**status["urban"]),
        population=ProviderStatusOut(**status["population"]),
        all_demo=status["all_demo"],
        notes=status["notes"],
        detection_model_version="xgboost-v1",
        detection_model_metrics=registry.detection_model.metrics,
        pinn_trained=registry.pinn is not None,
    )
