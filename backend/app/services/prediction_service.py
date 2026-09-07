from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..models.city import Ward
from ..models.heat import Prediction, RiskLevel as DBRiskLevel
from ..schemas.heat import PredictionPointOut, PredictionResponse
from .detection_service import build_current_features
from .ml_registry import get_ml_registry
from .ward_adapter import to_ward_base

MODEL_VERSION = "xgboost-v1"


def _record_predictions(db: Session, ward: Ward, as_of: date, points) -> None:
    """Persists each forecast point so predictions are auditable after the
    fact (e.g. comparing a past 7-day forecast against what was actually
    detected once that day arrives) -- idempotent per (ward, as_of, horizon,
    model_version), so repeated calls for the same ward/day don't pile up
    duplicate rows."""
    for p in points:
        exists = db.execute(
            select(Prediction).where(
                Prediction.ward_id == ward.id,
                Prediction.as_of == as_of,
                Prediction.horizon_days == p.horizon_days,
                Prediction.model_version == MODEL_VERSION,
            )
        ).scalars().first()
        if exists is not None:
            continue
        db.add(
            Prediction(
                ward_id=ward.id,
                as_of=as_of,
                horizon_days=p.horizon_days,
                target_date=datetime.strptime(p.target_date, "%Y-%m-%d").date(),
                predicted_lst=p.predicted_lst,
                predicted_lst_lower=p.predicted_lst_lower,
                predicted_lst_upper=p.predicted_lst_upper,
                change_from_current_c=p.change_from_current_c,
                risk_level=DBRiskLevel(p.risk_level.value),
                confidence=p.confidence,
                physics_estimate_lst=p.physics_estimate_lst,
                model_version=MODEL_VERSION,
            )
        )
    db.commit()


def predict_for_ward(db: Session, ward: Ward, as_of: date | None = None) -> PredictionResponse:
    as_of = as_of or get_settings().effective_today()
    registry = get_ml_registry()

    df = build_current_features(registry, [ward], as_of)
    feature_row = df.drop(columns=["ward_pk", "ward_code"])
    [current] = registry.detection_model.predict(feature_row)

    ward_base = to_ward_base(ward)
    points = registry.forecaster.forecast(ward_base, current_lst=current.lst_celsius, as_of=as_of)

    _record_predictions(db, ward, as_of, points)

    return PredictionResponse(
        ward_id=ward.id,
        ward_name=ward.name,
        as_of=as_of,
        current_lst=current.lst_celsius,
        points=[
            PredictionPointOut(
                horizon_days=p.horizon_days,
                target_date=p.target_date,
                predicted_lst=p.predicted_lst,
                predicted_lst_lower=p.predicted_lst_lower,
                predicted_lst_upper=p.predicted_lst_upper,
                change_from_current_c=p.change_from_current_c,
                risk_level=p.risk_level,
                confidence=p.confidence,
                physics_estimate_lst=p.physics_estimate_lst,
                disclaimer=p.disclaimer,
            )
            for p in points
        ],
    )
