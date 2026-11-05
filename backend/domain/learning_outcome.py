# -*- coding: utf-8 -*-
"""Learning Outcome Measurement Domain (V5-T039 / Wave W03 / Slot A09).

Scaffold for source-based historical inquiry assessment tasks (pre/post/delayed)
with independent rubric scoring, ethics protocol verification, and strict isolation
from subjective self-report surveys.

Key Invariant (Negative Abuse Rule):
Subjective survey responses (e.g. Google Forms feelings, Likert satisfaction) CANNOT
produce causal learning mastery metrics. Causal mastery measurements strictly require
objective pre/post source inquiry assessments evaluated by independent rubric assessors
under an active approved ethics protocol.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Union
from uuid import UUID


# --------------------------------------------------------------------------- #
# Controlled Vocabularies
# --------------------------------------------------------------------------- #
class AssessmentPhase(str, Enum):
    pre_test = "pre_test"
    post_test = "post_test"
    delayed_test = "delayed_test"


class EthicsProtocolStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    revoked = "revoked"
    expired = "expired"


class AssessmentInstrumentType(str, Enum):
    source_inquiry_rubric = "source_inquiry_rubric"
    self_report_survey = "self_report_survey"


class InquirySubmissionStatus(str, Enum):
    submitted = "submitted"
    evaluating = "evaluating"
    evaluated = "evaluated"
    flagged = "flagged"


class PilotConsentStatus(str, Enum):
    pending = "pending"
    verified = "verified"
    withdrawn = "withdrawn"


class TeacherWorkloadCategory(str, Enum):
    optimal = "optimal"
    acceptable = "acceptable"
    excessive = "excessive"


class TeacherActivityType(str, Enum):
    preparation = "preparation"
    inquiry_instruction = "inquiry_instruction"
    rubric_grading = "rubric_grading"
    reflection = "reflection"


class RubricCalibrationStatus(str, Enum):
    calibrated = "calibrated"
    divergent_requires_review = "divergent_requires_review"


# --------------------------------------------------------------------------- #
# Standard Rubric Criteria for Historical Inquiry (S1-S4)
# --------------------------------------------------------------------------- #
DEFAULT_HISTORICAL_INQUIRY_RUBRIC: dict[str, dict[str, Any]] = {
    "S1_SPATIAL": {
        "title": "Không gian & Địa lý Lịch sử",
        "description": "Nhận diện tọa độ, địa danh, định vị các hình tượng khắc trên Cửu Đỉnh trong cảnh quan Đại Nam.",
        "max_points": 25.0,
    },
    "S2_TEMPORAL": {
        "title": "Niên đại & Diễn trình Lịch sử",
        "description": "Xác lập chuỗi thời gian, thứ tự triều đại, niên hiệu Minh Mạng và bối cảnh đúc Cửu Đỉnh (1835-1837).",
        "max_points": 25.0,
    },
    "S3_EVIDENCE": {
        "title": "Chứng cứ & Khai thác Sử liệu Gốc",
        "description": "Trích dẫn chính xác Châu bản, Khâm Định Đại Nam Hội Điển Sự Lệ, Đại Nam Thực Lục Chính Biên; đối chiếu bản dập.",
        "max_points": 25.0,
    },
    "S4_ARGUMENT": {
        "title": "Lập luận & Đánh giá Biểu tượng Văn hóa",
        "description": "Phân tích ý nghĩa biểu tượng vương quyền, tính thống nhất sơn hà, và tổng hòa tư tưởng chính trị thời Nguyễn.",
        "max_points": 25.0,
    },
}


# --------------------------------------------------------------------------- #
# Domain Exceptions
# --------------------------------------------------------------------------- #
class LearningOutcomeError(Exception):
    """Base exception for learning outcome measurement failures."""
    pass


class EthicsProtocolRequiredError(LearningOutcomeError):
    """Raised when an inquiry assessment task is run without an active approved ethics protocol."""
    pass


class SubjectiveSurveyCannotProduceCausalMetricsError(LearningOutcomeError):
    """Raised when subjective survey responses are illegally used to derive causal learning metrics."""
    pass


class IndependentAssessorRequiredError(LearningOutcomeError):
    """Raised when an assessor is not independent (e.g. Student self-grading)."""
    pass


class InvalidRubricScoreError(LearningOutcomeError):
    """Raised when rubric evaluation scores are invalid or out of bounds."""
    pass


class UnpairedAssessmentError(LearningOutcomeError):
    """Raised when pre/post assessment pairing is incomplete or misaligned."""
    pass


class GuardianConsentRequiredError(LearningOutcomeError):
    """Raised when an empirical assessment or research metric lacks verified guardian consent."""
    pass


class GuardianConsentWithdrawnError(LearningOutcomeError):
    """Raised when an empirical assessment is attempted after guardian consent has been withdrawn."""
    pass


class RubricCalibrationDivergentError(LearningOutcomeError):
    """Raised when dual independent evaluations exceed maximum acceptable scoring divergence."""
    pass


# --------------------------------------------------------------------------- #
# Domain Invariant Checks & Calculators
# --------------------------------------------------------------------------- #
def verify_causal_learning_eligibility(
    instrument_type: Union[str, AssessmentInstrumentType],
    is_subjective_self_report: bool = False,
) -> None:
    """Enforce negative abuse invariant: Survey feelings cannot produce causal learning metrics.

    Raises:
        SubjectiveSurveyCannotProduceCausalMetricsError: If survey data or subjective
        self-report instruments are supplied.
    """
    type_str = instrument_type.value if isinstance(instrument_type, AssessmentInstrumentType) else str(instrument_type)
    if is_subjective_self_report or type_str == AssessmentInstrumentType.self_report_survey.value:
        raise SubjectiveSurveyCannotProduceCausalMetricsError(
            "Subjective survey responses (self-reported feelings or Likert scale satisfaction) "
            "cannot produce causal learning mastery metrics. Causal mastery measurements strictly "
            "require objective pre/post source-based inquiry assessments evaluated by independent rubric assessors."
        )


def validate_ethics_protocol_active(
    status: Union[str, EthicsProtocolStatus],
    valid_until: Optional[datetime] = None,
) -> None:
    """Validate that an ethics protocol is approved and has not expired."""
    status_str = status.value if isinstance(status, EthicsProtocolStatus) else str(status)
    if status_str != EthicsProtocolStatus.approved.value:
        raise EthicsProtocolRequiredError(
            f"Source-based inquiry assessments require an approved ethics protocol. Current status: '{status_str}'."
        )
    if valid_until is not None:
        now = datetime.now(timezone.utc)
        # Ensure timezone-aware comparison
        target_valid = valid_until if valid_until.tzinfo else valid_until.replace(tzinfo=timezone.utc)
        if target_valid < now:
            raise EthicsProtocolRequiredError(
                f"Ethics protocol expired on {valid_until.isoformat()}. Active protocol required."
            )


def validate_assessor_independence(student_id: UUID, assessor_id: UUID) -> None:
    """Validate that the assessor is independent of the student."""
    if student_id == assessor_id:
        raise IndependentAssessorRequiredError(
            f"Assessor {assessor_id} cannot evaluate their own inquiry submission. "
            "Independent assessment is mandatory for objective learning measurement."
        )


def validate_rubric_scores(
    rubric_schema: dict[str, Any],
    criteria_scores: dict[str, float],
) -> float:
    """Validate that criterion scores are within valid ranges and calculate total score.

    Returns:
        float: Total score across all criteria.
    Raises:
        InvalidRubricScoreError: If scores are negative, exceed max points, or invalid criteria exist.
    """
    if not criteria_scores:
        raise InvalidRubricScoreError("Evaluation must contain scores for rubric criteria.")

    schema = rubric_schema or DEFAULT_HISTORICAL_INQUIRY_RUBRIC
    total = 0.0

    for criterion, points in criteria_scores.items():
        if criterion not in schema:
            raise InvalidRubricScoreError(f"Unknown rubric criterion: '{criterion}'. Allowed: {list(schema.keys())}.")
        try:
            points_num = float(points)
        except (ValueError, TypeError):
            raise InvalidRubricScoreError(f"Criterion score for '{criterion}' must be numeric.")

        max_pts = float(schema[criterion].get("max_points", 25.0))
        if points_num < 0.0 or points_num > max_pts:
            raise InvalidRubricScoreError(
                f"Criterion '{criterion}' score {points_num} is out of bounds [0.0, {max_pts}]."
            )
        total += points_num

    return round(total, 2)


def calculate_normalized_learning_gain(
    pre_score: float,
    post_score: float,
    max_score: float = 100.0,
) -> float:
    """Calculate Hake's normalized learning gain: g = (post - pre) / (max - pre).

    Handles boundary conditions:
    - If pre == max: returns 0.0 if post == max else -1.0.
    - If post < pre: returns negative relative drop: (post - pre) / pre.
    """
    pre = float(pre_score)
    post = float(post_score)
    max_s = float(max_score)

    if max_s <= 0.0:
        return 0.0

    if post >= pre:
        denom = max_s - pre
        if denom <= 0.0:
            return 0.0 if post >= max_s else -1.0
        gain = (post - pre) / denom
        return round(min(1.0, max(0.0, gain)), 4)
    else:
        # Negative gain
        if pre <= 0.0:
            return 0.0
        neg_gain = (post - pre) / pre
        return round(max(-1.0, neg_gain), 4)


def calculate_effect_size_cohens_d(
    pre_scores: list[float],
    post_scores: list[float],
) -> float:
    """Calculate paired Cohen's d effect size: d = mean(diff) / sd(diff)."""
    if len(pre_scores) != len(post_scores) or len(pre_scores) < 2:
        return 0.0

    diffs = [float(p) - float(b) for b, p in zip(pre_scores, post_scores)]
    n = len(diffs)
    mean_diff = sum(diffs) / n

    variance = sum((x - mean_diff) ** 2 for x in diffs) / (n - 1)
    if variance <= 1e-9:
        return 0.0
    sd_diff = math.sqrt(variance)
    return round(mean_diff / sd_diff, 4)


