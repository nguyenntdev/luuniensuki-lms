"""Historical Learning Engine V2 tests (Phase 8, Spec sections 31-35).

Covers: server-authoritative grading per question type (chronology, map,
urn hotspot, evidence match, multi-select, comparison, source interpretation,
relationship chain), the content-validity invariant (32.2), the public/staff
question endpoints, mastery dimension updates (34), and the guarantee that a
client can never fabricate its own correctness (33.4).
"""
from uuid import uuid4

import pytest
from sqlalchemy import select

from backend.models import (
    HistoricalEntity,
    HistoricalEntityRelation,
    QuizQuestion,
    User,
    UserRole,
    UserSkillLevel,
)
from backend.services import history_learning as hl


@pytest.fixture(autouse=True)
def _reset_auth_rate_limit():
    """This file registers/logs in many users; the in-process auth rate limiter
    keys all TestClient traffic by one IP, so the cumulative 60s-window count
    across the whole suite would 429 these requests. Reset it per test (same
    pattern as test_rate_limit.py)."""
    import backend.main as main

    main._auth_rate_limit_state.clear()
    yield
    main._auth_rate_limit_state.clear()


def _register(client, email, display_name):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": display_name},
    )
    assert res.status_code == 201, res.text
    return res


def _login(client, email):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert res.status_code == 200, res.text


def _make_user(client, db_session, email, display_name, role=UserRole.learner):
    _register(client, email, display_name)
    user = db_session.execute(select(User).where(User.email == email)).scalar_one()
    user.role = role
    db_session.commit()
    _login(client, email)
    return user


def _seed_entity(db_session, **overrides):
    data = {
        "entity_type": "relief",
        "slug": f"relief-{uuid4().hex[:8]}",
        "name_vi": "Hoa văn thử nghiệm",
        "publication_status": "draft",
    }
    data.update(overrides)
    entity = HistoricalEntity(**data)
    db_session.add(entity)
    db_session.flush()
    return entity


def _create_question(client, motif_id, **overrides):
    payload = {
        "motif_id": str(motif_id),
        "question_type": "chronology_order",
        "question_text": "Sắp xếp các sự kiện theo trình tự thời gian.",
        "difficulty": 2,
        "skill_dimensions": ["chronology", "factual_recall"],
        "answer_contract": {"ordered_entity_ids": ["e1", "e2", "e3"]},
    }
    payload.update(overrides)
    res = client.post("/api/v1/history/questions", json=payload)
    assert res.status_code == 200, res.text
    return res.json()


# --------------------------------------------------------------------------- #
# Grading — service level
# --------------------------------------------------------------------------- #
def test_chronology_order_grading_exact_partial_wrong():
    expected = {"ordered_entity_ids": ["b", "a", "c"]}
    exact = hl.grade_chronology_order("?", {"ordered_entity_ids": ["b", "a", "c"]}, expected)
    assert exact["correct"] is True
    assert exact["score"] == 1.0
    assert exact["feedback_vi"]

    partial = hl.grade_chronology_order("?", {"ordered_entity_ids": ["b", "c", "a"]}, expected)
    assert partial["correct"] is False
    assert 0 < partial["score"] < 1.0

    wrong = hl.grade_chronology_order("?", {"ordered_entity_ids": ["x", "y", "z"]}, expected)
    assert wrong["correct"] is False
    assert wrong["score"] == 0.0


def test_relationship_chain_grading_order_sensitive():
    expected = {"chain_entity_ids": ["relief-a", "urn-cao", "relief-b"]}
    exact = hl.grade_relationship_chain(
        "?", {"chain_entity_ids": ["relief-a", "urn-cao", "relief-b"]}, expected
    )
    assert exact["correct"] is True and exact["score"] == 1.0
    wrong = hl.grade_relationship_chain(
        "?", {"chain_entity_ids": ["urn-cao", "relief-b", "relief-a"]}, expected
    )
    assert wrong["correct"] is False and wrong["score"] < 1.0


