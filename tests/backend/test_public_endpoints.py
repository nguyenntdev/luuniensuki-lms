"""Tests for public endpoints: health, badges, ranks."""


def test_health_endpoint(client):
    """Test that /health returns OK status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"


def test_get_all_badges(client, seeded_content):
    """Test GET /api/v1/badges returns all badges."""
    unauth = client.get("/api/v1/badges")
    assert unauth.status_code == 401, unauth.text

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "badges@example.com",
            "password": "password123",
            "display_name": "Badge User",
        },
    )
    response = client.get("/api/v1/badges")
    assert response.status_code == 200
    badges = response.json()
    assert isinstance(badges, list)
    assert len(badges) >= 1

    # Check badge structure
    badge = badges[0]
    assert "slug" in badge
    assert "name" in badge
    assert "description" in badge
    assert "xp_bonus" in badge


def test_get_all_ranks(client):
    """Test GET /api/v1/ranks returns all XP ranks."""
    unauth = client.get("/api/v1/ranks")
    assert unauth.status_code == 401, unauth.text

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "ranks@example.com",
            "password": "password123",
            "display_name": "Rank User",
        },
    )
    response = client.get("/api/v1/ranks")
    assert response.status_code == 200
    ranks = response.json()
    assert isinstance(ranks, list)
    assert len(ranks) >= 1

    # Check rank structure
    rank = ranks[0]
    assert "level" in rank
    assert "name" in rank
    assert "xp" in rank

    # Verify ranks are sorted by level
    levels = [r["level"] for r in ranks]
    assert levels == sorted(levels)
