"""Curriculum Crosswalk & Anchor Registry for Study LN-01.

Theory: Constructive Alignment; Spiral Curriculum (Bruner); Historical Reasoning.
Curriculum scope: GDĐP Thừa Thiên Huế (Khối 10, 11, 12).
Heritage context: Cửu Đỉnh - Minh Mạng - Quần thể di tích Cố đô Huế.

Pedagogical Invariants:
- INV-LN-01-03: No GDĐP relation can be formed without a verified curriculum version
  and authorized curriculum anchor.
- INV-LN-01-05: Learning resources used across grades must maintain provenance
  and rights status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


CURRICULUM_VERSION_DEFAULT = "CT-GDPT-2018-HUE"
LEGAL_SOURCE_DEFAULT = (
    "Chương trình GDPT 2018 (Thông tư 32/2018/TT-BGDĐT & Công văn 5512/BGDĐT-GDTrH)"
)


@dataclass(frozen=True)
class CurriculumAnchor:
    """Represents a regulatory curriculum requirement and outcome anchor."""

    id: str
    curriculum_version: str
    grade: int
    competency_code: str
    description: str
    approval_status: str = "approved"
    legal_source: str = LEGAL_SOURCE_DEFAULT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "curriculum_version": self.curriculum_version,
            "grade": self.grade,
            "competency_code": self.competency_code,
            "description": self.description,
            "approval_status": self.approval_status,
            "legal_source": self.legal_source,
        }


# Standard authorized GDĐP anchors for Thừa Thiên Huế high schools
STANDARD_GDDP_ANCHORS: Dict[str, CurriculumAnchor] = {
    "GDĐP-HUE-10-ART": CurriculumAnchor(
        id="GDĐP-HUE-10-ART",
        curriculum_version=CURRICULUM_VERSION_DEFAULT,
        grade=10,
        competency_code="S1_SPATIAL",
        description="Quan sát, nhận diện và mô tả mỹ thuật hoa văn bản đúc nổi trên Cửu Đỉnh và kiến trúc Đại Nội.",
    ),
    "GDĐP-HUE-11-HISTORY": CurriculumAnchor(
        id="GDĐP-HUE-11-HISTORY",
        curriculum_version=CURRICULUM_VERSION_DEFAULT,
        grade=11,
        competency_code="S2_TEMPORAL",
        description="Đối chiếu tư liệu chính sử triều Nguyễn về bối cảnh đúc Cửu Đỉnh dưới thời hoàng đế Minh Mạng.",
    ),
    "GDĐP-HUE-12-HERITAGE": CurriculumAnchor(
        id="GDĐP-HUE-12-HERITAGE",
        curriculum_version=CURRICULUM_VERSION_DEFAULT,
        grade=12,
        competency_code="S4_ARGUMENT",
        description="Đánh giá giá trị di sản, luận giải giải pháp bảo tồn và phát huy giá trị di sản Quần thể Cố đô Huế.",
    ),
}


def check_anchor_coverage(
    nodes: List[Dict[str, Any]],
    anchors: Dict[str, Any],
) -> Tuple[bool, List[int], float]:
    """Check if all grades present in nodes have an authorized curriculum anchor.

    Returns:
        (is_complete, missing_grades, unmapped_outcome_rate)
    """
    if not nodes:
        return True, [], 0.0

    referenced_grades = sorted({int(n.get("grade", 0)) for n in nodes if n.get("grade") is not None})
    missing_grades: List[int] = []

    for g in referenced_grades:
        key = f"grade{g}"
        anchor_val = anchors.get(key)
        if not anchor_val:
            missing_grades.append(g)

    total = len(referenced_grades)
    unmapped_count = len(missing_grades)
    unmapped_rate = round(unmapped_count / total, 4) if total > 0 else 0.0
    is_complete = unmapped_count == 0

    return is_complete, missing_grades, unmapped_rate
