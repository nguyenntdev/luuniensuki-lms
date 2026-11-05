# -*- coding: utf-8 -*-
"""Instructional Recommendations & Teacher Decision Support Domain (LN-09).

Theory: Learning analytics; teacher orchestration; formative assessment.
Curriculum: GDĐP Lớp 12 - Chủ đề Di sản văn hóa Cố đô Huế (Đại Nội, Cửu Đỉnh).

Pedagogical Invariants:
- INV-LN-09-01: Không suy ra người học kém từ dữ liệu thiếu (Missing logs => abstain_missing_evidence).
- INV-LN-09-02: Khuyến nghị có căn cứ phải truy ngược được tới nhiệm vụ và yêu cầu cần đạt (Unverified task => abstain_unverified_source).
- INV-LN-09-03: Gợi ý không tự động thành điểm hay hoạt động bắt buộc nếu giáo viên chưa chấp thuận (Teacher override required).
- INV-LN-09-04: Không dùng tên thật và điểm thật trong báo cáo benchmark synthetic (k-anonymity privacy protection).
- INV-LN-09-05: Điều kiện mâu thuẫn tín hiệu và không đủ dữ liệu phải được hiển thị tường minh, không ẩn (Conflicting signals => abstain_conflict).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


# --------------------------------------------------------------------------- #
# Controlled Vocabularies
# --------------------------------------------------------------------------- #
class DecisionCode(str, Enum):
    propose_explained_action = "propose_explained_action"
    abstain_missing_evidence = "abstain_missing_evidence"
    abstain_conflict = "abstain_conflict"
    abstain_unverified_source = "abstain_unverified_source"
    request_refresh = "request_refresh"
    descriptive_summary_only = "descriptive_summary_only"


class ReasonCode(str, Enum):
    nominal = "nominal"
    missing_logs = "missing_logs"
    conflicting_signals = "conflicting_signals"
    unverified_task = "unverified_task"
    stale_mastery = "stale_mastery"
    k_anonymity_violation = "k_anonymity_violation"
    unsupported_intervention = "unsupported_intervention"
    descriptive_only_no_action = "descriptive_only_no_action"
    teacher_rejected = "teacher_rejected"
    teacher_accepted = "teacher_accepted"
    teacher_modified = "teacher_modified"


class CompetencyArea(str, Enum):
    S1_SPATIAL = "spatial"
    S2_TEMPORAL = "temporal"
    S3_EVIDENCE = "evidence_use"
    S4_ARGUMENT = "argument"


class TeacherOverrideStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    modified = "modified"


# --------------------------------------------------------------------------- #
# Pedagogical Action Catalog (Curriculum-anchored)
# --------------------------------------------------------------------------- #
INSTRUCTIONAL_ACTION_CATALOG: Dict[str, Dict[str, Any]] = {
    "additional_source_comparison_activity": {
        "id": "ACT-REC-S3-SOURCE-COMPARISON",
        "action_type": "additional_source_comparison_activity",
        "competency": CompetencyArea.S3_EVIDENCE.value,
        "title": "Hoạt động đọc và đối chiếu tư liệu sử liệu gốc",
        "objective": "Đọc, đối chiếu và thẩm định tư liệu sử liệu gốc (Châu bản, Đại Nam Thực Lục) về di tích Huế",
        "curriculum_anchor_id": "GDDP12-HUE-HERITAGE-SOURCE-S3",
        "prerequisites": ["Đọc hiểu văn bản sử liệu sơ cấp", "Nhận diện thể loại tài liệu"],
        "resources": [
            "Châu bản triều Nguyễn (tờ dụ năm Minh Mạng 17)",
            "Đại Nam Thực Lục Chính Biên Đệ Nhị Kỷ",
            "Bản dập hoa văn Cửu Đỉnh (ban-duc-noi)",
        ],
        "remedial_trigger": "evidence_use <= 0.5",
    },
    "additional_spatial_orientation_activity": {
        "id": "ACT-REC-S1-SPATIAL-ORIENTATION",
        "action_type": "additional_spatial_orientation_activity",
        "competency": CompetencyArea.S1_SPATIAL.value,
        "title": "Hoạt động định vị không gian và sa bàn di tích",
        "objective": "Định vị không gian và phân tích bố cục phong thủy trục Ngọ Môn - Điện Thái Hòa",
        "curriculum_anchor_id": "GDDP12-HUE-HERITAGE-SPATIAL-S1",
        "prerequisites": ["Đọc bản đồ Hoàng thành", "Nhận diện các công trình chính trục Dũng Đạo"],
        "resources": [
            "Bản đồ Hoàng thành Huế thời Nguyễn",
            "Mô hình 3D Ngọ Môn và sân Đại Triều Nghi",
        ],
        "remedial_trigger": "spatial <= 0.5",
    },
    "additional_chronology_exercise": {
        "id": "ACT-REC-S2-CHRONOLOGY",
        "action_type": "additional_chronology_exercise",
        "competency": CompetencyArea.S2_TEMPORAL.value,
        "title": "Hoạt động sắp xếp niên biểu và diễn trình lịch sử",
        "objective": "Hệ thống hóa niên biểu và sự kiện lịch sử qua các triều vua Nguyễn tại Cố đô Huế",
        "curriculum_anchor_id": "GDDP12-HUE-HERITAGE-CHRONOLOGY-S2",
        "prerequisites": ["Niên hiệu các vua triều Nguyễn"],
        "resources": [
            "Khâm Định Đại Nam Hội Điển Sự Lệ",
            "Bảng đối chiếu niên hiệu - tây lịch",
        ],
        "remedial_trigger": "temporal <= 0.5",
    },
    "additional_argumentation_workshop": {
        "id": "ACT-REC-S4-ARGUMENTATION",
        "action_type": "additional_argumentation_workshop",
        "competency": CompetencyArea.S4_ARGUMENT.value,
        "title": "Hoạt động xây dựng lập luận lịch sử dựa trên chứng cứ",
        "objective": "Xây dựng lập luận lịch sử và giải thích ý nghĩa biểu tượng của di sản văn hóa Huế",
        "curriculum_anchor_id": "GDDP12-HUE-HERITAGE-ARGUMENT-S4",
        "prerequisites": ["Phương pháp lập luận sử học M-E-E"],
        "resources": [
            "Hồ sơ Di sản Thế giới Quần thể Di tích Cố đô Huế",
            "Bài tham luận khoa học về Cửu Đỉnh Huế",
        ],
        "remedial_trigger": "argument <= 0.5",
    },
}


# --------------------------------------------------------------------------- #
# Domain Models
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class LearningSignal:
    outcome: str
    score: float
    type: str
    verified: bool
    timestamp: Optional[str] = None

    def is_valid(self) -> bool:
        return 0.0 <= self.score <= 1.0 and bool(self.outcome) and bool(self.type)


@dataclass(frozen=True)
class PedagogicalNeed:
    competency: str
    confidence: float
    missing_information: bool
    diagnosis_summary: str


@dataclass(frozen=True)
class TeachingAction:
    id: str
    action_type: str
    objective: str
    curriculum_anchor_id: str
    prerequisites: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DecisionSupportCard:
    decision: str
    action: Optional[TeachingAction]
    rationale: str
    evidence_ids: List[str]
    limitations: List[str]
    k_anonymity_satisfied: bool
    data_freshness_days: int
    reason_codes: List[str]
    action_proposed: bool
    abstention_appropriate: bool
    intervention_traceable: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "action": (
                {
                    "id": self.action.id,
                    "action_type": self.action.action_type,
                    "objective": self.action.objective,
                    "curriculum_anchor_id": self.action.curriculum_anchor_id,
                    "prerequisites": list(self.action.prerequisites),
                    "resources": list(self.action.resources),
                }
                if self.action
                else None
            ),
            "rationale": self.rationale,
            "evidence_ids": list(self.evidence_ids),
            "limitations": list(self.limitations),
            "k_anonymity_satisfied": self.k_anonymity_satisfied,
            "data_freshness_days": self.data_freshness_days,
            "reason_codes": list(self.reason_codes),
            "action_proposed": self.action_proposed,
            "abstention_appropriate": self.abstention_appropriate,
            "intervention_traceable": self.intervention_traceable,
        }


@dataclass
class TeacherOverride:
    recommendation_id: str
    teacher_id: str
    status: TeacherOverrideStatus
    override_reason: str
    modified_action: Optional[Dict[str, Any]] = None

    def apply(self, card: DecisionSupportCard) -> DecisionSupportCard:
        if self.status == TeacherOverrideStatus.rejected:
            return DecisionSupportCard(
                decision=DecisionCode.descriptive_summary_only.value,
                action=None,
                rationale=f"Giáo viên từ chối gợi ý: {self.override_reason}",
                evidence_ids=card.evidence_ids,
                limitations=card.limitations,
                k_anonymity_satisfied=card.k_anonymity_satisfied,
                data_freshness_days=card.data_freshness_days,
                reason_codes=[ReasonCode.teacher_rejected.value],
                action_proposed=False,
                abstention_appropriate=True,
                intervention_traceable=False,
            )
        elif self.status == TeacherOverrideStatus.accepted:
            return DecisionSupportCard(
                decision=card.decision,
                action=card.action,
                rationale=f"{card.rationale} (Đã được giáo viên phê duyệt: {self.override_reason})",
                evidence_ids=card.evidence_ids,
                limitations=card.limitations,
                k_anonymity_satisfied=card.k_anonymity_satisfied,
                data_freshness_days=card.data_freshness_days,
                reason_codes=card.reason_codes + [ReasonCode.teacher_accepted.value],
                action_proposed=card.action_proposed,
                abstention_appropriate=card.abstention_appropriate,
                intervention_traceable=card.intervention_traceable,
            )
        elif self.status == TeacherOverrideStatus.modified and self.modified_action:
            new_action = TeachingAction(
                id=self.modified_action.get("id", "MODIFIED-ACTION"),
                action_type=self.modified_action.get("action_type", "custom_action"),
                objective=self.modified_action.get("objective", "Tùy biến bởi giáo viên"),
                curriculum_anchor_id=self.modified_action.get(
                    "curriculum_anchor_id", "GDDP12-TEACHER-CUSTOM"
                ),
                prerequisites=self.modified_action.get("prerequisites", []),
                resources=self.modified_action.get("resources", []),
            )
            return DecisionSupportCard(
                decision=card.decision,
                action=new_action,
                rationale=f"Giáo viên điều chỉnh can thiệp: {self.override_reason}",
                evidence_ids=card.evidence_ids,
                limitations=card.limitations,
                k_anonymity_satisfied=card.k_anonymity_satisfied,
                data_freshness_days=card.data_freshness_days,
                reason_codes=card.reason_codes + [ReasonCode.teacher_modified.value],
                action_proposed=True,
                abstention_appropriate=card.abstention_appropriate,
                intervention_traceable=True,
            )
        return card


# --------------------------------------------------------------------------- #
# Verification and Rule Checking Functions
# --------------------------------------------------------------------------- #
def check_data_freshness(observation_age_days: int, max_staleness_days: int = 30) -> bool:
    """Verify data is fresh enough for pedagogical decision making."""
    return observation_age_days <= max_staleness_days


def check_signal_consistency(signals_conflict: bool) -> bool:
    """Verify there are no unresolved contradictory signals."""
    return not signals_conflict


def check_evidence_verification(learning_evidence: List[Dict[str, Any]]) -> bool:
    """Verify that all evidence comes from validated assessment tasks."""
    if not learning_evidence:
        return False
    return all(bool(ev.get("verified", False)) for ev in learning_evidence)


def check_k_anonymity(cohort_size: Optional[int] = None, k_threshold: int = 5) -> bool:
    """Enforce k-anonymity privacy protection (n >= k) when reporting group metrics."""
    if cohort_size is None:
        # Single learner synthetic scenario with anonymized profile satisfies privacy
        return True
    return cohort_size >= k_threshold


# --------------------------------------------------------------------------- #
# Pedagogical Diagnostic & Recommendation Evaluation
# --------------------------------------------------------------------------- #
def evaluate_instructional_recommendation(
    scenario_input: Dict[str, Any],
    *,
    max_staleness_days: int = 30,
    k_threshold: int = 5,
    allow_unverified: bool = False,
    allow_conflicts: bool = False,
    allow_stale: bool = False,
    descriptive_only: bool = False,
    include_rationale: bool = True,
) -> DecisionSupportCard:
    """Evaluate learning analytics signals to produce an explainable instructional recommendation

    or an explicit, justified abstention.
    """
    evidence_list = scenario_input.get("learning_evidence") or []
    age_days = scenario_input.get("observation_age_days", 0)
    conflict = bool(scenario_input.get("signals_conflict", False))
    candidate = scenario_input.get("candidate_intervention") or "additional_source_comparison_activity"
    cohort_size = scenario_input.get("cohort_size")

    # K-anonymity check
    k_ok = check_k_anonymity(cohort_size, k_threshold)
    if not k_ok:
        return DecisionSupportCard(
            decision=DecisionCode.abstain_missing_evidence.value,
            action=None,
            rationale="Cỡ mẫu nhóm người học nhỏ hơn ngưỡng bảo mật k-anonymity (n < 5). Từ chối tạo khuyến nghị.",
            evidence_ids=[],
            limitations=["K-anonymity threshold not met"],
            k_anonymity_satisfied=False,
            data_freshness_days=age_days,
            reason_codes=[ReasonCode.k_anonymity_violation.value],
            action_proposed=False,
            abstention_appropriate=True,
            intervention_traceable=False,
        )

    # Descriptive-only mode (Ablation 1)
    if descriptive_only:
        return DecisionSupportCard(
            decision=DecisionCode.descriptive_summary_only.value,
            action=None,
            rationale="Chế độ báo cáo mô tả: chỉ hiển thị tiến độ và điểm số hiện có, không đề xuất can thiệp dạy học.",
            evidence_ids=[f"ev_{i}" for i in range(len(evidence_list))],
            limitations=["Descriptive-only mode active"],
            k_anonymity_satisfied=k_ok,
            data_freshness_days=age_days,
            reason_codes=[ReasonCode.descriptive_only_no_action.value],
            action_proposed=False,
            abstention_appropriate=False,
            intervention_traceable=False,
        )

    # Rule 1: Missing Evidence / Missing Logs (INV-LN-09-01)
    # Không suy ra người học kém từ dữ liệu thiếu
    if not evidence_list:
        return DecisionSupportCard(
            decision=DecisionCode.abstain_missing_evidence.value,
            action=None,
            rationale=(
                "Không đủ dữ liệu học tập hoặc nhật ký LMS để chẩn đoán năng lực. "
                "Hệ thống từ chối kết luận người học yếu kém khi chưa có minh chứng nộp bài."
            ),
            evidence_ids=[],
            limitations=["Không có bản ghi hoạt động học tập nào"],
            k_anonymity_satisfied=k_ok,
            data_freshness_days=age_days,
            reason_codes=[ReasonCode.missing_logs.value],
            action_proposed=False,
            abstention_appropriate=True,
            intervention_traceable=False,
        )

    # Rule 2: Conflicting Signals (INV-LN-09-05)
    # Tín hiệu mâu thuẫn không thể tự động phân giải
    if conflict and not allow_conflicts:
        return DecisionSupportCard(
            decision=DecisionCode.abstain_conflict.value,
            action=None,
            rationale=(
                "Phát hiện dấu hiệu học tập mâu thuẫn giữa các bài tập hoặc nhiệm vụ độc lập. "
                "Cần giáo viên trực tiếp trao đổi và quan sát trước khi áp dụng can thiệp."
            ),
            evidence_ids=[f"ev_{i}" for i in range(len(evidence_list))],
            limitations=["Dấu hiệu đánh giá mâu thuẫn nhau chưa thể phân giải thuật toán"],
            k_anonymity_satisfied=k_ok,
            data_freshness_days=age_days,
            reason_codes=[ReasonCode.conflicting_signals.value],
            action_proposed=False,
            abstention_appropriate=True,
            intervention_traceable=False,
        )

    # Rule 3: Unverified Tasks / Unreliable Sources (INV-LN-09-02)
    # Điểm nhiệm vụ không đủ độ tin cậy hoặc chưa kiểm định
    has_unverified = any(not ev.get("verified", False) for ev in evidence_list)
    if has_unverified and not allow_unverified:
        return DecisionSupportCard(
            decision=DecisionCode.abstain_unverified_source.value,
            action=None,
            rationale=(
                "Nhiệm vụ hoặc câu hỏi đánh giá chưa được kiểm định nguồn sử liệu và độ tin cậy đo lường. "
                "Từ chối gợi ý can thiệp để tránh sai lệch sư phạm."
            ),
            evidence_ids=[f"ev_{i}" for i, ev in enumerate(evidence_list) if not ev.get("verified")],
            limitations=["Bằng chứng học tập bắt nguồn từ nhiệm vụ chưa kiểm định"],
            k_anonymity_satisfied=k_ok,
            data_freshness_days=age_days,
            reason_codes=[ReasonCode.unverified_task.value],
            action_proposed=False,
            abstention_appropriate=True,
            intervention_traceable=False,
        )

    # Rule 4: Stale Mastery / Outdated Evidence
    # Điểm năng lực đã cũ cần yêu cầu làm mới
    is_stale = not check_data_freshness(age_days, max_staleness_days)
    if is_stale and not allow_stale:
        return DecisionSupportCard(
            decision=DecisionCode.request_refresh.value,
            action=None,
            rationale=(
                f"Dữ liệu quan sát đã cũ ({age_days} ngày, vượt ngưỡng cho phép {max_staleness_days} ngày). "
                "Yêu cầu giao bài kiểm tra ngắn định kỳ để làm mới trạng thái năng lực trước khi can thiệp."
            ),
            evidence_ids=[f"ev_{i}" for i in range(len(evidence_list))],
            limitations=[f"Observation age ({age_days} days) exceeds staleness threshold ({max_staleness_days} days)"],
            k_anonymity_satisfied=k_ok,
            data_freshness_days=age_days,
            reason_codes=[ReasonCode.stale_mastery.value],
            action_proposed=False,
            abstention_appropriate=True,
            intervention_traceable=False,
        )

    # Rule 5: Nominal / Actionable Recommendation
    # Tín hiệu có đủ nguồn, tươi mới, nhất quán và có thể hành động
    catalog_entry = INSTRUCTIONAL_ACTION_CATALOG.get(candidate)
    if not catalog_entry:
        catalog_entry = {
            "id": f"ACT-CUSTOM-{candidate.upper()}",
            "action_type": candidate,
            "competency": CompetencyArea.S3_EVIDENCE.value,
            "title": f"Hoạt động bổ trợ {candidate}",
            "objective": "Can thiệp sư phạm phù hợp với mục tiêu bài học di sản Huế",
            "curriculum_anchor_id": "GDDP12-HUE-HERITAGE-CUSTOM",
            "prerequisites": [],
            "resources": [],
        }

    action = TeachingAction(
        id=catalog_entry["id"],
        action_type=catalog_entry["action_type"],
        objective=catalog_entry["objective"],
        curriculum_anchor_id=catalog_entry["curriculum_anchor_id"],
        prerequisites=catalog_entry.get("prerequisites", []),
        resources=catalog_entry.get("resources", []),
    )

    rationale_text = (
        f"Đề xuất hoạt động '{action.objective}' dựa trên {len(evidence_list)} minh chứng đã kiểm định. "
        f"Mã neo chương trình GDĐP: {action.curriculum_anchor_id}."
        if include_rationale
        else ""
    )

    return DecisionSupportCard(
        decision=DecisionCode.propose_explained_action.value,
        action=action,
        rationale=rationale_text,
        evidence_ids=[f"ev_{i}" for i in range(len(evidence_list))],
        limitations=["Đề xuất mang tính chất khuyến nghị hỗ trợ giáo viên; không thay thế quyết định chuyên môn."],
        k_anonymity_satisfied=k_ok,
        data_freshness_days=age_days,
        reason_codes=[ReasonCode.nominal.value],
        action_proposed=True,
        abstention_appropriate=False,
        intervention_traceable=bool(include_rationale),
    )
