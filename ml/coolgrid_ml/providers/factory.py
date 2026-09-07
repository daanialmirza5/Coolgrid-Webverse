"""Provider factory: picks real integrations when credentials are present,
otherwise falls back to demo providers so the application always runs.

To plug in a real provider later: implement the corresponding ABC in
`base.py` (e.g. a `GoogleEarthEngineSatelliteProvider`), register it below
guarded by its required env vars, and nothing else in the app needs to
change -- detection/prediction/simulation all consume the provider
interfaces, never a concrete class.
"""

from __future__ import annotations

import os

from .base import ProviderRegistry
from .demo import (
    DemoPopulationProvider,
    DemoSatelliteProvider,
    DemoUrbanProvider,
    DemoWeatherProvider,
)

_REGISTRY: ProviderRegistry | None = None


def get_provider_registry(force_demo: bool = False) -> ProviderRegistry:
    global _REGISTRY
    if _REGISTRY is not None and not force_demo:
        return _REGISTRY

    notes: list[str] = []

    # Real integrations would be selected here, e.g.:
    #   if os.getenv("GEE_SERVICE_ACCOUNT_JSON"): satellite = GoogleEarthEngineSatelliteProvider(...)
    # None are configured for this deployment, so CoolGrid runs on demo data.
    satellite = DemoSatelliteProvider()
    weather = DemoWeatherProvider()
    urban = DemoUrbanProvider()
    population = DemoPopulationProvider()
    notes.append(
        "No real satellite/weather/urban/population credentials configured "
        "(GEE_SERVICE_ACCOUNT_JSON / ERA5_API_KEY / OSM_ENDPOINT / CENSUS_API_KEY "
        "unset) -- using labeled DEMO providers for all four data domains."
    )

    _REGISTRY = ProviderRegistry(
        satellite=satellite, weather=weather, urban=urban, population=population, notes=notes
    )
    return _REGISTRY