def calculate_inter_rater_reliability(
    score_a: float,
    score_b: float,
    max_score: float = 100.0,
) -> float:
    """Calculate inter-rater agreement between two independent evaluators [0.0, 1.0]."""
    if max_score <= 0.0:
        return 1.0
    diff = abs(float(score_a) - float(score_b))
    agreement = max(0.0, 1.0 - (diff / max_score))
    return round(agreement, 4)


def calculate_teacher_workload_category(
    minutes_spent: float,
    submissions_count: int = 0,
    cognitive_load_rating: float = 50.0,
) -> str:
    """Categorize teacher workload based on time per submission and cognitive load.
    
    Standards:
    - Optimal: <= 8 min/submission, cognitive load < 40, or total admin <= 60 min.
    - Acceptable: 8-15 min/submission, cognitive load 40-70.
    - Excessive: > 15 min/submission, cognitive load > 70, or total admin > 120 min.
    """
    mins = max(0.0, float(minutes_spent))
    count = max(0, int(submissions_count))
    c_load = max(0.0, min(100.0, float(cognitive_load_rating)))

    if c_load > 70.0:
        return TeacherWorkloadCategory.excessive.value

    if count > 0:
        mins_per_sub = mins / count
        if mins_per_sub > 15.0:
            return TeacherWorkloadCategory.excessive.value
        elif mins_per_sub >= 8.0 or c_load >= 40.0:
            return TeacherWorkloadCategory.acceptable.value
        else:
            return TeacherWorkloadCategory.optimal.value
    else:
        if mins > 120.0:
            return TeacherWorkloadCategory.excessive.value
        elif mins >= 60.0 or c_load >= 40.0:
            return TeacherWorkloadCategory.acceptable.value
        else:
            return TeacherWorkloadCategory.optimal.value


