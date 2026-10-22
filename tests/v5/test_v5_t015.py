# -*- coding: utf-8 -*-
"""V5-T015: RBPC Inquiry Idempotency and Retry Safety Test Suite.

Audits and verifies:
1. Idempotent replay with identical payload:
   - Submitting identical inquiry with same idempotency_key twice returns HTTP 202 Accepted.
   - Both responses contain identical public reference (INQ-*) and opaque status_token (tok_sec_*).
   - Only 1 row is created in the database.
2. Idempotency conflict with differing payloads:
   - Submitting inquiry with same idempotency_key but differing:
     a) party_size
     b) contact name
     c) contact value (email/phone)
     d) experience slug (experience_id)
   - Must return HTTP 409 Conflict with standard error code "RBPC_IDEMPOTENCY_CONFLICT".
   - Standard error envelope {"error": {"code": ..., "message": ..., "details": ...}} is enforced.
   - Database row count remains exactly 1.
3. Concurrent race condition handling:
   - When two requests race past the initial idempotency check simultaneously into db.flush()/commit():
     the losing transaction encounters IntegrityError on uq_rbpc_inquiries_idempotency.
   - The endpoint gracefully catches IntegrityError, performs rollback, re-fetches the committed record:
     * If payload matches: returns HTTP 202 Accepted with original reference and status_token.
     * If payload conflicts: returns HTTP 409 Conflict with RBPC_IDEMPOTENCY_CONFLICT.
4. Concurrent multi-threaded inquiry submissions:
   - Simultaneous requests across parallel worker threads with independent database sessions.
   - Both succeed with HTTP 202 and identical tokens, maintaining zero duplicate rows.
"""
from __future__ import annotations

import concurrent.futures
import uuid
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.base_model import Base
import backend.main as main
from backend.deps import get_db
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
)
from backend.routers.rbpc import _inquiry_rate_limit_store


# --------------------------------------------------------------------------- #
# Fixtures & Test Setup
# --------------------------------------------------------------------------- #

@pytest.fixture(autouse=True)
def clean_inquiry_rate_limiter():
    """Reset rate limiter state before each test for test isolation."""
    _inquiry_rate_limit_store.clear()
    yield
    _inquiry_rate_limit_store.clear()


