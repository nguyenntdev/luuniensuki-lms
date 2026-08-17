"""History Collection tests (Phase 11, Spec section 47).

Covers: staff create/update/publish, public visibility rules, owner/staff
guards, and entity/source reference validation.
"""
from sqlalchemy import select

from backend.models import (
    HistoricalEntity,
    HistoricalSource,
    HistoryCollection,
    User,
    UserRole,
)


def _register(client, email, display_name):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": display_name},
    )
    assert res.status_code == 201, res.text
    return res


def _make_user(client, db_session, email, display_name, role=UserRole.learner):
    _register(client, email, display_name)
    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    user.role = role
    db_session.commit()
    client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    return user


def _seed_refs(db_session):
    entity = HistoricalEntity(
        entity_type="relief", slug="song-hong-rel", name_vi="Sông Hồng"
    )
    source = HistoricalSource(
        source_type="royal_record",
        title="Châu bản triều Nguyễn",
        verification_status="metadata_verified",
    )
    db_session.add_all([entity, source])
    db_session.flush()
    return entity, source


def test_staff_create_and_publish_collection(client, db_session):
    _make_user(client, db_session, "colladmin@example.com", "Coll Admin", UserRole.admin)
    entity, source = _seed_refs(db_session)
    db_session.commit()

    res = client.post(
        "/api/v1/history/collections",
        json={
            "slug": "dia-ly-cuu-dinh",
            "title_vi": "Địa lý Cửu Đỉnh",
            "visibility": "private",
            "entity_ids": [str(entity.id)],
            "source_ids": [str(source.id)],
        },
    )
    assert res.status_code == 200, res.text
    cid = res.json()["id"]
    assert res.json()["status"] == "draft"

    res = client.post(f"/api/v1/history/collections/{cid}/publish")
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "published"
    assert res.json()["visibility"] == "public"

    public = client.get("/api/v1/history/collections/dia-ly-cuu-dinh")
    assert public.status_code == 200, public.text
    assert public.json()["title_vi"] == "Địa lý Cửu Đỉnh"


def test_learner_cannot_create_collection(client, db_session):
    _make_user(client, db_session, "collearner@example.com", "Coll Learner")
    res = client.post(
        "/api/v1/history/collections",
        json={"slug": "x", "title_vi": "X"},
    )
    assert res.status_code == 403, res.text


def test_public_cannot_see_private_draft(client, db_session):
    _make_user(client, db_session, "colowner@example.com", "Coll Owner", UserRole.teacher)
    entity, _ = _seed_refs(db_session)
    db_session.commit()
    res = client.post(
        "/api/v1/history/collections",
        json={"slug": "rieng-tu", "title_vi": "Riêng tư", "entity_ids": [str(entity.id)]},
    )
    assert res.status_code == 200, res.text

    # Anonymous read: private draft must be hidden (fresh client, no cookies).
    from fastapi.testclient import TestClient
    import backend.main as main_mod

    anon = TestClient(main_mod.app)
    res = anon.get("/api/v1/history/collections/rieng-tu")
    assert res.status_code == 404, res.text


def test_staff_create_rejects_missing_entity(client, db_session):
    _make_user(client, db_session, "collbad@example.com", "Coll Bad", UserRole.admin)
    res = client.post(
        "/api/v1/history/collections",
        json={
            "slug": "sai-tham-chieu",
            "title_vi": "Sai tham chiếu",
            "entity_ids": ["00000000-0000-0000-0000-000000000000"],
        },
    )
    assert res.status_code == 422, res.text
    assert res.json()["error"]["code"] == "HISTORY_COLLECTION_INVALID_REF"


def test_non_owner_cannot_update_collection(client, db_session):
    _make_user(client, db_session, "colla@example.com", "Coll A", UserRole.teacher)
    entity, _ = _seed_refs(db_session)
    db_session.commit()
    res = client.post(
        "/api/v1/history/collections",
        json={"slug": "cua-a", "title_vi": "Của A", "entity_ids": [str(entity.id)]},
    )
    cid = res.json()["id"]

    # Different teacher cannot edit A's private collection.
    _make_user(client, db_session, "collb@example.com", "Coll B", UserRole.teacher)
    res = client.patch(
        f"/api/v1/history/collections/{cid}", json={"title_vi": "Đổi tên"}
    )
    assert res.status_code == 403, res.text


def test_admin_can_update_any_collection(client, db_session):
    _make_user(client, db_session, "collc@example.com", "Coll C", UserRole.teacher)
    entity, _ = _seed_refs(db_session)
    db_session.commit()
    res = client.post(
        "/api/v1/history/collections",
        json={"slug": "cua-c", "title_vi": "Của C", "entity_ids": [str(entity.id)]},
    )
    cid = res.json()["id"]

    _make_user(client, db_session, "colld@example.com", "Coll D", UserRole.admin)
    res = client.patch(
        f"/api/v1/history/collections/{cid}", json={"description_vi": "Ghi chú của admin"}
    )
    assert res.status_code == 200, res.text
