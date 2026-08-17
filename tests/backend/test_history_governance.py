"""History-First Phase 1 governance tests.

Covers: entity/source/claim CRUD, the claim-source verification invariant,
the editorial state machine, relations, geography, audit trail, and public
read access without auth (Spec sections 5-14, 49-51, 66 FLOW-01).
"""
from sqlalchemy import select

from backend.models import (
    HistoricalClaim,
    HistoricalContentAuditLog,
    HistoricalEntity,
    HistoricalSource,
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


def _make_staff(client, db_session, email, display_name, role=UserRole.admin):
    _register(client, email, display_name)
    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    user.role = role
    db_session.commit()
    client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    return user


def _seed_entity(db_session, **overrides):
    data = {
        "entity_type": "relief",
        "slug": "dong-hai",
        "name_vi": "Đông Hải",
        "name_en": "Eastern Sea",
        "publication_status": "draft",
    }
    data.update(overrides)
    entity = HistoricalEntity(**data)
    db_session.add(entity)
    db_session.flush()
    return entity


def _seed_source(db_session, **overrides):
    data = {
        "source_type": "scholarly_book",
        "title": "Một nghiên cứu về Cửu Đỉnh",
        "author_text": "Nguyễn Văn A",
        "publication_year": 1999,
        "verification_status": "metadata_verified",
    }
    data.update(overrides)
    source = HistoricalSource(**data)
    db_session.add(source)
    db_session.flush()
    return source


# --------------------------------------------------------------------------- #
# Public read without auth
# --------------------------------------------------------------------------- #
def test_history_entities_public_without_auth(client, db_session):
    _seed_entity(db_session)
    db_session.commit()
    res = client.get("/api/v1/history/entities")
    assert res.status_code == 200, res.text
    assert res.json()["total"] >= 1


def test_history_search_public(client, db_session):
    _seed_entity(db_session, slug="song-hong", name_vi="Sông Hồng")
    db_session.commit()
    res = client.get("/api/v1/history/search", params={"q": "sông"})
    assert res.status_code == 200, res.text
    assert any("Sông Hồng" == i["name_vi"] for i in res.json()["items"])


def test_history_entity_by_slug(client, db_session):
    _seed_entity(db_session, slug="nui-ba-vi", name_vi="Núi Ba Vì")
    db_session.commit()
    res = client.get("/api/v1/history/entities/by-slug/nui-ba-vi")
    assert res.status_code == 200, res.text
    assert res.json()["name_vi"] == "Núi Ba Vì"


def test_history_entity_not_found(client):
    res = client.get(
        "/api/v1/history/entities/by-slug/does-not-exist"
    )
    assert res.status_code == 404


# --------------------------------------------------------------------------- #
# Admin CRUD
# --------------------------------------------------------------------------- #
def test_admin_create_entity(client, db_session):
    _make_staff(client, db_session, "histadmin1@example.com", "Hist Admin")
    res = client.post(
        "/api/v1/admin/history/entities",
        json={
            "entity_type": "urn",
            "slug": "cao-dinh",
            "name_vi": "Cao Đỉnh",
            "name_en": "Cao Urn",
            "publication_status": "draft",
        },
    )
    assert res.status_code == 200, res.text
    assert res.json()["slug"] == "cao-dinh"


def test_admin_create_entity_duplicate_slug_rejected(client, db_session):
    _make_staff(client, db_session, "histadmin2@example.com", "Hist Admin")
    entity = _seed_entity(db_session, slug="trung-dinh", name_vi="Trung Đỉnh")
    db_session.commit()
    res = client.post(
        "/api/v1/admin/history/entities",
        json={
            "entity_type": "urn",
            "slug": "trung-dinh",
            "name_vi": "Duplicate",
        },
    )
    assert res.status_code == 409, res.text


def test_non_staff_cannot_create_entity(client, db_session):
    _make_staff(client, db_session, "plainuser@example.com", "Plain", UserRole.learner)
    res = client.post(
        "/api/v1/admin/history/entities",
        json={"entity_type": "urn", "slug": "x", "name_vi": "X"},
    )
    assert res.status_code == 403, res.text


def test_staff_create_claim_and_source_and_bind(client, db_session):
    _make_staff(client, db_session, "histstaff@example.com", "Hist Staff")
    entity = _seed_entity(db_session)
    db_session.commit()

    res = client.post(
        "/api/v1/admin/history/sources",
        json={
            "source_type": "royal_record",
            "title": "Khâm định Đại Nam hội điển sự lệ",
            "author_text": "Quốc sử quán",
            "publication_year": 1855,
            "verification_status": "metadata_verified",
        },
    )
    assert res.status_code == 200, res.text
    source_id = res.json()["id"]

    res = client.post(
        "/api/v1/admin/history/claims",
        json={
            "entity_id": str(entity.id),
            "claim_type": "factual",
            "statement_vi": "Đông Hải được khắc trên Cao Đỉnh.",
            "confidence": "medium",
            "verification_status": "unreviewed",
            "origin": "editorial",
        },
    )
    assert res.status_code == 200, res.text
    claim_id = res.json()["id"]

    res = client.post(
        f"/api/v1/admin/history/claims/{claim_id}/sources",
        json={"source_id": source_id, "support_type": "supports", "page_start": "15"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["support_type"] == "supports"

    claim = db_session.get(HistoricalClaim, claim_id)
    assert claim.verification_status == "source_attached"


# --------------------------------------------------------------------------- #
# Verification invariant
# --------------------------------------------------------------------------- #
def test_expert_verify_without_source_rejected(client, db_session):
    _make_staff(client, db_session, "histverif@example.com", "Hist Verif")
    entity = _seed_entity(db_session)
    db_session.commit()

    res = client.post(
        "/api/v1/admin/history/claims",
        json={
            "entity_id": str(entity.id),
            "claim_type": "factual",
            "statement_vi": "Tuyên Đỉnh nặng nhất trong Cửu Đỉnh.",
            "verification_status": "unreviewed",
            "origin": "editorial",
        },
    )
    claim_id = res.json()["id"]

    res = client.post(
        f"/api/v1/admin/history/claims/{claim_id}/transition",
        params={"target": "expert_verified"},
    )
    assert res.status_code == 422, res.text
    assert res.json()["error"]["code"] == "HISTORY_CLAIM_INVALID_TRANSITION"

    claim = db_session.get(HistoricalClaim, claim_id)
    assert claim.verification_status == "unreviewed"


def test_expert_verify_with_source_and_review_ok(client, db_session):
    _make_staff(client, db_session, "histfull@example.com", "Hist Full")
    entity = _seed_entity(db_session)
    db_session.commit()

    src = client.post(
        "/api/v1/admin/history/sources",
        json={
            "source_type": "archival_record",
            "title": "Châu bản triều Nguyễn",
            "verification_status": "metadata_verified",
        },
    ).json()
    claim = client.post(
        "/api/v1/admin/history/claims",
        json={
            "entity_id": str(entity.id),
            "claim_type": "chronology",
            "statement_vi": "Cửu Đỉnh được đúc 1835–1837.",
            "confidence": "high",
            "verification_status": "unreviewed",
            "origin": "editorial",
        },
    ).json()
    bind = client.post(
        f"/api/v1/admin/history/claims/{claim['id']}/sources",
        json={"source_id": src["id"], "support_type": "supports"},
    )
    assert bind.status_code == 200, bind.text

    r = client.post(
        f"/api/v1/admin/history/claims/{claim['id']}/transition",
        params={"target": "editor_reviewed"},
    )
    assert r.status_code == 200, r.text
    r = client.post(
        f"/api/v1/admin/history/claims/{claim['id']}/transition",
        params={"target": "expert_verified"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["verification_status"] == "expert_verified"


def test_editor_review_without_source_is_blocked_for_factual(client, db_session):
    _make_staff(client, db_session, "histpartial@example.com", "Hist Partial")
    entity = _seed_entity(db_session)
    db_session.commit()
    claim = client.post(
        "/api/v1/admin/history/claims",
        json={
            "entity_id": str(entity.id),
            "claim_type": "factual",
            "statement_vi": "Một khẳng định thiếu nguồn.",
            "verification_status": "unreviewed",
            "origin": "ai_generated",
        },
    ).json()
    # editor_reviewed requires an eligible source
    r = client.post(
        f"/api/v1/admin/history/claims/{claim['id']}/transition",
        params={"target": "editor_reviewed"},
    )
    assert r.status_code == 422, r.text


# --------------------------------------------------------------------------- #
# Audit trail
# --------------------------------------------------------------------------- #
def test_admin_mutations_are_audited(client, db_session):
    admin = _make_staff(client, db_session, "histaudit@example.com", "Hist Audit")
    res = client.post(
        "/api/v1/admin/history/entities",
        json={"entity_type": "period", "slug": "nguyen-dynasty", "name_vi": "Nhà Nguyễn"},
    )
    assert res.status_code == 200, res.text
    entity_id = res.json()["id"]

    entity_id_uuid = entity_id  # string from API
    audit = db_session.scalar(
        select(HistoricalContentAuditLog).order_by(
            HistoricalContentAuditLog.id.desc()
        )
    )
    assert audit is not None
    assert audit.resource_type == "entity"
    assert str(audit.resource_id) == entity_id_uuid
    assert audit.actor_id == admin.id
    assert audit.action == "create"


# --------------------------------------------------------------------------- #
# Relations
# --------------------------------------------------------------------------- #
def test_create_relation_and_public_read(client, db_session):
    _make_staff(client, db_session, "histrel@example.com", "Hist Rel")
    a = _seed_entity(db_session, slug="cao-dinh", name_vi="Cao Đỉnh")
    b = _seed_entity(db_session, slug="dong-hai-rel", name_vi="Đông Hải")
    db_session.commit()

    res = client.post(
        "/api/v1/admin/history/relations",
        json={
            "subject_entity_id": str(a.id),
            "predicate": "located_on",
            "object_entity_id": str(b.id),
        },
    )
    assert res.status_code == 200, res.text

    public = client.get(f"/api/v1/history/entities/{a.id}/relations")
    assert public.status_code == 200, public.text
    assert len(public.json()) == 1


def test_self_relation_rejected(client, db_session):
    _make_staff(client, db_session, "histselfrel@example.com", "Hist Self")
    a = _seed_entity(db_session)
    db_session.commit()
    res = client.post(
        "/api/v1/admin/history/relations",
        json={
            "subject_entity_id": str(a.id),
            "predicate": "related_to",
            "object_entity_id": str(a.id),
        },
    )
    assert res.status_code == 422, res.text


# --------------------------------------------------------------------------- #
# Geography
# --------------------------------------------------------------------------- #
def test_upsert_geography(client, db_session):
    _make_staff(client, db_session, "histgeo@example.com", "Hist Geo")
    a = _seed_entity(db_session, slug="song-hong-geo", name_vi="Sông Hồng")
    db_session.commit()
    res = client.put(
        f"/api/v1/admin/history/entities/{a.id}/geography",
        json={
            "historical_name": "Sông Hồng",
            "modern_name": "Red River",
            "geo_precision": "approximate",
            "mapping_status": "probable",
        },
    )
    assert res.status_code == 200, res.text
    assert res.json()["mapping_status"] == "probable"

    public = client.get(f"/api/v1/history/entities/{a.id}/geography")
    assert public.status_code == 200
    assert public.json()["geo_precision"] == "approximate"
