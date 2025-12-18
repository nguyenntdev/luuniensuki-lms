def test_auth_register_login_me(client):
    email = "alice@example.com"
    password = "password123"

    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "Alice"},
    )
    assert register.status_code == 201, register.text
    tokens = register.json()
    assert tokens["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200, me.text
    payload = me.json()
    assert payload["user"]["email"] == email

    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    assert login.json()["access_token"]


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
    access_token = register.json()["access_token"]

    change = client.post(
        "/api/v1/users/me/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"current_password": old_password, "new_password": new_password},
    )
    assert change.status_code == 200, change.text
    assert change.json() == {"message": "Password changed successfully"}

    old_login = client.post("/api/v1/auth/login", json={"email": email, "password": old_password})
    assert old_login.status_code == 401, old_login.text

    new_login = client.post("/api/v1/auth/login", json={"email": email, "password": new_password})
    assert new_login.status_code == 200, new_login.text


def test_change_password_invalid_current_password(client):
    email = "wrongpass@example.com"
    password = "password123"

    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "WrongPass"},
    )
    assert register.status_code == 201, register.text
    access_token = register.json()["access_token"]

    change = client.post(
        "/api/v1/users/me/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"current_password": "incorrect", "new_password": "newpassword123"},
    )
    assert change.status_code == 400, change.text
    assert change.json()["detail"] == "Current password is incorrect"
