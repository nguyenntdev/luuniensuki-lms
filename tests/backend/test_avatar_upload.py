import io
from pathlib import Path

import backend.routers.users as users_module

# Valid PNG image bytes (works with Pillow verification and magic-byte sniff fallback).
def _make_png_bytes() -> bytes:
    try:
        from PIL import Image

        buf = io.BytesIO()
        Image.new("RGB", (1, 1), (200, 30, 30)).save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return b"\x89PNG\r\n\x1a\n" + b"\x00" * 32

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _register_user(client) -> None:
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "avatar@example.com",
            "password": "password123",
            "display_name": "Avatar User",
        },
    )
    assert register.status_code == 201, register.text


def test_upload_avatar_success(client, monkeypatch, tmp_path):
    upload_dir = tmp_path / "avatars"
    # The route reads AVATAR_DIR from the router module namespace (backend.routers.users),
    # not backend.main. Patch the router's bound globals.
    monkeypatch.setattr(users_module, "AVATAR_DIR", upload_dir)

    _register_user(client)
    response = client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("avatar.png", _make_png_bytes(), "image/png")},
    )
    assert response.status_code == 200, response.text
    avatar_url = response.json()["avatar_url"]
    assert avatar_url.startswith("/uploads/avatars/")
    assert avatar_url.endswith(".png")

    filename = Path(avatar_url).name
    assert (upload_dir / filename).exists()

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200, me.text
    assert me.json()["user"]["avatar_url"] == avatar_url


def test_upload_avatar_rejects_invalid_type(client, monkeypatch, tmp_path):
    monkeypatch.setattr(users_module, "AVATAR_DIR", tmp_path / "avatars")

    _register_user(client)
    response = client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("avatar.txt", b"not-an-image", "text/plain")},
    )
    assert response.status_code == 400, response.text
    assert response.json()["error"]["code"] == "INVALID_IMAGE_CONTENT"


def test_upload_avatar_rejects_too_large(client, monkeypatch, tmp_path):
    monkeypatch.setattr(users_module, "AVATAR_DIR", tmp_path / "avatars")
    monkeypatch.setattr(users_module, "MAX_AVATAR_SIZE", 10)

    _register_user(client)
    response = client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("avatar.png", PNG_MAGIC + b"x" * 11, "image/png")},
    )
    assert response.status_code == 400, response.text
    assert response.json()["error"]["code"] == "AVATAR_TOO_LARGE"
