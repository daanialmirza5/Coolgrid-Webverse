def test_non_admin_cannot_access_admin_routes(client, auth_headers):
    resp = client.get("/api/admin/system-status", headers=auth_headers)
    assert resp.status_code == 403


def test_admin_system_status(client, admin_headers, demo_city_and_ward):
    resp = client.get("/api/admin/system-status", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["database_connected"] is True
    assert body["ward_count"] >= 1
    assert body["data_sources"]["all_demo"] is True


def test_admin_list_and_update_users(client, admin_headers, demo_user):
    resp = client.get("/api/admin/users", headers=admin_headers)
    assert resp.status_code == 200
    assert any(u["email"] == demo_user.email for u in resp.json())

    update = client.patch(f"/api/admin/users/{demo_user.id}", headers=admin_headers, json={
        "role": "admin", "is_active": True,
    })
    assert update.status_code == 200
    assert update.json()["role"] == "admin"


def test_admin_audit_logs_populated_after_login(client, admin_headers):
    resp = client.get("/api/admin/audit-logs", headers=admin_headers)
    assert resp.status_code == 200
    actions = [a["action"] for a in resp.json()]
    assert "login" in actions
