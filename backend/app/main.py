import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import admin, auth, datasources, geo, heatmap, hotspots, optimization, predictions, reports, simulation, users
from .core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("coolgrid")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .services.ml_registry import get_ml_registry

    try:
        registry = get_ml_registry()
        logger.info(
            "CoolGrid ML registry loaded: detection model %s, pinn_trained=%s",
            registry.detection_model.metrics,
            registry.pinn is not None,
        )
    except RuntimeError as e:
        logger.error("ML artifacts missing: %s", e)
        raise
    yield


app = FastAPI(
    title="CoolGrid API",
    description="AI & Physics-Informed Urban Heat Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again."},
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "coolgrid-api"}


API_PREFIX = "/api"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(geo.router, prefix=API_PREFIX)
app.include_router(heatmap.router, prefix=API_PREFIX)
app.include_router(hotspots.router, prefix=API_PREFIX)
app.include_router(predictions.router, prefix=API_PREFIX)
app.include_router(simulation.router, prefix=API_PREFIX)
app.include_router(optimization.router, prefix=API_PREFIX)
app.include_router(reports.router, prefix=API_PREFIX)
app.include_router(datasources.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
