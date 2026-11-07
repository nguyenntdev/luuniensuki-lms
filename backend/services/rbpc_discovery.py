# -*- coding: utf-8 -*-
"""Customer Discovery Experiments & Anonymized Research Store for LƯU NIÊN / RBPC 2026.

Ticket: V5-T114 (Wave W11, Slot A04).
Goal:
- Customer discovery experiments in docs/rbpc/ and frontend/src/.
- Standardized interview scripts, structured usability tasks, anonymized feedback store,
  and pre-registered success criteria thresholds.
- Negative abuse invariant:
  Self-selected respondents are NOT labeled representative of general population
  without explicit, mandatory methodology disclaimer.
"""
from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class CohortType(str, Enum):
    ARTISAN_PARTNER = "artisan_partner"
    CULTURAL_TRAVELER = "cultural_traveler"
    HERITAGE_EDUCATOR = "heritage_educator"
    MUSEUM_VISITOR = "museum_visitor"
    GENERAL_PUBLIC = "general_public"


class ExperimentStatus(str, Enum):
    PRE_REGISTERED = "PRE_REGISTERED"
    IN_PROGRESS = "IN_PROGRESS"
    VALIDATED = "VALIDATED"
    FALSIFIED = "FALSIFIED"
    INCONCLUSIVE = "INCONCLUSIVE"


class SamplingMethodology(str, Enum):
    CONVENIENCE = "CONVENIENCE"
    PURPOSIVE_SELF_SELECTED = "PURPOSIVE_SELF_SELECTED"
    VOLUNTARY_OPT_IN = "VOLUNTARY_OPT_IN"
    RANDOMIZED_STRATIFIED = "RANDOMIZED_STRATIFIED"


class EvaluationOutcome(str, Enum):
    TARGET_MET = "TARGET_MET"
    INCONCLUSIVE = "INCONCLUSIVE"
    FALSIFIED = "FALSIFIED"


# PII Regex Patterns for client and server scrubbing
RE_EMAIL = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
RE_PHONE = re.compile(r"(\+?84|0)(3[2-9]|5[689]|7[06-9]|8[1-9]|9[0-9])[0-9]{7}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")
RE_IPV4 = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
RE_NAMES = re.compile(r"\b(Nguyễn|Trần|Lê|Phạm|Hoàng|Huỳnh|Phan|Vũ|Võ|Đặng|Bùi|Đỗ|Hồ|Ngô|Dương|Lý)\s+[A-ZÀ-Ỹa-zà-ỹ]+(?:\s+[A-ZÀ-Ỹa-zà-ỹ]+)?\b")


def scrub_pii(text: Optional[str]) -> Tuple[str, bool]:
    """Scrub PII (email, phone, IP, common Vietnamese full names) from qualitative text.
    
    Returns (cleaned_text, pii_detected).
    """
    if not text:
        return "", False
    
    cleaned = text
    pii_detected = False

    if RE_EMAIL.search(cleaned):
        cleaned = RE_EMAIL.sub("[EMAIL_REDACTED]", cleaned)
        pii_detected = True

    if RE_PHONE.search(cleaned):
        cleaned = RE_PHONE.sub("[PHONE_REDACTED]", cleaned)
        pii_detected = True

    if RE_IPV4.search(cleaned):
        cleaned = RE_IPV4.sub("[IP_REDACTED]", cleaned)
        pii_detected = True

    if RE_NAMES.search(cleaned):
        cleaned = RE_NAMES.sub("[NAME_REDACTED]", cleaned)
        pii_detected = True

    return cleaned, pii_detected


# Mandatory Disclaimer Clauses that must be present if claiming representativeness (supports English and Vietnamese)
REQUIRED_DISCLAIMER_KEYWORDS = {
    "sampling": [
        "convenience", "self-selected", "purposive", "non-probability", "opt-in",
        "thuận tiện", "tự nguyện", "phi xác suất", "lấy mẫu"
    ],
    "bias": [
        "selection bias", "early adopter", "tech-literate", "technologically fluent", "enthusiast",
        "độ lệch", "chọn mẫu", "đam mê", "thành thạo"
    ],
    "extrapolation": [
        "cannot be extrapolated", "not representative", "prohibition on extrapolating", "general population", "randomized stratified",
        "không thể suy rộng", "đại diện", "dân số", "phân tầng ngẫu nhiên"
    ],
}

