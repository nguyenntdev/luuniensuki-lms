# -*- coding: utf-8 -*-
"""V5-T114: Customer discovery experiments & research protocols Test Suite.

Ticket: V5-T114 (Wave W11, Slot A04).
Goal:
- Customer discovery experiments in docs/rbpc/ and frontend/src/.
- Interview scripts, usability tasks, anonymized feedback store, and pre-registered success criteria thresholds.
- Negative abuse: Self-selected respondents are not labeled representative of general population without methodology disclaimer.

Audits and verifies:
1. Pre-registered experiments coverage and falsification thresholds (EXP-01 to EXP-05).
2. Standardized interview scripts (ART-DISC, FIT-DISC, EDU-DISC) and questions.
3. Structured usability tasks (TASK-01 to TASK-04) with explicit pass/fail completion metrics.
4. Anonymized feedback store, PII scrubbing (emails, phones, IPs, Vietnamese names), and token validation.
5. Experiment evaluation mechanics (VALIDATED, FALSIFIED, INCONCLUSIVE) with threshold triggers.
6. NEGATIVE ABUSE INVARIANT:
   - Self-selected convenience samples CANNOT be labeled representative without mandatory methodology disclaimer.
   - Rejects missing, empty, or incomplete disclaimers missing sampling method, selection bias, or extrapolation prohibition.
   - Allows valid disclaimers when all three mandatory disclosure criteria are met.
7. Documentation and Business Plan parity:
   - docs/rbpc/CUSTOMER_DISCOVERY_PROTOCOLS_EXPERIMENTS.md
   - docs/rbpc/BUSINESS_PLAN_DRAFT.md
8. JSON & Markdown export utilities.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from backend.services.rbpc_discovery import (
    CANONICAL_EXPERIMENTS,
    CANONICAL_INTERVIEW_SCRIPTS,
    CANONICAL_USABILITY_TASKS,
    MANDATORY_METHODOLOGY_DISCLAIMER_EN,
    MANDATORY_METHODOLOGY_DISCLAIMER_VI,
    AnonymizedFeedbackRecord,
    CohortType,
    CustomerDiscoveryRegister,
    DiscoveryExperiment,
    DiscoveryFindingReport,
    EvaluationOutcome,
    ExperimentStatus,
    SamplingMethodology,
    default_discovery_register,
    scrub_pii,
    validate_methodology_disclaimer,
)


def test_v5_t114_canonical_experiments_coverage_and_thresholds():
    """Verify all 5 canonical experiments exist with pre-registered thresholds and falsification triggers."""
    register = default_discovery_register
    experiments = register.get_all_experiments()
    assert len(experiments) == 5, f"Expected 5 experiments, found {len(experiments)}"

    exp_ids = {e.experiment_id for e in experiments}
    assert exp_ids == {"EXP-01", "EXP-02", "EXP-03", "EXP-04", "EXP-05"}

    for exp in experiments:
        assert exp.experiment_id.startswith("EXP-")
        assert exp.title
        assert exp.hypothesis
        assert exp.metric_name
        assert exp.formula
        assert exp.target_threshold > 0
        assert exp.falsification_trigger > 0
        assert exp.status == ExperimentStatus.PRE_REGISTERED
        assert exp.sample_size_target > 0
        assert exp.comparison_operator in {">=", "<="}

    # Verify specific key thresholds
    exp01 = register.get_experiment("EXP-01")
    assert exp01.metric_name == "Form Completion Rate"
    assert exp01.target_threshold == 65.0
    assert exp01.falsification_trigger == 45.0

    exp02 = register.get_experiment("EXP-02")
    assert exp02.metric_name == "Trust Rating"
    assert exp02.target_threshold == 80.0
    assert exp02.falsification_trigger == 60.0

    exp03 = register.get_experiment("EXP-03")
    assert exp03.metric_name == "Partner Scheduling Conflict Rate"
    assert exp03.comparison_operator == "<="
    assert exp03.target_threshold == 5.0
    assert exp03.falsification_trigger == 15.0


def test_v5_t114_canonical_interview_scripts_and_questions():
    """Verify standardized interview scripts for artisans, cultural travelers, and educators."""
    register = default_discovery_register
    scripts = register.get_all_scripts()
    assert len(scripts) == 3

    script_ids = {s.script_id for s in scripts}
    assert script_ids == {"ART-DISC", "FIT-DISC", "EDU-DISC"}

    art_script = register.get_script("ART-DISC")
    assert art_script.cohort == CohortType.ARTISAN_PARTNER
    assert len(art_script.questions) == 5
    assert any("24h" in q.objective or "lead time" in q.objective for q in art_script.questions)
    assert any("take-rate" in q.objective or "monetization" in q.category for q in art_script.questions)

    fit_script = register.get_script("FIT-DISC")
    assert fit_script.cohort == CohortType.CULTURAL_TRAVELER
    assert len(fit_script.questions) == 5
    assert any(q.question_id == "FIT-Q04" for q in fit_script.questions)

    edu_script = register.get_script("EDU-DISC")
    assert edu_script.cohort == CohortType.HERITAGE_EDUCATOR
    assert len(edu_script.questions) == 5
    assert any("2D" in q.objective or "accessibility" in q.category for q in edu_script.questions)


def test_v5_t114_usability_tasks_and_zero_upfront_criterion():
    """Verify structured usability tasks with pass/fail metrics and zero upfront check."""
    register = default_discovery_register
    tasks = register.get_all_tasks()
    assert len(tasks) == 4

    task_ids = {t.task_id for t in tasks}
    assert task_ids == {"TASK-01", "TASK-02", "TASK-03", "TASK-04"}

    task01 = register.get_task("TASK-01")
    assert task01.zero_upfront_check is True
    assert task01.max_dwell_seconds == 180
    assert len(task01.steps) >= 6
    assert "0 VND upfront charge notice" in task01.success_criterion or "0 upfront charge notice" in task01.success_criterion

    task03 = register.get_task("TASK-03")
    assert task03.target_cohort == CohortType.ARTISAN_PARTNER
    assert "<=2 clicks" in task03.success_criterion


def test_v5_t114_anonymized_feedback_store_and_pii_scrubbing():
    """Verify feedback record persistence, token format, consent verification, and automatic PII scrub."""
    register = CustomerDiscoveryRegister()

    raw_text = (
        "Du khách Nguyễn Văn A tại 192.168.1.1 có email traveler@hue-visit.com và SĐT 0905123456 "
        "đã đánh giá rất tốt trải nghiệm Cửu Đỉnh."
    )
    cleaned, detected = scrub_pii(raw_text)
    assert detected is True
    assert "traveler@hue-visit.com" not in cleaned
    assert "0905123456" not in cleaned
    assert "192.168.1.1" not in cleaned
    assert "Nguyễn Văn A" not in cleaned
    assert "[EMAIL_REDACTED]" in cleaned
    assert "[PHONE_REDACTED]" in cleaned
    assert "[IP_REDACTED]" in cleaned
    assert "[NAME_REDACTED]" in cleaned

    # Create valid feedback record
    record = AnonymizedFeedbackRecord(
        record_id="rec_001",
        participant_token="FIT-99AB",
        cohort=CohortType.CULTURAL_TRAVELER,
        task_or_script_id="TASK-01",
        task_completed=True,
        dwell_seconds=124,
        rating_likert=5,
        qualitative_feedback=raw_text,
        consent_accepted=True,
        consent_version="rbpc-discovery-v1",
        is_self_selected=True,
    )
    saved = register.record_feedback(record)
    assert saved.record_id == "rec_001"
    # Verify feedback was scrubbed
    assert "[EMAIL_REDACTED]" in saved.qualitative_feedback

    # Reject without consent
    no_consent = AnonymizedFeedbackRecord(
        record_id="rec_002",
        participant_token="FIT-88BC",
        cohort=CohortType.CULTURAL_TRAVELER,
        task_or_script_id="TASK-01",
        task_completed=True,
        consent_accepted=False,
    )
    with pytest.raises(ValueError, match="Consent rejected"):
        register.record_feedback(no_consent)

    # Reject malformed token (e.g. real name or invalid format)
    bad_token = AnonymizedFeedbackRecord(
        record_id="rec_003",
        participant_token="NguyenVanA",
        cohort=CohortType.CULTURAL_TRAVELER,
        task_or_script_id="TASK-01",
        task_completed=True,
        consent_accepted=True,
        consent_version="rbpc-discovery-v1",
    )
    with pytest.raises(ValueError, match="Invalid pseudo-anonymized token"):
        register.record_feedback(bad_token)


def test_v5_t114_experiment_evaluation_mechanics():
    """Verify evaluation of pre-registered experiment against target vs falsification threshold."""
    register = default_discovery_register

    # 1. EXP-01 (target >= 65%, falsify < 45%)
    res_val = register.evaluate_experiment_outcome("EXP-01", 72.5)
    assert res_val["outcome"] == EvaluationOutcome.TARGET_MET.value
    assert res_val["updated_status"] == ExperimentStatus.VALIDATED.value
    assert res_val["is_validated"] is True
    assert res_val["is_falsified"] is False

    res_falsified = register.evaluate_experiment_outcome("EXP-01", 38.0)
    assert res_falsified["outcome"] == EvaluationOutcome.FALSIFIED.value
    assert res_falsified["updated_status"] == ExperimentStatus.FALSIFIED.value
    assert res_falsified["is_falsified"] is True

    res_inconclusive = register.evaluate_experiment_outcome("EXP-01", 55.0)
    assert res_inconclusive["outcome"] == EvaluationOutcome.INCONCLUSIVE.value
    assert res_inconclusive["updated_status"] == ExperimentStatus.INCONCLUSIVE.value

    # 2. EXP-03 (target <= 5.0%, falsify > 15.0%)
    res_exp3_val = register.evaluate_experiment_outcome("EXP-03", 3.2)
    assert res_exp3_val["outcome"] == EvaluationOutcome.TARGET_MET.value

    res_exp3_falsify = register.evaluate_experiment_outcome("EXP-03", 22.0)
    assert res_exp3_falsify["outcome"] == EvaluationOutcome.FALSIFIED.value


def test_v5_t114_negative_abuse_self_selected_representativeness_guardrail():
    """Negative Abuse Invariant:
    Self-selected respondents CANNOT be labeled representative of the general population
    without an explicit methodology disclaimer addressing sampling, selection bias, and extrapolation prohibition.
    """
    # 1. Non-representative claims on convenience sample do not trigger violation
    assert validate_methodology_disclaimer(SamplingMethodology.CONVENIENCE, False, None) is True

    # 2. Claiming representative WITH canonical disclaimers PASSES
    assert validate_methodology_disclaimer(
        SamplingMethodology.CONVENIENCE, True, MANDATORY_METHODOLOGY_DISCLAIMER_EN
    ) is True
    assert validate_methodology_disclaimer(
        SamplingMethodology.VOLUNTARY_OPT_IN, True, MANDATORY_METHODOLOGY_DISCLAIMER_VI
    ) is True

    # 3. Claiming representative WITHOUT disclaimer FAILS
    with pytest.raises(ValueError, match="Negative abuse invariant violation.*explicit methodology disclaimer"):
        validate_methodology_disclaimer(SamplingMethodology.CONVENIENCE, True, "")

    with pytest.raises(ValueError, match="Negative abuse invariant violation.*explicit methodology disclaimer"):
        validate_methodology_disclaimer(SamplingMethodology.PURPOSIVE_SELF_SELECTED, True, None)

    # 4. Incomplete disclaimer missing sampling methodology disclosure
    missing_sampling = (
        "Selection bias exists among early adopters and results cannot be extrapolated to the general population."
    )
    with pytest.raises(ValueError, match="missing sampling methodology disclosure"):
        validate_methodology_disclaimer(SamplingMethodology.CONVENIENCE, True, missing_sampling)

    # 5. Incomplete disclaimer missing selection bias disclosure
    missing_bias = (
        "Convenience sampling was used and results cannot be extrapolated to the general population without randomized stratified sampling."
    )
    with pytest.raises(ValueError, match="missing selection bias disclosure"):
        validate_methodology_disclaimer(SamplingMethodology.CONVENIENCE, True, missing_bias)

    # 6. Incomplete disclaimer missing extrapolation warning
    missing_extrapolation = (
        "Convenience sampling of self-selected tech-literate early adopters."
    )
    with pytest.raises(ValueError, match="missing extrapolation limitation"):
        validate_methodology_disclaimer(SamplingMethodology.CONVENIENCE, True, missing_extrapolation)


def test_v5_t114_discovery_report_validation_and_publishing():
    """Verify DiscoveryFindingReport enforces negative abuse invariant on report publication."""
    register = CustomerDiscoveryRegister()

    # Valid report with disclaimer
    report_valid = DiscoveryFindingReport(
        report_id="REP-001",
        title="Field Usability Study of Booking Inquiries in Huế",
        sample_methodology=SamplingMethodology.CONVENIENCE,
        sample_size=25,
        is_claimed_representative=True,
        methodology_disclaimer=MANDATORY_METHODOLOGY_DISCLAIMER_EN,
        key_findings=[
            "68% form completion with 0 VND upfront copy",
            "84% trust rating for primary source footnotes",
        ],
    )
    published = register.publish_discovery_report(report_valid)
    assert published["report_id"] == "REP-001"
    assert published["is_claimed_representative"] is True
    assert published["methodology_disclaimer"] is not None

    # Invalid report claiming representativeness without disclaimer
    report_invalid = DiscoveryFindingReport(
        report_id="REP-002",
        title="Overgeneralized Visitor Adoption Report",
        sample_methodology=SamplingMethodology.PURPOSIVE_SELF_SELECTED,
        sample_size=15,
        is_claimed_representative=True,
        methodology_disclaimer="",  # VIOLATION!
        key_findings=["All tourists in Huế will book craft workshops"],
    )
    with pytest.raises(ValueError, match="Negative abuse invariant"):
        register.publish_discovery_report(report_invalid)


def test_v5_t114_export_utilities_and_doc_parity():
    """Verify export utilities (JSON and Markdown) and documentation parity in docs/rbpc/."""
    register = default_discovery_register

    # 1. JSON Export
    json_out = register.export_json()
    assert isinstance(json_out, str)
    parsed = json.loads(json_out)
    assert parsed["document_id"] == "DOC-RBPC-DISCOVERY-001"
    assert len(parsed["experiments"]) == 5
    assert len(parsed["interview_scripts"]) == 3
    assert len(parsed["usability_tasks"]) == 4

    # 2. Markdown Export
    md_out = register.export_markdown_summary()
    assert isinstance(md_out, str)
    assert "# LƯU NIÊN — Customer Discovery Experiments & Research Protocols" in md_out
    assert "EXP-01" in md_out
    assert "TASK-01" in md_out
    assert "ART-DISC" in md_out
    assert "METHODOLOGY MANDATE (NEGATIVE ABUSE INVARIANT)" in md_out

    # 3. Documentation file check
    repo_root = Path(__file__).resolve().parents[2]
    doc_path = repo_root / "docs" / "rbpc" / "CUSTOMER_DISCOVERY_PROTOCOLS_EXPERIMENTS.md"
    bp_path = repo_root / "docs" / "rbpc" / "BUSINESS_PLAN_DRAFT.md"

    assert doc_path.exists(), "CUSTOMER_DISCOVERY_PROTOCOLS_EXPERIMENTS.md must exist"
    assert bp_path.exists(), "BUSINESS_PLAN_DRAFT.md must exist"

    doc_text = doc_path.read_text(encoding="utf-8")
    bp_text = bp_path.read_text(encoding="utf-8")

    assert "DOC-RBPC-DISCOVERY-001" in doc_text
    assert "EXP-01" in doc_text
    assert "EXP-05" in doc_text
    assert "TASK-01" in doc_text
    assert "TASK-04" in doc_text
    assert "ART-DISC" in doc_text
    assert "FIT-DISC" in doc_text
    assert "EDU-DISC" in doc_text
    assert "Section 6.2: Customer Discovery & Usability Experiments Register Summary" in bp_text
    assert "EXP-01" in bp_text
