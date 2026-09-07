def test_dashboard_and_driver_calls_record_feature_snapshots(client, auth_headers, demo_city_and_ward, db_session):
    """The `Feature` table exists to snapshot exactly what fed the detection
    model, for audit/reproducibility of a hotspot or driver explanation --
    it should never stay empty once detection/explainability has run."""
    from app.models.data import Feature

    city, ward = demo_city_and_ward
    assert db_session.query(Feature).count() == 0

    client.get(f"/api/dashboard/summary?city_id={city.id}", headers=auth_headers)
    after_dashboard = db_session.query(Feature).count()
    assert after_dashboard >= 1

    client.get(f"/api/wards/{ward.id}/drivers", headers=auth_headers)
    # Driver analysis recomputes the same (ward, date) snapshot the daily
    # detection run already recorded -- de-duplicated, not doubled.
    assert db_session.query(Feature).count() == after_dashboard

    snapshot = db_session.query(Feature).filter_by(ward_id=ward.id).one()
    assert snapshot.model_version == "xgboost-v1"
    assert set(snapshot.feature_json.keys()) >= {"ndvi", "ndbi", "albedo", "built_up_density", "air_temp_c"}


def test_dashboard_summary(client, auth_headers, demo_city_and_ward):
    city, ward = demo_city_and_ward
    resp = client.get(f"/api/dashboard/summary?city_id={city.id}", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_demo"] is True
    assert body["avg_lst"] > 0
    assert body["model_version"] == "xgboost-v1"


def test_hotspots_list_and_risk_filter(client, auth_headers, demo_city_and_ward):
    city, ward = demo_city_and_ward
    resp = client.get(f"/api/hotspots?city_id={city.id}", headers=auth_headers)
    assert resp.status_code == 200
    hotspots = resp.json()
    assert len(hotspots) == 1
    assert hotspots[0]["ward_name"] == "Test Ward"

    risk = hotspots[0]["risk_level"]
    resp2 = client.get(f"/api/hotspots?city_id={city.id}&risk={risk}", headers=auth_headers)
    assert len(resp2.json()) == 1

    resp3 = client.get(f"/api/hotspots?city_id={city.id}&risk=LOW", headers=auth_headers)
    assert isinstance(resp3.json(), list)


def test_ward_drivers(client, auth_headers, demo_city_and_ward):
    city, ward = demo_city_and_ward
    resp = client.get(f"/api/wards/{ward.id}/drivers", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ward_name"] == "Test Ward"
    assert len(body["drivers"]) > 0
    assert body["narrative"]
    pct_sum = sum(d["relative_contribution_pct"] for d in body["drivers"])
    assert 95 <= pct_sum <= 105


def test_ward_predictions(client, auth_headers, demo_city_and_ward):
    city, ward = demo_city_and_ward
    resp = client.get(f"/api/wards/{ward.id}/predictions", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert [p["horizon_days"] for p in body["points"]] == [1, 7, 30]
    for p in body["points"]:
        assert p["predicted_lst_lower"] <= p["predicted_lst"] <= p["predicted_lst_upper"]
        assert p["disclaimer"]


def test_predictions_are_persisted_and_deduplicated(client, auth_headers, demo_city_and_ward, db_session):
    from app.models.heat import Prediction

    city, ward = demo_city_and_ward
    assert db_session.query(Prediction).count() == 0

    client.get(f"/api/wards/{ward.id}/predictions", headers=auth_headers)
    assert db_session.query(Prediction).filter_by(ward_id=ward.id).count() == 3  # 1/7/30-day horizons

    # A second call the same day reuses the existing rows rather than duplicating them.
    client.get(f"/api/wards/{ward.id}/predictions", headers=auth_headers)
    assert db_session.query(Prediction).filter_by(ward_id=ward.id).count() == 3


def test_ward_comparison(client, auth_headers, demo_city_and_ward):
    city, ward = demo_city_and_ward
    resp = client.get(f"/api/comparison/wards?city_id={city.id}", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_hotspot_for_ward(client, auth_headers, demo_city_and_ward):
    city, ward = demo_city_and_ward
    resp = client.get(f"/api/wards/{ward.id}/hotspot", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["ward_id"] == str(ward.id)