MANDATORY_METHODOLOGY_DISCLAIMER_EN = (
    "Methodology Disclaimer: Participants in this discovery experiment were recruited via voluntary "
    "opt-in and convenience sampling (non-probability sample). The findings reflect selection bias toward "
    "technologically fluent cultural enthusiasts and early adopters, and cannot be extrapolated as "
    "statistically representative of the general population without randomized stratified sampling."
)

MANDATORY_METHODOLOGY_DISCLAIMER_VI = (
    "Tuyên bố Phương pháp luận: Người tham gia thử nghiệm khám phá khách hàng được tuyển chọn thông qua hình thức "
    "tự nguyện đăng ký và lấy mẫu thuận tiện (mẫu phi xác suất). Kết quả phản ánh độ lệch chọn mẫu hướng tới nhóm "
    "người đam mê văn hóa và thành thạo công nghệ, và không thể suy rộng thành đại diện thống kê cho toàn thể dân số "
    "nếu không có phương pháp lấy mẫu phân tầng ngẫu nhiên."
)


def validate_methodology_disclaimer(
    sample_method: SamplingMethodology | str,
    is_claimed_representative: bool,
    disclaimer_text: Optional[str],
) -> bool:
    """Validate Negative Abuse Invariant:
    Self-selected respondents are not labeled representative of general population without methodology disclaimer.

    If is_claimed_representative is True and sample is convenience/self-selected/opt-in:
    - disclaimer_text must not be empty or whitespace.
    - disclaimer_text must contain all 3 mandatory disclosure aspects:
      1) sampling method acknowledgment
      2) selection bias boundaries
      3) population extrapolation limitation
    """
    method_str = sample_method.value if isinstance(sample_method, SamplingMethodology) else str(sample_method)

    if method_str in {SamplingMethodology.CONVENIENCE.value, SamplingMethodology.PURPOSIVE_SELF_SELECTED.value, SamplingMethodology.VOLUNTARY_OPT_IN.value}:
        if is_claimed_representative:
            if not disclaimer_text or not disclaimer_text.strip():
                raise ValueError(
                    "Negative abuse invariant violation: Self-selected respondents cannot be labeled "
                    "representative of the general population without an explicit methodology disclaimer."
                )
            
            lower_text = disclaimer_text.lower()
            
            # Check clause 1: sampling methodology
            if not any(k in lower_text for k in REQUIRED_DISCLAIMER_KEYWORDS["sampling"]):
                raise ValueError(
                    "Negative abuse invariant violation: Methodology disclaimer is missing sampling methodology disclosure "
                    "(must state convenience / self-selected / opt-in / non-probability sampling)."
                )

            # Check clause 2: selection bias
            if not any(k in lower_text for k in REQUIRED_DISCLAIMER_KEYWORDS["bias"]):
                raise ValueError(
                    "Negative abuse invariant violation: Methodology disclaimer is missing selection bias disclosure "
                    "(must explicitly state selection bias boundaries e.g. early adopters or tech-literate enthusiasts)."
                )

            # Check clause 3: population extrapolation warning
            if not any(k in lower_text for k in REQUIRED_DISCLAIMER_KEYWORDS["extrapolation"]):
                raise ValueError(
                    "Negative abuse invariant violation: Methodology disclaimer is missing extrapolation limitation "
                    "(must explicitly prohibit extrapolating to general population without randomized stratified sampling)."
                )
    return True


@dataclass(frozen=True)
class DiscoveryInterviewQuestion:
    question_id: str
    prompt_vi: str
    prompt_en: str
    objective: str
    category: str
    follow_up_probes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DiscoveryInterviewScript:
    script_id: str
    title: str
    cohort: CohortType
    target_sample_size: str
    purpose: str
    questions: List[DiscoveryInterviewQuestion] = field(default_factory=list)


@dataclass(frozen=True)
class DiscoveryUsabilityTask:
    task_id: str
    title: str
    target_cohort: CohortType
    scenario: str
    steps: List[str]
    max_dwell_seconds: int
    success_criterion: str
    zero_upfront_check: bool = False


@dataclass(frozen=True)
class DiscoveryExperiment:
    experiment_id: str
    title: str
    hypothesis: str
    target_cohort: CohortType
    metric_name: str
    formula: str
    target_threshold: float
    falsification_trigger: float
    comparison_operator: str  # ">=" or "<="
    status: ExperimentStatus
    sample_size_target: int
    notes: str


