from jose import jwt


def test_auth_register_login_me(client):
    email = "alice@example.com"
    password = "password123"

    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "Alice"},
    )
    assert register.status_code == 201, register.text
    assert register.cookies.get("luuniensuki_access")
    assert register.cookies.get("luuniensuki_refresh")

    reg_claims = jwt.get_unverified_claims(register.cookies.get("luuniensuki_access"))
    assert reg_claims.get("role") == "learner"

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200, me.text
    payload = me.json()
    assert payload["user"]["email"] == email

    login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login.status_code == 200, login.text
    assert login.cookies.get("luuniensuki_access")
    assert login.cookies.get("luuniensuki_refresh")

    login_claims = jwt.get_unverified_claims(login.cookies.get("luuniensuki_access"))
    assert login_claims.get("role") == "learner"


def test_auth_register_duplicate_email(client):
    email = "dup@example.com"
    payload = {"email": email, "password": "password123", "display_name": "Dup"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_change_password(client):
    email = "bob@example.com"
    old_password = "password123"
    new_password = "newpassword123"

    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": old_password, "display_name": "Bob"},
    )
    assert register.status_code == 201, register.text

    change = client.post(
        "/api/v1/users/me/change-password",
        json={"current_password": old_password, "new_password": new_password},
    )
    assert change.status_code == 200, change.text
    assert change.json() == {"message": "Password changed successfully"}

    old_login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": old_password}
    )
    assert old_login.status_code == 401, old_login.text

    new_login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": new_password}
    )
    assert new_login.status_code == 200, new_login.text


def test_change_password_invalid_current_password(client):
    email = "wrongpass@example.com"
    password = "password123"

    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "WrongPass"},
    )
    assert register.status_code == 201, register.text

    change = client.post(
        "/api/v1/users/me/change-password",
        json={"current_password": "incorrect", "new_password": "newpassword123"},
    )
    assert change.status_code == 400, change.text
    assert (
        change.json()["error"]["message"] == "Current password is incorrect"
    )


def test_refresh_and_logout(client):
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "password": "password123",
            "display_name": "Refresh User",
        },
    )
    assert register.status_code == 201, register.text
    assert register.cookies.get("luuniensuki_refresh")

    refresh = client.post("/api/v1/auth/refresh")
    assert refresh.status_code == 200, refresh.text
    assert refresh.cookies.get("luuniensuki_access")

    refreshed_claims = jwt.get_unverified_claims(refresh.cookies.get("luuniensuki_access"))
    assert refreshed_claims.get("role") == "learner"

    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 200, logout.text

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 401, me.text


def test_forgot_password_default_does_not_return_token(client):
    email = "forgot@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Forgot User"},
    )
    resp = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["reset_token"] is None