def calibrate_dual_rubric_scores(
    scores_a: dict[str, float],
    scores_b: dict[str, float],
    max_score: float = 100.0,
    tolerance_pct: float = 0.15,
) -> dict[str, Any]:
    """Perform calibration audit between two independent assessor evaluations.
    
    Calculates total scores, score divergence, inter-rater reliability,
    and returns whether the evaluations meet calibration standards.
    """
    total_a = round(sum(float(v) for v in scores_a.values()), 2)
    total_b = round(sum(float(v) for v in scores_b.values()), 2)
    max_s = max(1.0, float(max_score))

    diff = round(abs(total_a - total_b), 2)
    divergence_pct = round(diff / max_s, 4)
    agreement = calculate_inter_rater_reliability(total_a, total_b, max_s)

    is_calibrated = divergence_pct <= float(tolerance_pct)
    status = (
        RubricCalibrationStatus.calibrated.value
        if is_calibrated
        else RubricCalibrationStatus.divergent_requires_review.value
    )
    consensus = round((total_a + total_b) / 2.0, 2) if is_calibrated else None

    # Criteria breakdown
    all_criteria = sorted(set(list(scores_a.keys()) + list(scores_b.keys())))
    breakdown = {}
    for crit in all_criteria:
        ca = float(scores_a.get(crit, 0.0))
        cb = float(scores_b.get(crit, 0.0))
        breakdown[crit] = {
            "score_a": ca,
            "score_b": cb,
            "difference": round(abs(ca - cb), 2),
        }

    return {
        "score_a": total_a,
        "score_b": total_b,
        "score_difference": diff,
        "divergence_pct": divergence_pct,
        "inter_rater_agreement": agreement,
        "tolerance_pct": tolerance_pct,
        "status": status,
        "consensus_score": consensus,
        "criteria_breakdown": breakdown,
    }


