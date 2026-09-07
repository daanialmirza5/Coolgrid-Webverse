"""Lightweight physics-informed neural network (PINN) for LST refinement.

A small MLP maps the same covariates used by the XGBoost detector to a
predicted LST, but its training loss combines:

    loss = data_mse(pred, observed_lst)
         + lambda_physics * mse(pred, energy_balance_estimate)

i.e. the network is penalized for straying from the simplified surface
energy balance estimate (`physics.energy_balance.estimate_lst`), not just
from observed data. This is a constraint-style PINN (a soft physical prior
via the loss function) rather than a PDE-residual PINN over spatiotemporal
coordinates -- a scope appropriate for ward-level tabular features rather
than a continuous thermal field.

Documented limitation: this network is trained entirely on CoolGrid's
synthetic demo dataset and has not been validated against real
observations. It demonstrates the *architecture* of physics-informed
learning, not a scientifically validated urban heat model.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn

FEATURE_ORDER = [
    "air_temp_c",
    "shortwave_wm2",
    "albedo",
    "green_space_pct",
    "water_body_pct",
    "built_up_density",
    "humidity_pct",
    "wind_speed_ms",
]


class PhysicsInformedLSTNet(nn.Module):
    def __init__(self, n_features: int = len(FEATURE_ORDER), hidden: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_features, hidden),
            nn.Tanh(),
            nn.Linear(hidden, hidden),
            nn.Tanh(),
            nn.Linear(hidden, 1),
        )
        self._mean = torch.zeros(n_features)
        self._std = torch.ones(n_features)
        self._fitted = False

    def set_normalization(self, mean: np.ndarray, std: np.ndarray) -> None:
        self._mean = torch.tensor(mean, dtype=torch.float32)
        self._std = torch.tensor(np.where(std < 1e-6, 1.0, std), dtype=torch.float32)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x_norm = (x - self._mean) / self._std
        return self.net(x_norm).squeeze(-1)

    @torch.no_grad()
    def predict(self, features: np.ndarray) -> np.ndarray:
        self.eval()
        x = torch.tensor(features, dtype=torch.float32)
        return self(x).numpy()


@dataclass
class PinnTrainResult:
    final_loss: float
    final_data_loss: float
    final_physics_loss: float
    epochs: int


def train_pinn(
    features: np.ndarray,
    observed_lst: np.ndarray,
    physics_estimate: np.ndarray,
    epochs: int = 400,
    lr: float = 0.01,
    physics_weight: float = 0.35,
    seed: int = 7,
) -> tuple[PhysicsInformedLSTNet, PinnTrainResult]:
    torch.manual_seed(seed)
    model = PhysicsInformedLSTNet(n_features=features.shape[1])
    model.set_normalization(features.mean(axis=0), features.std(axis=0))

    x = torch.tensor(features, dtype=torch.float32)
    y = torch.tensor(observed_lst, dtype=torch.float32)
    phys = torch.tensor(physics_estimate, dtype=torch.float32)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    final_loss = final_data = final_phys = 0.0
    for _ in range(epochs):
        optimizer.zero_grad()
        pred = model(x)
        data_loss = loss_fn(pred, y)
        physics_loss = loss_fn(pred, phys)
        loss = (1 - physics_weight) * data_loss + physics_weight * physics_loss
        loss.backward()
        optimizer.step()
        final_loss, final_data, final_phys = (
            float(loss.item()),
            float(data_loss.item()),
            float(physics_loss.item()),
        )

    return model, PinnTrainResult(
        final_loss=final_loss,
        final_data_loss=final_data,
        final_physics_loss=final_phys,
        epochs=epochs,
    )
