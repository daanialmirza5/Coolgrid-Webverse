import pytest

from coolgrid_ml.data.dataset import build_training_dataset
from coolgrid_ml.detection.model import HeatDetectionModel, RiskLevel
from coolgrid_ml.explain.shap_explainer import HeatExplainer


@pytest.fixture(scope="module")
def trained_model():
    df = build_training_dataset(n_days=180, sample_stride=3, seed=42)
    model = HeatDetectionModel()
    model.train(df)
    return model, df


def test_model_fits_well(trained_model):
    model, _ = trained_model
    assert model.metrics["r2"] > 0.9
    assert model.metrics["mae"] < 2.0


def test_predict_returns_valid_results(trained_model):
    model, df = trained_model
    results = model.predict(df.head(5))
    assert len(results) == 5
    for r in results:
        assert r.lst_lower <= r.lst_celsius <= r.lst_upper
        assert 0 <= r.heat_score <= 100
        assert isinstance(r.risk_level, RiskLevel)
        assert 0 < r.confidence <= 1


def test_hotter_row_gets_higher_or_equal_risk(trained_model):
    model, df = trained_model
    sorted_df = df.sort_values("lst_celsius")
    coolest = model.predict(sorted_df.head(1))[0]
    hottest = model.predict(sorted_df.tail(1))[0]
    risk_order = [RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.CRITICAL]
    assert risk_order.index(hottest.risk_level) >= risk_order.index(coolest.risk_level)


def test_shap_explainer_ranks_drivers(trained_model):
    model, df = trained_model
    explainer = HeatExplainer(model)
    contributions = explainer.explain(df.head(1))
    assert len(contributions) == len(model.feature_columns)
    # sorted by |shap value| descending
    abs_vals = [abs(c.shap_value) for c in contributions]
    assert abs_vals == sorted(abs_vals, reverse=True)
    total_pct = sum(c.relative_contribution_pct for c in contributions)
    assert 95 <= total_pct <= 105
    for c in contributions:
        assert c.direction in ("increases_heat", "decreases_heat")


def test_explain_grouped_collapses_weather_features(trained_model):
    model, df = trained_model
    explainer = HeatExplainer(model)
    grouped = explainer.explain_grouped(df.head(1))
    # 12 raw features -> 4 weather features collapsed into 1 = 9
    assert len(grouped) == len(model.feature_columns) - 4 + 1
    assert any(c.feature == "weather" for c in grouped)
    pct_total = sum(c.relative_contribution_pct for c in grouped)
    assert 95 <= pct_total <= 105


def test_save_and_load_roundtrip(trained_model, tmp_path):
    model, df = trained_model
    model.save(tmp_path / "model")
    loaded = HeatDetectionModel.load(tmp_path / "model")
    orig = model.predict(df.head(3))
    restored = loaded.predict(df.head(3))
    for o, r in zip(orig, restored):
        assert o.lst_celsius == r.lst_celsius
