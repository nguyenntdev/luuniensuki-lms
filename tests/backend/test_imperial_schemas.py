# -*- coding: utf-8 -*-
"""Unit tests for STTTNNĐ (Lưu Niên — Đại Nội Huế) Pydantic schemas.

Validates:
1. Normalized UV coordinate bounds ([0.0, 1.0]) on points and polygons.
2. Optimistic locking concurrency (`row_version`) handling.
3. Import/Export payload schema verification, scope integrity, and SHA-256 hash checks.
4. JSON round-trip serializability of all DTOs.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.apischemas.imperial import (
    ImperialActivityCreate,
    ImperialActivityOut,
    ImperialActivityUpdate,
    ImperialAnnotationAuditOut,
    ImperialAnnotationCreate,
    ImperialAnnotationLinkCreate,
    ImperialAnnotationLinkOut,
    ImperialAnnotationOut,
    ImperialAnnotationUpdate,
    ImperialExportPayload,
    ImperialImportPayload,
    ImperialLearningPathCreate,
    ImperialLearningPathDetail,
    ImperialLearningPathSummary,
    ImperialLearningPathUpdate,
    ImperialLensCreate,
    ImperialLensOut,
    ImperialLensSiteCreate,
    ImperialLensSiteOut,
    ImperialLensUpdate,
    ImperialMapAssetDetail,
    ImperialMapAssetPublish,
    ImperialMapAssetReview,
    ImperialMapAssetSummary,
    ImperialMapAssetUpload,
    ImperialMediaCreate,
    ImperialMediaOut,
    ImperialMediaUpdate,
    ImperialPathStepCreate,
    ImperialPathStepOut,
    ImperialSiteCreate,
    ImperialSiteDetail,
    ImperialSiteEvidence,
    ImperialSiteEvidenceItem,
    ImperialSiteSummary,
    ImperialSiteTimeline,
    ImperialSiteTimelineItem,
    ImperialSiteUpdate,
    ImperialSubmissionCreate,
    ImperialSubmissionGrade,
    ImperialSubmissionOut,
    ImperialZoneCreate,
    ImperialZoneOut,
    ImperialZoneSummary,
    ImperialZoneUpdate,
)


# =========================================================================== #
# 1. UV Bounds Validation Tests
# =========================================================================== #
class TestUVBoundsValidation:
    """Validates that point annotations and polygon vertices adhere strictly to [0.0, 1.0]."""

    def test_valid_uv_coordinates(self):
        map_id = uuid4()
        site_id = uuid4()

        # Edge cases: 0.0 and 1.0
        anno_min = ImperialAnnotationCreate(
            map_asset_id=map_id,
            site_id=site_id,
            u=0.0,
            v=0.0,
        )
        assert anno_min.u == 0.0
        assert anno_min.v == 0.0

        anno_max = ImperialAnnotationCreate(
            map_asset_id=map_id,
            site_id=site_id,
            u=1.0,
            v=1.0,
        )
        assert anno_max.u == 1.0
        assert anno_max.v == 1.0

        # Interior coordinate
        anno_mid = ImperialAnnotationCreate(
            map_asset_id=map_id,
            site_id=site_id,
            u=0.5234567,
            v=0.8765432,
        )
        assert anno_mid.u == 0.5234567
        assert anno_mid.v == 0.8765432

    @pytest.mark.parametrize(
        "invalid_u,invalid_v",
        [
            (-0.000001, 0.5),
            (1.000001, 0.5),
            (-1.0, 0.5),
            (2.5, 0.5),
            (0.5, -0.0001),
            (0.5, 1.0001),
            (0.5, -5.0),
            (0.5, 99.0),
            (-0.1, -0.1),
            (1.1, 1.1),
        ],
    )
    def test_reject_out_of_bound_uv(self, invalid_u: float, invalid_v: float):
        map_id = uuid4()
        site_id = uuid4()
        with pytest.raises(ValidationError) as exc_info:
            ImperialAnnotationCreate(
                map_asset_id=map_id,
                site_id=site_id,
                u=invalid_u,
                v=invalid_v,
            )
        errors = exc_info.value.errors()
        assert len(errors) >= 1

    def test_update_schema_uv_bounds(self):
        # Valid update
        update = ImperialAnnotationUpdate(u=0.75, v=0.25, row_version=1)
        assert update.u == 0.75
        assert update.v == 0.25

        # Invalid u in update
        with pytest.raises(ValidationError):
            ImperialAnnotationUpdate(u=1.01, row_version=1)

        # Invalid v in update
        with pytest.raises(ValidationError):
            ImperialAnnotationUpdate(v=-0.01, row_version=1)

    def test_valid_polygon_uv(self):
        map_id = uuid4()
        site_id = uuid4()
        anno = ImperialAnnotationCreate(
            map_asset_id=map_id,
            site_id=site_id,
            u=0.5,
            v=0.5,
            shape_type="polygon",
            polygon_uv=[[0.1, 0.1], [0.2, 0.8], [0.9, 0.5]],
        )
        assert anno.polygon_uv == [[0.1, 0.1], [0.2, 0.8], [0.9, 0.5]]

    def test_reject_polygon_fewer_than_3_vertices(self):
        map_id = uuid4()
        site_id = uuid4()
        with pytest.raises(ValidationError) as exc:
            ImperialAnnotationCreate(
                map_asset_id=map_id,
                site_id=site_id,
                u=0.5,
                v=0.5,
                shape_type="polygon",
                polygon_uv=[[0.1, 0.1], [0.2, 0.2]],
            )
        assert "at least 3 vertices" in str(exc.value)

    def test_reject_polygon_vertex_out_of_bounds(self):
        map_id = uuid4()
        site_id = uuid4()
        with pytest.raises(ValidationError) as exc:
            ImperialAnnotationCreate(
                map_asset_id=map_id,
                site_id=site_id,
                u=0.5,
                v=0.5,
                shape_type="polygon",
                polygon_uv=[[0.1, 0.1], [1.05, 0.5], [0.5, 0.8]],
            )
        assert "outside normalized bounds" in str(exc.value)

    def test_reject_polygon_vertex_invalid_dimension(self):
        map_id = uuid4()
        site_id = uuid4()
        with pytest.raises(ValidationError) as exc:
            ImperialAnnotationCreate(
                map_asset_id=map_id,
                site_id=site_id,
                u=0.5,
                v=0.5,
                shape_type="polygon",
                polygon_uv=[[0.1, 0.1], [0.2, 0.3, 0.4], [0.5, 0.8]],
            )
        assert "must have exactly 2 coordinates" in str(exc.value)


# =========================================================================== #
# 2. Optimistic Concurrency (`row_version`) Tests
# =========================================================================== #
class TestOptimisticLockSchema:
    """Validates row_version enforcement across mutable DTOs."""

    def test_annotation_update_requires_row_version(self):
        # Missing row_version raises ValidationError
        with pytest.raises(ValidationError) as exc:
            ImperialAnnotationUpdate(label="Cửa Ngọ Môn")  # type: ignore[call-arg]
        assert "row_version" in str(exc.value)

        # row_version < 1 is rejected
        with pytest.raises(ValidationError):
            ImperialAnnotationUpdate(label="Cửa Ngọ Môn", row_version=0)

        # row_version >= 1 succeeds
        update = ImperialAnnotationUpdate(label="Cửa Ngọ Môn", row_version=1)
        assert update.row_version == 1

        update_v5 = ImperialAnnotationUpdate(label="Cửa Ngọ Môn", row_version=5)
        assert update_v5.row_version == 5

    def test_map_asset_publish_requires_row_version(self):
        with pytest.raises(ValidationError):
            ImperialMapAssetPublish(is_active=True)  # type: ignore[call-arg]

        with pytest.raises(ValidationError):
            ImperialMapAssetPublish(is_active=True, row_version=0)

        pub = ImperialMapAssetPublish(is_active=True, row_version=2)
        assert pub.row_version == 2
        assert pub.is_active is True

    def test_site_update_row_version_bounds(self):
        # row_version is optional on site update, but if passed must be >= 1
        with pytest.raises(ValidationError):
            ImperialSiteUpdate(row_version=0)

        valid_update = ImperialSiteUpdate(name_vi="Điện Thái Hòa", row_version=3)
        assert valid_update.row_version == 3


# =========================================================================== #
# 3. Export / Import Payload & Integrity Verification Tests
# =========================================================================== #
class TestImportExportPayloadSchema:
    """Validates export payload assembly, SHA-256 calculation, and scope enforcement."""

    def test_export_payload_hash_verification_success(self):
        now = datetime.utcnow()
        zone_id = uuid4()
        zone = ImperialZoneOut(
            id=zone_id,
            content_scope="STTT_IMPERIAL_CITY",
            slug="truc-chinh-dien",
            title_vi="Trục Chính Điện",
            title_en="Central Ceremonial Axis",
            description="Khu vực trung tâm nghi lễ triều Nguyễn",
            display_order=1,
            created_at=now,
            updated_at=now,
            row_version=1,
        )

        raw_dict = {
            "schema_version": "1.0.0",
            "exported_at": now.isoformat(),
            "content_scope": "STTT_IMPERIAL_CITY",
            "zones": [zone.model_dump(mode="json")],
            "sites": [],
            "map_assets": [],
            "annotations": [],
            "lenses": [],
            "learning_paths": [],
            "activities": [],
        }

        # Compute valid hash
        computed_hash = ImperialExportPayload.compute_hash(raw_dict)
        raw_dict["verification_hash"] = computed_hash

        payload = ImperialExportPayload.model_validate(raw_dict)
        assert payload.verify_integrity() is True
        assert payload.content_scope == "STTT_IMPERIAL_CITY"
        assert payload.schema_version == "1.0.0"

    def test_export_payload_tampered_content_fails_verification(self):
        now = datetime.utcnow()
        raw_dict = {
            "schema_version": "1.0.0",
            "exported_at": now.isoformat(),
            "content_scope": "STTT_IMPERIAL_CITY",
            "zones": [],
            "sites": [],
            "map_assets": [],
            "annotations": [],
            "lenses": [],
            "learning_paths": [],
            "activities": [],
        }
        computed_hash = ImperialExportPayload.compute_hash(raw_dict)
        raw_dict["verification_hash"] = computed_hash

        payload = ImperialExportPayload.model_validate(raw_dict)
        assert payload.verify_integrity() is True

        # Tampering with verification_hash
        payload.verification_hash = "deadbeef" * 8
        assert payload.verify_integrity() is False

    def test_export_payload_rejects_non_imperial_scope(self):
        now = datetime.utcnow()
        raw_dict = {
            "schema_version": "1.0.0",
            "exported_at": now.isoformat(),
            "content_scope": "CUU_DINH_LEGACY",
            "zones": [],
            "sites": [],
            "map_assets": [],
            "annotations": [],
            "lenses": [],
            "learning_paths": [],
            "activities": [],
            "verification_hash": "dummy_hash",
        }
        with pytest.raises(ValidationError):
            ImperialExportPayload.model_validate(raw_dict)

    def test_export_payload_rejects_invalid_semver(self):
        now = datetime.utcnow()
        raw_dict = {
            "schema_version": "v1.0",
            "exported_at": now.isoformat(),
            "content_scope": "STTT_IMPERIAL_CITY",
            "zones": [],
            "sites": [],
            "map_assets": [],
            "annotations": [],
            "lenses": [],
            "learning_paths": [],
            "activities": [],
            "verification_hash": "dummy_hash",
        }
        with pytest.raises(ValidationError) as exc:
            ImperialExportPayload.model_validate(raw_dict)
        assert "schema_version" in str(exc.value)

    def test_import_payload_integrity(self):
        raw_import = {
            "schema_version": "1.0.0",
            "content_scope": "STTT_IMPERIAL_CITY",
            "zones": [
                {
                    "slug": "tu-cam-thanh",
                    "title_vi": "Tử Cấm Thành",
                    "display_order": 2,
                }
            ],
            "sites": [],
            "map_assets": [],
            "annotations": [],
            "lenses": [],
            "learning_paths": [],
            "activities": [],
        }
        # Compute hash
        import hashlib
        import json

        canonical_json = json.dumps(raw_import, sort_keys=True, default=str)
        vhash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
        raw_import["verification_hash"] = vhash

        import_obj = ImperialImportPayload.model_validate(raw_import)
        assert import_obj.verify_integrity() is True
        assert len(import_obj.zones) == 1
        assert import_obj.zones[0].slug == "tu-cam-thanh"


# =========================================================================== #
# 4. Serializability Round-Trip Tests of All DTOs
# =========================================================================== #
class TestDTOSerializability:
    """Verifies that all 13 entity DTOs serialize to/from JSON cleanly."""

    def test_zone_schemas(self):
        c = ImperialZoneCreate(
            slug="khu-vuc-ngo-mon",
            title_vi="Khu vực Ngọ Môn",
            title_en="Ngo Mon Gate Area",
            description="Khu vực cổng chính phía nam của Hoàng Thành",
            display_order=0,
        )
        json_data = c.model_dump_json()
        assert "khu-vuc-ngo-mon" in json_data

        u = ImperialZoneUpdate(title_vi="Khu vực Ngọ Môn Huế", row_version=2)
        assert u.row_version == 2

        now = datetime.utcnow()
        zid = uuid4()
        out = ImperialZoneOut(
            id=zid,
            slug="khu-vuc-ngo-mon",
            title_vi="Khu vực Ngọ Môn",
            display_order=0,
            created_at=now,
            updated_at=now,
            row_version=1,
        )
        round_tripped = ImperialZoneOut.model_validate_json(out.model_dump_json())
        assert round_tripped.id == zid
        assert round_tripped.content_scope == "STTT_IMPERIAL_CITY"

    def test_site_schemas(self):
        zid = uuid4()
        sid = uuid4()
        create = ImperialSiteCreate(
            zone_id=zid,
            slug="ngo-mon",
            name_vi="Ngọ Môn",
            name_en="Ngo Mon Gate",
            name_han_nom="午門",
            alternative_names=["Cổng Ngọ Môn", "Cửa Nam"],
            site_type="gate",
            condition="extant",
            learning_level="L1_DOCUMENTED",
            construction_year=1833,
            latitude=16.4697,
            longitude=107.5796,
            summary_vi="Cổng chính phía nam của Hoàng Thành Huế.",
            is_published=True,
            display_order=1,
        )
        assert create.slug == "ngo-mon"

        now = datetime.utcnow()
        detail = ImperialSiteDetail(
            id=sid,
            zone_id=zid,
            slug="ngo-mon",
            name_vi="Ngọ Môn",
            alternative_names=["Cổng Ngọ Môn"],
            site_type="gate",
            condition="extant",
            learning_level="L1_DOCUMENTED",
            is_published=True,
            display_order=1,
            created_at=now,
            updated_at=now,
            row_version=1,
            zone=ImperialZoneSummary(
                id=zid, slug="khu-nam", title_vi="Khu Nam", display_order=1
            ),
        )
        dumped = detail.model_dump_json()
        restored = ImperialSiteDetail.model_validate_json(dumped)
        assert restored.id == sid
        assert restored.zone is not None
        assert restored.zone.slug == "khu-nam"

    def test_site_timeline_and_evidence(self):
        tl = ImperialSiteTimeline(
            site_slug="ngo-mon",
            site_name_vi="Ngọ Môn",
            timeline=[
                ImperialSiteTimelineItem(
                    year=1833,
                    period_label="Triều Minh Mạng",
                    event_title="Khởi công xây dựng",
                    description="Vua Minh Mạng cho xây dựng Ngọ Môn trên nền Nam Khuyết Đài cũ.",
                    source_ref="Đại Nam Thực Lục Chính Biên",
                    is_verified=True,
                )
            ],
        )
        assert len(tl.timeline) == 1
        assert tl.timeline[0].year == 1833

        ev = ImperialSiteEvidence(
            site_slug="ngo-mon",
            site_name_vi="Ngọ Môn",
            evidence=[
                ImperialSiteEvidenceItem(
                    claim_id=uuid4(),
                    claim_type="architectural",
                    assertion_vi="Lầu Ngũ Phụng trên tầng hai của Ngọ Môn có 9 bộ mái.",
                    confidence_level="high",
                    source_title="Kiến trúc Cố đô Huế",
                    source_citation="Trang 45, NXB Thuận Hóa, 2002",
                    verification_status="verified",
                )
            ],
        )
        assert len(ev.evidence) == 1
        assert "Lầu Ngũ Phụng" in ev.evidence[0].assertion_vi

    def test_map_asset_schemas(self):
        now = datetime.utcnow()
        aid = uuid4()
        uid = uuid4()

        upload = ImperialMapAssetUpload(
            title_vi="Ảnh chụp từ trên cao Đại Nội Huế 2024",
            title_en="Hue Imperial City Aerial Orthophoto 2024",
            slug="dai-noi-aerial-2024",
            version=1,
            image_storage_key="maps/dai-noi-2024-master.webp",
            preview_storage_key="maps/dai-noi-2024-preview.webp",
            image_sha256="a" * 64,
            mime_type="image/webp",
            width_px=8192,
            height_px=6144,
            source_title="Trung tâm Bảo tồn Di tích Cố đô Huế",
            credit_text="Ảnh tư liệu do Trung tâm BTDT Cố đô Huế cung cấp",
            license_kind="CC-BY-NC-4.0",
        )
        assert upload.width_px == 8192

        detail = ImperialMapAssetDetail(
            id=aid,
            title_vi="Ảnh chụp từ trên cao Đại Nội Huế 2024",
            slug="dai-noi-aerial-2024",
            version=1,
            width_px=8192,
            height_px=6144,
            source_title="Trung tâm Bảo tồn Di tích Cố đô Huế",
            credit_text="Ảnh tư liệu",
            license_kind="CC-BY-NC-4.0",
            image_storage_key="maps/dai-noi-2024.webp",
            image_sha256="b" * 64,
            mime_type="image/webp",
            license_status="approved",
            review_status="published",
            is_active=True,
            created_by=uid,
            created_at=now,
            updated_at=now,
            published_at=now,
            row_version=1,
        )
        assert detail.is_active is True
        assert detail.content_scope == "STTT_IMPERIAL_CITY"

        review = ImperialMapAssetReview(action="approve", notes="Đã xác minh bản quyền.")
        assert review.action == "approve"

    def test_annotation_and_links_schemas(self):
        now = datetime.utcnow()
        aid = uuid4()
        mid = uuid4()
        sid = uuid4()
        uid = uuid4()
        link_id = uuid4()
        story_id = uuid4()

        link = ImperialAnnotationLinkOut(
            id=link_id,
            annotation_id=aid,
            target_type="story",
            target_id=story_id,
            sort_order=0,
        )

        anno = ImperialAnnotationOut(
            id=aid,
            map_asset_id=mid,
            site_id=sid,
            u=0.4851234,
            v=0.7629812,
            label="Ngọ Môn",
            marker_style="monument",
            z_index=10,
            is_visible=True,
            review_status="published",
            position_confidence="verified",
            created_by=uid,
            updated_by=uid,
            created_at=now,
            updated_at=now,
            row_version=2,
            links=[link],
        )
        json_anno = anno.model_dump_json()
        restored = ImperialAnnotationOut.model_validate_json(json_anno)
        assert restored.u == 0.4851234
        assert len(restored.links) == 1
        assert restored.links[0].target_type == "story"

        audit = ImperialAnnotationAuditOut(
            id=uuid4(),
            annotation_id=aid,
            actor_id=uid,
            action="update_coordinates",
            before_json={"u": 0.48, "v": 0.76},
            after_json={"u": 0.4851234, "v": 0.7629812},
            created_at=now,
        )
        assert audit.action == "update_coordinates"

    def test_lens_schemas(self):
        now = datetime.utcnow()
        lid = uuid4()
        sid = uuid4()

        lens_create = ImperialLensCreate(
            code="truc-nghi-le",
            title="Trục Nghi lễ Trung tâm",
            title_en="Central Ceremonial Axis",
            description="Tìm hiểu bố cục không gian quyền lực và nghi lễ của triều đình.",
            prompt="Các công trình trên trục này thể hiện tư tưởng gì của triều Nguyễn?",
            icon="monument",
            color="#C5A059",
            display_order=1,
            is_active=True,
        )
        assert lens_create.code == "truc-nghi-le"

        lens_out = ImperialLensOut(
            id=lid,
            code="truc-nghi-le",
            title="Trục Nghi lễ Trung tâm",
            display_order=1,
            is_active=True,
            created_at=now,
            updated_at=now,
            row_version=1,
        )
        assert lens_out.content_scope == "STTT_IMPERIAL_CITY"

        lens_site = ImperialLensSiteOut(
            id=uuid4(),
            lens_id=lid,
            site_id=sid,
            relevance_score=1.0,
            sequence=1,
            curatorial_notes="Công trình khởi đầu của trục nghi lễ.",
        )
        assert lens_site.relevance_score == 1.0

    def test_learning_path_and_step_schemas(self):
        now = datetime.utcnow()
        pid = uuid4()
        sid = uuid4()
        step_id = uuid4()

        step = ImperialPathStepOut(
            id=step_id,
            path_id=pid,
            site_id=sid,
            step_order=1,
            title="Quan sát bố cục Ngọ Môn",
            prompt="Em hãy ghi nhận vai trò phòng thủ và nghi lễ của Ngọ Môn.",
            estimated_minutes=15,
        )

        path = ImperialLearningPathDetail(
            id=pid,
            slug="kham-pha-hoang-thanh",
            title="Hành trình Khám phá Hoàng Thành Huế",
            description="Tuyến học tập qua các di tích trọng yếu của Hoàng Thành.",
            kind="standard",
            duration_min=60,
            age_group="secondary",
            learning_objectives=["Hiểu cấu trúc Hoàng Thành", "Phân tích tư liệu sử liệu"],
            is_published=True,
            display_order=1,
            created_at=now,
            updated_at=now,
            row_version=1,
            steps=[step],
        )
        json_path = path.model_dump_json()
        restored = ImperialLearningPathDetail.model_validate_json(json_path)
        assert len(restored.steps) == 1
        assert restored.steps[0].estimated_minutes == 15

    def test_activity_and_submission_schemas(self):
        now = datetime.utcnow()
        act_id = uuid4()
        sub_id = uuid4()
        stu_id = uuid4()

        act = ImperialActivityOut(
            id=act_id,
            title="Đối chiếu sử liệu về Ngọ Môn",
            instructions="Đọc đoạn trích Đại Nam Thực Lục và giải thích ý nghĩa tên gọi Ngọ Môn.",
            activity_type="evidence_reflection",
            max_points=100,
            is_active=True,
            created_at=now,
            updated_at=now,
            row_version=1,
        )
        assert act.max_points == 100

        sub = ImperialSubmissionOut(
            id=sub_id,
            activity_id=act_id,
            student_id=stu_id,
            status="graded",
            answer_text="Ngọ Môn là cửa hướng về phương Nam, phương của bậc thiên tử theo Dịch học.",
            evidence_refs=[{"source": "Đại Nam Thực Lục", "page": 120}],
            score=95.0,
            feedback="Phân tích rất chính xác và có dẫn chứng nguồn tốt.",
            submitted_at=now,
            updated_at=now,
            row_version=2,
        )
        assert sub.score == 95.0
        assert sub.status == "graded"

    def test_media_schemas(self):
        now = datetime.utcnow()
        mid = uuid4()
        sid = uuid4()

        media = ImperialMediaOut(
            id=mid,
            site_id=sid,
            media_kind="historical_photo",
            url="https://assets.dainoi.vn/photos/ngomon-1920.webp",
            title="Ngọ Môn thời Khải Định",
            description="Ảnh chụp toàn cảnh Ngọ Môn thập niên 1920.",
            license="Public Domain",
            credit="Ảnh tư liệu Viện Viễn Đông Bác Cổ (EFEO)",
            historical_year=1924,
            is_published=True,
            display_order=1,
            created_at=now,
            updated_at=now,
            row_version=1,
        )
        assert media.historical_year == 1924
        assert media.content_scope == "STTT_IMPERIAL_CITY"
