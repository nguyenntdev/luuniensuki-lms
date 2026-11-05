# -*- coding: utf-8 -*-
"""Curriculum Competency Catalog Service (V5-T095 / Wave W09 / Slot A05).

Implements standard historical competencies under the Vietnam 2018 General
Education Program (GDPT 2018):
- Historical Literacy (Tìm hiểu lịch sử)
- Source Criticism & Epistemic Reasoning (Nhận thức và tư duy lịch sử / Khảo chứng tư liệu)
- Historical Empathy & Perspective Taking (Đồng cảm và nhân sinh quan lịch sử)
- Historical Communication & Argumentation (Giao tiếp và trình bày lịch sử)

Mapped to grade bands (Grades 6–12) and real relics (Cửu Đỉnh 9 Urns and 162 Motifs).
Supports teacher editing, feedback, inaccuracy flagging, and review warning invariant.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..errors import AppError
from ..history_models import (
    CompetencyFlagReason,
    CompetencyGradeBand,
    CompetencyMappingStatus,
    CurriculumCompetency,
    CurriculumCompetencyFlag,
    CurriculumCompetencyRelicMapping,
    StandardCompetencyDomain,
)
from ..models import User, UserRole
from ..rbac import ADMIN_ROLES, STAFF_ROLES

# Default review warning for unreviewed mappings
UNREVIEWED_WARNING_TEXT = (
    "Cảnh báo: Ánh xạ năng lực chưa được thẩm định chuyên môn bởi giáo viên cốt cán"
)

# Standard competency catalog under Vietnam 2018 General Education Program
STANDARD_GDPT_COMPETENCIES = [
    {
        "code": "COMP_HIST_LITERACY",
        "standard_framework": "VN_GDPT_2018",
        "domain": StandardCompetencyDomain.historical_literacy.value,
        "name_vi": "Năng lực Tìm hiểu Lịch sử",
        "name_en": "Historical Literacy",
        "description_vi": (
            "Năng lực nhận diện, thu thập, và giải mã các sự kiện, nhân vật, mốc thời gian, "
            "hiện vật và biểu tượng lịch sử trong không gian và thời gian cụ thể theo chương trình GDPT 2018."
        ),
        "description_en": (
            "Ability to recognize, gather, and decode historical events, figures, timelines, "
            "artifacts, and symbols within specific spatial and temporal frameworks under Vietnam 2018 General Education Program."
        ),
        "grade_band_descriptors": {
            "GRADE_6_7": {
                "min_grade": 6,
                "max_grade": 7,
                "descriptor_vi": (
                    "Nhận diện được tên gọi, công năng cơ bản của 9 Đỉnh (Cửu Đỉnh), thời gian đúc "
                    "(1835-1837) dưới triều vua Minh Mạng; phân biệt được các nhóm họa tiết (động vật, thực vật, vũ khí, danh thắng)."
                ),
                "descriptor_en": (
                    "Identify names and functions of the Nine Dynastic Urns, casting timeline (1835-1837), "
                    "and categorize motifs (animals, plants, weapons, landscapes)."
                ),
            },
            "GRADE_8_9": {
                "min_grade": 8,
                "max_grade": 9,
                "descriptor_vi": (
                    "Mô tả chi tiết quá trình thu thập nguyên liệu đồng, kỹ thuật đúc của nghệ nhân "
                    "Phường Đúc; xác định vị trí các địa danh lịch sử khắc trên Cửu Đỉnh (sông, núi, biển đảo)."
                ),
                "descriptor_en": (
                    "Describe bronze raw material procurement and metallurgical craftsmanship of Phường Đúc "
                    "artisans; locate geographical reliefs (rivers, mountains, territorial waters)."
                ),
            },
            "GRADE_10_12": {
                "min_grade": 10,
                "max_grade": 12,
                "descriptor_vi": (
                    "Phân tích hệ thống biểu tượng Cửu Đỉnh trong mối liên hệ với tư tưởng thống nhất quốc gia, "
                    "cương vực lãnh thổ và chủ quyền biển đảo của Đại Nam thế kỷ XIX."
                ),
                "descriptor_en": (
                    "Analyze the symbolic system of the Nine Urns in relation to national unification ideology, "
                    "territorial integrity, and maritime sovereignty of 19th-century Đại Nam."
                ),
            },
        },
    },
    {
        "code": "COMP_SOURCE_CRITICISM",
        "standard_framework": "VN_GDPT_2018",
        "domain": StandardCompetencyDomain.source_criticism.value,
        "name_vi": "Năng lực Khảo chứng & Tư duy Sử liệu",
        "name_en": "Historical Source Criticism & Epistemic Reasoning",
        "description_vi": (
            "Năng lực phân loại, đối chiếu, thẩm định nguồn sử liệu (sử liệu sơ cấp, thứ cấp, "
            "văn bản Hán - Nôm, bản dập 2D, châu bản, văn bia), phát hiện mâu thuẫn và đánh giá độ tin cậy của chứng cứ."
        ),
        "description_en": (
            "Ability to classify, cross-examine, and authenticate historical sources (primary, secondary, "
            "Sino-Nom texts, 2D rubbings, imperial records, epigraphs), detect discrepancies, and evaluate evidentiary reliability."
        ),
        "grade_band_descriptors": {
            "GRADE_6_7": {
                "min_grade": 6,
                "max_grade": 7,
                "descriptor_vi": (
                    "Phân biệt được giữa bản dập 2D / phù điêu đồng thật trên Cửu Đỉnh với hình ảnh minh họa mô phỏng hiện đại; "
                    "chỉ ra được xuất xứ cơ bản của tư liệu."
                ),
                "descriptor_en": (
                    "Distinguish between authentic 2D rubbings / bronze reliefs and modern simulated imagery; "
                    "identify basic source provenance."
                ),
            },
            "GRADE_8_9": {
                "min_grade": 8,
                "max_grade": 9,
                "descriptor_vi": (
                    "Đối chiếu thông tin khắc trên bản dập Cửu Đỉnh với các đoạn trích từ Khâm Định Đại Nam Hội Điển Sự Lệ "
                    "và Đại Nam Thực Lục; phân biệt thông tin chính sử và truyền thuyết dân gian."
                ),
                "descriptor_en": (
                    "Cross-reference motifs on 2D rubbings with imperial statutes and chronicles; "
                    "separate official court records from folklore."
                ),
            },
            "GRADE_10_12": {
                "min_grade": 10,
                "max_grade": 12,
                "descriptor_vi": (
                    "Khảo chứng văn bản Hán - Nôm và chữ khắc trên từng đỉnh đồng; phản biện các giả thuyết lịch sử "
                    "trái chiều về địa danh biển đảo và niên đại chế tác."
                ),
                "descriptor_en": (
                    "Critique Sino-Nom inscriptions and epigraphic evidence; resolve scholarly disputes regarding maritime territory and chronology."
                ),
            },
        },
    },
    {
        "code": "COMP_HIST_EMPATHY",
        "standard_framework": "VN_GDPT_2018",
        "domain": StandardCompetencyDomain.historical_empathy.value,
        "name_vi": "Năng lực Đồng cảm & Nhân sinh quan Lịch sử",
        "name_en": "Historical Empathy & Perspective Taking",
        "description_vi": (
            "Năng lực thấu hiểu bối cảnh tâm lý, động cơ, giá trị và điều kiện sống của con người "
            "trong quá khứ mà không áp đặt định kiến hiện đại (chống quy hiện)."
        ),
        "description_en": (
            "Ability to reconstruct historical context, values, motives, and lived experiences of past "
            "human communities without presentist bias."
        ),
        "grade_band_descriptors": {
            "GRADE_6_7": {
                "min_grade": 6,
                "max_grade": 7,
                "descriptor_vi": (
                    "Cảm nhận được sự nhọc nhằn, khéo léo và lòng tự hào của các nghệ nhân đúc đồng thủ công thế kỷ XIX "
                    "khi tạo tác nên các đỉnh đồng đồ sộ."
                ),
                "descriptor_en": (
                    "Appreciate the labor, artisanal craftsmanship, and cultural pride of 19th-century bronze casters producing imperial monument urns."
                ),
            },
            "GRADE_8_9": {
                "min_grade": 8,
                "max_grade": 9,
                "descriptor_vi": (
                    "Thấu hiểu tâm tư của cộng đồng thợ đúc Phường Đúc trước lệnh triệu tập hoàng gia; "
                    "nhận thức về sự gắn bó giữa lao động thủ công và danh dự làng nghề."
                ),
                "descriptor_en": (
                    "Understand the social reality of Phường Đúc foundry workers answering imperial summons; recognize guild honor and tradition."
                ),
            },
            "GRADE_10_12": {
                "min_grade": 10,
                "max_grade": 12,
                "descriptor_vi": (
                    "Đặt tư tưởng đúc Cửu Đỉnh vào thế giới quan Nho giáo triều Minh Mạng, "
                    "phân tích khát vọng hòa hợp trời - đất - con người và tính chính thống vương quyền."
                ),
                "descriptor_en": (
                    "Contextualize the Nine Urns within the Confucian cosmology of the Minh Mạng era, analyzing imperial legitimacy and cosmic harmony."
                ),
            },
        },
    },
    {
        "code": "COMP_HIST_COMMUNICATION",
        "standard_framework": "VN_GDPT_2018",
        "domain": StandardCompetencyDomain.historical_communication.value,
        "name_vi": "Năng lực Giao tiếp & Trình bày Lịch sử",
        "name_en": "Historical Communication & Argumentation",
        "description_vi": (
            "Năng lực diễn đạt, lập luận và bảo vệ quan điểm lịch sử dựa trên bằng chứng xác thực; "
            "hợp tác trong điều tra lịch sử và thảo luận học thuật."
        ),
        "description_en": (
            "Ability to formulate, articulate, and defend evidence-based historical arguments; "
            "collaborate in historical inquiries and debates."
        ),
        "grade_band_descriptors": {
            "GRADE_6_7": {
                "min_grade": 6,
                "max_grade": 7,
                "descriptor_vi": (
                    "Trình bày rõ ràng trước nhóm về một họa tiết trên Cửu Đỉnh, sử dụng đúng thuật ngữ lịch sử cơ bản "
                    "và dẫn chứng trực quan từ bản dập 2D."
                ),
                "descriptor_en": (
                    "Deliver clear oral presentations on a selected motif, using accurate terminology and 2D rubbing visual evidence."
                ),
            },
            "GRADE_8_9": {
                "min_grade": 8,
                "max_grade": 9,
                "descriptor_vi": (
                    "Viết đoạn văn ngắn hoặc thuyết trình so sánh hai đỉnh đồng hoặc hai họa tiết cùng thể loại; "
                    "dẫn nguồn tài liệu tham khảo chính xác."
                ),
                "descriptor_en": (
                    "Compose comparative analyses or presentations between urns/motifs with formal citation of historical sources."
                ),
            },
            "GRADE_10_12": {
                "min_grade": 10,
                "max_grade": 12,
                "descriptor_vi": (
                    "Xây dựng báo cáo nghiên cứu hoặc hồ sơ di sản đa phương tiện; "
                    "tranh biện học thuật có trích dẫn xuất xứ thư tịch và bản dập khảo cổ."
                ),
                "descriptor_en": (
                    "Construct academic research dossiers and multimedia heritage exhibits; engage in structured debates with primary citations."
                ),
            },
        },
    },
]


def ensure_default_competencies(db: Session) -> list[CurriculumCompetency]:
    """Ensure standard 4 competencies under VN_GDPT_2018 exist in the database."""
    result: list[CurriculumCompetency] = []
    for item in STANDARD_GDPT_COMPETENCIES:
        stmt = select(CurriculumCompetency).where(CurriculumCompetency.code == item["code"])
        existing = db.execute(stmt).scalar_one_or_none()
        if not existing:
            comp = CurriculumCompetency(
                code=item["code"],
                standard_framework=item["standard_framework"],
                domain=item["domain"],
                name_vi=item["name_vi"],
                name_en=item["name_en"],
                description_vi=item["description_vi"],
                description_en=item["description_en"],
                grade_band_descriptors=item["grade_band_descriptors"],
                is_active=True,
            )
            db.add(comp)
            db.flush()
            result.append(comp)
        else:
            result.append(existing)

    # Also seed initial default relic mappings if none exist
    mapping_count = db.execute(select(func.count(CurriculumCompetencyRelicMapping.id))).scalar() or 0
    if mapping_count == 0:
        _seed_initial_relic_mappings(db)

    db.commit()
    return result


def _seed_initial_relic_mappings(db: Session) -> None:
    """Seed initial realistic mappings to Cửu Đỉnh relics."""
    comp_map = {c.code: c.id for c in db.execute(select(CurriculumCompetency)).scalars().all()}
    if not comp_map:
        return

    initial_mappings = [
        {
            "competency_code": "COMP_HIST_LITERACY",
            "relic_urn_slug": "cao-dinh",
            "relic_motif_id": "urn_cao_dinh_01",
            "entity_slug": "cao-dinh",
            "grade_band": "GRADE_6_7",
            "min_grade": 6,
            "max_grade": 7,
            "learning_activity_vi": "Quan sát bản dập 2D họa tiết Rồng mây bay trên Cao Đỉnh và ghi nhận các đặc điểm tạo hình hoàng gia.",
            "learning_activity_en": "Observe 2D rubbing of the imperial flying dragon motif on Cao Đỉnh and record royal stylistic features.",
            "evidence_requirement_vi": "Học sinh đối chiếu bản dập 2D với mô tả trong thư tịch cổ.",
            "evidence_requirement_en": "Students compare 2D rubbing with classical archival records.",
            "status": CompetencyMappingStatus.verified.value,
            "is_reviewed": True,
            "review_warning": None,
        },
        {
            "competency_code": "COMP_SOURCE_CRITICISM",
            "relic_urn_slug": "cao-dinh",
            "relic_motif_id": "urn_cao_dinh_02",
            "entity_slug": "kham-dinh-dai-nam-hoi-dien-su-le",
            "grade_band": "GRADE_10_12",
            "min_grade": 10,
            "max_grade": 12,
            "learning_activity_vi": "Khảo cứu quyển và số tờ trong Hội Điển Sự Lệ quy định hợp kim đúc Cao Đỉnh và đối chiếu với mẫu vật bảo tàng.",
            "learning_activity_en": "Examine volume and folios in imperial administrative statutes specifying Cao Đỉnh metallurgy.",
            "evidence_requirement_vi": "Trích dẫn chính xác xuất xứ quyển, tờ của Hội Điển Sự Lệ (1835).",
            "evidence_requirement_en": "Precise citation of volume and folio in imperial statutes (1835).",
            "status": CompetencyMappingStatus.verified.value,
            "is_reviewed": True,
            "review_warning": None,
        },
        {
            "competency_code": "COMP_HIST_EMPATHY",
            "relic_urn_slug": "nhan-dinh",
            "relic_motif_id": "urn_nhan_dinh_01",
            "entity_slug": "phuong-duc-bronze-foundry",
            "grade_band": "GRADE_8_9",
            "min_grade": 8,
            "max_grade": 9,
            "learning_activity_vi": "Nhập vai nghệ nhân Phường Đúc tham gia đúc Nhân Đỉnh, viết nhật ký mô tả kỹ thuật rót đồng thủ công.",
            "learning_activity_en": "Roleplay as a Phường Đúc foundry artisan casting Nhân Đỉnh and write a workshop log.",
            "evidence_requirement_vi": "Thể hiện hiểu biết về điều kiện làm việc và tâm lý thợ đúc thế kỷ XIX không áp đặt quan điểm hiện đại.",
            "evidence_requirement_en": "Demonstrate understanding of 19th-century foundry conditions without presentist bias.",
            "status": CompetencyMappingStatus.verified.value,
            "is_reviewed": True,
            "review_warning": None,
        },
        {
            "competency_code": "COMP_HIST_COMMUNICATION",
            "relic_urn_slug": "chuong-dinh",
            "relic_motif_id": "urn_chuong_dinh_01",
            "entity_slug": "chuong-dinh",
            "grade_band": "GRADE_10_12",
            "min_grade": 10,
            "max_grade": 12,
            "learning_activity_vi": "Thuyết trình và phản biện về thông điệp địa lý và cương vực lãnh thổ thể hiện trên Chương Đỉnh.",
            "learning_activity_en": "Present and debate territorial sovereignty messages engraved on Chương Đỉnh.",
            "evidence_requirement_vi": "Báo cáo sử dụng dữ liệu bản dập và luận điểm có đối chiếu tư liệu.",
            "evidence_requirement_en": "Report utilizing rubbing evidence and corroborated scholarly arguments.",
            "status": CompetencyMappingStatus.verified.value,
            "is_reviewed": True,
            "review_warning": None,
        },
        {
            "competency_code": "COMP_SOURCE_CRITICISM",
            "relic_urn_slug": "tuyen-dinh",
            "relic_motif_id": "urn_tuyen_dinh_01",
            "entity_slug": "tuyen-dinh",
            "grade_band": "GRADE_10_12",
            "min_grade": 10,
            "max_grade": 12,
            "learning_activity_vi": "Thẩm định sơ bộ văn tự Hán Nôm trên Tuyên Đỉnh (bản thảo ánh xạ thử nghiệm).",
            "learning_activity_en": "Preliminary assessment of Sino-Nom epigraphs on Tuyên Đỉnh (draft mapping).",
            "evidence_requirement_vi": "Yêu cầu dẫn chứng thêm châu bản triều Nguyễn.",
            "evidence_requirement_en": "Requires additional royal archive corroboration.",
            "status": CompetencyMappingStatus.unreviewed.value,
            "is_reviewed": False,
            "review_warning": UNREVIEWED_WARNING_TEXT,
        },
    ]

    for item in initial_mappings:
        cid = comp_map.get(item["competency_code"])
        if not cid:
            continue
        mapping = CurriculumCompetencyRelicMapping(
            competency_id=cid,
            relic_urn_slug=item["relic_urn_slug"],
            relic_motif_id=item["relic_motif_id"],
            entity_slug=item["entity_slug"],
            grade_band=item["grade_band"],
            min_grade=item["min_grade"],
            max_grade=item["max_grade"],
            learning_activity_vi=item["learning_activity_vi"],
            learning_activity_en=item["learning_activity_en"],
            evidence_requirement_vi=item["evidence_requirement_vi"],
            evidence_requirement_en=item["evidence_requirement_en"],
            status=item["status"],
            is_reviewed=item["is_reviewed"],
            review_warning=item["review_warning"],
            flag_count=0,
        )
        db.add(mapping)
    db.flush()


def validate_grade_range(min_grade: int, max_grade: int) -> None:
    """Validate that grade bounds conform to Vietnam secondary education (Grades 6–12)."""
    if min_grade < 6 or min_grade > 12:
        raise AppError(
            "INVALID_GRADE_RANGE",
            f"min_grade ({min_grade}) must be between 6 and 12 (Vietnam secondary education)",
            422,
        )
    if max_grade < 6 or max_grade > 12:
        raise AppError(
            "INVALID_GRADE_RANGE",
            f"max_grade ({max_grade}) must be between 6 and 12 (Vietnam secondary education)",
            422,
        )
    if min_grade > max_grade:
        raise AppError(
            "INVALID_GRADE_RANGE",
            f"min_grade ({min_grade}) cannot be greater than max_grade ({max_grade})",
            422,
        )


def check_teacher_or_staff_permission(user: User) -> None:
    """Ensure user is an authenticated teacher, staff, or admin."""
    if not user or user.role not in STAFF_ROLES:
        raise AppError(
            "FORBIDDEN_TEACHER_ACTION",
            "This action is restricted to teachers, staff, and administrators",
            403,
        )


def check_admin_permission(user: User) -> None:
    """Ensure user is an administrator."""
    if not user or user.role not in ADMIN_ROLES:
        raise AppError(
            "FORBIDDEN_ADMIN_ACTION",
            "This action is restricted to administrators",
            403,
        )


def list_competencies(
    db: Session,
    framework: Optional[str] = None,
    domain: Optional[str] = None,
) -> list[CurriculumCompetency]:
    """List standard historical competencies with optional framework/domain filters."""
    ensure_default_competencies(db)
    query = select(CurriculumCompetency).where(CurriculumCompetency.is_active.is_(True))
    if framework:
        query = query.where(CurriculumCompetency.standard_framework == framework)
    if domain:
        query = query.where(CurriculumCompetency.domain == domain)
    query = query.order_by(CurriculumCompetency.code)
    return list(db.execute(query).scalars().all())


def get_competency_by_code(db: Session, code: str) -> Optional[CurriculumCompetency]:
    """Fetch competency by unique code."""
    ensure_default_competencies(db)
    stmt = select(CurriculumCompetency).where(CurriculumCompetency.code == code)
    return db.execute(stmt).scalar_one_or_none()


def list_relic_mappings(
    db: Session,
    urn_slug: Optional[str] = None,
    motif_id: Optional[str] = None,
    competency_code: Optional[str] = None,
    grade: Optional[int] = None,
    grade_band: Optional[str] = None,
    status: Optional[str] = None,
) -> list[CurriculumCompetencyRelicMapping]:
    """Query competency-to-relic mappings with filtering support."""
    ensure_default_competencies(db)
    query = select(CurriculumCompetencyRelicMapping).join(CurriculumCompetency)
    if urn_slug:
        query = query.where(CurriculumCompetencyRelicMapping.relic_urn_slug == urn_slug)
    if motif_id:
        query = query.where(CurriculumCompetencyRelicMapping.relic_motif_id == motif_id)
    if competency_code:
        query = query.where(CurriculumCompetency.code == competency_code)
    if grade is not None:
        query = query.where(
            CurriculumCompetencyRelicMapping.min_grade <= grade,
            CurriculumCompetencyRelicMapping.max_grade >= grade,
        )
    if grade_band:
        query = query.where(CurriculumCompetencyRelicMapping.grade_band == grade_band)
    if status:
        query = query.where(CurriculumCompetencyRelicMapping.status == status)

    query = query.order_by(CurriculumCompetencyRelicMapping.created_at.desc())
    return list(db.execute(query).scalars().all())


def get_relic_mapping(db: Session, mapping_id: UUID) -> Optional[CurriculumCompetencyRelicMapping]:
    """Get single competency relic mapping with its competency and active flags."""
    return db.get(CurriculumCompetencyRelicMapping, mapping_id)


def create_relic_mapping(
    db: Session,
    user: User,
    data: dict[str, Any],
) -> CurriculumCompetencyRelicMapping:
    """Teacher creates a new competency relic mapping.

    New mappings default to unreviewed with a review warning banner.
    """
    check_teacher_or_staff_permission(user)

    min_g = int(data.get("min_grade", 6))
    max_g = int(data.get("max_grade", 12))
    validate_grade_range(min_g, max_g)

    competency_id = data.get("competency_id")
    if not competency_id:
        raise AppError("MISSING_COMPETENCY_ID", "competency_id is required", 422)

    comp = db.get(CurriculumCompetency, competency_id)
    if not comp:
        raise AppError("COMPETENCY_NOT_FOUND", f"Competency {competency_id} not found", 404)

    learning_vi = (data.get("learning_activity_vi") or "").strip()
    evidence_vi = (data.get("evidence_requirement_vi") or "").strip()
    if not learning_vi or not evidence_vi:
        raise AppError(
            "INVALID_MAPPING_CONTENT",
            "learning_activity_vi and evidence_requirement_vi are mandatory",
            422,
        )

    mapping = CurriculumCompetencyRelicMapping(
        competency_id=comp.id,
        relic_urn_slug=data.get("relic_urn_slug"),
        relic_motif_id=data.get("relic_motif_id"),
        entity_slug=data.get("entity_slug"),
        grade_band=data.get("grade_band", "GRADE_10_12"),
        min_grade=min_g,
        max_grade=max_g,
        learning_activity_vi=learning_vi,
        learning_activity_en=data.get("learning_activity_en"),
        evidence_requirement_vi=evidence_vi,
        evidence_requirement_en=data.get("evidence_requirement_en"),
        status=CompetencyMappingStatus.unreviewed.value,
        is_reviewed=False,
        review_warning=UNREVIEWED_WARNING_TEXT,
        flag_count=0,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return mapping


def update_relic_mapping(
    db: Session,
    user: User,
    mapping_id: UUID,
    data: dict[str, Any],
) -> CurriculumCompetencyRelicMapping:
    """Teacher or staff edits an existing competency mapping."""
    check_teacher_or_staff_permission(user)

    mapping = db.get(CurriculumCompetencyRelicMapping, mapping_id)
    if not mapping:
        raise AppError("MAPPING_NOT_FOUND", f"Mapping {mapping_id} not found", 404)

    min_g = int(data.get("min_grade", mapping.min_grade))
    max_g = int(data.get("max_grade", mapping.max_grade))
    validate_grade_range(min_g, max_g)

    mapping.min_grade = min_g
    mapping.max_grade = max_g

    if "grade_band" in data and data["grade_band"]:
        mapping.grade_band = data["grade_band"]
    if "learning_activity_vi" in data and data["learning_activity_vi"]:
        mapping.learning_activity_vi = data["learning_activity_vi"].strip()
    if "learning_activity_en" in data:
        mapping.learning_activity_en = data["learning_activity_en"]
    if "evidence_requirement_vi" in data and data["evidence_requirement_vi"]:
        mapping.evidence_requirement_vi = data["evidence_requirement_vi"].strip()
    if "evidence_requirement_en" in data:
        mapping.evidence_requirement_en = data["evidence_requirement_en"]
    if "relic_urn_slug" in data:
        mapping.relic_urn_slug = data["relic_urn_slug"]
    if "relic_motif_id" in data:
        mapping.relic_motif_id = data["relic_motif_id"]
    if "entity_slug" in data:
        mapping.entity_slug = data["entity_slug"]

    mapping.updated_by_id = user.id

    # If updated by a regular teacher, unreviewed warning is preserved unless admin verified
    if user.role not in ADMIN_ROLES and not mapping.is_reviewed:
        mapping.review_warning = UNREVIEWED_WARNING_TEXT

    db.commit()
    db.refresh(mapping)
    return mapping


def flag_relic_mapping(
    db: Session,
    user: User,
    mapping_id: UUID,
    reason: str,
    commentary: str,
    suggested_correction: Optional[dict[str, Any]] = None,
) -> CurriculumCompetencyFlag:
    """Teacher flags an inaccurate competency mapping.

    Immediately transitions mapping to 'flagged' status and updates the review warning.
    """
    check_teacher_or_staff_permission(user)

    # Validate reason
    valid_reasons = {r.value for r in CompetencyFlagReason}
    if reason not in valid_reasons:
        raise AppError(
            "INVALID_FLAG_REASON",
            f"Reason '{reason}' is invalid. Allowed: {sorted(list(valid_reasons))}",
            422,
        )

    commentary = (commentary or "").strip()
    if len(commentary) < 5:
        raise AppError(
            "INVALID_COMMENTARY",
            "Teacher commentary must be at least 5 characters detailing the inaccuracy",
            422,
        )

    mapping = db.get(CurriculumCompetencyRelicMapping, mapping_id)
    if not mapping:
        raise AppError("MAPPING_NOT_FOUND", f"Mapping {mapping_id} not found", 404)

    # Check for existing pending flag by this user
    existing_flag = db.execute(
        select(CurriculumCompetencyFlag).where(
            CurriculumCompetencyFlag.mapping_id == mapping.id,
            CurriculumCompetencyFlag.flagged_by_id == user.id,
            CurriculumCompetencyFlag.status == "pending",
        )
    ).scalar_one_or_none()

    if existing_flag:
        existing_flag.reason = reason
        existing_flag.commentary = commentary
        existing_flag.suggested_correction = suggested_correction or {}
        flag = existing_flag
    else:
        flag = CurriculumCompetencyFlag(
            mapping_id=mapping.id,
            flagged_by_id=user.id,
            reason=reason,
            commentary=commentary,
            suggested_correction=suggested_correction or {},
            status="pending",
        )
        db.add(flag)
        mapping.flag_count += 1

    # Update mapping status and warning banner
    mapping.status = CompetencyMappingStatus.flagged.value
    mapping.is_reviewed = False
    mapping.review_warning = (
        f"Cảnh báo: Ánh xạ bị giáo viên gắn cờ cảnh báo: {reason} — {commentary[:80]}"
    )

    db.commit()
    db.refresh(flag)
    db.refresh(mapping)
    return flag


def list_mapping_flags(
    db: Session,
    mapping_id: UUID,
    user: User,
) -> list[CurriculumCompetencyFlag]:
    """List flags associated with a specific mapping (teachers and staff only)."""
    check_teacher_or_staff_permission(user)
    stmt = (
        select(CurriculumCompetencyFlag)
        .where(CurriculumCompetencyFlag.mapping_id == mapping_id)
        .order_by(CurriculumCompetencyFlag.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def resolve_mapping_flag(
    db: Session,
    user: User,
    flag_id: UUID,
    action: str,
    resolution_notes: str,
    updated_mapping_status: Optional[str] = None,
) -> CurriculumCompetencyFlag:
    """Admin or staff resolves or dismisses a teacher flag."""
    check_teacher_or_staff_permission(user)

    if action not in ("resolved", "dismissed"):
        raise AppError("INVALID_ACTION", "Action must be 'resolved' or 'dismissed'", 422)

    flag = db.get(CurriculumCompetencyFlag, flag_id)
    if not flag:
        raise AppError("FLAG_NOT_FOUND", f"Flag {flag_id} not found", 404)

    flag.status = action
    flag.resolved_by_id = user.id
    flag.resolution_notes = resolution_notes.strip() if resolution_notes else None
    flag.resolved_at = datetime.now(timezone.utc)

    # Check remaining pending flags for mapping
    mapping = db.get(CurriculumCompetencyRelicMapping, flag.mapping_id)
    if mapping:
        remaining_pending = db.execute(
            select(func.count(CurriculumCompetencyFlag.id)).where(
                CurriculumCompetencyFlag.mapping_id == mapping.id,
                CurriculumCompetencyFlag.status == "pending",
                CurriculumCompetencyFlag.id != flag.id,
            )
        ).scalar() or 0

        if remaining_pending == 0:
            if updated_mapping_status in (s.value for s in CompetencyMappingStatus):
                mapping.status = updated_mapping_status
            else:
                mapping.status = CompetencyMappingStatus.unreviewed.value

            if mapping.status == CompetencyMappingStatus.verified.value:
                mapping.is_reviewed = True
                mapping.review_warning = None
            else:
                mapping.review_warning = UNREVIEWED_WARNING_TEXT

    db.commit()
    db.refresh(flag)
    return flag


def verify_relic_mapping(
    db: Session,
    user: User,
    mapping_id: UUID,
) -> CurriculumCompetencyRelicMapping:
    """Staff or administrator verifies a competency mapping, clearing review warnings."""
    check_admin_permission(user)

    mapping = db.get(CurriculumCompetencyRelicMapping, mapping_id)
    if not mapping:
        raise AppError("MAPPING_NOT_FOUND", f"Mapping {mapping_id} not found", 404)

    mapping.is_reviewed = True
    mapping.status = CompetencyMappingStatus.verified.value
    mapping.review_warning = None
    mapping.updated_by_id = user.id

    db.commit()
    db.refresh(mapping)
    return mapping
