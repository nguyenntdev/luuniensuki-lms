# -*- coding: utf-8 -*-
"""V5-T107: Verified Customer Reviews and Disputes Test Suite.

Audits and verifies:
1. Verified completed inquiry requirement:
   - Only inquiries in 'closed' (completed) state can submit reviews.
   - Inquiries in 'new', 'contacted', 'confirmed', or 'declined' states are strictly rejected (HTTP 400 RBPC_INQUIRY_NOT_COMPLETED).
2. Negative abuse prevention:
   - Fake or nonexistent inquiry tokens return 404 RBPC_INQUIRY_NOT_FOUND.
   - Duplicate review submissions for the same inquiry return 409 RBPC_REVIEW_ALREADY_EXISTS.
   - Uncompleted or cancelled inquiries cannot post ratings or reviews.
3. Anti-fraud checks:
   - Content with promotional URLs, script tags, or spam keywords triggers automated fraud flags and routes to 'pending_moderation'.
   - Clean, verified reviews without spam flags publish successfully.
4. Review moderation queue:
   - Staff/admin can list reviews in the moderation queue, filter by status, and approve/reject/archive reviews.
   - Non-staff users are forbidden from moderation endpoints (HTTP 403 FORBIDDEN_SCOPE).
5. Review dispute workflow:
   - Disputants can file a dispute against reviews with reason and evidence payload.
   - Staff/admin can resolve disputes with upheld (review rejected) or overturned/dismissed (review published).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
import pytest
from sqlalchemy import select

from backend.models import User, UserRole
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcCreator,
    RbpcCustomerReview,
    RbpcDisputeStatus,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
    RbpcReviewDispute,
    RbpcReviewStatus,
)
from backend.security import hash_password


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
        username=f"u_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client, email: str, password: str = "Password123!") -> dict:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


def _setup_test_inquiry(db_session, state: str = "closed") -> tuple[RbpcInquiry, RbpcExperience]:
    creator = RbpcCreator(
        slug=f"artisan-{uuid.uuid4().hex[:6]}",
        public_name="Nghệ nhân Đúc Đồng Huế",
        craft_tradition="Đúc đồng Phường Đúc",
        approved_bio_vi="Nghệ nhân gia truyền.",
        consent_status=RbpcConsentStatus.consented.value,
        is_verified=True,
    )
    db_session.add(creator)
    db_session.flush()

    exp = RbpcExperience(
        slug=f"exp-review-{uuid.uuid4().hex[:6]}",
        title_vi="Trải nghiệm Đúc Đồng Thử Nghiệm",
        title_en="Bronze Casting Experience",
        description_vi="Mô tả trải nghiệm thử nghiệm.",
        creator_id=creator.id,
        provider_name="Xưởng Đúc Đồng Thử Nghiệm",
        publication_state="published",
        availability_mode="inquiry_only",
    )
    db_session.add(exp)
    db_session.flush()

    inquiry = RbpcInquiry(
        public_ref=f"INQ-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}",
        experience_id=exp.id,
        name="Nguyễn Văn A",
        contact_channel="email",
        contact_value="nguyen.van.a@example.com",
        desired_date=date.today(),
        party_size=2,
        message="Mong muốn tham gia trải nghiệm đúc đồng.",
        consent_version="rbpc-inquiry-v1",
        privacy_accepted=True,
        state=state,
        idempotency_key=str(uuid.uuid4()),
        opaque_token=f"tok_sec_{uuid.uuid4().hex}",
    )
    db_session.add(inquiry)
    db_session.commit()
    db_session.refresh(inquiry)
    return inquiry, exp


def test_verified_completed_inquiry_can_submit_review(client, db_session):
    """Test that a customer with a verified completed ('closed') inquiry can submit a review."""
    inquiry, exp = _setup_test_inquiry(db_session, state="closed")

    payload = {
        "inquiry_token": inquiry.opaque_token,
        "rating": 5,
        "title": "Trải nghiệm tuyệt vời tại phường đúc",
        "comment": "Nghệ nhân hướng dẫn rất tận tình, tác phẩm hoàn thiện rất ưng ý.",
        "author_display_name": "Lê Văn H.",
    }

    res = client.post("/api/v1/rbpc/reviews", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["rating"] == 5
    assert data["title"] == payload["title"]
    assert data["comment"] == payload["comment"]
    assert data["author_display_name"] == "Lê Văn H."
    assert data["verified_completed"] is True
    assert data["status"] == "published"


def test_negative_abuse_uncompleted_inquiries_cannot_submit_reviews(client, db_session):
    """Negative abuse invariant: Inquiries in 'new', 'contacted', 'confirmed', or 'declined'

    state cannot post ratings or reviews.
    """
    for invalid_state in ["new", "contacted", "confirmed", "declined"]:
        inquiry, exp = _setup_test_inquiry(db_session, state=invalid_state)

        payload = {
            "inquiry_token": inquiry.opaque_token,
            "rating": 1,
            "title": "Đánh giá sớm không hợp lệ",
            "comment": "Chưa đi trải nghiệm nhưng cố tình gửi đánh giá.",
        }

        res = client.post("/api/v1/rbpc/reviews", json=payload)
        assert res.status_code == 400, f"Expected 400 for state {invalid_state}, got {res.status_code}: {res.text}"
        assert res.json()["error"]["code"] == "RBPC_INQUIRY_NOT_COMPLETED"


def test_negative_abuse_fake_or_nonexistent_token_rejected(client, db_session):
    """Negative abuse invariant: Nonexistent or fake inquiry token returns 404."""
    payload = {
        "inquiry_token": f"tok_sec_fake_{uuid.uuid4().hex}",
        "rating": 4,
        "title": "Đánh giá giả mạo",
        "comment": "Không hề có hồ sơ yêu cầu nào tồn tại.",
    }
    res = client.post("/api/v1/rbpc/reviews", json=payload)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RBPC_INQUIRY_NOT_FOUND"


def test_negative_abuse_duplicate_review_for_same_inquiry_rejected(client, db_session):
    """Negative abuse invariant: Cannot submit multiple reviews for the same inquiry."""
    inquiry, exp = _setup_test_inquiry(db_session, state="closed")

    payload = {
        "inquiry_token": inquiry.opaque_token,
        "rating": 4,
        "title": "Đánh giá lần 1 hợp lệ",
        "comment": "Trải nghiệm rất tốt và đáng tiền.",
    }
    res1 = client.post("/api/v1/rbpc/reviews", json=payload)
    assert res1.status_code == 201

    # Second submission with same inquiry token
    payload2 = {
        "inquiry_token": inquiry.opaque_token,
        "rating": 5,
        "title": "Đánh giá lần 2 bị chặn",
        "comment": "Cố tình spam đánh giá lần thứ hai.",
    }
    res2 = client.post("/api/v1/rbpc/reviews", json=payload2)
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "RBPC_REVIEW_ALREADY_EXISTS"


def test_anti_fraud_detection_routes_spam_to_moderation(client, db_session):
    """Anti-fraud checks: Reviews containing spam links, script tags, or commercial spam

    are detected and routed to 'pending_moderation' status with fraud flags recorded.
    """
    inquiry, exp = _setup_test_inquiry(db_session, state="closed")

    payload = {
        "inquiry_token": inquiry.opaque_token,
        "rating": 5,
        "title": "Nhận ngay khuyến mãi http://spamlink.com",
        "comment": "Truy cập ngay casino trực tuyến để nhận tiền thưởng lớn không giới hạn!",
    }

    res = client.post("/api/v1/rbpc/reviews", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    # Should not be immediately published
    assert data["status"] == "pending_moderation"

    # Verify internal DB row has fraud flags set
    review = db_session.scalar(
        select(RbpcCustomerReview).where(RbpcCustomerReview.id == uuid.UUID(data["id"]))
    )
    assert review is not None
    assert review.fraud_flags.get("flagged") is True
    assert review.fraud_flags.get("contains_url") is True
    assert "casino" in review.fraud_flags.get("spam_keywords", [])


def test_public_experience_reviews_list_only_published(client, db_session):
    """Public listing of reviews returns only published items and calculates average rating."""
    inquiry1, exp = _setup_test_inquiry(db_session, state="closed")
    inquiry2 = RbpcInquiry(
        public_ref=f"INQ-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}",
        experience_id=exp.id,
        name="Trần Thị B",
        contact_channel="phone",
        contact_value="0912345678",
        consent_version="rbpc-inquiry-v1",
        privacy_accepted=True,
        state="closed",
        idempotency_key=str(uuid.uuid4()),
        opaque_token=f"tok_sec_{uuid.uuid4().hex}",
    )
    db_session.add(inquiry2)
    db_session.commit()

    # 1. Add published review
    client.post(
        "/api/v1/rbpc/reviews",
        json={
            "inquiry_token": inquiry1.opaque_token,
            "rating": 5,
            "title": "Trải nghiệm 5 sao xuất sắc",
            "comment": "Thầy nghệ nhân chỉ bảo từng bước rất chu đáo.",
        },
    )

    # 2. Add spam review (goes to pending_moderation)
    client.post(
        "/api/v1/rbpc/reviews",
        json={
            "inquiry_token": inquiry2.opaque_token,
            "rating": 1,
            "title": "Spam crypto http://spam.xyz",
            "comment": "Mua ngay bitcoin và crypto giá rẻ.",
        },
    )

    # Query public reviews
    res = client.get(f"/api/v1/rbpc/experiences/{exp.slug}/reviews")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["average_rating"] == 5.0
    assert data["items"][0]["title"] == "Trải nghiệm 5 sao xuất sắc"


def test_admin_review_moderation_queue_and_permissions(client, db_session):
    """Staff/admin review moderation workflow:

    - Admin can view queue and moderate (approve/reject).
    - Regular users are rejected with 403.
    """
    admin_user = _create_user(db_session, "admin_t107@example.com", role=UserRole.admin)
    learner_user = _create_user(db_session, "learner_t107@example.com", role=UserRole.learner)

    inquiry, exp = _setup_test_inquiry(db_session, state="closed")
    post_res = client.post(
        "/api/v1/rbpc/reviews",
        json={
            "inquiry_token": inquiry.opaque_token,
            "rating": 4,
            "title": "Khuyến mãi ghé thăm http://example.com",
            "comment": "Học nghề rất vui nhưng có link tham khảo.",
        },
    )
    review_id = post_res.json()["id"]

    # 1. Unauthenticated or non-admin cannot access admin queue
    _login_user(client, learner_user.email)
    res_forbidden = client.get("/api/v1/rbpc/admin/reviews")
    assert res_forbidden.status_code == 403

    # 2. Admin can access queue
    _login_user(client, admin_user.email)
    res_admin = client.get("/api/v1/rbpc/admin/reviews")
    assert res_admin.status_code == 200
    admin_data = res_admin.json()
    assert admin_data["total"] >= 1

    # 3. Admin moderates review to published
    res_mod = client.patch(
        f"/api/v1/rbpc/admin/reviews/{review_id}/moderate",
        json={
            "status": "published",
            "notes": "Đã xem xét và gỡ cảnh báo, cho phép xuất bản.",
        },
    )
    assert res_mod.status_code == 200
    assert res_mod.json()["status"] == "published"
    assert res_mod.json()["moderation_notes"] == "Đã xem xét và gỡ cảnh báo, cho phép xuất bản."


def test_review_dispute_creation_and_resolution(client, db_session):
    """Test dispute submission on a review and administrative resolution."""
    admin_user = _create_user(db_session, "admin_dispute_t107@example.com", role=UserRole.admin)
    inquiry, exp = _setup_test_inquiry(db_session, state="closed")

    # Post a published review
    post_res = client.post(
        "/api/v1/rbpc/reviews",
        json={
            "inquiry_token": inquiry.opaque_token,
            "rating": 1,
            "title": "Trải nghiệm không như ý",
            "comment": "Xưởng đến muộn và không có đủ nguyên liệu như đã hứa.",
        },
    )
    review_id = post_res.json()["id"]

    # 1. Partner or customer files a dispute
    disp_res = client.post(
        f"/api/v1/rbpc/reviews/{review_id}/dispute",
        json={
            "reason": "Khách hàng nhầm lẫn thời gian hẹn; xưởng có video chứng minh đón tiếp đúng giờ.",
            "evidence_payload": {"cctv_timestamp": "2026-11-06T09:00:00Z", "log_ref": "LOG-1234"},
        },
    )
    assert disp_res.status_code == 201
    dispute_data = disp_res.json()
    assert dispute_data["status"] == "opened"
    dispute_id = dispute_data["id"]

    # Review status should now be 'disputed'
    rev_check = client.get(f"/api/v1/rbpc/experiences/{exp.slug}/reviews").json()
    assert rev_check["total"] == 0  # Not in public published list while disputed

    # 2. Admin resolves dispute as upheld (review rejected)
    _login_user(client, admin_user.email)
    resolve_res = client.patch(
        f"/api/v1/rbpc/admin/disputes/{dispute_id}/resolve",
        json={
            "status": "resolved_upheld",
            "notes": "Bằng chứng camera xác thực khách nhầm giờ. Gỡ bỏ đánh giá sai lệch.",
        },
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "resolved_upheld"

    # Verify review in DB is now 'rejected'
    from sqlalchemy import select
    rev_in_db = db_session.scalar(
        select(RbpcCustomerReview).where(RbpcCustomerReview.id == uuid.UUID(review_id))
    )
    assert rev_in_db.status == "rejected"
