# -*- coding: utf-8 -*-
"""V5-T011 (Wave W01, Slot A01): Remove fabricated inquiry success in frontend/src/lib/rbpc/inquiries.ts.

Audits and verifies:
1. Client-side contract verification (frontend/src/lib/rbpc/inquiries.ts):
   - submitInquiryToApi NEVER fabricates fake success references/tokens on 404 or network failure.
   - All fallback mock branches ("provide resilient simulated result") are completely removed.
   - Typed ApiError is thrown / propagated on failures so the UI can display appropriate error states.
   - Returns InquirySubmissionResult only when the server returns 202 Accepted.
2. Inquiries UI page verification (frontend/src/app/rbpc/inquiries/page.tsx):
   - Page form handler (handleSubmit) handles rejections cleanly via try-catch.
   - Displays error alert banner without setting submission result or assuming fake success.
   - Unused token generation utilities are not imported or called in page submission.
3. Unit/Integration contract verification via Vitest runner:
   - Vitest suite verifies that submitInquiryToApi rejects on 404.
   - Vitest suite verifies that submitInquiryToApi rejects on network failure.
   - Vitest suite verifies that submitInquiryToApi resolves with server-provided reference on 202.
4. Backend API & DB commit verification (/api/v1/rbpc/inquiries):
   - Valid inquiry commits to DB with HTTP 202 Accepted, generating genuine non-sequential
     public_ref (INQ-XXXX-XXXX) and high-entropy opaque_token (tok_sec_...).
   - Idempotency replay returns 202 with identical tokens and does not duplicate DB rows.
   - Invalid inquiries (nonexistent experience -> 404, missing consent -> 422, past date -> 422)
     fail with appropriate status codes and commit zero records to DB.
   - Public inquiry status lookup (/api/v1/rbpc/inquiries/status/{token}) returns 200 with zero PII.
"""
from __future__ import annotations

import json
import re
import subprocess
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import select

from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INQUIRIES_TS_PATH = REPO_ROOT / "frontend/src/lib/rbpc/inquiries.ts"
INQUIRIES_PAGE_PATH = REPO_ROOT / "frontend/src/app/rbpc/inquiries/page.tsx"


# ==============================================================================
# 1. Source Code Contract Tests
# ==============================================================================

def test_inquiries_ts_no_fabricated_success_contract():
    """Verify frontend/src/lib/rbpc/inquiries.ts does not fabricate success in submitInquiryToApi."""
    assert INQUIRIES_TS_PATH.exists(), f"Missing file: {INQUIRIES_TS_PATH}"
    content = INQUIRIES_TS_PATH.read_text(encoding="utf-8")

    # 1. Ensure the removed mock fallback comment and pattern are completely absent
    assert "provide resilient simulated result" not in content, (
        "Found forbidden fallback comment 'provide resilient simulated result' in inquiries.ts"
    )

    # 2. Extract submitInquiryToApi function body
    match = re.search(
        r"export\s+async\s+function\s+submitInquiryToApi\s*\([\s\S]*?\n\}",
        content,
    )
    assert match is not None, "submitInquiryToApi function not found in inquiries.ts"
    fn_body = match.group(0)

    # 3. submitInquiryToApi MUST NOT call generatePublicReference or generateOpaqueToken
    assert "generatePublicReference()" not in fn_body, (
        "submitInquiryToApi must not call generatePublicReference() to fabricate fake success"
    )
    assert "generateOpaqueToken()" not in fn_body, (
        "submitInquiryToApi must not call generateOpaqueToken() to fabricate fake success"
    )

    # 4. submitInquiryToApi MUST throw or re-throw an ApiError
    assert "throw" in fn_body, "submitInquiryToApi must throw errors on failure"
    assert "ApiError" in fn_body, "submitInquiryToApi must use typed ApiError for error propagation"

    # 5. submitInquiryToApi MUST NOT fabricate fallback reference or statusToken
    assert "fallbackRef" not in fn_body, "submitInquiryToApi must not contain fallbackRef"
    assert "fallbackToken" not in fn_body, "submitInquiryToApi must not contain fallbackToken"


def test_inquiries_page_handles_errors_without_assuming_success():
    """Verify frontend/src/app/rbpc/inquiries/page.tsx handles errors cleanly in handleSubmit."""
    assert INQUIRIES_PAGE_PATH.exists(), f"Missing file: {INQUIRIES_PAGE_PATH}"
    content = INQUIRIES_PAGE_PATH.read_text(encoding="utf-8")

    # 1. Ensure generatePublicReference & generateOpaqueToken are not imported in page.tsx
    assert "generatePublicReference" not in content, (
        "page.tsx should not import generatePublicReference"
    )
    assert "generateOpaqueToken" not in content, (
        "page.tsx should not import generateOpaqueToken"
    )

    # 2. Verify handleSubmit error handling
    assert "submitInquiryToApi" in content, "page.tsx must call submitInquiryToApi"
    assert "setFormErrors({ submit:" in content or "setFormErrors({" in content, (
        "page.tsx must set form error state when submit fails"
    )

    # 3. Verify error alert banner exists for user feedback
    assert "formErrors.submit" in content, (
        "page.tsx must display formErrors.submit alert banner to visitor"
    )


