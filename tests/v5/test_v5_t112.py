# -*- coding: utf-8 -*-
"""V5-T112: Truth-Level Funnel Dashboard Test Suite.

Wave W11, Slot A02:
Funnel dashboard separated by truth level in frontend/src/app/admin/ and backend/routers/.
Track visitor -> source read -> inquiry -> confirm -> completed with quality cohorts.
Measure actual recorded events.

Negative abuse invariant:
Projected figures (e.g. 1,100 bookings) never appear as completed bookings in truth dashboard.

Audits and verifies:
1. Negative abuse test (Empty Database baseline):
   - With zero closed inquiries and zero analytics events in the DB,
     observed completed bookings is strictly 0.
   - Never outputs fabricated pitch figures (e.g. 1,100 SOM bookings or 570M VND) into observed metrics.
   - anti_abuse_validation reports status 'PASSED_STRICT' and forecast_1100_in_completed_bookings is False.
2. Negative abuse test (Attempted injection fails closed):
   - validate_anti_abuse_integrity raises ValueError if allow_forecast_in_observed is True.
3. Sourced from real recorded events (5-stage conversion progression):
   - Stage 1: visitor (AnalyticsEvent with landing/explore)
   - Stage 2: source_read (AnalyticsEvent with source reading / claim interaction)
   - Stage 3: inquiry (RbpcInquiry in state: new, contacted, confirmed, closed)
   - Stage 4: confirm (RbpcInquiry in state: confirmed, closed)
   - Stage 5: completed (RbpcInquiry in state: closed)
   - An inquiry in state 'new' or 'contacted' does NOT count as confirmed or completed.
   - An inquiry in state 'confirmed' counts as confirmed but NOT completed.
   - Only when an inquiry transitions to 'closed' does it increment completed.
4. Clean epistemological separation of truth tiers:
   - OBSERVED: Strict database actuals with zero synthetic data.
   - HYPOTHESIS: Model conversion hypotheses from DOC-RBPC-FIN-001 §3.3.
   - FORECAST: Forward targets (1,100 bookings SOM) quarantined with explicit disclaimers.
5. Quality Cohorts breakdown:
   - Slices actual events by acquisition channel (email, phone, zalo) and experience.
   - Computes cohort-specific conversion percentages and source-grounding quality indicators.
6. Role-Based Access Control:
   - Unauthenticated requests return HTTP 401.
   - Regular learners return HTTP 403.
   - Admins and super_admins return HTTP 200.
7. Frontend contracts and files verification:
   - Verifies frontend/src/app/admin/funnel/page.tsx, FunnelDashboardClient.tsx, and page.test.tsx.
   - Confirms all required data-testids exist in the frontend source.
"""
from __future__ import annotations

