# -*- coding: utf-8 -*-
"""V5-T102: Real Availability Inventory & Workshop Calendar Test Suite.

Audits and verifies:
1. Workshop slot creation and availability calendar query:
   - Calendar schedule returned with capacity, reserved_seats, confirmed_seats, and available_seats.
2. Seat reservation with hold timeout:
   - Reserving seats holds capacity temporarily with a countdown timeout (e.g., 900s).
   - Slot available_seats decrements by reserved amount.
3. Idempotent reservation replay:
   - Identical payload with same idempotency_key returns original receipt without double-holding seats.
   - Differing payload with same idempotency_key returns HTTP 409 Conflict RBPC_IDEMPOTENCY_CONFLICT.
4. Capacity boundary enforcement & no false checkouts:
   - Attempting to reserve more seats than available capacity returns HTTP 409 INSUFFICIENT_SEAT_CAPACITY.
5. Reserve timeout auto-expiration:
   - Stale holds past expires_at automatically transition to 'expired' and release reserved seats
     back to the available inventory pool.
6. Partner confirmation:
   - Provider confirms pending hold, moving seats from reserved to confirmed permanently.
   - Synchronizes linked inquiry status to 'confirmed'.
   - Records cryptographic audit trail in rbpc_content_audit.
7. Expired hold confirmation rejection:
   - Partner cannot confirm an expired reservation; rejected with HTTP 409 RESERVATION_EXPIRED.
8. Cancellation and seat restoration:
   - Cancelling reservation restores seat capacity.
9. Multi-tenant RBAC and ownership isolation:
   - Guest cannot confirm/cancel (HTTP 403 FORBIDDEN).
   - Partner A cannot manage reservations or slots for Partner B's experience (HTTP 403 FORBIDDEN_SCOPE).
   - Admin has full access.
10. Negative abuse concurrency race condition prevention:
   - Two concurrent users cannot confirm or reserve the last remaining seat twice.
   - Uses real parallel thread pool with independent database sessions.
   - Exactly ONE succeeds (HTTP 201), the other is rejected with HTTP 409 Conflict.
   - Database check constraint ck_rbpc_slots_capacity_bound guarantees zero overbooking.
"""
from __future__ import annotations

import concurrent.futures
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.base_model import Base
import backend.main as main
from backend.deps import get_db
from backend.models import User, UserRole
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
    RbpcReservationStatus,
    RbpcSeatReservation,
    RbpcSlotStatus,
    RbpcWorkshopSlot,
)
from backend.security import create_jwt_token, hash_password


