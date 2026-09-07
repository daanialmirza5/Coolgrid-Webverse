def test_intervention_catalog(client, auth_headers):
    resp = client.get("/api/interventions/catalog", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 6


def test_run_simulation(client, auth_headers, demo_city_and_ward):
    city, ward = demo_city_and_ward
    resp = client.post("/api/simulations", headers=auth_headers, json={
        "ward_id": str(ward.id),
        "interventions": [{"type": "urban_trees", "coverage_pct": 25}, {"type": "cool_roofs", "coverage_pct": 30}],
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["simulated_lst"] < body["baseline_lst"]
    assert body["expected_cooling_c"] > 0
    assert body["cost_usd"] > 0
    assert body["population_benefited"] > 0

    get_resp = client.get(f"/api/simulations/{body['id']}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == body["id"]


def test_simulation_requires_at_least_one_intervention(client, auth_headers, demo_city_and_ward):
    city, ward = demo_city_and_ward
    resp = client.post("/api/simulations", headers=auth_headers, json={"ward_id": str(ward.id), "interventions": []})
    assert resp.status_code == 422


def test_simulation_unknown_ward_404(client, auth_headers):
    resp = client.post("/api/simulations", headers=auth_headers, json={
        "ward_id": "00000000-0000-0000-0000-000000000000",
        "interventions": [{"type": "urban_trees", "coverage_pct": 20}],
    })
    assert resp.status_code == 404


def test_run_optimization_and_recommendations(client, auth_headers, demo_city_and_ward):
    city, ward = demo_city_and_ward
    resp = client.post("/api/optimizations", headers=auth_headers, json={
        "ward_id": str(ward.id), "budget_usd": 60_000_000, "land_km2": 5, "water_m3_per_year": 5_000_000,
    })
    assert resp.status_code == 201
    body = resp.json()
    assert len(body["strategies"]) > 0
    ranks = [s["rank"] for s in body["strategies"]]
    assert ranks == sorted(ranks)
    for s in body["strategies"]:
        assert s["cost_usd"] <= 60_000_000 + 1e-6
        assert s["reason"]

    rec_resp = client.get(f"/api/wards/{ward.id}/recommendations", headers=auth_headers)
    assert rec_resp.status_code == 200
    assert len(rec_resp.json()) > 0


def test_optimization_infeasible_budget_returns_empty_strategies(client, auth_headers, demo_city_and_ward):
    city, ward = demo_city_and_ward
    resp = client.post("/api/optimizations", headers=auth_headers, json={
        "ward_id": str(ward.id), "budget_usd": 1, "land_km2": 5, "water_m3_per_year": 5_000_000,
    })
    assert resp.status_code == 201
    assert resp.json()["strategies"] == []
