"""Trains and exports all CoolGrid ML artifacts from the demo dataset:

  1. The demo city (wards + GeoJSON) -> data/demo/seed/
  2. The historical observation dataset -> data/demo/seed/observations.csv
  3. The XGBoost heat detection model (+ quantile models) -> data/demo/models/heat_detection/
  4. The physics-informed PINN -> data/demo/models/pinn/

Run from the `ml/` directory: `python train.py`
The backend's seed script (backend/app/seed.py) reads these exported files.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

from coolgrid_ml.data.city_grid import generate_city
from coolgrid_ml.data.dataset import build_training_dataset
from coolgrid_ml.detection.features import build_feature_frame
from coolgrid_ml.detection.model import HeatDetectionModel
from coolgrid_ml.physics.energy_balance import estimate_lst
from coolgrid_ml.physics.pinn import FEATURE_ORDER, train_pinn

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SEED_DIR = DATA_DIR / "demo" / "seed"
MODEL_DIR = DATA_DIR / "demo" / "models"


def export_city():
    print("[1/4] Generating demo city (wards)...")
    wards = generate_city(seed=42)
    SEED_DIR.mkdir(parents=True, exist_ok=True)

    geojson = {"type": "FeatureCollection", "features": [w.to_geojson_feature() for w in wards]}
    with open(SEED_DIR / "wards.geojson", "w") as f:
        json.dump(geojson, f, indent=2)

    with open(SEED_DIR / "wards.json", "w") as f:
        json.dump([w.to_dict() for w in wards], f, indent=2)

    print(f"    {len(wards)} wards written to {SEED_DIR}")
    return wards


def export_dataset():
    print("[2/4] Building historical observation dataset (demo)...")
    df = build_training_dataset(n_days=240, sample_stride=3, seed=42)
    df.to_csv(SEED_DIR / "observations.csv", index=False)
    print(f"    {len(df)} rows written to {SEED_DIR / 'observations.csv'}")
    return df


def train_detection_model(df):
    print("[3/4] Training XGBoost heat detection model...")
    model = HeatDetectionModel()
    metrics = model.train(df)
    print(f"    metrics: {metrics}")
    out_dir = MODEL_DIR / "heat_detection"
    model.save(out_dir)
    print(f"    saved to {out_dir}")
    return model


def train_physics_pinn(df):
    print("[4/4] Training physics-informed PINN...")
    features = df[FEATURE_ORDER].astype(float).values
    observed_lst = df["lst_celsius"].astype(float).values

    physics_estimates = []
    for row in df.itertuples():
        est = estimate_lst(
            air_temp_c=row.air_temp_c,
            shortwave_wm2=row.shortwave_wm2,
            albedo=row.albedo,
            green_space_pct=row.green_space_pct,
            water_body_pct=row.water_body_pct,
            built_up_density=row.built_up_density,
            humidity_pct=row.humidity_pct,
            wind_speed_ms=row.wind_speed_ms,
        )
        physics_estimates.append(est.lst_celsius)
    physics_estimates = np.array(physics_estimates)

    model, result = train_pinn(features, observed_lst, physics_estimates)
    print(f"    final_loss={result.final_loss:.4f} data_loss={result.final_data_loss:.4f} physics_loss={result.final_physics_loss:.4f}")

    out_dir = MODEL_DIR / "pinn"
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out_dir / "pinn.pt")
    with open(out_dir / "meta.json", "w") as f:
        json.dump(
            {
                "feature_order": FEATURE_ORDER,
                "mean": model._mean.tolist(),
                "std": model._std.tolist(),
                "train_result": result.__dict__,
            },
            f,
            indent=2,
        )
    print(f"    saved to {out_dir}")


def main():
    export_city()
    df = export_dataset()
    train_detection_model(df)
    train_physics_pinn(df)
    print("\nAll CoolGrid ML artifacts trained and exported successfully.")


if __name__ == "__main__":
    main()