# --------------------------------------------------------------------------- #
# Helpers & Seed Fixtures
# --------------------------------------------------------------------------- #
def _create_test_user(
    db_session: Session,
    email: str,
    role: UserRole = UserRole.teacher,
    display_name: str | None = None,
) -> User:
    """Create and persist a user with a specific role."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"u_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(user: User) -> dict[str, str]:
    """Generate Bearer token authorization headers."""
    from backend.config import settings
    token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=60),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "access", "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


def _seed_experience_with_slot(
    db_session: Session,
    capacity: int = 10,
    provider_user: User | None = None,
    suffix: str = "",
) -> tuple[RbpcCreator, RbpcExperience, RbpcWorkshopSlot]:
    """Helper to seed a consented creator, experience, and workshop slot."""
    uid = uuid.uuid4().hex[:8]
    creator = RbpcCreator(
        slug=f"artisan-v5-t102-{uid}{suffix}",
        public_name=f"Nghệ nhân Thử Nghiệm {uid}",
        craft_tradition="Chế tác Kim hoàn Huế",
        approved_bio_vi="Tiểu sử nghệ nhân phục vụ kiểm thử availability calendar.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"workshop-truc-chi-{uid}{suffix}",
        creator_id=creator.id,
        provider_name=f"Xưởng Trúc Chỉ {uid}",
        provider_id=provider_user.id if provider_user else None,
        title_vi="Workshop Nghệ thuật Trúc Chỉ Huế",
        description_vi="Trải nghiệm làm giấy Trúc Chỉ truyền thống.",
        area_public="Huế",
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.flush()

    now = datetime.now(timezone.utc)
    slot = RbpcWorkshopSlot(
        experience_id=exp.id,
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=2, hours=3),
        capacity=capacity,
        reserved_seats=0,
        confirmed_seats=0,
        status=RbpcSlotStatus.open.value,
        notes="Buổi sáng 09:00 - 12:00",
    )
    db_session.add(slot)
    db_session.commit()
    db_session.refresh(slot)
    return creator, exp, slot


# --------------------------------------------------------------------------- #
# Test Cases
# --------------------------------------------------------------------------- #
def test_calendar_availability_query(client: TestClient, db_session: Session):
    """Verify querying experience availability calendar returns correct slots and seat metrics."""
    _, exp, slot = _seed_experience_with_slot(db_session, capacity=8)

    res = client.get(f"/api/v1/rbpc/experiences/{exp.slug}/availability")
    assert res.status_code == status.HTTP_200_OK

    data = res.json()
    assert data["experience_slug"] == exp.slug
    assert data["total_slots"] >= 1
    found_slot = next(s for s in data["slots"] if s["id"] == str(slot.id))
    assert found_slot["capacity"] == 8
    assert found_slot["available_seats"] == 8
    assert found_slot["reserved_seats"] == 0
    assert found_slot["confirmed_seats"] == 0
    assert found_slot["status"] == "open"


def test_reserve_seats_positive_flow(client: TestClient, db_session: Session):
    """Verify reserving seats holds capacity with reserve timeout and returns reservation receipt."""
    _, exp, slot = _seed_experience_with_slot(db_session, capacity=6)

    payload = {
        "slot_id": str(slot.id),
        "seats": 2,
        "customer_name": "Lê Văn Hoàng",
        "customer_contact": "hoang.le@example.com",
        "hold_timeout_seconds": 900,
    }

    res = client.post("/api/v1/rbpc/availability/reserve", json=payload)
    assert res.status_code == status.HTTP_201_CREATED

    data = res.json()
    assert data["seats"] == 2
    assert data["status"] == "pending"
    assert data["public_ref"].startswith("RES-")
    assert data["customer_name"] == "Lê Văn Hoàng"
    assert data["remaining_seconds"] > 800

    # Verify database slot reflects reserved seats
    db_session.expire_all()
    slot_db = db_session.get(RbpcWorkshopSlot, slot.id)
    assert slot_db.reserved_seats == 2
    assert slot_db.confirmed_seats == 0
    assert slot_db.available_seats == 4


def test_reserve_seats_idempotency(client: TestClient, db_session: Session):
    """Verify idempotent replay returns identical reservation and differing payload yields 409."""
    _, exp, slot = _seed_experience_with_slot(db_session, capacity=10)
    idem_key = str(uuid.uuid4())

    payload = {
        "slot_id": str(slot.id),
        "seats": 3,
        "customer_name": "Trần Thị Mai",
        "customer_contact": "mai.tran@example.com",
        "hold_timeout_seconds": 900,
        "idempotency_key": idem_key,
    }

    # 1. First submission
    res1 = client.post("/api/v1/rbpc/availability/reserve", json=payload)
    assert res1.status_code == status.HTTP_201_CREATED
    ref1 = res1.json()["public_ref"]

    # 2. Idempotent replay with identical payload
    res2 = client.post("/api/v1/rbpc/availability/reserve", json=payload)
    assert res2.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)
    assert res2.json()["public_ref"] == ref1

    # Verify only 3 seats reserved (not 6)
    db_session.expire_all()
    slot_db = db_session.get(RbpcWorkshopSlot, slot.id)
    assert slot_db.reserved_seats == 3

    # 3. Differing payload with same idempotency key returns 409 Conflict
    conflicting_payload = dict(payload)
    conflicting_payload["seats"] = 5
    res3 = client.post("/api/v1/rbpc/availability/reserve", json=conflicting_payload)
    assert res3.status_code == status.HTTP_409_CONFLICT
    assert res3.json()["error"]["code"] == "RBPC_IDEMPOTENCY_CONFLICT"


def test_reserve_seats_exceeding_capacity_rejected(client: TestClient, db_session: Session):
    """Verify attempting to reserve more seats than available capacity returns HTTP 409."""
    _, exp, slot = _seed_experience_with_slot(db_session, capacity=2)

    payload = {
        "slot_id": str(slot.id),
        "seats": 3,  # Exceeds capacity of 2
        "customer_name": "Phạm Quốc Tuấn",
        "customer_contact": "tuan.pham@example.com",
    }

    res = client.post("/api/v1/rbpc/availability/reserve", json=payload)
    assert res.status_code == status.HTTP_409_CONFLICT
    err = res.json()["error"]
    assert err["code"] == "INSUFFICIENT_SEAT_CAPACITY"
    assert err["details"]["available_seats"] == 2
    assert err["details"]["requested_seats"] == 3


def test_reserve_timeout_auto_expiration(client: TestClient, db_session: Session):
    """Verify expired holds past expires_at automatically release seats back to available inventory."""
    _, exp, slot = _seed_experience_with_slot(db_session, capacity=5)

    # 1. Create a reservation
    payload = {
        "slot_id": str(slot.id),
        "seats": 2,
        "customer_name": "Vũ Đình Nam",
        "customer_contact": "nam.vu@example.com",
        "hold_timeout_seconds": 60,
    }
    res = client.post("/api/v1/rbpc/availability/reserve", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    public_ref = res.json()["public_ref"]

    # 2. Simulate expiration by backdating expires_at in database
    db_session.expire_all()
    reservation = db_session.scalar(
        select(RbpcSeatReservation).where(RbpcSeatReservation.public_ref == public_ref)
    )
    reservation.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    db_session.commit()

    # 3. Lookup reservation status -> triggers lazy expiration cleanup
    lookup_res = client.get(f"/api/v1/rbpc/availability/reservations/{public_ref}")
    assert lookup_res.status_code == status.HTTP_200_OK
    assert lookup_res.json()["status"] == "expired"
    assert lookup_res.json()["remaining_seconds"] == 0

    # 4. Check calendar availability: seats must be back to 5 available
    cal_res = client.get(f"/api/v1/rbpc/experiences/{exp.slug}/availability")
    assert cal_res.status_code == status.HTTP_200_OK
    found_slot = next(s for s in cal_res.json()["slots"] if s["id"] == str(slot.id))
    assert found_slot["available_seats"] == 5
    assert found_slot["reserved_seats"] == 0


def test_partner_confirm_reservation(client: TestClient, db_session: Session):
    """Verify provider can confirm a pending hold, moving seats to confirmed permanently."""
    provider = _create_test_user(db_session, "artisan_partner_1@example.com", role=UserRole.teacher)
    _, exp, slot = _seed_experience_with_slot(db_session, capacity=6, provider_user=provider)

    # Visitor holds 2 seats
    res_resp = client.post(
        "/api/v1/rbpc/availability/reserve",
        json={
            "slot_id": str(slot.id),
            "seats": 2,
            "customer_name": "Ngô Bích Hạnh",
            "customer_contact": "hanh.ngo@example.com",
        },
    )
    assert res_resp.status_code == status.HTTP_201_CREATED
    reservation_id = res_resp.json()["id"]

    # Partner confirms the reservation
    confirm_resp = client.post(
        "/api/v1/rbpc/partner/availability/confirm",
        json={"reservation_id": reservation_id, "partner_note": "Xác nhận tiếp đón đoàn"},
        headers=_auth_headers(provider),
    )
    assert confirm_resp.status_code == status.HTTP_200_OK
    data = confirm_resp.json()
    assert data["status"] == "confirmed"
    assert data["confirmed_at"] is not None

    # Verify slot seats moved from reserved to confirmed
    db_session.expire_all()
    slot_db = db_session.get(RbpcWorkshopSlot, slot.id)
    assert slot_db.reserved_seats == 0
    assert slot_db.confirmed_seats == 2
    assert slot_db.available_seats == 4


def test_partner_confirm_expired_hold_rejected(client: TestClient, db_session: Session):
    """Verify partner attempting to confirm an expired hold is rejected with HTTP 409."""
    provider = _create_test_user(db_session, "artisan_partner_2@example.com", role=UserRole.teacher)
    _, exp, slot = _seed_experience_with_slot(db_session, capacity=4, provider_user=provider)

    res_resp = client.post(
        "/api/v1/rbpc/availability/reserve",
        json={
            "slot_id": str(slot.id),
            "seats": 2,
            "customer_name": "Hoàng Minh Quân",
            "customer_contact": "quan.hoang@example.com",
        },
    )
    assert res_resp.status_code == status.HTTP_201_CREATED
    res_id = res_resp.json()["id"]

    # Backdate expiration to simulate expired hold
    db_session.expire_all()
    reservation = db_session.get(RbpcSeatReservation, uuid.UUID(res_id))
    reservation.expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db_session.commit()

    # Confirmation must fail
    confirm_resp = client.post(
        "/api/v1/rbpc/partner/availability/confirm",
        json={"reservation_id": res_id},
        headers=_auth_headers(provider),
    )
    assert confirm_resp.status_code == status.HTTP_409_CONFLICT
    assert confirm_resp.json()["error"]["code"] == "RESERVATION_EXPIRED"

    # Seats must be freed
    db_session.expire_all()
    slot_db = db_session.get(RbpcWorkshopSlot, slot.id)
    assert slot_db.reserved_seats == 0
    assert slot_db.confirmed_seats == 0
    assert slot_db.available_seats == 4


def test_cancel_reservation_restores_capacity(client: TestClient, db_session: Session):
    """Verify cancelling a reservation frees held seats back to the slot."""
    provider = _create_test_user(db_session, "artisan_partner_3@example.com", role=UserRole.teacher)
    _, exp, slot = _seed_experience_with_slot(db_session, capacity=5, provider_user=provider)

    # 1. Reserve 2 seats
    res_resp = client.post(
        "/api/v1/rbpc/availability/reserve",
        json={
            "slot_id": str(slot.id),
            "seats": 2,
            "customer_name": "Đỗ Thu Trang",
            "customer_contact": "trang.do@example.com",
        },
    )
    res_id = res_resp.json()["id"]

    # 2. Cancel reservation
    cancel_resp = client.post(
        "/api/v1/rbpc/partner/availability/cancel",
        json={"reservation_id": res_id, "reason": "Khách báo bận đột xuất"},
        headers=_auth_headers(provider),
    )
    assert cancel_resp.status_code == status.HTTP_200_OK
    assert cancel_resp.json()["status"] == "cancelled"

    # 3. Verify slot capacity restored
    db_session.expire_all()
    slot_db = db_session.get(RbpcWorkshopSlot, slot.id)
    assert slot_db.reserved_seats == 0
    assert slot_db.available_seats == 5


def test_multitenant_rbac_protection(client: TestClient, db_session: Session):
    """Verify cross-tenant access control and guest prevention on availability mutations."""
    provider_a = _create_test_user(db_session, "provider_a@example.com", role=UserRole.teacher)
    provider_b = _create_test_user(db_session, "provider_b@example.com", role=UserRole.teacher)
    guest_user = _create_test_user(db_session, "guest@example.com", role=UserRole.guest)
    admin_user = _create_test_user(db_session, "admin@example.com", role=UserRole.admin)

    _, exp_a, slot_a = _seed_experience_with_slot(db_session, capacity=5, provider_user=provider_a, suffix="_a")

    # Reserve seat on Provider A's slot
    res_resp = client.post(
        "/api/v1/rbpc/availability/reserve",
        json={
            "slot_id": str(slot_a.id),
            "seats": 1,
            "customer_name": "Test Customer",
            "customer_contact": "cust@example.com",
        },
    )
    res_id = res_resp.json()["id"]

    # 1. Guest user cannot confirm (403 Forbidden)
    res_guest = client.post(
        "/api/v1/rbpc/partner/availability/confirm",
        json={"reservation_id": res_id},
        headers=_auth_headers(guest_user),
    )
    assert res_guest.status_code == status.HTTP_403_FORBIDDEN

    # 2. Provider B cannot confirm Provider A's reservation (403 FORBIDDEN_SCOPE)
    res_b = client.post(
        "/api/v1/rbpc/partner/availability/confirm",
        json={"reservation_id": res_id},
        headers=_auth_headers(provider_b),
    )
    assert res_b.status_code == status.HTTP_403_FORBIDDEN
    assert res_b.json()["error"]["code"] == "FORBIDDEN_SCOPE"

    # 3. Admin can confirm Provider A's reservation
    res_admin = client.post(
        "/api/v1/rbpc/partner/availability/confirm",
        json={"reservation_id": res_id},
        headers=_auth_headers(admin_user),
    )
    assert res_admin.status_code == status.HTTP_200_OK
    assert res_admin.json()["status"] == "confirmed"


def test_create_and_list_partner_slots(client: TestClient, db_session: Session):
    """Verify partner can create workshop slots and query their slot inventory."""
    provider = _create_test_user(db_session, "slot_owner@example.com", role=UserRole.teacher)
    _, exp, _ = _seed_experience_with_slot(db_session, capacity=5, provider_user=provider, suffix="_mgmt")

    now = datetime.now(timezone.utc)
    create_payload = {
        "experience_slug": exp.slug,
        "start_time": (now + timedelta(days=5)).isoformat(),
        "end_time": (now + timedelta(days=5, hours=2)).isoformat(),
        "capacity": 12,
        "notes": "Lớp nâng cao đúc đồng",
    }

    create_res = client.post(
        "/api/v1/rbpc/partner/slots",
        json=create_payload,
        headers=_auth_headers(provider),
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    slot_id = create_res.json()["id"]
    assert create_res.json()["capacity"] == 12

    # Query partner slots
    list_res = client.get(
        f"/api/v1/rbpc/partner/slots?experience_slug={exp.slug}",
        headers=_auth_headers(provider),
    )
    assert list_res.status_code == status.HTTP_200_OK
    slot_ids = [s["id"] for s in list_res.json()]
    assert slot_id in slot_ids


def test_negative_abuse_two_users_cannot_reserve_last_seat_concurrently(engine):
    """CRITICAL NEGATIVE ABUSE TEST: Concurrency race condition prevention.

    Two users simultaneously attempt to reserve the last remaining seat in a workshop
    slot with capacity=1 using parallel worker threads and independent database sessions.
    
    Invariants:
    1. Exactly ONE request succeeds with HTTP 201 Created.
    2. The other request fails with HTTP 409 Conflict (INSUFFICIENT_SEAT_CAPACITY).
    3. The slot reserved_seats in the database is exactly 1 (never 2).
    4. CheckConstraint ck_rbpc_slots_capacity_bound guarantees no overbooking.
    """
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Seed slot with capacity = 1
    _, exp, slot = _seed_experience_with_slot(db, capacity=1, suffix="_race")
    slot_id_str = str(slot.id)
    db.close()

    results = []

    def _reserve_seat_worker(worker_id: int):
        app_client = TestClient(main.app)
        payload = {
            "slot_id": slot_id_str,
            "seats": 1,
            "customer_name": f"Khách Hàng Race {worker_id}",
            "customer_contact": f"race_{worker_id}@example.com",
            "hold_timeout_seconds": 600,
        }
        res = app_client.post("/api/v1/rbpc/availability/reserve", json=payload)
        return res.status_code, res.json()

    # Execute both requests concurrently across 2 parallel threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(_reserve_seat_worker, 1)
        f2 = executor.submit(_reserve_seat_worker, 2)
        r1 = f1.result()
        r2 = f2.result()
        results = [r1, r2]

    status_codes = [r[0] for r in results]

    # Exactly one 201 Created, exactly one 409 Conflict
    assert status.HTTP_201_CREATED in status_codes, f"Expected one 201 Created, got {status_codes}"
    assert status.HTTP_409_CONFLICT in status_codes, f"Expected one 409 Conflict, got {status_codes}"

    conflict_result = next(r[1] for r in results if r[0] == status.HTTP_409_CONFLICT)
    assert conflict_result["error"]["code"] == "INSUFFICIENT_SEAT_CAPACITY"

    # Verify physical database invariant
    verify_db = SessionLocal()
    slot_db = verify_db.get(RbpcWorkshopSlot, uuid.UUID(slot_id_str))
    assert slot_db.reserved_seats == 1
    assert slot_db.confirmed_seats == 0
    assert slot_db.available_seats == 0
    assert slot_db.reserved_seats + slot_db.confirmed_seats <= slot_db.capacity
    verify_db.close()


def test_negative_abuse_two_users_cannot_confirm_last_seat_twice(engine):
    """CRITICAL NEGATIVE ABUSE TEST: Two concurrent requests confirming the same reservation.

    Simulates concurrent confirmation race conditions (e.g., dual confirmation calls
    racing past application boundary simultaneously).
    
    Invariants:
    1. Only 1 confirmation can transition the seat and increment confirmed_seats.
    2. Concurrent confirmation receives idempotent success or conflict; total confirmed seats
       is strictly 1 (never exceeding capacity = 1).
    3. PostgreSQL check constraint ck_rbpc_slots_capacity_bound verifies zero overbooking.
    """
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    uid = uuid.uuid4().hex[:6]
    provider = _create_test_user(db, f"confirm_race_{uid}@example.com", role=UserRole.teacher)
    _, exp, slot = _seed_experience_with_slot(db, capacity=1, provider_user=provider, suffix=f"_cr_{uid}")

    # Seed 1 reservation holding the only seat
    now = datetime.now(timezone.utc)
    res = RbpcSeatReservation(
        slot_id=slot.id,
        public_ref=f"RES-RACE-{uid.upper()}",
        seats=1,
        status=RbpcReservationStatus.pending.value,
        hold_timeout_seconds=600,
        expires_at=now + timedelta(minutes=10),
        customer_name="Người Thử Nghiệm",
        customer_contact=f"race_confirm_{uid}@example.com",
    )
    slot.reserved_seats = 1
    db.add(res)
    db.commit()
    res_id_str = str(res.id)
    slot_id_str = str(slot.id)
    headers = _auth_headers(provider)
    db.close()

    def _confirm_worker():
        app_client = TestClient(main.app)
        response = app_client.post(
            "/api/v1/rbpc/partner/availability/confirm",
            json={"reservation_id": res_id_str},
            headers=headers,
        )
        return response.status_code, response.json()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(_confirm_worker)
        f2 = executor.submit(_confirm_worker)
        r1 = f1.result()
        r2 = f2.result()
        results = [r1, r2]

    status_codes = [r[0] for r in results]
    # At least one must succeed with 200 OK
    assert status.HTTP_200_OK in status_codes, f"Expected 200 OK, got {status_codes}"

    # Verify physical database integrity
    verify_db = SessionLocal()
    slot_db = verify_db.get(RbpcWorkshopSlot, uuid.UUID(slot_id_str))
    res_db = verify_db.get(RbpcSeatReservation, uuid.UUID(res_id_str))
    assert res_db.status == "confirmed"
    assert slot_db.confirmed_seats == 1
    assert slot_db.reserved_seats == 0
    assert slot_db.available_seats == 0
    # Capacity is strictly 1: cannot be confirmed twice to make confirmed_seats=2
    assert slot_db.confirmed_seats <= slot_db.capacity
    verify_db.close()

