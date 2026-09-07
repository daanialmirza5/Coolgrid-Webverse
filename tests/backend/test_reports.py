def test_create_and_download_ward_report(client, auth_headers, demo_city_and_ward):
    city, ward = demo_city_and_ward
    resp = client.post("/api/reports", headers=auth_headers, json={"ward_id": str(ward.id)})
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "ready"
    assert body["download_url"]

    download = client.get(body["download_url"], headers=auth_headers)
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert len(download.content) > 500


def test_create_city_wide_report(client, auth_headers, demo_city_and_ward):
    city, ward = demo_city_and_ward
    resp = client.post("/api/reports", headers=auth_headers, json={"city_id": str(city.id)})
    assert resp.status_code == 201
    assert resp.json()["status"] == "ready"


def test_report_with_simulation_and_optimization(client, auth_headers, demo_city_and_ward):
    city, ward = demo_city_and_ward
    sim = client.post("/api/simulations", headers=auth_headers, json={
        "ward_id": str(ward.id), "interventions": [{"type": "urban_trees", "coverage_pct": 20}],
    }).json()
    opt = client.post("/api/optimizations", headers=auth_headers, json={
        "ward_id": str(ward.id), "budget_usd": 60_000_000, "land_km2": 5, "water_m3_per_year": 5_000_000,
    }).json()

    resp = client.post("/api/reports", headers=auth_headers, json={
        "ward_id": str(ward.id), "simulation_id": sim["id"], "optimization_run_id": opt["id"],
    })
    assert resp.status_code == 201
    assert resp.json()["status"] == "ready"


def test_list_reports_scoped_to_user(client, auth_headers, demo_city_and_ward):
    city, ward = demo_city_and_ward
    client.post("/api/reports", headers=auth_headers, json={"ward_id": str(ward.id)})
    resp = client.get("/api/reports", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
