from datetime import date

import pytest

from coolgrid_ml.data.city_grid import generate_city
from coolgrid_ml.data.dataset import build_training_dataset
from coolgrid_ml.detection.model import HeatDetectionModel
from coolgrid_ml.prediction.forecaster import HeatForecaster


@pytest.fixture(scope="module")
def trained_model():
    df = build_training_dataset(n_days=120, sample_stride=4, seed=42)
    model = HeatDetectionModel()
    model.train(df)
    return model


def test_forecast_has_widening_confidence_interval_with_horizon(trained_model):
    ward = generate_city(seed=42)[0]
    forecaster = HeatForecaster(trained_model)
    points = forecaster.forecast(ward, current_lst=38.0, as_of=date(2026, 4, 15))
    assert [p.horizon_days for p in points] == [1, 7, 30]
    widths = [p.predicted_lst_upper - p.predicted_lst_lower for p in points]
    assert widths[0] <= widths[1] <= widths[2]
    confidences = [p.confidence for p in points]
    assert confidences[0] >= confidences[-1]
    for p in points:
        assert p.disclaimer


def test_forecast_persists_todays_anomaly_short_term(trained_model):
    """A noisy 'current' reading well above today's climatology should still
    be visible in the 1-day forecast (persistence), and fade out by 30 days
    (decay toward climatology) -- not jump straight to climatology at h=1."""
    ward = generate_city(seed=42)[0]
    forecaster = HeatForecaster(trained_model)
    as_of = date(2026, 4, 20)

    normal = forecaster.forecast(ward, current_lst=38.0, as_of=as_of, horizons=(1, 30))
    anomalously_hot = forecaster.forecast(ward, current_lst=50.0, as_of=as_of, horizons=(1, 30))

    gap_at_1d = anomalously_hot[0].predicted_lst - normal[0].predicted_lst
    gap_at_30d = anomalously_hot[1].predicted_lst - normal[1].predicted_lst
    assert gap_at_1d > gap_at_30d
    assert gap_at_1d > 5  # most of the +12C anomaly should still show up next day


def test_forecast_scenario_override_cools_prediction(trained_model):
    ward = generate_city(seed=42)[0]
    forecaster = HeatForecaster(trained_model)
    baseline = forecaster.forecast(ward, current_lst=38.0, as_of=date(2026, 4, 15), horizons=(7,))[0]
    greener = forecaster.forecast(
        ward,
        current_lst=38.0,
        as_of=date(2026, 4, 15),
        horizons=(7,),
        scenario_overrides={"green_space_pct": min(100, ward.green_space_pct + 40)},
    )[0]
    assert greener.predicted_lst < baseline.predicted_lst
