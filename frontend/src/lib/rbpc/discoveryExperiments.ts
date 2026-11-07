/**
 * LƯU NIÊN — RBPC 2026: Customer Discovery Experiments, Usability Tasks & Anonymized Feedback Store
 *
 * Ticket: V5-T114 (Wave W11, Slot A04)
 * Scope:
 * - Pre-registered discovery experiment hypotheses and falsification thresholds (EXP-01 to EXP-05).
 * - Standardized usability tasks (TASK-01 to TASK-04).
 * - Standardized interview scripts (ART-DISC, FIT-DISC, EDU-DISC).
 * - Client-side PII scrubbing and anonymized feedback store validation.
 * - Negative abuse invariant: Self-selected respondents are NOT labeled representative
 *   of general population without mandatory methodology disclaimer.
 */

export type CohortType =
  | "artisan_partner"
  | "cultural_traveler"
  | "heritage_educator"
  | "museum_visitor"
  | "general_public";

export type ExperimentStatus =
  | "PRE_REGISTERED"
  | "IN_PROGRESS"
  | "VALIDATED"
  | "FALSIFIED"
  | "INCONCLUSIVE";

export type SamplingMethodology =
  | "CONVENIENCE"
  | "PURPOSIVE_SELF_SELECTED"
  | "VOLUNTARY_OPT_IN"
  | "RANDOMIZED_STRATIFIED";

export interface DiscoveryInterviewQuestion {
  question_id: string;
  prompt_vi: string;
  prompt_en: string;
  objective: string;
  category: string;
  follow_up_probes?: string[];
}

export interface DiscoveryInterviewScript {
  script_id: string;
  title: string;
  cohort: CohortType;
  target_sample_size: string;
  purpose: string;
  questions: DiscoveryInterviewQuestion[];
}

export interface DiscoveryUsabilityTask {
  task_id: string;
  title: string;
  target_cohort: CohortType;
  scenario: string;
  steps: string[];
  max_dwell_seconds: number;
  success_criterion: string;
  zero_upfront_check?: boolean;
}

export interface DiscoveryExperiment {
  experiment_id: string;
  title: string;
  hypothesis: string;
  target_cohort: CohortType;
  metric_name: string;
  formula: string;
  target_threshold: number;
  falsification_trigger: number;
  comparison_operator: ">=" | "<=";
  status: ExperimentStatus;
  sample_size_target: number;
  notes: string;
}

export interface AnonymizedFeedbackSubmission {
  record_id: string;
  participant_token: string;
  cohort: CohortType;
  task_or_script_id: string;
  task_completed: boolean;
  dwell_seconds?: number;
  rating_likert?: number; // 1 to 5
  qualitative_feedback?: string;
  consent_accepted: boolean;
  consent_version: string;
  timestamp: string;
  is_self_selected: boolean;
}

export const MANDATORY_METHODOLOGY_DISCLAIMER_EN =
  "Methodology Disclaimer: Participants in this discovery experiment were recruited via voluntary opt-in and convenience sampling (non-probability sample). The findings reflect selection bias toward technologically fluent cultural enthusiasts and early adopters, and cannot be extrapolated as statistically representative of the general population without randomized stratified sampling.";

export const MANDATORY_METHODOLOGY_DISCLAIMER_VI =
  "Tuyên bố Phương pháp luận: Người tham gia thử nghiệm khám phá khách hàng được tuyển chọn thông qua hình thức tự nguyện đăng ký và lấy mẫu thuận tiện (mẫu phi xác suất). Kết quả phản ánh độ lệch chọn mẫu hướng tới nhóm người đam mê văn hóa và thành thạo công nghệ, và không thể suy rộng thành đại diện thống kê cho toàn thể dân số nếu không có phương pháp lấy mẫu phân tầng ngẫu nhiên.";

/**
 * PII scrubbing patterns
 */