def test_map_location_tolerance_respects_geo_precision():
    expected = {"lat": 16.46, "lng": 107.59, "tolerance_km": 10, "geo_precision": "exact"}
    inside = hl.grade_map_location("?", {"lat": 16.5, "lng": 107.6}, expected)
    assert inside["correct"] is True
    assert inside["score"] == 1.0

    outside = hl.grade_map_location("?", {"lat": 15.5, "lng": 107.5}, expected)
    assert outside["correct"] is False

    approximate_expected = {**expected, "geo_precision": "approximate"}
    still_inside = hl.grade_map_location("?", {"lat": 16.35, "lng": 107.55}, approximate_expected)
    assert still_inside["correct"] is True
    far_out = hl.grade_map_location("?", {"lat": 16.0, "lng": 107.5}, approximate_expected)
    assert far_out["correct"] is False
    assert far_out["score"] < 1.0


def test_map_location_rejects_missing_coordinates():
    res = hl.grade_map_location("?", {}, {"lat": 16.46, "lng": 107.59})
    assert res["correct"] is False
    assert res["score"] == 0.0


def test_urn_hotspot_relief_must_belong_to_urn(db_session):
    urn = _seed_entity(db_session, entity_type="urn", slug="urn-cao", name_vi="Cao Đỉnh")
    relief = _seed_entity(db_session, slug="relief-hai", name_vi="Hải")
    unrelated = _seed_entity(db_session, slug="relief-khac", name_vi="Khác")
    db_session.add(
        HistoricalEntityRelation(
            subject_entity_id=relief.id,
            predicate="located_on",
            object_entity_id=urn.id,
        )
    )
    db_session.commit()

    expected = {
        "hotspot_id": "hs-1",
        "urn_entity_id": str(urn.id),
        "relief_entity_id": str(relief.id),
    }
    ok = hl.grade_urn_hotspot("?", {"hotspot_id": "hs-1"}, expected, db=db_session)
    assert ok["correct"] is True

    mismatch = hl.grade_urn_hotspot(
        "?", {"hotspot_id": "hs-1"}, {**expected, "relief_entity_id": str(unrelated.id)}, db=db_session
    )
    assert mismatch["correct"] is False

    wrong_hotspot = hl.grade_urn_hotspot("?", {"hotspot_id": "hs-9"}, expected, db=db_session)
    assert wrong_hotspot["correct"] is False


def test_evidence_match_scoring():
    expected = {"claim_id": "c1", "correct_source_ids": ["s1", "s2"]}
    exact = hl.grade_evidence_match("?", {"source_ids": ["s1", "s2"]}, expected)
    assert exact["correct"] is True and exact["score"] == 1.0

    partial = hl.grade_evidence_match("?", {"source_ids": ["s1"]}, expected)
    assert partial["correct"] is False and partial["score"] == 0.5

    wrong = hl.grade_evidence_match("?", {"source_ids": ["s3"]}, expected)
    assert wrong["correct"] is False and wrong["score"] == 0.0

    extra = hl.grade_evidence_match("?", {"source_ids": ["s1", "s2", "s9"]}, expected)
    assert extra["correct"] is False and extra["score"] < 1.0


def test_multi_select_set_comparison():
    expected = {"correct_option_ids": ["o1", "o3"]}
    exact = hl.grade_multi_select("?", {"option_ids": ["o1", "o3"]}, expected)
    assert exact["correct"] is True and exact["score"] == 1.0
    partial = hl.grade_multi_select("?", {"option_ids": ["o1"]}, expected)
    assert partial["correct"] is False and partial["score"] == 0.5


def test_compare_two_rubric():
    expected = {"dimensions": {"geography": "mountainous", "economy": "riverine"}}
    exact = hl.grade_compare_two("?", {"dimensions": {"geography": "mountainous", "economy": "riverine"}}, expected)
    assert exact["correct"] is True and exact["score"] == 1.0
    partial = hl.grade_compare_two("?", {"dimensions": {"geography": "mountainous"}}, expected)
    assert partial["correct"] is False and partial["score"] == 0.5


