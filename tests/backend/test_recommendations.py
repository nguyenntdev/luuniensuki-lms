from uuid import UUID

from sqlalchemy import select

import backend.main as main
from backend.models import (
    ContentFlag,
    ContentProvenance,
    QuizAttempt,
    UnlockStatus,
    User,
    UserProgress,
    UserRole,
)


def _register_user(client, email="reco@example.com"):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Reco"},
    )
    assert res.status_code == 201, res.text
    return res


def test_rules_recommendations(client, db_session, seeded_content):
    _register_user(client)
    user = db_session.execute(
        select(User).where(User.email == "reco@example.com")
    ).scalar_one()
    motif = seeded_content["motif"]

    db_session.add(
        UserProgress(
            user_id=user.id,
            motif_id=motif.id,
            status=UnlockStatus.learned,
        )
    )
    db_session.add(
        QuizAttempt(
            user_id=user.id,
            motif_id=motif.id,
            score=0,
            max_score=1,
            percentage=40,
            answers=[],
            time_taken_seconds=12,
        )
    )
    db_session.commit()

    res = client.post(
        "/api/v1/users/me/recommendations/refresh", json={"use_llm": False}
    )
    assert res.status_code == 200, res.text
    payload = res.json()
    assert payload["source"] == "rules"
    assert payload["items"]


def test_llm_recommendation_provenance(client, db_session, monkeypatch):
    _register_user(client, "ai@example.com")
    user = db_session.execute(
        select(User).where(User.email == "ai@example.com")
    ).scalar_one()
    user.ai_personalization_enabled = True
    db_session.commit()

    def fake_generate(session, *, user, rules_items):
        return (
            [
                {
                    "kind": "note",
                    "title": "Test AI",
                    "description": "LLM suggestion",
                    "href": "/explore",
                }
            ],
            "ok",
        )

    monkeypatch.setattr(main, "_generate_llm_recommendations", fake_generate)

    res = client.post(
        "/api/v1/users/me/recommendations/refresh", json={"use_llm": True}
    )
    assert res.status_code == 200, res.text
    payload = res.json()
    assert payload["source"] == "llm"

    rec_id = UUID(payload["id"])
    provenance = db_session.execute(
        select(ContentProvenance).where(
            ContentProvenance.content_type == "recommendation",
            ContentProvenance.content_id == rec_id,
        )
    ).scalar_one_or_none()
    assert provenance is not None
    assert provenance.provider == "deepseek"


def test_content_flag_create_and_list(client, db_session, seeded_content):
    _register_user(client, "flagger@example.com")
    motif = seeded_content["motif"]

    res = client.post(
        "/api/v1/content/flags",
        json={
            "content_type": "motif",
            "content_id": str(motif.id),
            "reason": "Incorrect info",
        },
    )
    assert res.status_code == 201, res.text
    payload = res.json()
    flag_id = UUID(payload["id"])

    flag = db_session.execute(
        select(ContentFlag).where(ContentFlag.id == flag_id)
    ).scalar_one_or_none()
    assert flag is not None
    assert flag.reason == "Incorrect info"

    _register_user(client, "admin@example.com")
    admin_user = db_session.execute(
        select(User).where(User.email == "admin@example.com")
    ).scalar_one()
    admin_user.role = UserRole.admin
    db_session.commit()

    res = client.get("/api/v1/admin/content/flags")
    assert res.status_code == 200, res.text
    items = res.json()
    assert any(item["id"] == str(flag_id) for item in items)
