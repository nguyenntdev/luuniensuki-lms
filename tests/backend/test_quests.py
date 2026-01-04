from datetime import datetime, timezone

from sqlalchemy import select

from backend.models import (
    Certificate,
    Quest,
    QuestObjective,
    QuestReward,
    QuestStep,
    UnlockStatus,
    User,
    UserProgress,
)


def _register_user(client, email="quester@example.com"):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Quest User"},
    )
    assert res.status_code == 201, res.text
    return res


def test_quest_completion_awards_certificate(client, db_session, seeded_content):
    _register_user(client)

    user = db_session.execute(
        select(User).where(User.email == "quester@example.com")
    ).scalar_one()
    motif = seeded_content["motif"]

    db_session.add(
        UserProgress(
            user_id=user.id,
            motif_id=motif.id,
            status=UnlockStatus.discovered,
            discovered_at=datetime.now(timezone.utc),
        )
    )
    db_session.flush()

    quest = Quest(
        slug="quest-test",
        name="Quest Test",
        description="Test quest",
        category="dong_vat",
        display_order=1,
        is_active=True,
    )
    db_session.add(quest)
    db_session.flush()

    step = QuestStep(
        quest_id=quest.id,
        title="Bước 1",
        description="Khám phá động vật",
        display_order=1,
    )
    db_session.add(step)
    db_session.flush()

    db_session.add(
        QuestObjective(
            quest_step_id=step.id,
            objective_type="discover_category",
            target_value=1,
            params={"category": "dong_vat"},
            display_order=1,
        )
    )
    db_session.add(
        QuestReward(
            quest_id=quest.id,
            reward_type="xp",
            amount=50,
        )
    )
    db_session.commit()

    res = client.post("/api/v1/quests/quest-test/start")
    assert res.status_code == 200, res.text
    payload = res.json()
    assert payload["status"] == "completed"
    assert payload["certificate"]["code"]

    cert = db_session.execute(
        select(Certificate).where(
            Certificate.user_id == user.id,
            Certificate.reason_type == "quest",
            Certificate.reason_id == quest.id,
        )
    ).scalar_one_or_none()
    assert cert is not None

    db_session.refresh(user)
    assert user.total_xp >= 50
