# -*- coding: utf-8 -*-
"""SQLAlchemy 2.x declarative models for Research Results Truth Gate (V5-T128 / W12-A08).

Stores:
- research_survey_batches: Metadata and provenance for the n=1,502 student survey.
- research_survey_item_audits: Authoritative item-by-item counts, denominators,
  positive percentages, and strict epistemic boundaries (isolation from causal claims).
- research_paper_truth_audits: Cryptographic audit history validating academic
  manuscripts (e.g. LuuNien_Q2_EN_Revised.tex) against truth gate benchmarks.

Strict Additive Safety: Models conform to migration 0090_research_results_truth_gate.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base


class ResearchSurveyBatch(Base):
    """Metadata and provenance record for a research survey dataset."""

    __tablename__ = "research_survey_batches"
    __table_args__ = (
        Index("idx_research_survey_batch_code", "batch_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    study_title: Mapped[str] = mapped_column(Text, nullable=False)
    form_version: Mapped[str] = mapped_column(Text, nullable=False)
    total_respondents: Mapped[int] = mapped_column(Integer, nullable=False)
    school_count: Mapped[int] = mapped_column(Integer, nullable=False)
    collection_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    collection_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    dataset_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    ethics_protocol_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    anonymization_standard: Mapped[str] = mapped_column(Text, nullable=False, default="Decree_13_2023_ND_CP")
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    provenance_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    item_audits: Mapped[list["ResearchSurveyItemAudit"]] = relationship(
        "ResearchSurveyItemAudit", back_populates="batch", cascade="all, delete-orphan"
    )


class ResearchSurveyItemAudit(Base):
    """Authoritative audit record for an individual survey questionnaire item."""

    __tablename__ = "research_survey_item_audits"
    __table_args__ = (
        UniqueConstraint("batch_id", "item_id", name="uq_research_survey_batch_item"),
        Index("idx_research_survey_item_id", "item_id"),
        Index("idx_research_survey_item_batch", "batch_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("research_survey_batches.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[str] = mapped_column(Text, nullable=False)
    table_number: Mapped[str] = mapped_column(Text, nullable=False)
    original_question_vi: Mapped[str] = mapped_column(Text, nullable=False)
    question_text_en: Mapped[str] = mapped_column(Text, nullable=False)
    response_type: Mapped[str] = mapped_column(Text, nullable=False)
    allowed_max_choices: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    valid_respondents: Mapped[int] = mapped_column(Integer, nullable=False)
    missing_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    positive_count: Mapped[int] = mapped_column(Integer, nullable=False)
    positive_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    analysis_group: Mapped[str] = mapped_column(Text, nullable=False)
    is_subjective_self_report: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    epistemic_limitation: Mapped[str] = mapped_column(Text, nullable=False)
    discrepancy_log: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    batch: Mapped["ResearchSurveyBatch"] = relationship("ResearchSurveyBatch", back_populates="item_audits")


class ResearchPaperTruthAudit(Base):
    """Cryptographic audit result validating paper manuscript claims and figures."""

    __tablename__ = "research_paper_truth_audits"
    __table_args__ = (
        Index("idx_research_paper_truth_audit_paper", "paper_code"),
        Index("idx_research_paper_truth_audit_status", "audit_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_code: Mapped[str] = mapped_column(Text, nullable=False)
    manuscript_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    audit_status: Mapped[str] = mapped_column(Text, nullable=False)  # VERIFIED, REJECTED_CAUSAL_CLAIM, REJECTED_FIGURE_MISMATCH
    claims_checked: Mapped[int] = mapped_column(Integer, nullable=False)
    claims_passed: Mapped[int] = mapped_column(Integer, nullable=False)
    figures_checked: Mapped[int] = mapped_column(Integer, nullable=False)
    figures_passed: Mapped[int] = mapped_column(Integer, nullable=False)
    anomaly_a_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    anomaly_b_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    perf_benchmarks_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    audit_details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    audited_by: Mapped[str] = mapped_column(Text, nullable=False)
    audited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
