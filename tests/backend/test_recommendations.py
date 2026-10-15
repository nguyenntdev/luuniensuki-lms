from uuid import UUID

from sqlalchemy import select

import backend.main as main
import backend.routers.gamification as gamification_module
from backend.models import (
    ContentFlag,
    ContentProvenance,
    ContentTag,
    Quest,
    QuizAttempt,
    Tag,
    TagType,
    UnlockStatus,
    User,
    UserContentInteraction,
    UserProgress,
    UserRole,
)
from backend.services.recommendations import get_similar_content


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

    # The route calls its own module-global name (backend.routers.gamification),
    # which resolves to the real backend.domain.helpers function. Patch that
    # namespace so the mock is actually observed.
    monkeypatch.setattr(
        gamification_module, "_generate_llm_recommendations", fake_generate
    )

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


def test_record_interaction_endpoint(client, db_session, seeded_content):
    _register_user(client, "interactor@example.com")
    motif = seeded_content["motif"]

    res = client.post(
        "/api/v1/recommendations/interaction",
        json={
            "content_type": "motif",
            "content_id": str(motif.id),
            "interaction_type": "view",
            "duration_seconds": 30,
            "metadata": {"source": "test"},
        },
    )
    assert res.status_code == 200, res.text
    payload = res.json()
    assert payload["success"] is True
    assert "interaction_id" in payload

    interaction_id = UUID(payload["interaction_id"])
    interaction = db_session.execute(
        select(UserContentInteraction).where(UserContentInteraction.id == interaction_id)
    ).scalar_one_or_none()
    assert interaction is not None
    assert interaction.content_type == "motif"


def test_recommendation_feedback_endpoint(client, db_session, seeded_content):
    _register_user(client, "feedbacker@example.com")
    motif = seeded_content["motif"]

    res = client.post(
        "/api/v1/recommendations/feedback",
        json={
            "content_type": "motif",
            "content_id": str(motif.id),
            "feedback_type": "helpful",
            "metadata": {"page": "explore"},
        },
    )
    assert res.status_code == 200, res.text
    payload = res.json()
    assert payload["success"] is True


def test_quest_content_based_recommendation_title(db_session, seeded_content):
    motif = seeded_content["motif"]
    user = db_session.execute(select(User)).scalars().first()

    tag = Tag(name="heritage_test", slug="heritage-test", tag_type=TagType.topic)
    db_session.add(tag)
    db_session.flush()

    quest = Quest(
        slug="test-quest-slug",
        name="Hành Trình Cửu Đỉnh",
        description="Khám phá biểu tượng hoàng gia",
        is_active=True,
    )
    db_session.add(quest)
    db_session.flush()

    db_session.add(ContentTag(content_type="motif", content_id=motif.id, tag_id=tag.id))
    db_session.add(ContentTag(content_type="quest", content_id=quest.id, tag_id=tag.id))
    db_session.commit()

    recs = get_similar_content(
        db=db_session,
        content_type="motif",
        content_id=motif.id,
        user=user,
        limit=5,
    )
    quest_recs = [r for r in recs if r["content_type"] == "quest"]
    assert len(quest_recs) == 1
    assert quest_recs[0]["title"] == "Hành Trình Cửu Đỉnh"
    assert quest_recs[0]["content_id"] == str(quest.id)