def test_source_interpretation_rubric():
    expected = {"inferable": True, "allowed_conclusion_ids": ["k1", "k2"]}
    ok = hl.grade_source_interpretation("?", {"conclusion_ids": ["k1"]}, expected)
    assert ok["correct"] is True and ok["score"] == 1.0
    overreach = hl.grade_source_interpretation("?", {"conclusion_ids": ["k9"]}, expected)
    assert overreach["correct"] is False

    not_inferable = {"inferable": False, "allowed_conclusion_ids": []}
    cautious = hl.grade_source_interpretation("?", {"conclusion_ids": []}, not_inferable)
    assert cautious["correct"] is True
    hasty = hl.grade_source_interpretation("?", {"conclusion_ids": ["k1"]}, not_inferable)
    assert hasty["correct"] is False


# --------------------------------------------------------------------------- #
# Content validity invariant (32.2)
# --------------------------------------------------------------------------- #
def _expert_verified_claim(client, db_session, entity):
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
            "claim_type": "factual",
            "statement_vi": "Hoa văn được khắc trên đỉnh.",
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
    assert client.post(
        f"/api/v1/admin/history/claims/{claim['id']}/transition",
        params={"target": "editor_reviewed"},
    ).status_code == 200
    assert client.post(
        f"/api/v1/admin/history/claims/{claim['id']}/transition",
        params={"target": "expert_verified"},
    ).status_code == 200
    return claim["id"]


def test_unreviewed_claim_blocks_authoritative_learning(client, db_session, seeded_content):
    staff = _make_user(
        client, db_session, "hlearn-staff1@example.com", "HLearn Staff", UserRole.admin
    )
    entity = _seed_entity(db_session)
    db_session.commit()
    claim = client.post(
        "/api/v1/admin/history/claims",
        json={
            "entity_id": str(entity.id),
            "claim_type": "factual",
            "statement_vi": "Một khẳng định chưa được kiểm chứng.",
            "verification_status": "unreviewed",
            "origin": "ai_generated",
        },
    ).json()
    assert claim["verification_status"] == "unreviewed"

    q = _create_question(
        client,
        seeded_content["motif"].id,
        question_type="evidence_match",
        claim_ids=[claim["id"]],
        answer_contract={"claim_id": claim["id"], "correct_source_ids": []},
    )
    assert q["content_validation_status"] == "blocked_for_authoritative_learning"

    stored = db_session.get(QuizQuestion, q["id"])
    assert hl.content_validity_check(db_session, stored) is False


def test_expert_verified_claim_allows_authoritative_learning(client, db_session, seeded_content):
    _make_user(client, db_session, "hlearn-staff2@example.com", "HLearn Staff2", UserRole.admin)
    entity = _seed_entity(db_session)
    db_session.commit()
    claim_id = _expert_verified_claim(client, db_session, entity)

    q = _create_question(
        client,
        seeded_content["motif"].id,
        question_type="evidence_match",
        claim_ids=[claim_id],
        answer_contract={"claim_id": claim_id, "correct_source_ids": []},
    )
    assert q["content_validation_status"] == "valid"

    stored = db_session.get(QuizQuestion, q["id"])
    assert hl.content_validity_check(db_session, stored) is True


def test_question_without_claims_is_valid(client, db_session, seeded_content):
    _make_user(client, db_session, "hlearn-staff3@example.com", "HLearn Staff3", UserRole.admin)
    q = _create_question(client, seeded_content["motif"].id)
    assert q["content_validation_status"] == "valid"