@dataclass
class AnonymizedFeedbackRecord:
    record_id: str
    participant_token: str
    cohort: CohortType
    task_or_script_id: str
    task_completed: bool
    dwell_seconds: Optional[int] = None
    rating_likert: Optional[int] = None  # 1-5 scale
    qualitative_feedback: Optional[str] = None
    consent_accepted: bool = False
    consent_version: str = "rbpc-discovery-v1"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_self_selected: bool = True

    def validate(self) -> None:
        """Validate feedback record integrity and zero-PII guarantee."""
        if not self.consent_accepted:
            raise ValueError(f"Consent rejected: participant '{self.participant_token}' has not accepted research consent.")
        if self.consent_version != "rbpc-discovery-v1":
            raise ValueError(f"Invalid consent version '{self.consent_version}', expected 'rbpc-discovery-v1'.")
        
        # Validate anonymous token format (e.g. FIT-A1B2, ART-1234, EDU-9X8Y)
        if not re.match(r"^[A-Z]{2,4}-[A-Z0-9]{4,8}$", self.participant_token):
            raise ValueError(
                f"Invalid pseudo-anonymized token '{self.participant_token}'. "
                "Must follow token pattern e.g. 'FIT-A1B2', 'ART-001', 'EDU-44X8'."
            )
        
        if self.rating_likert is not None and not (1 <= self.rating_likert <= 5):
            raise ValueError(f"Likert rating {self.rating_likert} out of bounds (must be 1-5).")

        # Ensure no unscrubbed PII remains in qualitative feedback
        if self.qualitative_feedback:
            cleaned, detected = scrub_pii(self.qualitative_feedback)
            if detected:
                # auto-scrub in place
                self.qualitative_feedback = cleaned


@dataclass
class DiscoveryFindingReport:
    report_id: str
    title: str
    sample_methodology: SamplingMethodology
    sample_size: int
    is_claimed_representative: bool
    methodology_disclaimer: Optional[str]
    key_findings: List[str]
    experiment_evaluations: Dict[str, Any] = field(default_factory=dict)
    date_published: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    def validate(self) -> None:
        validate_methodology_disclaimer(
            sample_method=self.sample_methodology,
            is_claimed_representative=self.is_claimed_representative,
            disclaimer_text=self.methodology_disclaimer,
        )


# =========================================================================
# Canonical Pre-Registered Discovery Experiments (EXP-01 to EXP-05)
# =========================================================================
CANONICAL_EXPERIMENTS: List[DiscoveryExperiment] = [
    DiscoveryExperiment(
        experiment_id="EXP-01",
        title="Inquiry Transparency & Upfront Charge Friction",
        hypothesis="Transparent inquiry copy ('Send Booking Request', 0 VND upfront) produces higher completion than instant checkout.",
        target_cohort=CohortType.CULTURAL_TRAVELER,
        metric_name="Form Completion Rate",
        formula="Completed Submissions / Form Starts",
        target_threshold=65.0,  # >= 65.0%
        falsification_trigger=45.0,  # < 45.0%
        comparison_operator=">=",
        status=ExperimentStatus.PRE_REGISTERED,
        sample_size_target=30,
        notes="Pre-registered to prevent false claims of frictionless visitor booking flow.",
    ),
    DiscoveryExperiment(
        experiment_id="EXP-02",
        title="Primary Source Footnote Trustworthiness",
        hypothesis="Primary source footnote drawer increases perceived trustworthiness among cultural travelers.",
        target_cohort=CohortType.CULTURAL_TRAVELER,
        metric_name="Trust Rating",
        formula="% rating 4 or 5 on 5-point Likert scale",
        target_threshold=80.0,  # >= 80.0%
        falsification_trigger=60.0,  # < 60.0%
        comparison_operator=">=",
        status=ExperimentStatus.PRE_REGISTERED,
        sample_size_target=25,
        notes="Evaluates whether archival citations (Đại Nam Thực Lục) generate tangible visitor confidence.",
    ),
    DiscoveryExperiment(
        experiment_id="EXP-03",
        title="24-Hour Advance Lead-Time Partner Friction",
        hypothesis="24-hour advance lead-time constraint eliminates artisan scheduling friction and last-minute cancellation stress.",
        target_cohort=CohortType.ARTISAN_PARTNER,
        metric_name="Partner Scheduling Conflict Rate",
        formula="Conflicted or Stressed Requests / Total Inquiries",
        target_threshold=5.0,  # <= 5.0%
        falsification_trigger=15.0,  # > 15.0%
        comparison_operator="<=",
        status=ExperimentStatus.PRE_REGISTERED,
        sample_size_target=10,
        notes="Prevents sudden tour bus crowding at family-owned master artisan workshops.",
    ),
    DiscoveryExperiment(
        experiment_id="EXP-04",
        title="Educator Lesson Planning Efficiency",
        hypothesis="Teacher lesson wizard reduces lesson planning time from 3 hours to under 45 minutes.",
        target_cohort=CohortType.HERITAGE_EDUCATOR,
        metric_name="Task Completion Time",
        formula="Median minutes to select motif and export compliant worksheet",
        target_threshold=45.0,  # <= 45.0 min
        falsification_trigger=60.0,  # > 60.0 min
        comparison_operator="<=",
        status=ExperimentStatus.PRE_REGISTERED,
        sample_size_target=12,
        notes="Tested with Grade 10-12 history teachers under 2018 General Education Program.",
    ),
    DiscoveryExperiment(
        experiment_id="EXP-05",
        title="Low-Bandwidth 2D Rubbing Pedagogical Equivalence",
        hypothesis="Printable 2D rubbing kit delivers pedagogical equivalence in bandwidth-constrained classrooms.",
        target_cohort=CohortType.HERITAGE_EDUCATOR,
        metric_name="Task Feasibility & Comprehension Score",
        formula="% of students demonstrating evidence-based motif reasoning on paper rubbing worksheet",
        target_threshold=85.0,  # >= 85.0%
        falsification_trigger=70.0,  # < 70.0%
        comparison_operator=">=",
        status=ExperimentStatus.PRE_REGISTERED,
        sample_size_target=40,
        notes="Proves no school is disenfranchised by weak Wi-Fi or lack of 3D smartphones.",
    ),
]