const EMAIL_REGEX = /[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+/g;
const PHONE_REGEX = /(\+?84|0)(3[2-9]|5[689]|7[06-9]|8[1-9]|9[0-9])[0-9]{7}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b/g;
const IP_REGEX = /\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b/g;
const VI_NAME_REGEX = /\b(Nguyễn|Trần|Lê|Phạm|Hoàng|Huỳnh|Phan|Vũ|Võ|Đặng|Bùi|Đỗ|Hồ|Ngô|Dương|Lý)\s+[A-ZÀ-Ỹa-zà-ỹ]+(?:\s+[A-ZÀ-Ỹa-zà-ỹ]+)?\b/g;

export function scrubPii(text?: string): { cleanedText: string; piiDetected: boolean } {
  if (!text) return { cleanedText: "", piiDetected: false };

  let piiDetected = false;
  let cleaned = text;

  if (EMAIL_REGEX.test(cleaned)) {
    cleaned = cleaned.replace(EMAIL_REGEX, "[EMAIL_REDACTED]");
    piiDetected = true;
  }
  if (PHONE_REGEX.test(cleaned)) {
    cleaned = cleaned.replace(PHONE_REGEX, "[PHONE_REDACTED]");
    piiDetected = true;
  }
  if (IP_REGEX.test(cleaned)) {
    cleaned = cleaned.replace(IP_REGEX, "[IP_REDACTED]");
    piiDetected = true;
  }
  if (VI_NAME_REGEX.test(cleaned)) {
    cleaned = cleaned.replace(VI_NAME_REGEX, "[NAME_REDACTED]");
    piiDetected = true;
  }

  return { cleanedText: cleaned, piiDetected };
}

/**
 * Negative abuse validation:
 * Self-selected respondents cannot be labeled representative of general population without methodology disclaimer.
 */
export function validateMethodologyDisclaimer(
  sampleMethod: SamplingMethodology | string,
  isClaimedRepresentative: boolean,
  disclaimerText?: string | null
): boolean {
  const isConvenience = [
    "CONVENIENCE",
    "PURPOSIVE_SELF_SELECTED",
    "VOLUNTARY_OPT_IN",
  ].includes(sampleMethod);

  if (isConvenience && isClaimedRepresentative) {
    if (!disclaimerText || !disclaimerText.trim()) {
      throw new Error(
        "Negative abuse invariant violation: Self-selected respondents cannot be labeled representative of the general population without an explicit methodology disclaimer."
      );
    }
    const lower = disclaimerText.toLowerCase();

    // Check sampling keyword
    const hasSampling = [
      "convenience",
      "self-selected",
      "purposive",
      "non-probability",
      "opt-in",
      "thuận tiện",
      "tự nguyện",
      "phi xác suất",
      "lấy mẫu",
    ].some(k => lower.includes(k));
    if (!hasSampling) {
      throw new Error(
        "Negative abuse invariant violation: Methodology disclaimer is missing sampling methodology disclosure."
      );
    }

    // Check bias keyword
    const hasBias = [
      "selection bias",
      "early adopter",
      "tech-literate",
      "technologically fluent",
      "enthusiast",
      "độ lệch",
      "chọn mẫu",
      "đam mê",
      "thành thạo",
    ].some(k => lower.includes(k));
    if (!hasBias) {
      throw new Error(
        "Negative abuse invariant violation: Methodology disclaimer is missing selection bias disclosure."
      );
    }

    // Check extrapolation keyword
    const hasExtrapolate = [
      "cannot be extrapolated",
      "not representative",
      "prohibition on extrapolating",
      "general population",
      "randomized stratified",
      "không thể suy rộng",
      "đại diện",
      "dân số",
      "phân tầng ngẫu nhiên",
    ].some(k => lower.includes(k));
    if (!hasExtrapolate) {
      throw new Error(
        "Negative abuse invariant violation: Methodology disclaimer is missing population extrapolation limitation."
      );
    }
  }

  return true;
}

export const CANONICAL_DISCOVERY_EXPERIMENTS: DiscoveryExperiment[] = [
  {
    experiment_id: "EXP-01",
    title: "Inquiry Transparency & Upfront Charge Friction",
    hypothesis:
      "Transparent inquiry copy ('Send Booking Request', 0 VND upfront) produces higher completion than instant checkout.",
    target_cohort: "cultural_traveler",
    metric_name: "Form Completion Rate",
    formula: "Completed Submissions / Form Starts",
    target_threshold: 65.0,
    falsification_trigger: 45.0,
    comparison_operator: ">=",
    status: "PRE_REGISTERED",
    sample_size_target: 30,
    notes: "Pre-registered to prevent false claims of frictionless visitor booking flow.",
  },
  {
    experiment_id: "EXP-02",
    title: "Primary Source Footnote Trustworthiness",
    hypothesis:
      "Primary source footnote drawer increases perceived trustworthiness among cultural travelers.",
    target_cohort: "cultural_traveler",
    metric_name: "Trust Rating",
    formula: "% rating 4 or 5 on 5-point Likert scale",
    target_threshold: 80.0,
    falsification_trigger: 60.0,
    comparison_operator: ">=",
    status: "PRE_REGISTERED",
    sample_size_target: 25,
    notes: "Evaluates whether archival citations (Đại Nam Thực Lục) generate tangible visitor confidence.",
  },
  {
    experiment_id: "EXP-03",
    title: "24-Hour Advance Lead-Time Partner Friction",
    hypothesis:
      "24-hour advance lead-time constraint eliminates artisan scheduling friction and last-minute cancellation stress.",
    target_cohort: "artisan_partner",
    metric_name: "Partner Scheduling Conflict Rate",
    formula: "Conflicted or Stressed Requests / Total Inquiries",
    target_threshold: 5.0,
    falsification_trigger: 15.0,
    comparison_operator: "<=",
    status: "PRE_REGISTERED",
    sample_size_target: 10,
    notes: "Prevents sudden tour bus crowding at family-owned master artisan workshops.",
  },
  {
    experiment_id: "EXP-04",
    title: "Educator Lesson Planning Efficiency",
    hypothesis:
      "Teacher lesson wizard reduces lesson planning time from 3 hours to under 45 minutes.",
    target_cohort: "heritage_educator",
    metric_name: "Task Completion Time",
    formula: "Median minutes to select motif and export compliant worksheet",
    target_threshold: 45.0,
    falsification_trigger: 60.0,
    comparison_operator: "<=",
    status: "PRE_REGISTERED",
    sample_size_target: 12,
    notes: "Tested with Grade 10-12 history teachers under 2018 General Education Program.",
  },
  {
    experiment_id: "EXP-05",
    title: "Low-Bandwidth 2D Rubbing Pedagogical Equivalence",
    hypothesis:
      "Printable 2D rubbing kit delivers pedagogical equivalence in bandwidth-constrained classrooms.",
    target_cohort: "heritage_educator",
    metric_name: "Task Feasibility & Comprehension Score",
    formula: "% of students demonstrating evidence-based motif reasoning on paper rubbing worksheet",
    target_threshold: 85.0,
    falsification_trigger: 70.0,
    comparison_operator: ">=",
    status: "PRE_REGISTERED",
    sample_size_target: 40,
    notes: "Proves no school is disenfranchised by weak Wi-Fi or lack of 3D smartphones.",
  },
];

export const CANONICAL_USABILITY_TASKS: DiscoveryUsabilityTask[] = [
  {
    task_id: "TASK-01",
    title: "Story Citation Inspection & Transparent Inquiry Submission",
    target_cohort: "cultural_traveler",
    scenario:
      "Explore the 'Đại Triều Nghi' story, click source citation [^1], inspect archive locator, and submit booking inquiry with preferred date >=24h in advance.",
    steps: [
      "Navigate to story 'dai-trieu-nghi'",
      "Click on footnote citation marker [^1]",
      "Inspect archive locator drawer for Đại Nam Thực Lục",
      "Click 'Request Availability' button",
      "Select date at least 24 hours in advance",
      "Confirm zero upfront payment notice is displayed",
      "Submit inquiry and observe confirmation token",
    ],
    max_dwell_seconds: 180,
    success_criterion:
      "Complete submission without validation error; verify 0 VND upfront charge notice was seen.",
    zero_upfront_check: true,
  },
  {
    task_id: "TASK-02",
    title: "2D Rubbing Fallback & Hán-Nôm Translation Navigation",
    target_cohort: "museum_visitor",
    scenario:
      "Scan QR token for Cao Đỉnh, navigate 2D rubbing fallback when WebGL disabled, and inspect Hán-Nôm inscription translation.",
    steps: [
      "Open relic view with WebGL disabled or fallback mode enabled",
      "Verify high-contrast 2D rubbing is displayed immediately",
      "Toggle Hán-Nôm transcript overlay",
      "Inspect Sino-Vietnamese reading and English translation",
    ],
    max_dwell_seconds: 120,
    success_criterion:
      "Successful navigation to rubbing view and reading translation without UI lockup or layout breakage.",
  },
  {
    task_id: "TASK-03",
    title: "Craft Partner 2-Click Inquiry Confirmation",
    target_cohort: "artisan_partner",
    scenario:
      "Receive inquiry notification, review visitor party size and date, and confirm availability via partner dashboard.",
    steps: [
      "Open partner inbox at /rbpc/partner",
      "Select newly arrived pending inquiry",
      "Inspect requested date, time, and guest count",
      "Click 'Confirm Availability' status button",
      "Verify state transition to 'confirmed' executed in <=2 clicks",
    ],
    max_dwell_seconds: 90,
    success_criterion:
      "State transition from 'new' -> 'confirmed' executed in <=2 clicks with zero data corruption.",
  },
  {
    task_id: "TASK-04",
    title: "Teacher Lesson Wizard & Low-Bandwidth Printable Export",
    target_cohort: "heritage_educator",
    scenario:
      "Access Lesson Wizard, select Cửu Đỉnh motif, filter by Grade 10 competency, and export printable low-bandwidth worksheet.",
    steps: [
      "Open educator lesson planner",
      "Select motif 'Hỏa đĩnh' (Cao Đỉnh)",
      "Filter curriculum competency: Grade 10 - Historical Source Evaluation",
      "Generate 45-minute lesson plan",
      "Click 'Export Printable Worksheet (Monochrome 2D)'",
    ],
    max_dwell_seconds: 150,
    success_criterion:
      "PDF/Printable generated with verified source citations and zero unreviewed claims within 150 seconds.",
  },
];
