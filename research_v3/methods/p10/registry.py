"""P10 frozen curriculum-anchor registry (GDPT 2018, grades 10-12) with provenance.

HONESTY CONTRACT (this file is the paper's honesty core)
--------------------------------------------------------
GDPT 2018 (Chương trình Giáo dục Phổ thông 2018, ban hành kèm Thông tư
32/2018/TT-BGDĐT) is a public ministerial document. Entries below fall into
exactly two classes:

1. ``documented`` — the anchor names curriculum content whose existence the
   authors are CERTAIN of from the public document, with the exact citation.
   We deliberately keep this class minimal: unit-level topics of Lịch sử 10-12
   that are publicly quoted in the repo's own GDPT-2018-aligned catalog
   (``data/imperial/curriculum_units_gdpt2018_hue.json``, SHA-256 recorded in
   the data card produced by ``provenance.py``) and the four standard history
   competencies already codified in the production backend service
   (``backend/services/curriculum_competency.py``, codes COMP_*).

2. ``needs_expert_review`` — any anchor whose *specific pairing* of a motif
   category to a competency/grade needs a teacher or curriculum expert to
   confirm. These are counted in every run report and flagged in the
   manuscript; they are never presented as validated.

We do NOT invent official competency codes (e.g. no fabricated "NH 10.2.3"
numeraire): where the ministerial numeraire is not certain, the anchor uses a
repo-local descriptor code prefixed ``P10-LOCAL-`` and is honest about it.

The guard ``assert_anchor_known`` raises on ANY unknown anchor code, so an
invented competency code can never silently enter a sequence (see tests).
"""
from __future__ import annotations

from .anchors import CurriculumAnchor, P10ContractError, UnknownAnchorError

CITATION_TT32 = (
    "Chương trình Giáo dục Phổ thông 2018 — Lịch sử, ban hành kèm Thông tư "
    "32/2018/TT-BGDĐT (Bộ Giáo dục và Đào tạo, 26/12/2018)"
)
CITATION_CV5512 = (
    "Công văn 5512/BGDĐT-GDTrH (2020), Giáo dục địa phương cấp THPT — "
    "dẫn theo data/imperial/curriculum_units_gdpt2018_hue.json (sha256 ghi trong data card P10)"
)
CITATION_BACKEND_CATALOG = (
    "Repo backend/services/curriculum_competency.py STANDARD_GDPT_COMPETENCIES "
    "(VN_GDPT_2018; V5-T095), soát lại bởi chuyên gia trước khi tuyên bố 'documented'"
)

# ---------------------------------------------------------------------------
# Documented anchors — minimal, citation-backed
# ---------------------------------------------------------------------------
DOCUMENTED_ANCHORS: tuple[CurriculumAnchor, ...] = (
    # The existence of "Chuyên đề 10.2: Bảo tồn và phát huy giá trị di sản
    # văn hóa" inside Lịch sử 10 under Thông tư 32/2018 is reflected in the
    # repo's own GDPT-2018-aligned curriculum catalog (unit UNIT_GRADE_10_HUE_03).
    CurriculumAnchor(
        anchor_code="LS10-CHUYENDE-BAO_TON_DI_SAN",
        grade=10,
        competency_ref="P10-LOCAL-chuyen-de-bao-ton-di-san",
        source_citation=CITATION_TT32
        + "; data/imperial/curriculum_units_gdpt2018_hue.json UNIT_GRADE_10_HUE_03",
        confidence_status="documented",
    ),
    # Grade-11 local-education unit on Minh Mạng institutional reform and Huế
    # epigraphy (catalog unit UNIT_GRADE_11_HUE_04, Công văn 5512 framing).
    CurriculumAnchor(
        anchor_code="GDDP11-DI_SAN_HUE_VAN_KHAC",
        grade=11,
        competency_ref="P10-LOCAL-gddp-di-san-hue",
        source_citation=CITATION_CV5512
        + "; data/imperial/curriculum_units_gdpt2018_hue.json UNIT_GRADE_11_HUE_04",
        confidence_status="documented",
    ),
    # The four standard GDPT-2018 history competencies codified repo-wide
    # (backend STANDARD_GDPT_COMPETENCIES). Their existence in the GDPT 2018
    # History curriculum (Tìm hiểu lịch sử / Tư duy lịch sử / etc.) is public;
    # the exact official numeraire must still be re-checked against the Thông
    # tư text by a teacher before publication — kept as documented content,
    # local code name.
    CurriculumAnchor(
        anchor_code="GDPT2018-HIST-COMPETENCIES",
        grade=10,
        competency_ref="COMP_HIST_LITERACY|COMP_SOURCE_CRITICISM|COMP_HIST_EMPATHY|COMP_HIST_COMMUNICATION",
        source_citation=CITATION_BACKEND_CATALOG,
        confidence_status="documented",
    ),
)

