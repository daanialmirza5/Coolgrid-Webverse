def test_list_cities_and_wards(client, auth_headers, demo_city_and_ward):
    city, ward = demo_city_and_ward
    resp = client.get("/api/cities", headers=auth_headers)
    assert resp.status_code == 200
    assert any(c["id"] == str(city.id) for c in resp.json())

    resp = client.get(f"/api/cities/{city.id}/wards", headers=auth_headers)
    assert resp.status_code == 200
    wards = resp.json()
    assert len(wards) == 1
    assert wards[0]["name"] == "Test Ward"


def test_wards_geojson(client, auth_headers, demo_city_and_ward):
    city, ward = demo_city_and_ward
    resp = client.get(f"/api/cities/{city.id}/wards.geojson", headers=auth_headers)
    assert resp.status_code == 200
    fc = resp.json()
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 1
    assert fc["features"][0]["geometry"]["type"] == "Polygon"


def test_get_ward_404(client, auth_headers):
    resp = client.get("/api/wards/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404


def test_city_not_found(client, auth_headers):
    resp = client.get("/api/cities/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404
