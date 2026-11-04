# -*- coding: utf-8 -*-
"""V5-T022: Stop Auto-Verified Seed Claims in Heritage Knowledge Catalogue.

Verifies:
1. Newly imported seed claims default to unreviewed / internal_review, NOT auto-verified.
2. Negative abuse test: A fabricated citation (e.g. placeholder, unknown, none, fabricated text)
   remains unreviewed/needs_source/draft, never auto-promoted to verified/published.
3. Explicit verification guardrail: Claims can only be ingested as verified if an authentic
   human expert reviewer is referenced and verified bibliographic citation is present.
4. Idempotent re-import preservation: Re-running import preserves existing human approvals
   and verifications (verified/expert_verified status is never downgraded or overwritten).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import pytest
from sqlalchemy import select

from backend.models import User, UserRole
from backend.models_rbpc import (
    HeritagePlace,
    RbpcClaimEvidence,
    RbpcStory,
    RbpcStoryStatus,
)
from backend.security import hash_password
from backend.services.heritage_import import (
    HeritageImportService,
    import_heritage_data,
    is_valid_bibliographic_citation,
)


def _setup_story_fixtures(db_session) -> tuple[HeritagePlace, User]:
    """Helper to setup a parent place and a human reviewer user."""
    place = HeritagePlace(
        slug=f"place-t022-{uuid.uuid4().hex[:6]}",
        name_vi="Di tích Thử Nghiệm",
        entity_type="monument",
        heritage_category="imperial_architecture",
        content_scope="RBPC_HUE",
        editorial_status="published",
    )
    db_session.add(place)

    expert_user = User(
        email=f"expert-{uuid.uuid4().hex[:6]}@histolab.icu",
        password_hash=hash_password("ExpertPass123!"),
        display_name="TS. Nguyễn Sử Gia",
        username=f"expert_{uuid.uuid4().hex[:6]}",
        role=UserRole.admin,
        is_profile_public=True,
    )
    db_session.add(expert_user)
    db_session.commit()
    db_session.refresh(place)
    db_session.refresh(expert_user)
    return place, expert_user


def test_newly_imported_seed_claims_default_to_unreviewed_not_verified(db_session):
    """Novel unverified evidence or imported claims must default to unreviewed or internal_review."""
    place, _ = _setup_story_fixtures(db_session)

    stories_data = {
        "stories": [
            {
                "id": str(uuid.uuid4()),
                "slug": f"story-unreviewed-{uuid.uuid4().hex[:6]}",
                "title_vi": "Câu chuyện kiểm thử chứng tích",
                "intro_vi": "Mô tả câu chuyện di sản cho việc kiểm chứng tuyên bố lịch sử.",
                "place_slug": place.slug,
                "status": "published",
                "claims": [
                    {
                        "statement_vi": "Chiếc đỉnh đồng được đúc với hợp kim đặc biệt vào thế kỷ 19.",
                        "source_title": "Đại Nam Thực Lục Chính Biên",
                        "source_locator": "Tập 2, tr. 150-155",
                        "support_type": "direct",
                        # Notice: no human reviewer provided, even if someone wrote review_status: verified
                        "review_status": "verified",
                    },
                    {
                        "statement_vi": "Nghề gốm cổ truyền được lưu truyền qua 5 thế hệ.",
                        "source_title": "Nghiên cứu văn hóa dân gian Huế",
                        "source_locator": "NXB Thuận Hóa 1998, tr. 40",
                        "support_type": "direct",
                    },
                ],
            }
        ]
    }

    import tempfile
    import yaml

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tf:
        yaml.safe_dump(stories_data, tf, allow_unicode=True)
        tmp_stories_path = tf.name

    try:
        from backend.services.heritage_import import DEFAULT_INVENTORY_PATH, DEFAULT_SKETCHFAB_PATH
        report, stats = import_heritage_data(
            db=db_session,
            inventory_path=DEFAULT_INVENTORY_PATH,
            sketchfab_path=DEFAULT_SKETCHFAB_PATH,
            stories_path=tmp_stories_path,
            creators_path=None,
            experiences_path=None,
            dry_run=False,
        )
        assert report.is_valid is True

        story_slug = stories_data["stories"][0]["slug"]
        db_story = db_session.scalar(select(RbpcStory).where(RbpcStory.slug == story_slug))
        assert db_story is not None
        assert len(db_story.claims) == 2

        for c in db_story.claims:
            # Crucial requirement: Must NOT be auto-verified!
            assert c.review_status != "verified"
            assert c.review_status in ("unreviewed", "internal_review", "draft_pending_review")
            assert c.reviewed_by is None
    finally:
        Path(tmp_stories_path).unlink(missing_ok=True)


def test_negative_abuse_fabricated_citation_remains_needs_source_or_unreviewed(db_session):
    """Negative abuse test: A fabricated citation remains needs_source / unreviewed, never auto-promoted."""
    place, expert_user = _setup_story_fixtures(db_session)

    # 1. Test citation validator helper
    assert is_valid_bibliographic_citation("none", "n/a") is False
    assert is_valid_bibliographic_citation("Unknown Source", "todo") is False
    assert is_valid_bibliographic_citation("Placeholder", "citation needed") is False
    assert is_valid_bibliographic_citation("Fabricated Title", "dummy") is False
    assert is_valid_bibliographic_citation("Đại Nam Thực Lục", "Quyển 8, tr. 12") is True

    # 2. Test import behavior when seed data attempts to push fabricated/placeholder sources as verified
    fabricated_story_data = {
        "stories": [
            {
                "id": str(uuid.uuid4()),
                "slug": f"story-fabricated-{uuid.uuid4().hex[:6]}",
                "title_vi": "Truyền thuyết hư cấu không nguồn",
                "intro_vi": "Tuyên bố lịch sử không có trích dẫn thực tế.",
                "place_slug": place.slug,
                "status": "published",
                "claims": [
                    {
                        "statement_vi": "Tuyên bố giả định với nguồn placeholder.",
                        "source_title": "placeholder",
                        "source_locator": "tbd",
                        "support_type": "direct",
                        "review_status": "verified",
                    },
                    {
                        "statement_vi": "Tuyên bố giả mạo cố tình kèm user ID nhưng nguồn fabricated.",
                        "source_title": "fabricated",
                        "source_locator": "none",
                        "support_type": "direct",
                        "review_status": "verified",
                        "reviewed_by": str(expert_user.id),
                    },
                    {
                        "statement_vi": "Tuyên bố với locator rỗng.",
                        "source_title": "Đại Nam Nhất Thống Chí",
                        "source_locator": "-",
                        "support_type": "direct",
                        "review_status": "verified",
                    },
                ],
            }
        ]
    }

    import tempfile
    import yaml

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tf:
        yaml.safe_dump(fabricated_story_data, tf, allow_unicode=True)
        tmp_stories_path = tf.name

    try:
        from backend.services.heritage_import import DEFAULT_INVENTORY_PATH, DEFAULT_SKETCHFAB_PATH
        report, stats = import_heritage_data(
            db=db_session,
            inventory_path=DEFAULT_INVENTORY_PATH,
            sketchfab_path=DEFAULT_SKETCHFAB_PATH,
            stories_path=tmp_stories_path,
            creators_path=None,
            experiences_path=None,
            dry_run=False,
        )
        assert report.is_valid is True

        story_slug = fabricated_story_data["stories"][0]["slug"]
        db_story = db_session.scalar(select(RbpcStory).where(RbpcStory.slug == story_slug))
        assert db_story is not None
        assert len(db_story.claims) == 3

        for c in db_story.claims:
            # Invariant: Never auto-promoted to verified/published
            assert c.review_status != "verified"
            assert c.review_status != "published_human_approved"
            assert c.review_status in ("needs_source", "unreviewed")
    finally:
        Path(tmp_stories_path).unlink(missing_ok=True)


def test_reimport_preserves_human_editorial_approvals(db_session):
    """Test that re-running import preserves human editorial decisions, statuses, and notes."""
    place, expert_user = _setup_story_fixtures(db_session)

    initial_story_data = {
        "stories": [
            {
                "id": str(uuid.uuid4()),
                "slug": f"story-preserve-{uuid.uuid4().hex[:6]}",
                "title_vi": "Bảo tồn quyết định thẩm định con người",
                "intro_vi": "Mô tả câu chuyện cần bảo lưu trạng thái phê duyệt.",
                "place_slug": place.slug,
                "status": "published",
                "claims": [
                    {
                        "statement_vi": "Tuyên bố số 1 đã được chuyên gia thẩm định và cấp phép.",
                        "source_title": "Khâm Định Đại Nam Hội Điển Sự Lệ",
                        "source_locator": "Quyển 159, Tập 10, tr. 312",
                        "support_type": "direct",
                        "statement_en": "Initial seed translation statement.",
                    },
                    {
                        "statement_vi": "Tuyên bố số 2 được biên tập viên kiểm tra thực địa.",
                        "source_title": "Đồng Khánh Địa Dư Chí",
                        "source_locator": "Tập 2, tr. 1282",
                        "support_type": "direct",
                    },
                    {
                        "statement_vi": "Tuyên bố số 3 vẫn đang trong quá trình đối chiếu nguồn.",
                        "source_title": "Đại Nam Nhất Thống Chí",
                        "source_locator": "Tập Kinh sư, tr. 45",
                        "support_type": "direct",
                    },
                ],
            }
        ]
    }

    import tempfile
    import yaml

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tf:
        yaml.safe_dump(initial_story_data, tf, allow_unicode=True)
        tmp_stories_path = tf.name

    try:
        from backend.services.heritage_import import DEFAULT_INVENTORY_PATH, DEFAULT_SKETCHFAB_PATH

        # Step 1: Initial import
        report1, stats1 = import_heritage_data(
            db=db_session,
            inventory_path=DEFAULT_INVENTORY_PATH,
            sketchfab_path=DEFAULT_SKETCHFAB_PATH,
            stories_path=tmp_stories_path,
            creators_path=None,
            experiences_path=None,
            dry_run=False,
        )
        assert report1.is_valid is True

        story_slug = initial_story_data["stories"][0]["slug"]
        db_story = db_session.scalar(select(RbpcStory).where(RbpcStory.slug == story_slug))
        assert db_story is not None
        assert len(db_story.claims) == 3

        # Step 2: Human editorial reviews occur
        # Claim 1: expert_verified with human reviewer notes
        claim1 = next(c for c in db_story.claims if "Tuyên bố số 1" in c.statement)
        # Claim 2: editor_reviewed with editorial notes
        claim2 = next(c for c in db_story.claims if "Tuyên bố số 2" in c.statement)
        # Claim 3: left unreviewed
        claim3 = next(c for c in db_story.claims if "Tuyên bố số 3" in c.statement)

        claim1.review_status = "expert_verified"
        claim1.reviewed_by = expert_user.id
        claim1.notes = "Thẩm định chuyên gia: Khớp chính xác với bản khắc mộc bản triều Nguyễn."

        claim2.review_status = "editor_reviewed"
        claim2.reviewed_by = expert_user.id
        claim2.notes = "Biên tập viên xác thực: Đã đối chiếu toạ độ thực địa."

        db_session.commit()

        # Step 3: Re-run import (simulating a batch re-sync of the catalogue with new seed data)
        # Seed file attempts to overwrite statement_en/notes on Claim 1 and Claim 2
        updated_seed_data = {
            "stories": [
                {
                    "id": initial_story_data["stories"][0]["id"],
                    "slug": story_slug,
                    "title_vi": "Bảo tồn quyết định thẩm định con người",
                    "intro_vi": "Mô tả câu chuyện cần bảo lưu trạng thái phê duyệt.",
                    "place_slug": place.slug,
                    "status": "published",
                    "claims": [
                        {
                            "statement_vi": "Tuyên bố số 1 đã được chuyên gia thẩm định và cấp phép.",
                            "source_title": "Khâm Định Đại Nam Hội Điển Sự Lệ (Tái bản 2020)",
                            "source_locator": "Quyển 159, Tập 10, tr. 312-320",
                            "support_type": "direct",
                            "review_status": "unreviewed",  # Seed attempts to downgrade
                            "statement_en": "Malicious seed attempt to wipe human notes.",
                        },
                        {
                            "statement_vi": "Tuyên bố số 2 được biên tập viên kiểm tra thực địa.",
                            "source_title": "Đồng Khánh Địa Dư Chí (Tập 2)",
                            "source_locator": "Tập 2, tr. 1282",
                            "support_type": "direct",
                            "review_status": "draft",  # Seed attempts to downgrade
                            "notes": "Another seed overwrite attempt.",
                        },
                        {
                            "statement_vi": "Tuyên bố số 3 vẫn đang trong quá trình đối chiếu nguồn.",
                            "source_title": "Đại Nam Nhất Thống Chí",
                            "source_locator": "Tập Kinh sư, tr. 45",
                            "support_type": "direct",
                        },
                    ],
                }
            ]
        }

        with open(tmp_stories_path, "w", encoding="utf-8") as tf:
            yaml.safe_dump(updated_seed_data, tf, allow_unicode=True)

        report2, stats2 = import_heritage_data(
            db=db_session,
            inventory_path=DEFAULT_INVENTORY_PATH,
            sketchfab_path=DEFAULT_SKETCHFAB_PATH,
            stories_path=tmp_stories_path,
            creators_path=None,
            experiences_path=None,
            dry_run=False,
        )
        assert report2.is_valid is True
        assert stats2.claims_inserted == 0
        assert stats2.claims_preserved_review >= 2

        # Step 4: Verify that human approval and notes were NOT downgraded or overwritten
        db_session.refresh(claim1)
        db_session.refresh(claim2)
        db_session.refresh(claim3)

        # Claim 1: preserved expert_verified status and reviewer notes
        assert claim1.review_status == "expert_verified"
        assert claim1.reviewed_by == expert_user.id
        assert claim1.notes == "Thẩm định chuyên gia: Khớp chính xác với bản khắc mộc bản triều Nguyễn."

        # Claim 2: preserved editor_reviewed status and reviewer notes
        assert claim2.review_status == "editor_reviewed"
        assert claim2.reviewed_by == expert_user.id
        assert claim2.notes == "Biên tập viên xác thực: Đã đối chiếu toạ độ thực địa."

        # Claim 3: remained unreviewed
        assert claim3.review_status == "unreviewed"
        assert claim3.reviewed_by is None
    finally:
        Path(tmp_stories_path).unlink(missing_ok=True)


def test_explicit_verified_provenance_allows_verified_import(db_session):
    """Explicit verified provenance record with authenticated human reviewer allows verified claim ingestion."""
    place, expert_user = _setup_story_fixtures(db_session)

    verified_provenance_story = {
        "stories": [
            {
                "id": str(uuid.uuid4()),
                "slug": f"story-provenance-{uuid.uuid4().hex[:6]}",
                "title_vi": "Chứng tích có hồ sơ thẩm định chuẩn tắc",
                "intro_vi": "Hồ sơ nguồn lịch sử đã qua hội đồng thẩm định chuyên môn.",
                "place_slug": place.slug,
                "status": "published",
                "claims": [
                    {
                        "statement_vi": "Bản dập văn bia Linh Mụ tự bi được đối chiếu với nguyên bản năm 1715.",
                        "source_title": "Văn bia thời chúa Nguyễn (Viện Nghiên cứu Hán Nôm)",
                        "source_locator": "Mã số thác bản 1420/HN, tr. 88",
                        "support_type": "direct",
                        "review_status": "expert_verified",
                        "reviewed_by": str(expert_user.id),
                        "provenance_verified": True,
                        "notes": "Hội đồng sử học phê duyệt theo biên bản số 42/HĐ-2025.",
                    }
                ],
            }
        ]
    }

    import tempfile
    import yaml

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tf:
        yaml.safe_dump(verified_provenance_story, tf, allow_unicode=True)
        tmp_stories_path = tf.name

    try:
        from backend.services.heritage_import import DEFAULT_INVENTORY_PATH, DEFAULT_SKETCHFAB_PATH

        report, stats = import_heritage_data(
            db=db_session,
            inventory_path=DEFAULT_INVENTORY_PATH,
            sketchfab_path=DEFAULT_SKETCHFAB_PATH,
            stories_path=tmp_stories_path,
            creators_path=None,
            experiences_path=None,
            dry_run=False,
        )
        assert report.is_valid is True
        assert stats.claims_inserted == 1

        story_slug = verified_provenance_story["stories"][0]["slug"]
        db_story = db_session.scalar(select(RbpcStory).where(RbpcStory.slug == story_slug))
        assert db_story is not None
        assert len(db_story.claims) == 1

        claim = db_story.claims[0]
        # Invariant: Allowed to be expert_verified because authenticated reviewer and valid citation exist
        assert claim.review_status == "expert_verified"
        assert claim.reviewed_by == expert_user.id
        assert claim.notes == "Hội đồng sử học phê duyệt theo biên bản số 42/HĐ-2025."
    finally:
        Path(tmp_stories_path).unlink(missing_ok=True)