def verify_guardian_consent_status(
    consent_status: Optional[str],
    participant_consent_required: bool = True,
) -> None:
    """Verify that participant has valid guardian consent when required.
    
    Raises:
        GuardianConsentWithdrawnError: If consent was previously withdrawn.
        GuardianConsentRequiredError: If consent is missing, pending, or unverified.
    """
    if not participant_consent_required:
        return

    status = (consent_status or "").strip().lower()
    if status == PilotConsentStatus.withdrawn.value:
        raise GuardianConsentWithdrawnError(
            "Guardian informed consent has been withdrawn for this participant. Research participation is suspended."
        )
    if status != PilotConsentStatus.verified.value:
        raise GuardianConsentRequiredError(
            f"Participant requires verified guardian consent for empirical research. Current status: '{status or 'missing'}'."
        )


def verify_learning_improvement_claim_basis(
    claim_type: str,
    evidence_basis: str,
) -> None:
    """Enforce negative abuse invariant:
    
    Results based solely on subjective sentiment, feelings, or satisfaction surveys
    CANNOT be labeled as evidence of learning improvement.
    
    Raises:
        SubjectiveSurveyCannotProduceCausalMetricsError: If subjective basis is used.
    """
    claim = (claim_type or "").strip().lower()
    basis = (evidence_basis or "").strip().lower()

    learning_claim_types = {
        "learning_improvement",
        "causal_mastery",
        "learning_gain",
        "evidence_of_learning",
        "academic_growth",
    }
    subjective_bases = {
        "subjective_survey",
        "sentiment_analysis",
        "feelings_survey",
        "likert_scale",
        "satisfaction_rating",
        "self_report_survey",
        "google_forms_feelings",
    }

    if claim in learning_claim_types and basis in subjective_bases:
        raise SubjectiveSurveyCannotProduceCausalMetricsError(
            f"Results based solely on subjective sentiment or feelings surveys ('{evidence_basis}') "
            f"cannot be labeled as evidence of learning improvement ('{claim_type}'). "
            "Authoritative learning improvement evidence strictly requires objective pre/post source inquiry "
            "assessments evaluated by independent calibrated rubric assessors."
        )
