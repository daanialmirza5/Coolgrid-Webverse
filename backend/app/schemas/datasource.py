from pydantic import BaseModel


class ProviderStatusOut(BaseModel):
    provider: str
    is_demo: bool


class DataSourceStatusOut(BaseModel):
    satellite: ProviderStatusOut
    weather: ProviderStatusOut
    urban: ProviderStatusOut
    population: ProviderStatusOut
    all_demo: bool
    notes: list[str]
    detection_model_version: str
    detection_model_metrics: dict
    pinn_trained: bool