def _seed_test_experience(db_session, suffix: str = "") -> tuple[RbpcCreator, RbpcExperience]:
    """Helper to seed a consented creator and published inquiry-only experience."""
    uid = uuid.uuid4().hex[:8]
    creator = RbpcCreator(
        slug=f"artisan-v5-t015-{uid}{suffix}",
        public_name=f"Nghệ nhân Thử Nghiệm {uid}",
        craft_tradition="Chế tác Kim hoàn Huế",
        approved_bio_vi="Tiểu sử nghệ nhân phục vụ kiểm thử idempotency.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"workshop-kim-hoan-{uid}{suffix}",
        creator_id=creator.id,
        provider_name=f"Hiệu Kim Hoàn {uid}",
        title_vi="Workshop Chế tác Kim hoàn Huế",
        description_vi="Trải nghiệm chế tác kim hoàn truyền thống cung đình Huế.",
        area_public="Huế",
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return creator, exp


def _build_inquiry_payload(exp_slug: str, idempotency_key: str, **overrides) -> dict:
    """Build a valid visitor booking inquiry payload with customizable fields."""
    future_date = (date.today() + timedelta(days=14)).isoformat()
    payload = {
        "experience_slug": exp_slug,
        "contact": {
            "name": "Nguyễn Thị Phương Thảo",
            "method": "email",
            "value": "thao.nguyen@example.com",
        },
        "preferred_date": future_date,
        "party_size": 2,
        "message": "Quan tâm đến kỹ thuật đúc bạc truyền thống Huế.",
        "consent": {
            "version": "rbpc-inquiry-v1",
            "accepted": True,
            "privacy_accepted": True,
        },
        "idempotency_key": idempotency_key,
    }
    payload.update(overrides)
    return payload


# --------------------------------------------------------------------------- #
# 1. Identical Payload Replay & DB Single-Row Invariant
# --------------------------------------------------------------------------- #

def test_identical_inquiry_idempotency_replay(client, db_session):
    """Submitting identical inquiry with same idempotency_key twice returns 202 with identical tokens."""
    _, exp = _seed_test_experience(db_session, "-replay")
    idem_key = f"idem-key-{uuid.uuid4().hex}"
    payload = _build_inquiry_payload(exp.slug, idem_key)

    # 1. First submission -> HTTP 202 Accepted
    res1 = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res1.status_code == 202, f"Expected 202, got {res1.status_code}: {res1.text}"
    data1 = res1.json()
    assert data1["status"] == "new"
    assert data1["reference"].startswith("INQ-")
    assert data1["status_token"].startswith("tok_sec_")

    # 2. Replay with identical payload and same idempotency key -> HTTP 202 Accepted
    res2 = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res2.status_code == 202, f"Expected 202 on replay, got {res2.status_code}: {res2.text}"
    data2 = res2.json()

    # Exact token and reference identity
    assert data2["reference"] == data1["reference"], "Public reference must be identical on idempotent replay"
    assert data2["status_token"] == data1["status_token"], "Status token must be identical on idempotent replay"
    assert data2["status"] == data1["status"]

    # 3. Database Invariant: Exactly one record persisted in database
    db_records = list(
        db_session.scalars(select(RbpcInquiry).where(RbpcInquiry.idempotency_key == idem_key))
    )
    assert len(db_records) == 1, f"Expected exactly 1 DB record for idempotency key, found {len(db_records)}"
    assert db_records[0].public_ref == data1["reference"]
    assert db_records[0].opaque_token == data1["status_token"]


# --------------------------------------------------------------------------- #
# 2. Differing Payload Conflicts (HTTP 409 RBPC_IDEMPOTENCY_CONFLICT)
# --------------------------------------------------------------------------- #

def test_differing_inquiry_party_size_conflict(client, db_session):
    """Submitting inquiry with same idempotency_key but differing party_size returns 409 Conflict."""
    _, exp = _seed_test_experience(db_session, "-party-size")
    idem_key = f"idem-key-{uuid.uuid4().hex}"
    base_payload = _build_inquiry_payload(exp.slug, idem_key, party_size=2)

    res_init = client.post("/api/v1/rbpc/inquiries", json=base_payload)
    assert res_init.status_code == 202

    # Modified party_size
    conflict_payload = _build_inquiry_payload(exp.slug, idem_key, party_size=6)
    res_conflict = client.post("/api/v1/rbpc/inquiries", json=conflict_payload)
    assert res_conflict.status_code == 409, f"Expected 409, got {res_conflict.status_code}: {res_conflict.text}"

    err = res_conflict.json()["error"]
    assert err["code"] == "RBPC_IDEMPOTENCY_CONFLICT"
    assert "differing parameters" in err["message"].lower()

    # Verify DB still has exactly 1 record with original party_size
    db_inq = db_session.scalar(select(RbpcInquiry).where(RbpcInquiry.idempotency_key == idem_key))
    assert db_inq is not None
    assert db_inq.party_size == 2


def test_differing_inquiry_contact_name_conflict(client, db_session):
    """Submitting inquiry with same idempotency_key but differing contact name returns 409 Conflict."""
    _, exp = _seed_test_experience(db_session, "-name")
    idem_key = f"idem-key-{uuid.uuid4().hex}"
    base_payload = _build_inquiry_payload(exp.slug, idem_key)

    res_init = client.post("/api/v1/rbpc/inquiries", json=base_payload)
    assert res_init.status_code == 202

    # Differing contact name
    conflict_payload = dict(base_payload)
    conflict_payload["contact"] = {
        "name": "Lê Văn Toàn",
        "method": base_payload["contact"]["method"],
        "value": base_payload["contact"]["value"],
    }
    res_conflict = client.post("/api/v1/rbpc/inquiries", json=conflict_payload)
    assert res_conflict.status_code == 409

    err = res_conflict.json()["error"]
    assert err["code"] == "RBPC_IDEMPOTENCY_CONFLICT"


def test_differing_inquiry_contact_value_conflict(client, db_session):
    """Submitting inquiry with same idempotency_key but differing contact value returns 409 Conflict."""
    _, exp = _seed_test_experience(db_session, "-contact-val")
    idem_key = f"idem-key-{uuid.uuid4().hex}"
    base_payload = _build_inquiry_payload(exp.slug, idem_key)

    res_init = client.post("/api/v1/rbpc/inquiries", json=base_payload)
    assert res_init.status_code == 202

    # Differing contact value (different email)
    conflict_payload = dict(base_payload)
    conflict_payload["contact"] = {
        "name": base_payload["contact"]["name"],
        "method": "email",
        "value": "different.recipient@example.com",
    }
    res_conflict = client.post("/api/v1/rbpc/inquiries", json=conflict_payload)
    assert res_conflict.status_code == 409

    err = res_conflict.json()["error"]
    assert err["code"] == "RBPC_IDEMPOTENCY_CONFLICT"


def test_differing_inquiry_experience_conflict(client, db_session):
    """Submitting inquiry with same idempotency_key but differing experience returns 409 Conflict."""
    _, exp1 = _seed_test_experience(db_session, "-exp1")
    _, exp2 = _seed_test_experience(db_session, "-exp2")
    idem_key = f"idem-key-{uuid.uuid4().hex}"

    payload_exp1 = _build_inquiry_payload(exp1.slug, idem_key)
    res_init = client.post("/api/v1/rbpc/inquiries", json=payload_exp1)
    assert res_init.status_code == 202

    # Differing experience slug
    payload_exp2 = _build_inquiry_payload(exp2.slug, idem_key)
    res_conflict = client.post("/api/v1/rbpc/inquiries", json=payload_exp2)
    assert res_conflict.status_code == 409

    err = res_conflict.json()["error"]
    assert err["code"] == "RBPC_IDEMPOTENCY_CONFLICT"


# --------------------------------------------------------------------------- #
# 3. Simulated Concurrent Race Condition Handling
# --------------------------------------------------------------------------- #

def test_simulated_race_condition_matching_payload_recovers_202(engine):
    """Simulate concurrent race condition where initial check misses committed record:

    1. Row exists in DB.
    2. Concurrent request initial scalar lookup returns None (simulating race window before commit).
    3. Request proceeds to db.flush(), encounters IntegrityError on uq_rbpc_inquiries_idempotency.
    4. Exception handler catches IntegrityError, rolls back, re-queries, finds row, and returns 202.
    """
    _inquiry_rate_limit_store.clear()
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    setup_session = SessionLocal()
    uid = uuid.uuid4().hex[:8]
    creator = RbpcCreator(
        slug=f"artisan-race-{uid}",
        public_name=f"Nghệ nhân Race {uid}",
        craft_tradition="Chế tác Kim hoàn",
        approved_bio_vi="Tiểu sử nghệ nhân.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    setup_session.add(creator)
    setup_session.flush()

    exp = RbpcExperience(
        slug=f"workshop-race-{uid}",
        creator_id=creator.id,
        provider_name=f"Hiệu Kim Hoàn Race {uid}",
        title_vi="Workshop Kim Hoàn Race",
        description_vi="Trải nghiệm.",
        area_public="Huế",
        publication_state="published",
        availability_mode="inquiry_only",
    )
    setup_session.add(exp)
    setup_session.commit()
    exp_slug = exp.slug
    setup_session.close()

    def get_isolated_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    main.app.dependency_overrides[get_db] = get_isolated_db
    try:
        with TestClient(main.app) as test_client:
            idem_key = f"idem-key-{uuid.uuid4().hex}"
            payload = _build_inquiry_payload(exp_slug, idem_key)

            # First request commits to DB
            res_first = test_client.post("/api/v1/rbpc/inquiries", json=payload)
            assert res_first.status_code == 202
            first_data = res_first.json()

            # Now simulate the racing request with patched scalar on Session class
            original_scalar = Session.scalar
            lookup_calls = 0

            def racing_scalar(self, statement, *args, **kwargs):
                nonlocal lookup_calls
                stmt_str = str(statement)
                if "idempotency_key" in stmt_str:
                    lookup_calls += 1
                    if lookup_calls == 1:
                        # First lookup returns None: simulates racing past the pre-check
                        return None
                return original_scalar(self, statement, *args, **kwargs)

            with patch.object(Session, "scalar", racing_scalar):
                res_raced = test_client.post("/api/v1/rbpc/inquiries", json=payload)

            assert res_raced.status_code == 202, f"Expected 202 on race recovery, got {res_raced.status_code}: {res_raced.text}"
            raced_data = res_raced.json()
            assert raced_data["reference"] == first_data["reference"]
            assert raced_data["status_token"] == first_data["status_token"]
            assert lookup_calls >= 2, f"Expected at least 2 lookups, got {lookup_calls}"
    finally:
        main.app.dependency_overrides.clear()


def test_simulated_race_condition_conflicting_payload_returns_409(engine):
    """Simulate concurrent race condition with differing payload:

    1. Row exists in DB.
    2. Racing request with conflicting party_size misses initial check (simulated None).
    3. Hits IntegrityError on db.flush().
    4. Handler rolls back, re-fetches, compares payload, detects conflict, and returns 409.
    """
    _inquiry_rate_limit_store.clear()
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    setup_session = SessionLocal()
    uid = uuid.uuid4().hex[:8]
    creator = RbpcCreator(
        slug=f"artisan-race-conf-{uid}",
        public_name=f"Nghệ nhân Race Conf {uid}",
        craft_tradition="Chế tác Kim hoàn",
        approved_bio_vi="Tiểu sử nghệ nhân.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    setup_session.add(creator)
    setup_session.flush()

    exp = RbpcExperience(
        slug=f"workshop-race-conf-{uid}",
        creator_id=creator.id,
        provider_name=f"Hiệu Kim Hoàn Race {uid}",
        title_vi="Workshop Kim Hoàn Race",
        description_vi="Trải nghiệm.",
        area_public="Huế",
        publication_state="published",
        availability_mode="inquiry_only",
    )
    setup_session.add(exp)
    setup_session.commit()
    exp_slug = exp.slug
    setup_session.close()

    def get_isolated_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    main.app.dependency_overrides[get_db] = get_isolated_db
    try:
        with TestClient(main.app) as test_client:
            idem_key = f"idem-key-{uuid.uuid4().hex}"
            base_payload = _build_inquiry_payload(exp_slug, idem_key, party_size=2)

            res_first = test_client.post("/api/v1/rbpc/inquiries", json=base_payload)
            assert res_first.status_code == 202

            # Racing request has differing party_size
            conflicting_payload = _build_inquiry_payload(exp_slug, idem_key, party_size=10)

            original_scalar = Session.scalar
            lookup_calls = 0

            def racing_scalar(self, statement, *args, **kwargs):
                nonlocal lookup_calls
                stmt_str = str(statement)
                if "idempotency_key" in stmt_str:
                    lookup_calls += 1
                    if lookup_calls == 1:
                        return None
                return original_scalar(self, statement, *args, **kwargs)

            with patch.object(Session, "scalar", racing_scalar):
                res_raced = test_client.post("/api/v1/rbpc/inquiries", json=conflicting_payload)

            assert res_raced.status_code == 409, f"Expected 409 on conflict race, got {res_raced.status_code}: {res_raced.text}"
            err = res_raced.json()["error"]
            assert err["code"] == "RBPC_IDEMPOTENCY_CONFLICT"
            assert lookup_calls >= 2, f"Expected at least 2 lookups, got {lookup_calls}"
    finally:
        main.app.dependency_overrides.clear()


# --------------------------------------------------------------------------- #
# 4. Multi-Threaded Concurrent Race Condition Handling
# --------------------------------------------------------------------------- #

def test_multithreaded_concurrent_inquiry_submissions(engine):
    """Test authentic concurrent race condition across parallel threads with independent sessions.

    Spawns multiple threads submitting the exact same payload with same idempotency_key simultaneously.
    Verifies:
    - All threads receive HTTP 202 Accepted.
    - All threads receive the identical public reference and status token.
    - Exactly 1 record is created in PostgreSQL.
    """
    _inquiry_rate_limit_store.clear()

    # 1. Seed experience using a standalone session committed to DB
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    setup_session = SessionLocal()
    uid = uuid.uuid4().hex[:8]
    creator = RbpcCreator(
        slug=f"artisan-mt-{uid}",
        public_name=f"Nghệ nhân MT {uid}",
        craft_tradition="Chế tác Kim hoàn",
        approved_bio_vi="Phục vụ kiểm thử đa luồng.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    setup_session.add(creator)
    setup_session.flush()

    exp = RbpcExperience(
        slug=f"workshop-mt-{uid}",
        creator_id=creator.id,
        provider_name=f"Hiệu Kim Hoàn MT {uid}",
        title_vi="Workshop Kim Hoàn Đa Luồng",
        description_vi="Trải nghiệm kim hoàn đa luồng.",
        area_public="Huế",
        publication_state="published",
        availability_mode="inquiry_only",
    )
    setup_session.add(exp)
    setup_session.commit()
    exp_slug = exp.slug
    setup_session.close()

    # 2. Dependency override: Each request gets a fresh, isolated DB session
    def get_isolated_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    main.app.dependency_overrides[get_db] = get_isolated_db

    idem_key = f"idem-key-{uuid.uuid4().hex}"
    payload = _build_inquiry_payload(exp_slug, idem_key)

    def submit_request():
        with TestClient(main.app) as thread_client:
            return thread_client.post("/api/v1/rbpc/inquiries", json=payload)

    # 3. Fire concurrent requests simultaneously
    num_threads = 4
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(submit_request) for _ in range(num_threads)]
        responses = [f.result() for f in futures]

    main.app.dependency_overrides.clear()

    # 4. Verify all responses are 202 Accepted with identical reference and token
    references = set()
    status_tokens = set()
    for resp in responses:
        assert resp.status_code == 202, f"Concurrent thread failed: {resp.status_code}: {resp.text}"
        data = resp.json()
        references.add(data["reference"])
        status_tokens.add(data["status_token"])

    assert len(references) == 1, f"Expected 1 unique reference across concurrent threads, got: {references}"
    assert len(status_tokens) == 1, f"Expected 1 unique status_token across concurrent threads, got: {status_tokens}"

    # 5. Database Verification: Exactly 1 row in PostgreSQL
    verify_session = SessionLocal()
    try:
        rows = list(
            verify_session.scalars(select(RbpcInquiry).where(RbpcInquiry.idempotency_key == idem_key))
        )
        assert len(rows) == 1, f"Expected exactly 1 row in DB, found {len(rows)}"
        assert rows[0].public_ref == list(references)[0]
    finally:
        verify_session.close()
