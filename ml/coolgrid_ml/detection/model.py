"""XGBoost-based heat detection: predicts LST, a 0-100 heat score, a
categorical risk level, and a data-driven confidence interval.

Confidence intervals come from XGBoost's native quantile regression
objective (`reg:quantileerror`, available since XGBoost 2.0) rather than a
single fixed +/- band, so wards with less typical feature combinations get
wider intervals.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

from .features import FEATURE_COLUMNS, build_feature_frame


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class DetectionResult:
    lst_celsius: float
    lst_lower: float
    lst_upper: float
    heat_score: float
    risk_level: RiskLevel
    confidence: float


_XGB_PARAMS = dict(
    n_estimators=250,
    max_depth=4,
    learning_rate=0.06,
    subsample=0.85,
    colsample_bytree=0.85,
    reg_lambda=1.0,
    random_state=42,
)


class HeatDetectionModel:
    def __init__(self):
        self.median_model: xgb.XGBRegressor | None = None
        self.lower_model: xgb.XGBRegressor | None = None
        self.upper_model: xgb.XGBRegressor | None = None
        self.city_stats: dict = {}
        self.feature_columns = FEATURE_COLUMNS
        self.metrics: dict = {}

    def train(self, df: pd.DataFrame, test_size: float = 0.2) -> dict:
        X = build_feature_frame(df)
        y = df["lst_celsius"].astype(float).values

        rng = np.random.default_rng(42)
        idx = rng.permutation(len(X))
        split = int(len(X) * (1 - test_size))
        train_idx, test_idx = idx[:split], idx[split:]
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        self.median_model = xgb.XGBRegressor(objective="reg:squarederror", **_XGB_PARAMS)
        self.median_model.fit(X_train, y_train)

        self.lower_model = xgb.XGBRegressor(
            objective="reg:quantileerror", quantile_alpha=0.1, **_XGB_PARAMS
        )
        self.lower_model.fit(X_train, y_train)

        self.upper_model = xgb.XGBRegressor(
            objective="reg:quantileerror", quantile_alpha=0.9, **_XGB_PARAMS
        )
        self.upper_model.fit(X_train, y_train)

        preds = self.median_model.predict(X_test)
        mae = float(np.mean(np.abs(preds - y_test)))
        rmse = float(np.sqrt(np.mean((preds - y_test) ** 2)))
        r2 = float(1 - np.sum((y_test - preds) ** 2) / np.sum((y_test - y_test.mean()) ** 2))

        full_preds = self.median_model.predict(X)
        self.city_stats = {
            "mean": float(full_preds.mean()),
            "std": float(full_preds.std()),
            "p50": float(np.percentile(full_preds, 50)),
            "p75": float(np.percentile(full_preds, 75)),
            "p90": float(np.percentile(full_preds, 90)),
            "min": float(full_preds.min()),
            "max": float(full_preds.max()),
        }
        self.metrics = {"mae": mae, "rmse": rmse, "r2": r2, "n_train": len(X_train), "n_test": len(X_test)}
        return self.metrics

    def _risk_level(self, lst: float) -> RiskLevel:
        s = self.city_stats
        if lst >= s["p90"]:
            return RiskLevel.CRITICAL
        if lst >= s["p75"]:
            return RiskLevel.HIGH
        if lst >= s["p50"]:
            return RiskLevel.MODERATE
        return RiskLevel.LOW

    def _heat_score(self, lst: float) -> float:
        s = self.city_stats
        span = max(s["max"] - s["min"], 1e-6)
        score = (lst - s["min"]) / span * 100.0
        return float(np.clip(score, 0, 100))

    def predict(self, df: pd.DataFrame) -> list[DetectionResult]:
        if self.median_model is None:
            raise RuntimeError("Model not trained/loaded.")
        X = build_feature_frame(df)
        median = self.median_model.predict(X)
        lower = np.minimum(self.lower_model.predict(X), median)
        upper = np.maximum(self.upper_model.predict(X), median)

        results = []
        for m, lo, hi in zip(median, lower, upper):
            width = max(hi - lo, 0.1)
            confidence = float(np.clip(1.0 - (width / 12.0), 0.35, 0.97))
            results.append(
                DetectionResult(
                    lst_celsius=round(float(m), 2),
                    lst_lower=round(float(lo), 2),
                    lst_upper=round(float(hi), 2),
                    heat_score=round(self._heat_score(float(m)), 1),
                    risk_level=self._risk_level(float(m)),
                    confidence=round(confidence, 3),
                )
            )
        return results

    def save(self, dir_path: str | Path) -> None:
        dir_path = Path(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.median_model, dir_path / "median_model.joblib")
        joblib.dump(self.lower_model, dir_path / "lower_model.joblib")
        joblib.dump(self.upper_model, dir_path / "upper_model.joblib")
        with open(dir_path / "meta.json", "w") as f:
            json.dump(
                {"city_stats": self.city_stats, "metrics": self.metrics, "feature_columns": self.feature_columns},
                f,
                indent=2,
            )

    @classmethod
    def load(cls, dir_path: str | Path) -> "HeatDetectionModel":
        dir_path = Path(dir_path)
        inst = cls()
        inst.median_model = joblib.load(dir_path / "median_model.joblib")
        inst.lower_model = joblib.load(dir_path / "lower_model.joblib")
        inst.upper_model = joblib.load(dir_path / "upper_model.joblib")
        with open(dir_path / "meta.json") as f:
            meta = json.load(f)
        inst.city_stats = meta["city_stats"]
        inst.metrics = meta["metrics"]
        inst.feature_columns = meta["feature_columns"]
        return inst