# =========================================================================
# Canonical Standardized Interview Scripts
# =========================================================================
CANONICAL_INTERVIEW_SCRIPTS: List[DiscoveryInterviewScript] = [
    DiscoveryInterviewScript(
        script_id="ART-DISC",
        title="Artisan Guild Lineage Masters & Studio Leads Protocol",
        cohort=CohortType.ARTISAN_PARTNER,
        target_sample_size="4-8 Master Artisans in Huế (Pháp Lam, Bronze casting, Trúc Chỉ, Embroidery)",
        purpose="Map workshop lead times, unannounced visitor friction, intermediary exploitation, and take-rate viability.",
        questions=[
            DiscoveryInterviewQuestion(
                question_id="ART-Q01",
                prompt_vi="Hiện nay du khách tự túc tìm đến xưởng của bác qua những kênh nào khi không đi theo tour du lịch lớn?",
                prompt_en="How do independent travelers currently discover your atelier without tour buses?",
                objective="Identify organic vs fragmented discovery channels and middleman commissions.",
                category="acquisition",
                follow_up_probes=["Do they call in advance?", "What percentage comes through hotel concierges?"],
            ),
            DiscoveryInterviewQuestion(
                question_id="ART-Q02",
                prompt_vi="Khi khách đến đột xuất mà xưởng chưa chuẩn bị nguyên liệu (đun đồng, ngâm giang tre), bác xử lý thế nào?",
                prompt_en="What happens when guests arrive unannounced or expect instant crafting sessions?",
                objective="Validate urgency of 24h inquiry lead time.",
                category="operations",
                follow_up_probes=["Have you ever had to turn away travelers?", "How long does material preparation take?"],
            ),
            DiscoveryInterviewQuestion(
                question_id="ART-Q03",
                prompt_vi="Bác đã từng bị các hướng dẫn viên bên ngoài ép giá hoặc giới thiệu sai lịch sử gia tộc chưa?",
                prompt_en="Have third-party tour guides ever dictated prices or misrepresented historical lineages?",
                objective="Establish artisan dignity safeguards and anti-misrepresentation protections.",
                category="dignity",
                follow_up_probes=["How much commission do intermediaries take?", "Do they tell tourists fake imperial stories?"],
            ),
            DiscoveryInterviewQuestion(
                question_id="ART-Q04",
                prompt_vi="Thời gian tối thiểu bác cần để chuẩn bị chu đáo cho một buổi trải nghiệm 2-4 khách là bao lâu?",
                prompt_en="What is the absolute minimum lead time required to prep materials for 2-4 guests?",
                objective="Confirm SLA parameters for inquiry intake engine.",
                category="operations",
                follow_up_probes=["Can you accommodate same-day bookings?", "Is 24 hours sufficient?"],
            ),
            DiscoveryInterviewQuestion(
                question_id="ART-Q05",
                prompt_vi="Nếu nền tảng chỉ thu 10% phí dịch vụ khi khách đã đến và hoàn tất trải nghiệm (không thu phí trước), bác thấy thế nào?",
                prompt_en="Would an incremental 10% fee on completed verified visits be acceptable if zero upfront fees are charged?",
                objective="Validate unit economics take-rate hypothesis without upfront financial risk.",
                category="monetization",
                follow_up_probes=["What pricing would you charge per attendee?", "Is 700,000 VND appropriate?"],
            ),
        ],
    ),
    DiscoveryInterviewScript(
        script_id="FIT-DISC",
        title="Cultural Independent Travelers & Museum Visitors Protocol",
        cohort=CohortType.CULTURAL_TRAVELER,
        target_sample_size="15-30 Domestic & International Cultural Travelers in Huế",
        purpose="Assess travel discovery friction, trust in heritage narratives, inquiry UX expectations, and willingness to pay.",
        questions=[
            DiscoveryInterviewQuestion(
                question_id="FIT-Q01",
                prompt_vi="Khi tìm kiếm các trải nghiệm nghề thủ công đích thực tại Huế, bạn thường gặp khó khăn gì trên mạng?",
                prompt_en="When seeking authentic local craft experiences, where do online searches fail?",
                objective="Discover information fragmentation and commercial noise.",
                category="discovery",
                follow_up_probes=["Did you find direct artisan contact info?", "Were Google Maps listings outdated?"],
            ),
            DiscoveryInterviewQuestion(
                question_id="FIT-Q02",
                prompt_vi="Làm thế nào bạn biết một làng nghề là truyền thống thật hay là điểm mua sắm công nghiệp cho tour?",
                prompt_en="How do you verify whether a marketed 'traditional village' is genuine or a commercial tourist trap?",
                objective="Determine the value of archival proof and historical citations.",
                category="trust",
                follow_up_probes=["Do you read TripAdvisor reviews?", "Does seeing imperial source citations help?"],
            ),
            DiscoveryInterviewQuestion(
                question_id="FIT-Q03",
                prompt_vi="Việc gửi yêu cầu hẹn trước và chờ nghệ nhân xác nhận trong 24h làm bạn tăng hay giảm độ tin cậy so với đặt phòng tức thì?",
                prompt_en="Does requesting an appointment and waiting up to 24h for artisan confirmation increase or decrease your trust?",
                objective="Test inquiry vs instant checkout perception.",
                category="booking_friction",
                follow_up_probes=["Does instant booking feel like a factory tour?", "Does 0 VND upfront reassure you?"],
            ),
            DiscoveryInterviewQuestion(
                question_id="FIT-Q04",
                prompt_vi="Nếu trợ lý AI giải thích tích xưa trên Cửu Đỉnh có dẫn chú thích thư tịch gốc (Đại Nam Thực Lục), bạn thấy tin tưởng hơn không?",
                prompt_en="If an AI explains an imperial motif, does seeing primary historical footnotes make you trust the content?",
                objective="Validate AI citation faithfulness value proposition.",
                category="ai_trust",
                follow_up_probes=["Would you click the footnote to see the archive locator?"],
            ),
            DiscoveryInterviewQuestion(
                question_id="FIT-Q05",
                prompt_vi="Mức giá nào bạn cảm thấy xứng đáng cho một buổi học nghề 2 giờ trực tiếp cùng nghệ nhân ưu tú (500k - 850k VND)?",
                prompt_en="What price range would you consider reasonable for a 2-hour master-guided workshop?",
                objective="Gauge willingness to pay (WTP) distribution.",
                category="willingness_to_pay",
                follow_up_probes=["Is 700,000 VND ($27 USD) fair?", "What takeaway item do you expect?"],
            ),
        ],
    ),
    DiscoveryInterviewScript(
        script_id="EDU-DISC",
        title="Secondary School Heritage Educators Protocol",
        cohort=CohortType.HERITAGE_EDUCATOR,
        target_sample_size="8-15 History & Civic Education Teachers (Grades 10-12)",
        purpose="Identify curriculum obstacles, worksheet preparation time, and 2D printable fallback necessity.",
        questions=[
            DiscoveryInterviewQuestion(
                question_id="EDU-Q01",
                prompt_vi="Trở ngại lớn nhất của thầy/cô khi giảng dạy phần lịch sử địa phương và di sản triều Nguyễn là gì?",
                prompt_en="What are the primary obstacles in teaching the 2018 General Education Program local heritage modules?",
                objective="Map curriculum compliance and source scarcity pain points.",
                category="curriculum",
                follow_up_probes=["Are textbooks lacking detailed visual rubbings?", "Is there unverified lore online?"],
            ),
            DiscoveryInterviewQuestion(
                question_id="EDU-Q02",
                prompt_vi="Mỗi tuần thầy/cô mất bao nhiêu giờ để tìm tài liệu, bản dập sắc nét và chú thích lịch sử cho tiết học?",
                prompt_en="How many hours per week are spent finding high-resolution rubbings and cited historical sources?",
                objective="Measure baseline prep time burden.",
                category="efficiency",
                follow_up_probes=["Is it 2-3 hours per lesson?", "Where do you download rubbings?"],
            ),
            DiscoveryInterviewQuestion(
                question_id="EDU-Q03",
                prompt_vi="Trong điều kiện phòng học wifi yếu hoặc học sinh không có điện thoại, tài liệu in bản dập 2D quan trọng thế nào?",
                prompt_en="If classrooms have weak Wi-Fi or lack phones, how essential are printable rubbings and 2D fallbacks?",
                objective="Verify offline accessibility and Universal Design for Learning (UDL) requirement.",
                category="accessibility",
                follow_up_probes=["Can you use 3D WebGL in class?", "Is a printable PDF mandatory?"],
            ),
            DiscoveryInterviewQuestion(
                question_id="EDU-Q04",
                prompt_vi="Làm thế nào thầy/cô chấm điểm lập luận lịch sử theo mô hình Luận điểm - Dẫn chứng - Diễn giải (M-E-E)?",
                prompt_en="How do you evaluate historical reasoning (M-E-E evidence framework) without subjective grading bias?",
                objective="Confirm rubric utility and assessment standardization.",
                category="assessment",
                follow_up_probes=["Do students struggle to cite evidence?", "Is an objective rubric helpful?"],
            ),
            DiscoveryInterviewQuestion(
                question_id="EDU-Q05",
                prompt_vi="Quy trình phê duyệt ngân sách hoặc thủ tục thí điểm nào nhà trường yêu cầu trước khi triển khai phần mềm?",
                prompt_en="What budget approvals or pilot proofs are required before school administrators greenlight EdTech tools?",
                objective="Understand B2B school sales cycle and pilot requirements.",
                category="procurement",
                follow_up_probes=["Is Department of Education (Sở GD&ĐT) approval needed?"],
            ),
        ],
    ),
]


