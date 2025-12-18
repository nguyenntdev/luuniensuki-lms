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

