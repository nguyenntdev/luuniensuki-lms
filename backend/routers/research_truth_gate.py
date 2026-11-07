# -*- coding: utf-8 -*-
"""FastAPI router for Research Results Truth Gate (V5-T128 / W12-A08).

Provides:
- GET  /api/v1/history/research/truth-gate/survey-1502/audit
- GET  /api/v1/history/research/truth-gate/survey-1502/reproduce
- POST /api/v1/history/research/truth-gate/verify-paper-figures
- POST /api/v1/history/research/truth-gate/validate-paper-claims
- GET  /api/v1/history/research/truth-gate/benchmarks
- POST /api/v1/history/research/truth-gate/audit-manuscript
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..apischemas.research_truth_gate import (
    BenchmarkRunsOut,
    ManuscriptAuditOut,
    PaperClaimVerifyIn,
    PaperClaimVerifyOut,
    PaperFigureVerifyIn,
    PaperFigureVerifyOut,
    SurveyAuditReportOut,
)
from ..db import get_db
from ..deps import get_current_user
from ..domain.research_truth_gate import (
    InvalidSurveyCohortError,
    InvalidSurveyDenominatorError,
    PaperFigureMismatchError,
    ResearchResultsTruthError,
    SubjectiveSurveyCannotProduceCausalMetricsError,
)
from ..errors import AppError
from ..models import User
from ..services.research_truth_gate import default_truth_gate_service

router = APIRouter(
    prefix="/api/v1/history/research/truth-gate",
    tags=["research-truth-gate"],
)


@router.get("/survey-1502/audit", response_model=SurveyAuditReportOut)
def get_survey_1502_audit_report(
    db: Session = Depends(get_db),
):
    """Retrieve authoritative audit report for the n=1,502 secondary student survey.
    
    Includes Table 1 items with exact denominators, numerators, and percentages,
    as well as full reconciliation of the two anomalies (4,506 multi-select and 544 vs 812).
    """
    try:
        report = default_truth_gate_service.get_survey_audit_report(db)
        return SurveyAuditReportOut(**report)
    except ResearchResultsTruthError as exc:
        raise AppError(code=exc.code, message=exc.message, status_code=400, details=exc.details)


@router.get("/survey-1502/reproduce")
def reproduce_survey_1502_dataset(
    seed: int = Query(1502, description="RNG seed for deterministic dataset permutation"),
):
    """Execute end-to-end de-identified survey dataset reproduction and return checksums."""
    try:
        return default_truth_gate_service.reproduce_dataset_pipeline(seed=seed)
    except ResearchResultsTruthError as exc:
        raise AppError(code=exc.code, message=exc.message, status_code=400, details=exc.details)


@router.post("/verify-paper-figures", response_model=PaperFigureVerifyOut)
def verify_paper_figures(
    payload: PaperFigureVerifyIn,
):
    """Verify submitted paper table items against authoritative survey metrics.
    
    Negative abuse defense: Any deviation in count, denominator, or percentage is rejected.
    """
    try:
        items = [item.model_dump() for item in payload.items]
        res = default_truth_gate_service.verify_submitted_figures(items)
        return PaperFigureVerifyOut(**res)
    except (PaperFigureMismatchError, InvalidSurveyDenominatorError) as exc:
        raise AppError(
            code=exc.code,
            message=exc.message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=exc.details,
        )
    except ResearchResultsTruthError as exc:
        raise AppError(code=exc.code, message=exc.message, status_code=400, details=exc.details)


@router.post("/validate-paper-claims", response_model=PaperClaimVerifyOut)
def validate_paper_claims(
    payload: PaperClaimVerifyIn,
):
    """Validate research claims against overclaiming invariants.
    
    Negative abuse defense: Subjective sentiment CANNOT be used to assert causal learning gains.
    1,502 secondary students CANNOT be labeled as tourists or commercial customers.
    """
    try:
        claims = [claim.model_dump() for claim in payload.claims]
        res = default_truth_gate_service.validate_claims(claims)
        return PaperClaimVerifyOut(**res)
    except (SubjectiveSurveyCannotProduceCausalMetricsError, InvalidSurveyCohortError) as exc:
        raise AppError(
            code=exc.code,
            message=exc.message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=exc.details,
        )
    except ResearchResultsTruthError as exc:
        raise AppError(code=exc.code, message=exc.message, status_code=400, details=exc.details)


@router.get("/benchmarks", response_model=BenchmarkRunsOut)
def get_benchmarks():
    """Retrieve real measured performance runs (PERF-RESEARCH-01, PERF-API-01, PERF-AI-01)."""
    res = default_truth_gate_service.get_benchmarks()
    return BenchmarkRunsOut(**res)


@router.post("/audit-manuscript", response_model=ManuscriptAuditOut)
def audit_manuscript(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Audit LuuNien_Q2_EN_Revised.tex on the filesystem and record the cryptographic audit."""
    try:
        audited = default_truth_gate_service.audit_manuscript_file(
            db=db,
            audited_by=current_user.email or str(current_user.id),
        )
        return ManuscriptAuditOut(**audited)
    except (PaperFigureMismatchError, SubjectiveSurveyCannotProduceCausalMetricsError) as exc:
        raise AppError(
            code=exc.code,
            message=exc.message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=exc.details,
        )
    except ResearchResultsTruthError as exc:
        raise AppError(code=exc.code, message=exc.message, status_code=400, details=exc.details)
