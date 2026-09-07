def test_register_and_login(client):
    reg = client.post("/api/auth/register", json={
        "email": "newuser@coolgrid.app", "password": "StrongPass123", "full_name": "New User",
    })
    assert reg.status_code == 201
    body = reg.json()
    assert body["user"]["email"] == "newuser@coolgrid.app"
    assert body["user"]["role"] == "viewer"
    assert body["access_token"]

    login = client.post("/api/auth/login", json={"email": "newuser@coolgrid.app", "password": "StrongPass123"})
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_duplicate_registration_rejected(client, demo_user):
    resp = client.post("/api/auth/register", json={
        "email": demo_user.email, "password": "AnotherPass123", "full_name": "Dup",
    })
    assert resp.status_code == 409


def test_login_wrong_password_rejected(client, demo_user):
    resp = client.post("/api/auth/login", json={"email": demo_user.email, "password": "WrongPassword"})
    assert resp.status_code == 401


def test_protected_route_requires_token(client):
    resp = client.get("/api/cities")
    assert resp.status_code == 401


def test_me_endpoint_returns_current_user(client, auth_headers, demo_user):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == demo_user.email


def test_forgot_password_and_reset_flow(client, demo_user):
    forgot = client.post("/api/auth/forgot-password", json={"email": demo_user.email})
    assert forgot.status_code == 200
    reset_token = forgot.json()["reset_token"]

    reset = client.post("/api/auth/reset-password", json={"token": reset_token, "new_password": "NewPass456"})
    assert reset.status_code == 204

    login = client.post("/api/auth/login", json={"email": demo_user.email, "password": "NewPass456"})
    assert login.status_code == 200


def test_forgot_password_unknown_email_does_not_leak(client):
    resp = client.post("/api/auth/forgot-password", json={"email": "nobody@nowhere.com"})
    assert resp.status_code == 200
    assert "reset_token" not in resp.json()


def test_change_password_requires_current_password(client, auth_headers):
    resp = client.post("/api/users/me/change-password", headers=auth_headers, json={
        "current_password": "WrongOldPassword", "new_password": "Whatever123",
    })
    assert resp.status_code == 400