# --------------------------------------------------------------------------- #
# Server-authoritative grading endpoint
# --------------------------------------------------------------------------- #
def test_grade_endpoint_is_server_authoritative(client, db_session, seeded_content):
    _make_user(client, db_session, "hlearn-staff4@example.com", "HLearn Staff4", UserRole.admin)
    q = _create_question(client, seeded_content["motif"].id)

    # The client submits a wrong answer but fabricates correct=true / score=0.99.
    res = client.post(
        f"/api/v1/history/questions/{q['id']}/grade",
        json={
            "answer": {"ordered_entity_ids": ["zzz", "yyy", "xxx"]},
            "correct": True,
            "score": 0.99,
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["correct"] is False
    assert body["score"] == 0.0
    assert body["skill_dimensions"] == ["chronology", "factual_recall"]
    assert "feedback_vi" in body


def test_grade_endpoint_correct_answer_scores_full(client, db_session, seeded_content):
    user = _make_user(client, db_session, "hlearn-staff5@example.com", "HLearn Staff5", UserRole.admin)
    q = _create_question(client, seeded_content["motif"].id)

    res = client.post(
        f"/api/v1/history/questions/{q['id']}/grade",
        json={"answer": {"ordered_entity_ids": ["e1", "e2", "e3"]}},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["correct"] is True
    assert body["score"] == 1.0

    # Mastery V2: each skill dimension on the question got a weighted update.
    row = db_session.scalar(
        select(UserSkillLevel).where(
            UserSkillLevel.user_id == user.id,
            UserSkillLevel.skill_type == "chronology",
        )
    )
    assert row is not None
    assert row.total_questions == 1
    assert row.correct_answers == 1
    assert row.skill_level == 1.0
    assert (row.skill_dimensions or {}).get("last_score") == 1.0

    # A follow-up wrong answer pulls the running average down.
    client.post(
        f"/api/v1/history/questions/{q['id']}/grade",
        json={"answer": {"ordered_entity_ids": ["x", "y", "z"]}},
    )
    db_session.expire_all()
    row = db_session.scalar(
        select(UserSkillLevel).where(
            UserSkillLevel.user_id == user.id,
            UserSkillLevel.skill_type == "chronology",
        )
    )
    assert row.total_questions == 2
    assert row.skill_level == 0.5  # (1.0 * 1 + 0.0) / 2


def test_grade_requires_auth(client, seeded_content):
    res = client.post(
        f"/api/v1/history/questions/{uuid4()}/grade",
        json={"answer": {}},
    )
    assert res.status_code == 401


def test_grade_unknown_question_404(client, db_session):
    _make_user(client, db_session, "hlearn-user1@example.com", "HLearn User")
    res = client.post(
        f"/api/v1/history/questions/{uuid4()}/grade",
        json={"answer": {}},
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "HISTORY_QUESTION_NOT_FOUND"


# --------------------------------------------------------------------------- #
# Public/staff question endpoints
# --------------------------------------------------------------------------- #
def test_public_question_list_and_detail(client, db_session, seeded_content):
    _make_user(
        client, db_session, "hlearn-staff6@example.com", "HLearn Staff6", UserRole.admin
    )
    q = _create_question(client, seeded_content["motif"].id)

    # Public endpoints work without auth (the client may carry a staff cookie;
    # the list/detail routes declare no auth dependency).
    res = client.get("/api/v1/history/questions")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["total"] >= 1
    ids = [i["id"] for i in body["items"]]
    assert q["id"] in ids

    detail = client.get(f"/api/v1/history/questions/{q['id']}")
    assert detail.status_code == 200
    assert detail.json()["content_validation_status"] == "valid"
    assert detail.json()["answer_contract"]["ordered_entity_ids"] == ["e1", "e2", "e3"]


def test_public_question_list_filters(client, db_session, seeded_content):
    _make_user(client, db_session, "hlearn-staff7@example.com", "HLearn Staff7", UserRole.admin)
    _create_question(
        client,
        seeded_content["motif"].id,
        question_type="map_location",
        answer_contract={"lat": 16.46, "lng": 107.59, "tolerance_km": 10, "geo_precision": "exact"},
    )
    _create_question(
        client,
        seeded_content["motif"].id,
        question_type="chronology_order",
        answer_contract={"ordered_entity_ids": ["a", "b"]},
    )
    res = client.get(
        "/api/v1/history/questions",
        params={"question_type": "map_location", "content_validation_status": "valid"},
    )
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["question_type"] == "map_location"


def test_create_question_requires_staff(client, db_session, seeded_content):
    _make_user(client, db_session, "hlearn-user2@example.com", "HLearn User2")
    res = client.post(
        "/api/v1/history/questions",
        json={
            "motif_id": str(seeded_content["motif"].id),
            "question_type": "chronology_order",
            "question_text": "Sắp xếp theo thời gian.",
        },
    )
    assert res.status_code == 403


def test_create_question_rejects_unknown_type(client, db_session, seeded_content):
    _make_user(client, db_session, "hlearn-staff8@example.com", "HLearn Staff8", UserRole.admin)
    res = client.post(
        "/api/v1/history/questions",
        json={
            "motif_id": str(seeded_content["motif"].id),
            "question_type": "not_a_real_type",
            "question_text": "Sắp xếp theo thời gian.",
        },
    )
    assert res.status_code == 422


def test_create_question_with_entity_id_validates(client, db_session, seeded_content):
    _make_user(client, db_session, "hlearn-staff9@example.com", "HLearn Staff9", UserRole.admin)
    res = client.post(
        "/api/v1/history/questions",
        json={
            "motif_id": str(seeded_content["motif"].id),
            "question_type": "urn_hotspot",
            "question_text": "Chọn điểm nóng.",
            "entity_id": str(uuid4()),
            "answer_contract": {"hotspot_id": "hs-1"},
        },
    )
    assert res.status_code == 404


# --------------------------------------------------------------------------- #
# Mastery V2 skills endpoint
# --------------------------------------------------------------------------- #
def test_skills_endpoint_returns_eight_null_dimensions(client, db_session):
    user = _make_user(client, db_session, "hlearn-user3@example.com", "HLearn User3")
    res = client.get(f"/api/v1/history/skills/{user.id}")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["user_id"] == str(user.id)
    dims = {d["dimension"]: d for d in body["dimensions"]}
    assert len(dims) == 8
    assert dims["recognition"]["value"] is None
    assert dims["chronology"]["value"] is None
    assert body["overall"] is None


def test_skills_endpoint_idor_protection(client, db_session):
    student1 = _make_user(client, db_session, "hlearn-student1@example.com", "Student One", UserRole.learner)
    student2 = _make_user(client, db_session, "hlearn-student2@example.com", "Student Two", UserRole.learner)
    teacher = _make_user(client, db_session, "hlearn-teacher1@example.com", "Teacher One", UserRole.teacher)
    admin = _make_user(client, db_session, "hlearn-admin1@example.com", "Admin One", UserRole.admin)

    # Student 2 tries to access Student 1's skills -> 403 Forbidden
    _login(client, student2.email)
    res = client.get(f"/api/v1/history/skills/{student1.id}")
    assert res.status_code == 403

    # Student 1 accesses own skills -> 200 OK
    _login(client, student1.email)
    res = client.get(f"/api/v1/history/skills/{student1.id}")
    assert res.status_code == 200

    # Teacher accesses Student 1's skills -> 200 OK
    _login(client, teacher.email)
    res = client.get(f"/api/v1/history/skills/{student1.id}")
    assert res.status_code == 200

    # Admin accesses Student 1's skills -> 200 OK
    _login(client, admin.email)
    res = client.get(f"/api/v1/history/skills/{student1.id}")
    assert res.status_code == 200


def test_skills_endpoint_reflects_graded_dimensions(client, db_session, seeded_content):
    user = _make_user(client, db_session, "hlearn-staff10@example.com", "HLearn Staff10", UserRole.admin)
    q = _create_question(
        client,
        seeded_content["motif"].id,
        skill_dimensions=["chronology", "geography"],
    )
    client.post(
        f"/api/v1/history/questions/{q['id']}/grade",
        json={"answer": {"ordered_entity_ids": ["e1", "e2", "e3"]}},
    )
    res = client.get(f"/api/v1/history/skills/{user.id}")
    assert res.status_code == 200
    dims = {d["dimension"]: d for d in res.json()["dimensions"]}
    assert dims["chronology"]["value"] == 1.0
    assert dims["chronology"]["total_questions"] == 1
    assert dims["geography"]["value"] == 1.0
    assert dims["recognition"]["value"] is None
    assert res.json()["overall"] == 1.0


def test_history_question_types_registry_populated_on_authoring(client, db_session, seeded_content):
    _make_user(client, db_session, "hlearn-staff11@example.com", "HLearn Staff11", UserRole.admin)
    _create_question(client, seeded_content["motif"].id)
    _create_question(
        client,
        seeded_content["motif"].id,
        question_type="urn_hotspot",
        answer_contract={"hotspot_id": "hs-1"},
    )
    from backend.models import HistoryQuestionType

    keys = {r.key for r in db_session.scalars(select(HistoryQuestionType))}
    assert "chronology_order" in keys
    assert "urn_hotspot" in keys