# -*- coding: utf-8 -*-
"""Pydantic schemas for Research Results Truth Gate (V5-T128 / W12-A08)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SurveyItemAuditOut(BaseModel):
    item_id: str
    table_number: str
    question_text_vi: str
    question_text_en: str
    response_type: str
    allowed_max_choices: int
    valid_respondents: int
    missing_count: int
    positive_count: int
    positive_percentage: float
    analysis_group: str
    is_subjective_self_report: bool
    epistemic_limitation: str


class SurveyAuditReportOut(BaseModel):
    batch_code: str
    study_title: str
    total_respondents: int
    school_count: int
    dataset_sha256: str
    anonymization_standard: str
    items: List[SurveyItemAuditOut]
    anomalies_audited: Dict[str, Any]
    epistemic_rule: str


class PaperFigureItemIn(BaseModel):
    item_id: str
    valid_respondents: Optional[int] = None
    positive_count: Optional[int] = None
    positive_percentage: Optional[float] = None


class PaperFigureVerifyIn(BaseModel):
    table_number: str = "Table 1"
    items: List[PaperFigureItemIn]


class PaperFigureVerifyOut(BaseModel):
    status: str
    checked: int
    passed: int
    discrepancies: List[str] = Field(default_factory=list)


class PaperClaimIn(BaseModel):
    claim_id: Optional[str] = None
    claim_text: str
    evidence_basis: str = "survey_1502"
    cohort_type: str = "secondary_students"


class PaperClaimVerifyIn(BaseModel):
    paper_code: str = "LUUNIEN_Q2_EN_REVISED"
    claims: List[PaperClaimIn]


class PaperClaimVerifyOut(BaseModel):
    status: str
    checked: int
    passed: int
    flagged: List[str] = Field(default_factory=list)


class BenchmarkRunsOut(BaseModel):
    benchmarks: Dict[str, Any]
    status: str


class ManuscriptAuditOut(BaseModel):
    audit_id: str
    paper_code: str
    manuscript_sha256: str
    status: str
    claims_checked: int
    claims_passed: int
    figures_checked: int
    figures_passed: int
    anomaly_a_verified: bool
    anomaly_b_verified: bool
    perf_benchmarks_verified: bool