# =========================================================================
# Canonical Structured Usability Evaluation Tasks
# =========================================================================
CANONICAL_USABILITY_TASKS: List[DiscoveryUsabilityTask] = [
    DiscoveryUsabilityTask(
        task_id="TASK-01",
        title="Story Citation Inspection & Transparent Inquiry Submission",
        target_cohort=CohortType.CULTURAL_TRAVELER,
        scenario="Explore the 'Đại Triều Nghi' story, click source citation [^1], inspect archive locator, and submit booking inquiry with preferred date >=24h in advance.",
        steps=[
            "Navigate to story 'dai-trieu-nghi'",
            "Click on footnote citation marker [^1]",
            "Inspect archive locator drawer for Đại Nam Thực Lục",
            "Click 'Request Availability' button",
            "Select date at least 24 hours in advance",
            "Confirm zero upfront payment notice is displayed",
            "Submit inquiry and observe confirmation token",
        ],
        max_dwell_seconds=180,
        success_criterion="Complete submission without validation error; verify 0 VND upfront charge notice was seen.",
        zero_upfront_check=True,
    ),
    DiscoveryUsabilityTask(
        task_id="TASK-02",
        title="2D Rubbing Fallback & Hán-Nôm Translation Navigation",
        target_cohort=CohortType.MUSEUM_VISITOR,
        scenario="Scan QR token for Cao Đỉnh, navigate 2D rubbing fallback when WebGL disabled, and inspect Hán-Nôm inscription translation.",
        steps=[
            "Open relic view with WebGL disabled or fallback mode enabled",
            "Verify high-contrast 2D rubbing is displayed immediately",
            "Toggle Hán-Nôm transcript overlay",
            "Inspect Sino-Vietnamese reading and English translation",
        ],
        max_dwell_seconds=120,
        success_criterion="Successful navigation to rubbing view and reading translation without UI lockup or layout breakage.",
    ),
    DiscoveryUsabilityTask(
        task_id="TASK-03",
        title="Craft Partner 2-Click Inquiry Confirmation",
        target_cohort=CohortType.ARTISAN_PARTNER,
        scenario="Receive inquiry notification, review visitor party size and date, and confirm availability via partner dashboard.",
        steps=[
            "Open partner inbox at /rbpc/partner",
            "Select newly arrived pending inquiry",
            "Inspect requested date, time, and guest count",
            "Click 'Confirm Availability' status button",
            "Verify state transition to 'confirmed' executed in <=2 clicks",
        ],
        max_dwell_seconds=90,
        success_criterion="State transition from 'new' -> 'confirmed' executed in <=2 clicks with zero data corruption.",
    ),
    DiscoveryUsabilityTask(
        task_id="TASK-04",
        title="Teacher Lesson Wizard & Low-Bandwidth Printable Export",
        target_cohort=CohortType.HERITAGE_EDUCATOR,
        scenario="Access Lesson Wizard, select Cửu Đỉnh motif, filter by Grade 10 competency, and export printable low-bandwidth worksheet.",
        steps=[
            "Open educator lesson planner",
            "Select motif 'Hỏa đĩnh' (Cao Đỉnh)",
            "Filter curriculum competency: Grade 10 - Historical Source Evaluation",
            "Generate 45-minute lesson plan",
            "Click 'Export Printable Worksheet (Monochrome 2D)'",
        ],
        max_dwell_seconds=150,
        success_criterion="PDF/Printable generated with verified source citations and zero unreviewed claims within 150 seconds.",
    ),
]


