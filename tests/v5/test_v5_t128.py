# -*- coding: utf-8 -*-
"""V5-T128 (Wave W12, Slot A08): Research Results Truth Gate Test Suite.

Audits and verifies:
1. Exact Survey Methodology & Data Provenance (n=1,502 across 6 secondary schools).
2. Table 1 Item Frequencies & Denominator Precision:
   - All 8 canonical items match exact numbers and percentages (958/63.8%, 1412/94.0%,
     1308/87.1%, 1413/94.1%, 1420/94.5%, 1435/95.5%, 1465/97.5%, 1393/92.7%).
3. Anomaly A Reconciliation:
   - 4,506 multi-select selections across 4 options strictly matches 3 * 1,502.
4. Anomaly B Reconciliation:
   - 544 relief motif familiarity vs 812 textbook monument recognition with distinct scopes.
5. Negative Abuse Invariant 1 (Strict Epistemic Isolation):
   - Subjective survey data CANNOT be used to assert causal learning improvement or
     historical thinking gains (HTTP 422 CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY).
6. Negative Abuse Invariant 2 (Figure Mismatch & Fabrication Defense):
   - Altered counts, forged percentages, or modified denominators are strictly rejected
     with HTTP 422 (FIGURE_REPRODUCTION_MISMATCH / INVALID_DENOMINATOR).
7. Negative Abuse Invariant 3 (Cohort Mislabeling Defense):
   - Secondary student survey cohort (N=1,502) cannot be labeled as tourists or commercial customers.
8. Benchmark PERF-RESEARCH-01 Permutation Invariance:
   - 1,502-row de-identified dataset produces identical summary metrics and SHA-256
     hash across randomized row shuffling.
9. LaTeX Manuscript LuuNien_Q2_EN_Revised.tex Verification:
   - File exists, contains exact survey methodology, Table 1 counts, anomaly reconciliations,
     Decree 13/2023/ND-CP compliance, real benchmark runs, and zero overclaims.
10. Database Persistence & Audit Ledger:
    - Verifies research_survey_batches, research_survey_item_audits, and
      research_paper_truth_audits persistence in PostgreSQL.
11. REST API Endpoints Integration:
    - GET /api/v1/history/research/truth-gate/survey-1502/audit
    - GET /api/v1/history/research/truth-gate/survey-1502/reproduce
    - POST /api/v1/history/research/truth-gate/verify-paper-figures
    - POST /api/v1/history/research/truth-gate/validate-paper-claims
    - GET /api/v1/history/research/truth-gate/benchmarks
    - POST /api/v1/history/research/truth-gate/audit-manuscript
12. Documentation Parity:
    - Verifies docs/research/RESEARCH_RESULTS_TRUTH_GATE.md parity.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.domain.research_truth_gate import (
    ANOMALY_A_MULTI_SELECT,
    ANOMALY_B_AWARENESS_CHANNEL,
    BENCHMARK_RUNS,
    CANONICAL_TABLE_1_ITEMS,
    SURVEY_METADATA,
    InvalidSurveyCohortError,
    InvalidSurveyDenominatorError,
    PaperFigureMismatchError,
    SubjectiveSurveyCannotProduceCausalMetricsError,
    generate_synthetic_anonymized_1502_dataset,
    get_canonical_item_dict,
    reproduce_1502_survey_aggregates,
    verify_multi_select_distribution,
    verify_paper_claims,
    verify_paper_figure_table,
    verify_perf_research_shuffle_invariant,
)
from backend.models import User
from backend.models_research_truth_gate import (
    ResearchPaperTruthAudit,
    ResearchSurveyBatch,
    ResearchSurveyItemAudit,
)
from backend.services.research_truth_gate import (
    ResearchTruthGateService,
    default_truth_gate_service,
)


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Helper Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture
def auth_staff_headers(db_session) -> dict[str, str]:
    """Create a staff user and return authorization header."""
    user = User(
        id=uuid.uuid4(),
        email=f"truth_gate_admin_{uuid.uuid4().hex[:8]}@histolab.icu",
        display_name="Truth Gate Admin",
        password_hash="fake_password_hash_for_testing",
        role="admin",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    from datetime import timedelta
    from backend.config import settings
    from backend.security import create_jwt_token
    token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=60),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        extra_claims={"type": "access", "role": "admin"},
    )
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------- #
# 1. Survey 1,502 Canonical Items and Denominators
# --------------------------------------------------------------------------- #

def test_v5_t128_survey_1502_canonical_items_and_denominators():
    """Verify all 8 Table 1 items match canonical counts, denominators, and percentages."""
    items = CANONICAL_TABLE_1_ITEMS
    assert len(items) == 8, f"Expected exactly 8 Table 1 items, got {len(items)}"

    expected_specs = {
        "AWARENESS_RELIEF_01": (1502, 958, 63.8),
        "DIGITAL_ACCESS_WANTED_02": (1502, 1412, 94.0),
        "INTEREST_NEW_FORMATS_03": (1502, 1308, 87.1),
        "CONTENT_INTERESTING_04": (1502, 1413, 94.1),
        "PERCEIVED_UNDERSTANDING_05": (1502, 1420, 94.5),
        "PERCEIVED_EFFECTIVENESS_06": (1502, 1435, 95.5),
        "PERCEIVED_CHANGE_PRIDE_07": (1502, 1465, 97.5),
        "WILLINGNESS_SHARE_08": (1502, 1393, 92.7),
    }

    for item in items:
        assert item.item_id in expected_specs, f"Unexpected item_id {item.item_id}"
        expected_denom, expected_pos, expected_pct = expected_specs[item.item_id]

        assert item.valid_respondents == expected_denom
        assert item.positive_count == expected_pos
        assert item.positive_percentage == expected_pct
        assert item.is_subjective_self_report is True
        assert len(item.epistemic_limitation) > 10, "Epistemic limitation description must be substantive"

    # Verify study metadata
    assert SURVEY_METADATA["total_respondents"] == 1502
    assert SURVEY_METADATA["school_count"] == 6
    assert len(SURVEY_METADATA["schools"]) == 6
    assert SURVEY_METADATA["anonymization_standard"] == "Decree_13_2023_ND_CP"


# --------------------------------------------------------------------------- #
# 2. Anomaly A Multi-Select Reconciliation
# --------------------------------------------------------------------------- #

def test_v5_t128_anomaly_a_multi_select_reconciliation():
    """Verify exact mathematical reconciliation of the 4,506 multi-select selections."""
    anomaly = ANOMALY_A_MULTI_SELECT
    assert anomaly["allowed_max_choices"] == 3
    assert anomaly["total_participants"] == 1502

    options = anomaly["option_breakdown"]
    opt_sum = sum(v["count"] for v in options.values())
    assert opt_sum == 4506, f"Sum of options must equal 4,506, got {opt_sum}"
    assert opt_sum == 3 * 1502, "4,506 must equal exactly 3 * 1,502"
    assert anomaly["calculated_multiplier"] == 3.0
    assert anomaly["is_fully_reconciled"] is True

    # Test pure distribution validator
    selections_all_three = [3] * 1502
    res = verify_multi_select_distribution(selections_all_three)
    assert res["status"] == "PASSED"
    assert res["total_selections"] == 4506
    assert res["average_per_participant"] == 3.0


# --------------------------------------------------------------------------- #
# 3. Anomaly B Awareness vs Channel Reconciliation
# --------------------------------------------------------------------------- #

def test_v5_t128_anomaly_b_awareness_vs_channel_reconciliation():
    """Verify reconciliation between 544 relief motif familiarity and 812 textbook contacts."""
    anomaly = ANOMALY_B_AWARENESS_CHANNEL
    assert anomaly["item_prior_heard_reliefs"]["count"] == 544
    assert anomaly["item_textbook_channel"]["count"] == 812
    assert anomaly["is_fully_reconciled"] is True
    assert "distinct measurement targets" in anomaly["reconciliation_explanation"]


# --------------------------------------------------------------------------- #
# 4. Negative Abuse: Reject Causal Learning Gains from Survey Data
# --------------------------------------------------------------------------- #

def test_v5_t128_negative_abuse_reject_causal_learning_gains_from_survey():
    """Ensure claims asserting causal learning gains from the survey are strictly rejected."""
    prohibited_claims = [
        {
            "claim_text": "The survey proved that LuuNien increased historical reasoning among students by 35%.",
            "evidence_basis": "survey_1502",
        },
        {
            "claim_text": "Results showed improved learning by 40% after viewing the 3D urn models.",
            "evidence_basis": "survey_likert",
        },
        {
            "claim_text": "Khảo sát chứng nhận hệ thống giúp tăng kết quả học tập môn lịch sử.",
            "evidence_basis": "survey_1502",
        },
    ]

    for claim in prohibited_claims:
        with pytest.raises(SubjectiveSurveyCannotProduceCausalMetricsError) as exc_info:
            verify_paper_claims([claim])
        assert "Negative abuse detected" in str(exc_info.value)
        assert exc_info.value.code == "CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY"

    # Permitted descriptive claims pass without error
    valid_claims = [
        {
            "claim_text": "94.0% of students expressed a positive desire to access Cửu Đỉnh heritage via 3D/AR media.",
            "evidence_basis": "survey_1502",
        },
        {
            "claim_text": "95.5% of respondents evaluated the digital school implementation as effective.",
            "evidence_basis": "survey_1502",
        },
    ]
    res = verify_paper_claims(valid_claims)
    assert res["status"] == "PASSED"
    assert res["passed"] == 2


# --------------------------------------------------------------------------- #
# 5. Negative Abuse: Reject Figure Mismatch or Fabricated Denominators
# --------------------------------------------------------------------------- #

def test_v5_t128_negative_abuse_reject_figure_mismatch_or_fabricated_denominators():
    """Ensure deviations in item counts, percentages, or denominators are rejected."""
    # Count mismatch
    altered_count = [
        {"item_id": "AWARENESS_RELIEF_01", "valid_respondents": 1502, "positive_count": 960, "positive_percentage": 63.8}
    ]
    with pytest.raises(PaperFigureMismatchError) as exc_info:
        verify_paper_figure_table(altered_count)
    assert "Item AWARENESS_RELIEF_01 count mismatch" in str(exc_info.value)

    # Percentage mismatch
    altered_pct = [
        {"item_id": "DIGITAL_ACCESS_WANTED_02", "valid_respondents": 1502, "positive_count": 1412, "positive_percentage": 98.0}
    ]
    with pytest.raises(PaperFigureMismatchError) as exc_info:
        verify_paper_figure_table(altered_pct)
    assert "Item DIGITAL_ACCESS_WANTED_02 percentage mismatch" in str(exc_info.value)

    # Denominator mismatch (hardcoding 1,500 instead of 1,502)
    altered_denom = [
        {"item_id": "INTEREST_NEW_FORMATS_03", "valid_respondents": 1500, "positive_count": 1308, "positive_percentage": 87.1}
    ]
    with pytest.raises(InvalidSurveyDenominatorError) as exc_info:
        verify_paper_figure_table(altered_denom)
    assert "Denominator mismatch" in str(exc_info.value)
    assert exc_info.value.code == "INVALID_DENOMINATOR"


# --------------------------------------------------------------------------- #
# 6. Negative Abuse: Reject Mislabeling Students as Tourists
# --------------------------------------------------------------------------- #

def test_v5_t128_negative_abuse_reject_mislabeling_students_as_tourists():
    """Ensure the 1,502 secondary student cohort is not mislabeled as tourists."""
    tourist_claims = [
        {
            "claim_text": "Analysis of 1502 surveyed participants showed tourist satisfaction reached 95%.",
            "cohort_type": "tourists",
            "evidence_basis": "survey_1502",
        },
        {
            "claim_text": "Commercial conversion for 1502 visitors indicates strong market demand.",
            "cohort_type": "visitors",
            "evidence_basis": "survey_1502",
        },
    ]

    for claim in tourist_claims:
        with pytest.raises(InvalidSurveyCohortError) as exc_info:
            verify_paper_claims([claim])
        assert "Invalid cohort" in str(exc_info.value)
        assert exc_info.value.code == "INVALID_COHORT_CLASSIFICATION"


# --------------------------------------------------------------------------- #
# 7. Benchmark PERF-RESEARCH-01 Permutation Invariance
# --------------------------------------------------------------------------- #

def test_v5_t128_benchmark_perf_research_01_shuffle_invariance():
    """Verify PERF-RESEARCH-01: Row shuffling leaves aggregate metrics 100% invariant."""
    dataset = generate_synthetic_anonymized_1502_dataset(seed=1502)
    assert len(dataset) == 1502

    # Reproduce base aggregates
    base_results = reproduce_1502_survey_aggregates(dataset)
    assert base_results["status"] == "REPRODUCED_MATCH"
    assert base_results["total_respondents"] == 1502

    # Check that all 8 items matched expected numbers
    for item_id, it in base_results["items"].items():
        assert it["matches_truth"] is True, f"Item {item_id} failed exact match"

    # Multi-select 4,506 audit in dataset
    assert base_results["multi_select_audit"]["total_selections"] == 4506
    assert base_results["multi_select_audit"]["is_reconciled"] is True

    # Validate permutation invariance across 5 randomized trials
    is_invariant = verify_perf_research_shuffle_invariant(dataset, trials=5)
    assert is_invariant is True, "PERF-RESEARCH-01 failed: Row permutation changed summary hash or counts"


# --------------------------------------------------------------------------- #
# 8. LaTeX Manuscript LuuNien_Q2_EN_Revised.tex Verification
# --------------------------------------------------------------------------- #

def test_v5_t128_latex_manuscript_truth_gate_audit(db_session):
    """Verify LuuNien_Q2_EN_Revised.tex on the filesystem conforms to Truth Gate."""
    manuscript_path = WORKSPACE_ROOT / "LuuNien_Q2_EN_Revised.tex"
    assert manuscript_path.exists(), f"Missing manuscript: {manuscript_path}"

    service = ResearchTruthGateService(workspace_root=WORKSPACE_ROOT)
    audit = service.audit_manuscript_file(
        db=db_session,
        manuscript_path=manuscript_path,
        audited_by="pytest_runner_w12_a08",
    )

    assert audit["status"] == "VERIFIED"
    assert audit["paper_code"] == "LUUNIEN_Q2_EN_REVISED"
    assert audit["figures_checked"] == 8
    assert audit["figures_passed"] == 8
    assert audit["anomaly_a_verified"] is True
    assert audit["anomaly_b_verified"] is True
    assert audit["perf_benchmarks_verified"] is True
    assert len(audit["manuscript_sha256"]) == 64

    # Verify audit record persisted in DB
    db_audit = db_session.get(ResearchPaperTruthAudit, uuid.UUID(audit["audit_id"]))
    assert db_audit is not None
    assert db_audit.audit_status == "VERIFIED"


# --------------------------------------------------------------------------- #
# 9. Database Persistence & Audit Ledger
# --------------------------------------------------------------------------- #

def test_v5_t128_database_persistence_and_audit_ledger(db_session):
    """Verify PostgreSQL persistence of research survey batch and item audits."""
    service = ResearchTruthGateService(workspace_root=WORKSPACE_ROOT)
    batch = service.get_or_create_canonical_batch(db_session)

    assert batch.batch_code == "SURVEY_1502_ORIGINAL_2026"
    assert batch.total_respondents == 1502
    assert batch.school_count == 6

    # Verify items in DB
    items = list(db_session.scalars(
        select(ResearchSurveyItemAudit).where(ResearchSurveyItemAudit.batch_id == batch.id)
    ).all())
    assert len(items) == 8

    item_map = {it.item_id: it for it in items}
    assert item_map["AWARENESS_RELIEF_01"].positive_count == 958
    assert item_map["DIGITAL_ACCESS_WANTED_02"].positive_count == 1412
    assert item_map["PERCEIVED_CHANGE_PRIDE_07"].positive_count == 1465

    # Verify idempotency: calling get_or_create_canonical_batch again returns existing
    batch2 = service.get_or_create_canonical_batch(db_session)
    assert batch2.id == batch.id


# --------------------------------------------------------------------------- #
# 10. REST API Endpoints Integration
# --------------------------------------------------------------------------- #

def test_v5_t128_rest_api_endpoints_integration(client: TestClient, auth_staff_headers):
    """Test all Research Results Truth Gate REST API endpoints."""
    # 1. GET survey audit report
    resp = client.get("/api/v1/history/research/truth-gate/survey-1502/audit")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["batch_code"] == "SURVEY_1502_ORIGINAL_2026"
    assert data["total_respondents"] == 1502
    assert len(data["items"]) == 8
    assert "anomaly_a_multi_select" in data["anomalies_audited"]
    assert "anomaly_b_awareness_vs_channel" in data["anomalies_audited"]

    # 2. GET survey reproduction
    resp_reprod = client.get("/api/v1/history/research/truth-gate/survey-1502/reproduce?seed=1502")
    assert resp_reprod.status_code == 200, resp_reprod.text
    reprod_data = resp_reprod.json()
    assert reprod_data["status"] == "REPRODUCED_SUCCESS"
    assert reprod_data["respondent_count"] == 1502
    assert reprod_data["shuffle_invariant_verified"] is True
    assert reprod_data["multi_select_audit"]["total_selections"] == 4506

    # 3. POST verify paper figures (positive golden case)
    golden_figures = [
        {"item_id": "AWARENESS_RELIEF_01", "valid_respondents": 1502, "positive_count": 958, "positive_percentage": 63.8},
        {"item_id": "DIGITAL_ACCESS_WANTED_02", "valid_respondents": 1502, "positive_count": 1412, "positive_percentage": 94.0},
    ]
    resp_fig = client.post(
        "/api/v1/history/research/truth-gate/verify-paper-figures",
        json={"table_number": "Table 1", "items": golden_figures},
    )
    assert resp_fig.status_code == 200, resp_fig.text
    assert resp_fig.json()["status"] == "PASSED"
    assert resp_fig.json()["passed"] == 2

    # 4. POST verify paper figures (negative abuse: figure mismatch)
    tampered_figures = [
        {"item_id": "AWARENESS_RELIEF_01", "valid_respondents": 1502, "positive_count": 965, "positive_percentage": 63.8},
    ]
    resp_tampered = client.post(
        "/api/v1/history/research/truth-gate/verify-paper-figures",
        json={"table_number": "Table 1", "items": tampered_figures},
    )
    assert resp_tampered.status_code == 422
    assert resp_tampered.json()["error"]["code"] == "FIGURE_REPRODUCTION_MISMATCH"

    # 5. POST validate paper claims (positive case)
    valid_claims = [
        {"claim_text": "Students showed high interest in 3D models (87.1%).", "evidence_basis": "survey_1502"},
    ]
    resp_claim = client.post(
        "/api/v1/history/research/truth-gate/validate-paper-claims",
        json={"paper_code": "LUUNIEN_Q2_EN_REVISED", "claims": valid_claims},
    )
    assert resp_claim.status_code == 200, resp_claim.text
    assert resp_claim.json()["status"] == "PASSED"

    # 6. POST validate paper claims (negative abuse: causal claim from survey)
    causal_claims = [
        {"claim_text": "The survey proved that the app increased historical thinking by 30%.", "evidence_basis": "survey_1502"},
    ]
    resp_causal = client.post(
        "/api/v1/history/research/truth-gate/validate-paper-claims",
        json={"paper_code": "LUUNIEN_Q2_EN_REVISED", "claims": causal_claims},
    )
    assert resp_causal.status_code == 422
    assert resp_causal.json()["error"]["code"] == "CANNOT_DERIVE_CAUSAL_METRICS_FROM_SURVEY"

    # 7. GET benchmarks
    resp_bench = client.get("/api/v1/history/research/truth-gate/benchmarks")
    assert resp_bench.status_code == 200, resp_bench.text
    assert "PERF-RESEARCH-01" in resp_bench.json()["benchmarks"]
    assert "PERF-API-01" in resp_bench.json()["benchmarks"]
    assert "PERF-AI-01" in resp_bench.json()["benchmarks"]

    # 8. POST audit manuscript file
    resp_manuscript = client.post(
        "/api/v1/history/research/truth-gate/audit-manuscript",
        headers=auth_staff_headers,
    )
    assert resp_manuscript.status_code == 200, resp_manuscript.text
    manu_data = resp_manuscript.json()
    assert manu_data["status"] == "VERIFIED"
    assert manu_data["paper_code"] == "LUUNIEN_Q2_EN_REVISED"
    assert manu_data["figures_passed"] == 8


# --------------------------------------------------------------------------- #
# 11. Documentation Parity
# --------------------------------------------------------------------------- #

def test_v5_t128_documentation_parity():
    """Verify docs/research/RESEARCH_RESULTS_TRUTH_GATE.md exists and is consistent."""
    doc_path = WORKSPACE_ROOT / "docs" / "research" / "RESEARCH_RESULTS_TRUTH_GATE.md"
    assert doc_path.exists(), f"Missing documentation file: {doc_path}"

    content = doc_path.read_text(encoding="utf-8")
    assert "1,502" in content
    assert "4,506" in content
    assert "544" in content
    assert "812" in content
    assert "AWARENESS_RELIEF_01" in content
    assert "WILLINGNESS_SHARE_08" in content
    assert "Decree 13/2023/ND-CP" in content
    assert "PERF-RESEARCH-01" in content
    assert "PERF-API-01" in content
    assert "PERF-AI-01" in content