def test_vitest_frontend_contract():
    """Run Vitest suite to verify submitInquiryToApi rejection and non-fabrication contracts."""
    result = subprocess.run(
        ["npx", "vitest", "run", "src/components/rbpc/inquiriesPages.test.ts"],
        cwd=str(REPO_ROOT / "frontend"),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"Vitest test suite failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert "passed" in result.stdout, (
        f"Expected Vitest passing output, got: {result.stdout}"
    )


# ==============================================================================
# 2. Backend Endpoint & Database Commit Integration Tests
# ==============================================================================

@pytest.fixture
def seeded_experience(db_session):
    """Seed a verified, published experience with a consented creator for testing."""
    creator_slug = f"artisan-v5t011-{uuid.uuid4().hex[:6]}"
    creator = RbpcCreator(
        slug=creator_slug,
        public_name="Nghệ nhân Thử nghiệm V5-T011",
        craft_tradition="Đúc đồng thủ công Huế",
        approved_bio_vi="Tiểu sử nghệ nhân phục vụ kiểm thử tích hợp.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp_slug = f"workshop-v5t011-{uuid.uuid4().hex[:6]}"
    exp = RbpcExperience(
        slug=exp_slug,
        creator_id=creator.id,
        provider_id=creator.id,
        provider_name="Xưởng Đúc Đồng Gia Tộc Nguyễn Văn",
        title_vi="Trải nghiệm Đúc đồng V5-T011",
        title_en="Bronze Smelting Masterclass V5-T011",
        description_vi="Khóa trải nghiệm nghệ thuật đúc đồng truyền thống.",
        area_public="Phường Đúc, Huế",
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return exp


def test_backend_inquiry_valid_commits_to_db_with_202(client, db_session, seeded_experience):
    """Verify that valid inquiries commit to DB with 202 Accepted and return authentic references."""
    idempotency_key = str(uuid.uuid4())
    future_date = (date.today() + timedelta(days=14)).isoformat()

    payload = {
        "experience_slug": seeded_experience.slug,
        "contact": {
            "name": "Nguyễn Hoàng Nam",
            "method": "email",
            "value": "nam.nguyen@example.com",
        },
        "preferred_date": future_date,
        "party_size": 3,
        "message": "Quan tâm kỹ thuật đúc đồng truyền thống triều Nguyễn.",
        "consent": {
            "version": "rbpc-inquiry-v1",
            "accepted": True,
            "privacy_accepted": True,
        },
        "idempotency_key": idempotency_key,
    }

    # 1. API Call: Expect 202 Accepted
    response = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert response.status_code == 202, f"Expected 202 Accepted, got {response.status_code}: {response.text}"

    data = response.json()
    assert "reference" in data
    assert "status_token" in data
    assert data["status"] == "new"

    # Reference must follow non-sequential format INQ-XXXX-XXXX
    ref = data["reference"]
    assert re.match(r"^INQ-[A-Z0-9]{4}-[A-Z0-9]{4}$", ref), f"Invalid reference format: {ref}"

    # Status token must be high-entropy bearer token tok_sec_<32hex>
    token = data["status_token"]
    assert re.match(r"^tok_sec_[0-9a-f]{32}$", token), f"Invalid status token format: {token}"

    # 2. Database Verification: Record must actually exist in PostgreSQL
    inquiry_record = db_session.scalar(
        select(RbpcInquiry).where(RbpcInquiry.idempotency_key == idempotency_key)
    )
    assert inquiry_record is not None, "Inquiry was NOT committed to PostgreSQL database!"
    assert inquiry_record.public_ref == ref
    assert inquiry_record.opaque_token == token
    assert inquiry_record.state == RbpcInquiryStatus.new.value
    assert inquiry_record.name == "Nguyễn Hoàng Nam"
    assert inquiry_record.contact_channel == "email"
    assert inquiry_record.contact_value == "nam.nguyen@example.com"
    assert inquiry_record.party_size == 3
    assert inquiry_record.experience_id == seeded_experience.id

    # 3. Public Status Verification: Lookup via opaque_token returns 200 with zero PII
    status_res = client.get(f"/api/v1/rbpc/inquiries/status/{token}")
    assert status_res.status_code == 200
    st_data = status_res.json()
    assert st_data["reference"] == ref
    assert st_data["status"] == "new"
    assert st_data["experience_title"] == seeded_experience.title_vi
    assert "name" not in st_data
    assert "contact_value" not in st_data
    assert "email" not in st_data


def test_backend_inquiry_idempotency_replay_returns_same_tokens(client, db_session, seeded_experience):
    """Verify that replaying identical idempotency_key returns identical 202 response without duping DB."""
    idempotency_key = str(uuid.uuid4())
    future_date = (date.today() + timedelta(days=20)).isoformat()

    payload = {
        "experience_slug": seeded_experience.slug,
        "contact": {
            "name": "Trần Thị Lan",
            "method": "phone",
            "value": "0912345678",
        },
        "preferred_date": future_date,
        "party_size": 2,
        "message": "Thử nghiệm replay idempotency.",
        "consent": {
            "version": "rbpc-inquiry-v1",
            "accepted": True,
            "privacy_accepted": True,
        },
        "idempotency_key": idempotency_key,
    }

    # First submission
    res1 = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res1.status_code == 202
    data1 = res1.json()

    # Replay identical submission
    res2 = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res2.status_code == 202
    data2 = res2.json()

    assert data1["reference"] == data2["reference"]
    assert data1["status_token"] == data2["status_token"]

    # Verify exactly 1 record in database
    records = list(
        db_session.scalars(
            select(RbpcInquiry).where(RbpcInquiry.idempotency_key == idempotency_key)
        )
    )
    assert len(records) == 1, f"Expected 1 record in DB, found {len(records)}"


def test_backend_inquiry_rejects_nonexistent_experience_404(client, db_session):
    """Negative test: Nonexistent experience returns 404, does NOT commit to DB."""
    idempotency_key = str(uuid.uuid4())
    payload = {
        "experience_slug": "nonexistent-experience-slug-xyz-999",
        "contact": {
            "name": "Test User",
            "method": "email",
            "value": "user@example.com",
        },
        "party_size": 2,
        "consent": {
            "version": "rbpc-inquiry-v1",
            "accepted": True,
            "privacy_accepted": True,
        },
        "idempotency_key": idempotency_key,
    }

    res = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res.status_code == 404, f"Expected 404 Not Found, got {res.status_code}"
    err = res.json()
    assert err["error"]["code"] == "RBPC_EXPERIENCE_NOT_FOUND"

    # Verify zero database records inserted
    count = db_session.scalar(
        select(RbpcInquiry).where(RbpcInquiry.idempotency_key == idempotency_key)
    )
    assert count is None, "Inquiry with nonexistent experience MUST NOT be committed to DB"


def test_backend_inquiry_rejects_missing_consent_422(client, db_session, seeded_experience):
    """Negative test: Missing consent returns 422, does NOT commit to DB."""
    idempotency_key = str(uuid.uuid4())
    payload = {
        "experience_slug": seeded_experience.slug,
        "contact": {
            "name": "Test User",
            "method": "email",
            "value": "user@example.com",
        },
        "party_size": 2,
        "consent": {
            "version": "rbpc-inquiry-v1",
            "accepted": False,  # Not accepted
            "privacy_accepted": True,
        },
        "idempotency_key": idempotency_key,
    }

    res = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res.status_code in (422, 400), f"Expected 422/400, got {res.status_code}"
    err = res.json()
    assert err["error"]["code"] in ("VALIDATION_ERROR", "RBPC_CONSENT_REQUIRED")

    # Verify zero database records inserted
    count = db_session.scalar(
        select(RbpcInquiry).where(RbpcInquiry.idempotency_key == idempotency_key)
    )
    assert count is None, "Inquiry without consent MUST NOT be committed to DB"


def test_backend_inquiry_rejects_past_date_422(client, db_session, seeded_experience):
    """Negative test: Preferred date in the past returns 422, does NOT commit to DB."""
    idempotency_key = str(uuid.uuid4())
    past_date = (date.today() - timedelta(days=5)).isoformat()
    payload = {
        "experience_slug": seeded_experience.slug,
        "contact": {
            "name": "Test User",
            "method": "email",
            "value": "user@example.com",
        },
        "preferred_date": past_date,
        "party_size": 2,
        "consent": {
            "version": "rbpc-inquiry-v1",
            "accepted": True,
            "privacy_accepted": True,
        },
        "idempotency_key": idempotency_key,
    }

    res = client.post("/api/v1/rbpc/inquiries", json=payload)
    assert res.status_code in (422, 400), f"Expected 422/400, got {res.status_code}"
    err = res.json()
    assert err["error"]["code"] in ("VALIDATION_ERROR", "RBPC_DATE_PAST")

    # Verify zero database records inserted
    count = db_session.scalar(
        select(RbpcInquiry).where(RbpcInquiry.idempotency_key == idempotency_key)
    )
    assert count is None, "Inquiry with past date MUST NOT be committed to DB"