class CustomerDiscoveryRegister:
    """In-memory and persistent register for customer discovery experiments and feedback store."""

    def __init__(self) -> None:
        self._experiments: Dict[str, DiscoveryExperiment] = {
            e.experiment_id: e for e in CANONICAL_EXPERIMENTS
        }
        self._scripts: Dict[str, DiscoveryInterviewScript] = {
            s.script_id: s for s in CANONICAL_INTERVIEW_SCRIPTS
        }
        self._tasks: Dict[str, DiscoveryUsabilityTask] = {
            t.task_id: t for t in CANONICAL_USABILITY_TASKS
        }
        self._feedback_store: List[AnonymizedFeedbackRecord] = []

    # Experiment accessors
    def get_all_experiments(self) -> List[DiscoveryExperiment]:
        return list(self._experiments.values())

    def get_experiment(self, exp_id: str) -> Optional[DiscoveryExperiment]:
        return self._experiments.get(exp_id)

    # Script accessors
    def get_all_scripts(self) -> List[DiscoveryInterviewScript]:
        return list(self._scripts.values())

    def get_script(self, script_id: str) -> Optional[DiscoveryInterviewScript]:
        return self._scripts.get(script_id)

    # Task accessors
    def get_all_tasks(self) -> List[DiscoveryUsabilityTask]:
        return list(self._tasks.values())

    def get_task(self, task_id: str) -> Optional[DiscoveryUsabilityTask]:
        return self._tasks.get(task_id)

    # Feedback submission & retrieval
    def record_feedback(self, record: AnonymizedFeedbackRecord) -> AnonymizedFeedbackRecord:
        """Submit feedback record after strict PII scrubbing and consent validation."""
        record.validate()
        self._feedback_store.append(record)
        return record

    def get_feedback_records(self, task_or_script_id: Optional[str] = None) -> List[AnonymizedFeedbackRecord]:
        if task_or_script_id:
            return [r for r in self._feedback_store if r.task_or_script_id == task_or_script_id]
        return list(self._feedback_store)

    def evaluate_experiment_outcome(
        self, experiment_id: str, observed_metric_value: float
    ) -> Dict[str, Any]:
        """Evaluate pre-registered hypothesis against target threshold vs falsification trigger."""
        exp = self.get_experiment(experiment_id)
        if not exp:
            raise KeyError(f"Experiment '{experiment_id}' not found in pre-registered registry.")

        if exp.comparison_operator == ">=":
            if observed_metric_value >= exp.target_threshold:
                outcome = EvaluationOutcome.TARGET_MET
                status = ExperimentStatus.VALIDATED
            elif observed_metric_value < exp.falsification_trigger:
                outcome = EvaluationOutcome.FALSIFIED
                status = ExperimentStatus.FALSIFIED
            else:
                outcome = EvaluationOutcome.INCONCLUSIVE
                status = ExperimentStatus.INCONCLUSIVE
        else:  # "<="
            if observed_metric_value <= exp.target_threshold:
                outcome = EvaluationOutcome.TARGET_MET
                status = ExperimentStatus.VALIDATED
            elif observed_metric_value > exp.falsification_trigger:
                outcome = EvaluationOutcome.FALSIFIED
                status = ExperimentStatus.FALSIFIED
            else:
                outcome = EvaluationOutcome.INCONCLUSIVE
                status = ExperimentStatus.INCONCLUSIVE

        return {
            "experiment_id": exp.experiment_id,
            "title": exp.title,
            "metric_name": exp.metric_name,
            "formula": exp.formula,
            "observed_value": observed_metric_value,
            "target_threshold": exp.target_threshold,
            "falsification_trigger": exp.falsification_trigger,
            "comparison_operator": exp.comparison_operator,
            "outcome": outcome.value,
            "updated_status": status.value,
            "is_falsified": outcome == EvaluationOutcome.FALSIFIED,
            "is_validated": outcome == EvaluationOutcome.TARGET_MET,
        }

    def publish_discovery_report(self, report: DiscoveryFindingReport) -> Dict[str, Any]:
        """Publish discovery finding report, strictly enforcing negative abuse invariants."""
        report.validate()
        return {
            "report_id": report.report_id,
            "title": report.title,
            "sample_methodology": report.sample_methodology.value,
            "sample_size": report.sample_size,
            "is_claimed_representative": report.is_claimed_representative,
            "methodology_disclaimer": report.methodology_disclaimer,
            "key_findings": report.key_findings,
            "experiment_evaluations": report.experiment_evaluations,
            "date_published": report.date_published,
        }

    def export_json(self) -> str:
        """Export complete pre-registered experiments, scripts, tasks, and anonymized feedback."""
        data = {
            "title": "LƯU NIÊN RBPC 2026 Customer Discovery Experiments Register",
            "document_id": "DOC-RBPC-DISCOVERY-001",
            "mandatory_disclaimer": MANDATORY_METHODOLOGY_DISCLAIMER_EN,
            "experiments": [asdict(e) for e in self.get_all_experiments()],
            "interview_scripts": [asdict(s) for s in self.get_all_scripts()],
            "usability_tasks": [asdict(t) for t in self.get_all_tasks()],
            "feedback_store": [asdict(f) for f in self._feedback_store],
            "total_feedback_count": len(self._feedback_store),
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def export_markdown_summary(self) -> str:
        """Generate formatted Markdown report with pre-registered tables and methodology disclaimer."""
        lines = [
            "# LƯU NIÊN — Customer Discovery Experiments & Research Protocols",
            "",
            "> **METHODOLOGY MANDATE (NEGATIVE ABUSE INVARIANT):**",
            f"> {MANDATORY_METHODOLOGY_DISCLAIMER_EN}",
            "",
            "## 1. Pre-Registered Experiment Hypotheses & Success Criteria",
            "",
            "| Exp ID | Target Cohort | Metric & Formula | Target Threshold | Falsification Trigger | Pre-Reg Status |",
            "|---|---|---|---|---|---|",
        ]
        for exp in self.get_all_experiments():
            target_str = f"{exp.comparison_operator} {exp.target_threshold}"
            falsify_str = f"{'<' if exp.comparison_operator == '>=' else '>'} {exp.falsification_trigger}"
            lines.append(
                f"| `{exp.experiment_id}` | `{exp.target_cohort.value}` | **{exp.metric_name}** (`{exp.formula}`) | "
                f"`{target_str}` | `{falsify_str}` | `{exp.status.value}` |"
            )

        lines.extend([
            "",
            "## 2. Standardized Discovery Interview Scripts",
            "",
            "| Script ID | Target Cohort | Questions Count | Target Sample | Purpose |",
            "|---|---|---|---|---|",
        ])
        for s in self.get_all_scripts():
            lines.append(
                f"| `{s.script_id}` | `{s.cohort.value}` | {len(s.questions)} questions | {s.target_sample_size} | {s.purpose} |"
            )

        lines.extend([
            "",
            "## 3. Structured Usability Evaluation Tasks",
            "",
            "| Task ID | Target Cohort | Max Dwell | Zero Upfront Check | Success Criterion |",
            "|---|---|---|---|---|",
        ])
        for t in self.get_all_tasks():
            lines.append(
                f"| `{t.task_id}` | `{t.target_cohort.value}` | `{t.max_dwell_seconds}s` | {'✅ YES' if t.zero_upfront_check else '—'} | {t.success_criterion} |"
            )

        lines.extend([
            "",
            "## 4. Anonymized Feedback Store Telemetry",
            f"- Total Anonymized Records Captured: `{len(self._feedback_store)}`",
            "- PII Scrubbing: Automatic server and client sanitization (Emails, Phones, IPs, Full Names).",
            "- Consent Policy: Explicit `rbpc-discovery-v1` acceptance required on all entries.",
        ])

        return "\n".join(lines)


# Default singleton register initialized with canonical definitions
default_discovery_register = CustomerDiscoveryRegister()