# ---------------------------------------------------------------------------
# Needs-expert-review anchors — honest pending-confirmation mappings.
# Motif-category → grade → competency pairings a teacher must confirm.
# ---------------------------------------------------------------------------
CATEGORY_TO_LOCAL_TOPIC: dict[str, str] = {
    "linh_thu": "họa tiết linh thú (rồng, phượng…)",
    "dong_vat": "họa tiết động vật",
    "thao_moc": "họa tiết thực vật",
    "kien_truc": "họa tiết kiến trúc",
    "dia_ly": "họa tiết danh thắng - địa lý (sông núi, biển đảo)",
    "giao_thuong": "họa tiết giao thương (thuyền buôn, chợ búa…)",
    "nong_nghiep": "họa tiết nông nghiệp",
    "thien_van": "họa tiết thiên văn",
    "vo_bi": "họa tiết vũ khí",
}


def build_needs_review_anchors() -> tuple[CurriculumAnchor, ...]:
    """One pending anchor per (category, grade) pairing = 9 x 3 = 27.

    These encode the plausible-but-unconfirmed hypothesis that each motif
    category can carry the GDPT-2018 competency ladder at each grade. A
    teacher must confirm or reject each pairing; until then they are counted
    as needs_expert_review everywhere.
    """
    out: list[CurriculumAnchor] = []
    for category in sorted(CATEGORY_TO_LOCAL_TOPIC):
        for grade in sorted({10, 11, 12}):
            out.append(
                CurriculumAnchor(
                    anchor_code=f"P10-LOCAL-{category}-G{grade}",
                    grade=grade,
                    competency_ref="P10-LOCAL-motif-category-ladder",
                    source_citation=(
                        "Giả thuyết ánh xạ nội bộ P10 (chưa thẩm định): "
                        f"{CATEGORY_TO_LOCAL_TOPIC[category]} lớp {grade} — "
                        "cần giáo viên sử học xác nhận theo Thông tư 32/2018/TT-BGDĐT"
                    ),
                    confidence_status="needs_expert_review",
                )
            )
    return tuple(out)


def build_anchor_registry() -> dict[str, CurriculumAnchor]:
    """Frozen registry: documented anchors + pending category/grade anchors."""
    registry: dict[str, CurriculumAnchor] = {}
    for anchor in DOCUMENTED_ANCHORS + build_needs_review_anchors():
        if anchor.anchor_code in registry:
            raise P10ContractError(f"duplicate anchor code {anchor.anchor_code!r}")
        registry[anchor.anchor_code] = anchor
    return registry


def assert_anchor_known(registry: dict[str, CurriculumAnchor], anchor_code: str) -> CurriculumAnchor:
    """Fail-closed gate: unknown anchor codes are fabrication, raise loudly."""
    anchor = registry.get(anchor_code)
    if anchor is None:
        raise UnknownAnchorError(
            f"anchor_code {anchor_code!r} is not in the frozen "
            "P10 registry. Inventing a curriculum code is prohibited — either cite "
            "the GDPT 2018 document text or mark the mapping needs_expert_review "
            "with a P10-LOCAL code."
        )
    return anchor


def anchor_confidence_summary(registry: dict[str, CurriculumAnchor]) -> dict[str, int]:
    counts = {"documented": 0, "needs_expert_review": 0}
    for anchor in registry.values():
        counts[anchor.confidence_status] += 1
    return counts
