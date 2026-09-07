import pytest

from coolgrid_ml.data.city_grid import generate_city
from coolgrid_ml.data.dataset import build_training_dataset
from coolgrid_ml.detection.model import HeatDetectionModel
from coolgrid_ml.optimization.optimizer import InterventionOptimizer, OptimizationConstraints
from coolgrid_ml.simulation.engine import SimulationEngine
from coolgrid_ml.simulation.interventions import InterventionConfig, InterventionType


@pytest.fixture(scope="module")
def trained_model():
    df = build_training_dataset(n_days=120, sample_stride=4, seed=42)
    model = HeatDetectionModel()
    model.train(df)
    return model


@pytest.fixture(scope="module")
def dense_ward():
    wards = generate_city(seed=42)
    return max(wards, key=lambda w: w.built_up_density)


def test_simulation_trees_and_cool_roofs_cool_the_ward(trained_model, dense_ward):
    engine = SimulationEngine(trained_model)
    result = engine.simulate(
        dense_ward,
        [
            InterventionConfig(InterventionType.URBAN_TREES, 30),
            InterventionConfig(InterventionType.COOL_ROOFS, 40),
        ],
    )
    assert result.simulated_lst < result.baseline_lst
    assert result.expected_cooling_c > 0
    assert result.cooling_ci_low <= result.expected_cooling_c <= result.cooling_ci_high
    assert result.cost_usd > 0
    assert result.population_benefited > 0


def test_simulation_anchors_baseline_to_current_lst(trained_model, dense_ward):
    engine = SimulationEngine(trained_model)
    result = engine.simulate(
        dense_ward,
        [InterventionConfig(InterventionType.URBAN_TREES, 30)],
        current_lst_anchor=62.5,
    )
    assert result.baseline_lst == 62.5
    assert result.simulated_lst == pytest.approx(62.5 - result.expected_cooling_c, abs=1e-6)


def test_simulation_zero_coverage_is_near_zero_cooling(trained_model, dense_ward):
    engine = SimulationEngine(trained_model)
    result = engine.simulate(dense_ward, [InterventionConfig(InterventionType.URBAN_TREES, 0)])
    assert abs(result.expected_cooling_c) < 0.5


def test_optimizer_respects_budget_constraint(trained_model, dense_ward):
    optimizer = InterventionOptimizer(trained_model)
    constraints = OptimizationConstraints(
        budget_usd=50_000_000, land_km2=5.0, water_m3_per_year=5_000_000
    )
    strategies = optimizer.optimize(dense_ward, constraints, top_k=5)
    assert len(strategies) > 0
    for s in strategies:
        assert s.cost_usd <= 50_000_000 + 1e-6
    # ranked descending by score
    scores = [s.score for s in strategies]
    assert scores == sorted(scores, reverse=True)


def test_optimizer_returns_reasons_and_ranks(trained_model, dense_ward):
    optimizer = InterventionOptimizer(trained_model)
    constraints = OptimizationConstraints(
        budget_usd=80_000_000, land_km2=5.0, water_m3_per_year=5_000_000, population_priority=1.5
    )
    strategies = optimizer.optimize(dense_ward, constraints, top_k=3)
    assert [s.rank for s in strategies] == list(range(1, len(strategies) + 1))
    for s in strategies:
        assert s.reason
        assert len(s.interventions) > 0