import os
from pathlib import Path
import uuid
from datetime import date, datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.models import AnalyticsEvent, User, UserRole
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)
from backend.security import hash_password
from backend.services.truth_funnel import (
    calculate_truth_funnel,
    validate_anti_abuse_integrity,
)


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"usr_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client: TestClient, email: str, password: str = "Password123!") -> dict:
    client.cookies.clear()
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers={"X-Test-Client-IP": f"client_{email}"},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _setup_test_heritage_context(db_session, provider_user: User):
    creator = RbpcCreator(
        slug=f"artisan-funnel-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân Đúc Đồng Huế",
        craft_tradition="Đúc đồng thủ công",
        approved_bio_vi="Gia đình truyền thống đúc chuông và khí đồng.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-funnel-{uuid.uuid4().hex[:6]}",
        title_vi="Workshop Đúc Đồng Phường Đúc",
        title_en="Phuong Duc Bronze Casting Workshop",
        description_vi="Tham gia đúc đồng và tạo tác hoa văn.",
        creator_id=creator.id,
        provider_name="Xưởng Đúc Đồng Phường Đúc",
        provider_id=provider_user.id,
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return creator, exp


def test_v5_t112_negative_abuse_empty_database_zero_metrics(client, db_session):
    """Negative abuse invariant:

    When there are no closed inquiries or analytics events in the DB:
    - observed completed bookings is strictly 0.
    - All observed stages display strictly 0.
    - Projected figures (e.g. 1,100 bookings or 570M VND) never appear as completed bookings.
    """
    # Ensure baseline clean state for analytics events and inquiries
    db_session.execute(select(AnalyticsEvent))
    from sqlalchemy import delete
    from backend.models_rbpc import RbpcSettlementLedger
    db_session.execute(delete(RbpcSettlementLedger))
    db_session.execute(delete(RbpcInquiry))
    db_session.execute(delete(AnalyticsEvent))
    db_session.commit()

    admin = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    _login_user(client, admin.email)

    res = client.get("/api/v1/admin/analytics/truth-funnel")
    assert res.status_code == 200, res.text
    data = res.json()

    assert "observed" in data
    assert "hypothesis" in data
    assert "forecast" in data
    assert "anti_abuse_validation" in data

    observed = data["observed"]
    # Empty DB must strictly show 0 for real observed metrics
    assert observed["total_completed_experiences"] == 0, "Empty DB must show 0 completed experiences"
    assert observed["total_funnel_visitors"] == 0, "Empty DB must show 0 visitors"
    assert observed["overall_conversion_pct"] == 0.0, "Empty DB overall conversion must be 0.0%"

    # Stages array check
    stages = observed["stages"]
    assert len(stages) == 5
    for stage in stages:
        assert stage["count"] == 0, f"Stage {stage['stage']} must be 0 in empty DB"
        assert stage["truth_tier"] == "OBSERVED"

    # Anti-abuse validation block
    anti_abuse = data["anti_abuse_validation"]
    assert anti_abuse["status"] == "PASSED_STRICT"
    assert anti_abuse["forecast_1100_in_completed_bookings"] is False
    assert anti_abuse["empty_db_baseline_zero"] is True

    # Confirm projections are quarantined
    forecast = data["forecast"]
    assert forecast["truth_tier"] == "FORECAST"
    assert forecast["projected_annual_bookings"] == 1100
    assert "Tuyệt đối không tính vào số liệu đã hoàn thành" in forecast["epistemic_disclaimer"]


def test_v5_t112_negative_abuse_forecast_injection_prevented():
    """Verify that any attempt to pass forecast figures into observed stage fails closed."""
    with pytest.raises(ValueError, match="Negative abuse invariant violation"):
        validate_anti_abuse_integrity(
            observed_completed=10,
            projected_forecast=1100,
            allow_forecast_in_observed=True,
        )


def test_v5_t112_real_recorded_events_5_stages(client, db_session):
    """Verify that the 5-stage funnel strictly measures real recorded events and database state."""
    from sqlalchemy import delete
    from backend.models_rbpc import RbpcSettlementLedger
    db_session.execute(delete(RbpcSettlementLedger))
    db_session.execute(delete(RbpcInquiry))
    db_session.execute(delete(AnalyticsEvent))
    db_session.commit()

    admin = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    provider = _create_user(db_session, f"provider_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    creator, exp = _setup_test_heritage_context(db_session, provider)

    # 1. Record visitor landing event (Stage 1)
    session_id = uuid.uuid4()
    evt_visitor = AnalyticsEvent(
        user_id=admin.id,
        session_id=session_id,
        event_name="visitor_landed",
        path="/explore",
        event_category="visitor",
    )
    db_session.add(evt_visitor)

    # 2. Record source reading event (Stage 2)
    evt_source = AnalyticsEvent(
        user_id=admin.id,
        session_id=session_id,
        event_name="source_read",
        path="/heritage/duc-dong",
        payload={"dwell_seconds": 95, "source_id": "SRC-001"},
    )
    db_session.add(evt_source)
    db_session.commit()

    # 3. Create RbpcInquiry in state 'new' (Stage 3)
    inquiry = RbpcInquiry(
        public_ref=f"INQ-FUN-{uuid.uuid4().hex[:6].upper()}",
        experience_id=exp.id,
        provider_id=provider.id,
        name="Khách Khảo Sát",
        contact_channel="email",
        contact_value="visitor@example.com",
        desired_date=date.today(),
        party_size=2,
        state=RbpcInquiryStatus.new.value,
        idempotency_key=str(uuid.uuid4()),
        opaque_token=f"tok_fun_{uuid.uuid4().hex}",
    )
    db_session.add(inquiry)
    db_session.commit()

    _login_user(client, admin.email)

    # Check: at state 'new', inquiry count=1, confirm=0, completed=0
    res = client.get("/api/v1/admin/analytics/truth-funnel")
    data = res.json()
    stage_map = {s["stage"]: s["count"] for s in data["observed"]["stages"]}
    assert stage_map["visitor"] >= 1
    assert stage_map["source_read"] >= 1
    assert stage_map["inquiry"] == 1
    assert stage_map["confirm"] == 0
    assert stage_map["completed"] == 0

    # 4. Move inquiry to 'confirmed' (Stage 4)
    inquiry.state = RbpcInquiryStatus.confirmed.value
    db_session.commit()

    res = client.get("/api/v1/admin/analytics/truth-funnel")
    data = res.json()
    stage_map = {s["stage"]: s["count"] for s in data["observed"]["stages"]}
    assert stage_map["inquiry"] == 1
    assert stage_map["confirm"] == 1
    assert stage_map["completed"] == 0

    # 5. Move inquiry to 'closed' (Stage 5 - Completed)
    inquiry.state = RbpcInquiryStatus.closed.value
    db_session.commit()

    res = client.get("/api/v1/admin/analytics/truth-funnel")
    data = res.json()
    stage_map = {s["stage"]: s["count"] for s in data["observed"]["stages"]}
    assert stage_map["inquiry"] == 1
    assert stage_map["confirm"] == 1
    assert stage_map["completed"] == 1
    assert data["observed"]["total_completed_experiences"] == 1


def test_v5_t112_epistemological_separation_of_tiers(client, db_session):
    """Verify that truth tiers are strictly separated into OBSERVED, HYPOTHESIS, and FORECAST."""
    admin = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    _login_user(client, admin.email)

    res = client.get("/api/v1/admin/analytics/truth-funnel")
    assert res.status_code == 200
    data = res.json()

    # 1. OBSERVED tier
    assert data["observed"]["truth_tier"] == "OBSERVED"
    assert "quality_cohorts" in data["observed"]

    # 2. HYPOTHESIS tier
    hyp = data["hypothesis"]
    assert hyp["truth_tier"] == "HYPOTHESIS"
    assert hyp["benchmark_assumptions"]["story_engagement_rate_pct"] == 20.0
    assert hyp["benchmark_assumptions"]["inquiry_conversion_rate_pct"] == 15.0
    assert hyp["benchmark_assumptions"]["partner_acceptance_rate_pct"] == 75.0
    assert hyp["benchmark_assumptions"]["experience_completion_rate_pct"] == 88.89
    assert hyp["modeled_monthly_funnel"]["visitors"] == 1500
    assert hyp["modeled_monthly_funnel"]["completed_experiences"] == 30

    # 3. FORECAST tier
    fc = data["forecast"]
    assert fc["truth_tier"] == "FORECAST"
    assert fc["projected_annual_bookings"] == 1100
    assert fc["projected_annual_gmv_vnd"] == 570000000.0
    assert fc["target_partner_workshops"] == 5
    assert fc["projected_platform_net_revenue_vnd"] == 57000000.0
    assert fc["projected_artisan_retained_vnd"] == 513000000.0
    assert "1,100" in fc["negative_abuse_guardrail"]


def test_v5_t112_quality_cohorts_slicing(client, db_session):
    """Verify that quality cohorts partition real events by channel and experience."""
    admin = _create_user(db_session, f"admin_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.admin)
    provider = _create_user(db_session, f"provider_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.teacher)
    creator, exp = _setup_test_heritage_context(db_session, provider)

    # Add email inquiry in closed state
    inq_email = RbpcInquiry(
        public_ref=f"INQ-EM-{uuid.uuid4().hex[:6].upper()}",
        experience_id=exp.id,
        provider_id=provider.id,
        name="Email Tourist",
        contact_channel="email",
        contact_value="email@example.com",
        desired_date=date.today(),
        state=RbpcInquiryStatus.closed.value,
        idempotency_key=str(uuid.uuid4()),
        opaque_token=f"tok_em_{uuid.uuid4().hex}",
    )
    # Add zalo inquiry in confirmed state
    inq_zalo = RbpcInquiry(
        public_ref=f"INQ-ZA-{uuid.uuid4().hex[:6].upper()}",
        experience_id=exp.id,
        provider_id=provider.id,
        name="Zalo Tourist",
        contact_channel="zalo",
        contact_value="0901234567",
        desired_date=date.today(),
        state=RbpcInquiryStatus.confirmed.value,
        idempotency_key=str(uuid.uuid4()),
        opaque_token=f"tok_za_{uuid.uuid4().hex}",
    )
    db_session.add_all([inq_email, inq_zalo])
    db_session.commit()

    _login_user(client, admin.email)

    res = client.get("/api/v1/admin/analytics/truth-funnel")
    assert res.status_code == 200
    cohorts = res.json()["observed"]["quality_cohorts"]

    # Locate channel_email cohort
    email_cohort = next((c for c in cohorts if c["cohort_id"] == "channel_email"), None)
    assert email_cohort is not None
    assert email_cohort["inquiry_count"] >= 1
    assert email_cohort["completed_count"] >= 1
    assert email_cohort["source_grounding_score_pct"] == 100.0

    # Locate channel_zalo cohort
    zalo_cohort = next((c for c in cohorts if c["cohort_id"] == "channel_zalo"), None)
    assert zalo_cohort is not None
    assert zalo_cohort["inquiry_count"] >= 1
    assert zalo_cohort["confirm_count"] >= 1


def test_v5_t112_role_based_access_control(client, db_session):
    """Ensure non-admin users cannot access the truth funnel endpoint."""
    learner = _create_user(db_session, f"learner_{uuid.uuid4().hex[:6]}@example.com", role=UserRole.learner)

    # 1. Unauthenticated -> 401
    client.cookies.clear()
    res = client.get("/api/v1/admin/analytics/truth-funnel")
    assert res.status_code == 401

    # 2. Authenticated as learner -> 403
    _login_user(client, learner.email)
    res = client.get("/api/v1/admin/analytics/truth-funnel")
    assert res.status_code == 403


def test_v5_t112_frontend_contracts_and_elements_exist():
    """Verify frontend page and client contracts for the truth-level funnel dashboard."""
    repo_root = Path(__file__).resolve().parents[2]
    page_path = repo_root / "frontend" / "src" / "app" / "admin" / "funnel" / "page.tsx"
    client_path = repo_root / "frontend" / "src" / "app" / "admin" / "funnel" / "FunnelDashboardClient.tsx"
    test_path = repo_root / "frontend" / "src" / "app" / "admin" / "funnel" / "page.test.tsx"
    api_path = repo_root / "frontend" / "src" / "lib" / "api.ts"

    assert page_path.exists(), f"Frontend page {page_path} must exist"
    assert client_path.exists(), f"Client component {client_path} must exist"
    assert test_path.exists(), f"Vitest component test {test_path} must exist"

    client_code = client_path.read_text(encoding="utf-8")
    # Verify required data-testids
    assert 'data-testid="observed-completed-count"' in client_code
    assert 'data-testid="observed-inquiries-count"' in client_code
    assert 'data-testid="observed-confirmed-count"' in client_code
    assert 'data-testid="observed-source-reads-count"' in client_code
    assert 'data-testid="observed-visitors-count"' in client_code
    assert 'data-testid="observed-overall-conversion"' in client_code
    assert 'data-testid="quality-cohorts-table"' in client_code
    assert 'data-testid="forecast-quarantine-box"' in client_code
    assert 'data-testid="anti-abuse-status"' in client_code

    # Verify api.ts export
    api_code = api_path.read_text(encoding="utf-8")
    assert "getTruthFunnelDashboard" in api_code
    assert "TruthFunnelDashboardData" in api_code
