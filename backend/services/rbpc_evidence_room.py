# -*- coding: utf-8 -*-
"""Startup Evidence Room and Pitch Review Evaluation Service.

Ticket: V5-T120 (Wave W11, Slot A10).
Classification: NEW_PRODUCT_FEATURE / GOVERNANCE.

Features:
- Versioned evidence pointers across 7 domains:
  product, customer, market, finances, impact, legal, and team.
- Negative abuse guardrail:
  Every quantitative pitch claim must have an immutable evidence reference and status;
  ungrounded metrics are strictly flagged (UNGROUNDED_FLAGGED) and pitch readiness is FLAGGED_UNREADY.
- Due diligence audit recording with SHA-256 hashes and structured metric payloads.
- JSON and Markdown due diligence exports for pitch evaluations and investor review.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models_rbpc import (
    RbpcEvidenceDomain,
    RbpcEvidencePointer,
    RbpcEvidencePointerStatus,
    RbpcPitchClaimStatus,
    RbpcPitchReadiness,
    RbpcPitchReview,
)


@dataclass(frozen=True)
class CanonicalEvidencePointer:
    pointer_id: str
    domain: RbpcEvidenceDomain
    title: str
    doc_ref: str
    version: str
    status: RbpcEvidencePointerStatus
    hash_sha256: str
    metrics_payload: Dict[str, Any]
    summary: str
    owner: str
    verified_at: str  # ISO-8601 string

    def to_dict(self) -> dict:
        return {
            "pointer_id": self.pointer_id,
            "domain": self.domain.value,
            "title": self.title,
            "doc_ref": self.doc_ref,
            "version": self.version,
            "status": self.status.value,
            "hash_sha256": self.hash_sha256,
            "metrics_payload": self.metrics_payload,
            "summary": self.summary,
            "owner": self.owner,
            "verified_at": self.verified_at,
        }


def _hash_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# Canonical Seed Evidence Pointers across 7 domains
CANONICAL_EVIDENCE_POINTERS: list[CanonicalEvidencePointer] = [
    # ---------------- 1. PRODUCT DOMAIN ----------------
    CanonicalEvidencePointer(
        pointer_id="EVID-PROD-001",
        domain=RbpcEvidenceDomain.product,
        title="3D/AR WebGL Engine & Heritage Motifs Lineage",
        doc_ref="docs/rbpc/3D_LINEAGE_REPORT.md",
        version="1.0.0",
        status=RbpcEvidencePointerStatus.active_verified,
        hash_sha256=_hash_text("DOC-3D-LINEAGE-V1-URN-MOTIFS-162"),
        metrics_payload={
            "canonical_urns_count": 9,
            "canonical_motifs_count": 162,
            "webgl_3d_lod_levels": 3,
            "fallback_2d_rubbing_coverage_percent": 100.0,
            "rendering_target_fps": 60,
        },
        summary="Complete 3D mesh and 2D rubbing asset inventory for 9 Urns and 162 motifs with authentic lineage and WebGL fallback.",
        owner="S4 Frontend Lead",
        verified_at="2026-10-20T08:00:00Z",
    ),
    CanonicalEvidencePointer(
        pointer_id="EVID-PROD-002",
        domain=RbpcEvidenceDomain.product,
        title="Delimited Scoped RAG AI Tutor Pipeline",
        doc_ref="docs/rbpc/AI_DEMO_CASES.md",
        version="1.0.0",
        status=RbpcEvidencePointerStatus.active_verified,
        hash_sha256=_hash_text("DOC-AI-RAG-DELIMITED-SCOPED-TUTOR"),
        metrics_payload={
            "rag_provider_gateway": "router.theclaracare.com",
            "max_p95_latency_seconds": 1.2,
            "hallucination_guardrail_status": "enforced",
            "primary_annals_coverage_percent": 100.0,
            "gold_set_benchmark_score": 98.5,
        },
        summary="Historical AI Tutor service strictly constrained to verified imperial annals with prompt injection defenses and zero speculation.",
        owner="S1 Integrator",
        verified_at="2026-10-22T10:00:00Z",
    ),

    # ---------------- 2. CUSTOMER DOMAIN ----------------
    CanonicalEvidencePointer(
        pointer_id="EVID-CUST-001",
        domain=RbpcEvidenceDomain.customer,
        title="5-Stage Value Journey & Visitor Intercept Discovery",
        doc_ref="docs/rbpc/CUSTOMER_DISCOVERY_PROTOCOLS_EXPERIMENTS.md",
        version="1.0.0",
        status=RbpcEvidencePointerStatus.active_verified,
        hash_sha256=_hash_text("DOC-CUSTOMER-DISCOVERY-CITADEL-INTERCEPTS"),
        metrics_payload={
            "citadel_intercepts_n": 50,
            "comprehension_difficulty_percent": 78.0,
            "engaged_readers_conversion_percent": 15.0,
            "dwell_time_threshold_seconds": 60,
            "story_engagement_benchmark_percent": 20.0,
        },
        summary="Field interviews and usability trials with international cultural travelers in Huế Citadel validating contextual heritage interest.",
        owner="S3 Business Lead",
        verified_at="2026-10-18T14:30:00Z",
    ),
    CanonicalEvidencePointer(
        pointer_id="EVID-CUST-002",
        domain=RbpcEvidenceDomain.customer,
        title="Living Master Lineage & Consent Studio Records",
        doc_ref="docs/rbpc/CREATOR_CONSENT_AUDIT.md",
        version="1.0.0",
        status=RbpcEvidencePointerStatus.active_verified,
        hash_sha256=_hash_text("DOC-CREATOR-CONSENT-AUDIT-HUEMASTERS"),
        metrics_payload={
            "verified_consented_masters": 5,
            "erasure_sla_hours": 24,
            "consent_form_ref": "EVID-ARTISAN-001",
            "active_studio_ateliers": 5,
            "artisan_satisfaction_score": 4.9,
        },
        summary="Consented creator profiles backed by signed bilingual consent agreements with right of erasure and workshop terms.",
        owner="S2 Historian",
        verified_at="2026-10-25T11:00:00Z",
    ),

    # ---------------- 3. MARKET DOMAIN ----------------
    CanonicalEvidencePointer(
        pointer_id="EVID-MKT-001",
        domain=RbpcEvidenceDomain.market,
        title="TAM / SAM / SOM Bottom-Up Market Sizing Model",
        doc_ref="docs/rbpc/FINANCIAL_ASSUMPTIONS.md",
        version="1.0.0",
        status=RbpcEvidencePointerStatus.active_verified,
        hash_sha256=_hash_text("DOC-MKT-SIZING-TAM-SAM-SOM-2026"),
        metrics_payload={
            "tam_gbv_vnd": 28500000000,
            "sam_gbv_vnd": 5700000000,
            "som_year1_experiences": 1100,
            "som_year1_gmv_vnd": 570000000,
            "annual_visitor_arrivals_province": 4050000,
            "cultural_fit_segment_percent": 14.8,
        },
        summary="Bottom-up sizing starting from 4.05M provincial visitor arrivals and master guild ateliers in Huế.",
        owner="S3 Business Lead",
        verified_at="2026-10-18T16:00:00Z",
    ),
    CanonicalEvidencePointer(
        pointer_id="EVID-MKT-002",
        domain=RbpcEvidenceDomain.market,
        title="OTA Commission Arbitrage & Competitive Audit",
        doc_ref="docs/rbpc/BUSINESS_PLAN_DRAFT.md",
        version="1.0.0",
        status=RbpcEvidencePointerStatus.active_verified,
        hash_sha256=_hash_text("DOC-OTA-COMMISSION-ARBITRAGE-AUDIT"),
        metrics_payload={
            "ota_commission_rate_min_percent": 25.0,
            "ota_commission_rate_max_percent": 30.0,
            "platform_commission_percent": 10.0,
            "artisan_commission_savings_percent": 15.0,
            "operator_time_burden_hours_per_week": 5.8,
            "operator_time_saved_hours_per_week": 4.5,
        },
        summary="Audit of commercial OTA terms (Klook, Viator) versus LƯU NIÊN's 10% performance commission and automated inquiry intake.",
        owner="S3 Business Lead",
        verified_at="2026-10-19T09:00:00Z",
    ),

    # ---------------- 4. FINANCES DOMAIN ----------------
    CanonicalEvidencePointer(
        pointer_id="EVID-FIN-001",
        domain=RbpcEvidenceDomain.finances,
        title="Unit Economics & Sensitivity Model (10 vs 30 vs 60 Bookings)",
        doc_ref="docs/rbpc/PITCH_EXHIBITS.md",
        version="1.0.0",
        status=RbpcEvidencePointerStatus.active_verified,
        hash_sha256=_hash_text("DOC-UNIT-ECONOMICS-SENSITIVITY-EXHIBIT-2"),
        metrics_payload={
            "average_booking_vnd": 700000,
            "platform_fee_percent": 10.0,
            "artisan_share_percent": 90.0,
            "commission_per_booking_vnd": 70000,
            "base_contribution_margin_percent": 92.4,
            "breakeven_bookings_per_month": 2.9,
            "monsoon_burn_vnd_per_month": 28500,
            "provider_cac_payback_months": 0.31,
        },
        summary="Master unit economics model demonstrating 92.4% contribution margin and 2.9 booking/month commercial breakeven.",
        owner="S3 Business Lead",
        verified_at="2026-10-18T18:00:00Z",
    ),
    CanonicalEvidencePointer(
        pointer_id="EVID-FIN-002",
        domain=RbpcEvidenceDomain.finances,
        title="Documented In-Kind Corporate Sponsorship Audit",
        doc_ref="docs/rbpc/PITCH_EXHIBITS.md",
        version="1.0.0",
        status=RbpcEvidencePointerStatus.active_verified,
        hash_sha256=_hash_text("DOC-SPONSORSHIP-AUDIT-202360638-VND"),
        metrics_payload={
            "total_in_kind_sponsorship_vnd": 202360638,
            "bnix_cloud_vps_vnd": 1142400,
            "pho_tue_ai_credits_usd": 7610.0,
            "pho_tue_ai_credits_vnd": 200447400,
            "tld_domain_vnd": 770838,
            "fx_rate_vnd_per_usd": 26340,
            "unverified_verbal_claim_vnd": 206000000,
            "unverified_variance_rejected_vnd": -3639362,
        },
        summary="Strict audit of executed corporate sponsorship agreements from BNIX and Phổ Tuệ totaling 202,360,638 VND; rejects verbal 206M claim.",
        owner="S1 Integrator",
        verified_at="2026-10-18T18:30:00Z",
    ),
    CanonicalEvidencePointer(
        pointer_id="EVID-FIN-003",
        domain=RbpcEvidenceDomain.finances,
        title="Dual P&L Pro-Forma: Sponsored Runway vs Commercial Replacement",
        doc_ref="docs/rbpc/FINANCIAL_ASSUMPTIONS.md",
        version="1.0.0",
        status=RbpcEvidencePointerStatus.active_verified,
        hash_sha256=_hash_text("DOC-DUAL-PL-SPONSORED-VS-COMMERCIAL"),
        metrics_payload={
            "annual_gbv_12m_vnd": 1050000000,
            "artisan_retained_12m_vnd": 945000000,
            "platform_revenue_12m_vnd": 105000000,
            "sponsored_cogs_vnd": 0,
            "commercial_shadow_cogs_vnd": 4624900,
            "operating_expenses_12m_vnd": 14000000,
            "net_operating_profit_sponsored_vnd": 91000000,
            "net_operating_profit_commercial_vnd": 86375100,
            "net_margin_sponsored_percent": 86.7,
            "net_margin_commercial_percent": 82.3,
        },
        summary="Dual P&L pro-forma verifying long-term commercial survival and self-sufficiency even if all in-kind sponsorships cease.",
        owner="S3 Business Lead",
        verified_at="2026-10-18T19:00:00Z",
    ),

    # ---------------- 5. IMPACT DOMAIN ----------------
    CanonicalEvidencePointer(
        pointer_id="EVID-IMP-001",
        domain=RbpcEvidenceDomain.impact,
        title="UN SDG 8 Decent Work & Artisan Wage Retention Framework",
        doc_ref="docs/rbpc/PITCH_EXHIBITS.md",
        version="1.0.0",
        status=RbpcEvidencePointerStatus.active_verified,
        hash_sha256=_hash_text("DOC-SDG8-DECENT-WORK-ARTISAN-RETENTION"),
        metrics_payload={
            "direct_artisan_retention_percent": 90.0,
            "commission_reinvestment_pledge_percent": 50.0,
            "monthly_wage_uplift_min_vnd": 4200000,
            "monthly_wage_uplift_max_vnd": 12600000,
            "youth_guild_apprenticeship_hours_target": 240,
            "un_sdg_targets": ["8.5", "8.9"],
        },
        summary="Measurement methodology ensuring 90% direct economic transfer to artisan households and 50% commission reinvestment into youth apprenticeships.",
        owner="S3 Business Lead",
        verified_at="2026-10-18T20:00:00Z",
    ),
    CanonicalEvidencePointer(
        pointer_id="EVID-IMP-002",
        domain=RbpcEvidenceDomain.impact,
        title="UN SDG 4 Quality Education & Verified Open Cultural Literacy",
        doc_ref="docs/rbpc/CUSTOMER_VALUE_METRICS.md",
        version="1.0.0",
        status=RbpcEvidencePointerStatus.active_verified,
        hash_sha256=_hash_text("DOC-SDG4-QUALITY-EDUCATION-OPEN-LITERACY"),
        metrics_payload={
            "historical_provenance_citation_rate_percent": 100.0,
            "open_cultural_literacy_target_readers": 18000,
            "living_ateliers_documented": 5,
            "un_sdg_targets": ["4.7"],
            "free_public_educational_access_percent": 100.0,
        },
        summary="Educational metrics verifying 100% cited primary source provenance, open cultural literacy access, and living craft oral histories.",
        owner="S2 Historian",
        verified_at="2026-10-18T20:30:00Z",
    ),

    # ---------------- 6. LEGAL DOMAIN ----------------
    CanonicalEvidencePointer(
        pointer_id="EVID-LEG-001",
        domain=RbpcEvidenceDomain.legal,
        title="Creator Oral History Consent & Right of Erasure SLA",
        doc_ref="docs/rbpc/CONTENT_RIGHTS.md",
        version="1.0.0",
        status=RbpcEvidencePointerStatus.active_verified,
        hash_sha256=_hash_text("DOC-CREATOR-RIGHTS-AND-ERASURE-POLICY"),
        metrics_payload={
            "consent_model": "bilingual_written",
            "revocation_policy": "immediate_cascade",
            "right_of_erasure_sla_hours": 24,
            "minor_pii_storage": "prohibited",
            "data_residency": "Vietnam",
        },
        summary="Governance charter protecting living artisans with versioned audio release waivers and strict 24-hour right of erasure.",
        owner="S1 Integrator",
        verified_at="2026-10-16T12:00:00Z",
    ),
    CanonicalEvidencePointer(
        pointer_id="EVID-LEG-002",
        domain=RbpcEvidenceDomain.legal,
        title="Corporate In-Kind Sponsorship Executed Contracts",
        doc_ref="docs/rbpc/BASELINE.md",
        version="1.0.0",
        status=RbpcEvidencePointerStatus.active_verified,
        hash_sha256=_hash_text("DOC-EXECUTED-SPONSORSHIPS-BNIX-PHOTUE"),
        metrics_payload={
            "agreements_count": 2,
            "bnix_contract_status": "fully_executed",
            "pho_tue_contract_status": "fully_executed",
            "governing_law": "Vietnam",
            "audit_compliance_status": "PASS",
        },
        summary="Executed contracts with BNIX Infrastructure Solutions and Phổ Tuệ Technology Solutions guaranteeing infrastructure runway.",
        owner="S1 Integrator",
        verified_at="2026-10-17T15:00:00Z",
    ),

    # ---------------- 7. TEAM DOMAIN ----------------
    CanonicalEvidencePointer(
        pointer_id="EVID-TEAM-001",
        domain=RbpcEvidenceDomain.team,
        title="Core Student Founder Cap Table & S1–S4 Architecture",
        doc_ref="docs/rbpc/PITCH_THESIS.md",
        version="1.0.0",
        status=RbpcEvidencePointerStatus.active_verified,
        hash_sha256=_hash_text("DOC-TEAM-FOUNDERS-CAP-TABLE-S1-S4"),
        metrics_payload={
            "founder_count": 4,
            "student_roles": ["S1 Integrator", "S2 Historian", "S3 Business Lead", "S4 Frontend Lead"],
            "equity_vesting_years": 4,
            "monthly_committed_hours_per_founder": 120,
            "ip_assignment_status": "fully_assigned",
        },
        summary="Four multidisciplinary student co-founders with balanced tech, heritage curation, and commercial execution capability.",
        owner="S3 Business Lead",
        verified_at="2026-10-15T09:00:00Z",
    ),
    CanonicalEvidencePointer(
        pointer_id="EVID-TEAM-002",
        domain=RbpcEvidenceDomain.team,
        title="Academic Advisory Board & Heritage Mentorship Roster",
        doc_ref="docs/rbpc/PITCH_EXHIBITS.md",
        version="1.0.0",
        status=RbpcEvidencePointerStatus.active_verified,
        hash_sha256=_hash_text("DOC-TEAM-ADVISORY-BOARD-MENTORS"),
        metrics_payload={
            "advisory_board_members": 3,
            "advisory_institutions": [
                "Huế Imperial Monuments Conservation Centre",
                "RMIT University School of Business & Management",
                "Thừa Thiên Huế Traditional Craft Association",
            ],
            "quarterly_editorial_review": True,
        },
        summary="External advisory roster ensuring historiographical fidelity and institutional enterprise alignment.",
        owner="S2 Historian",
        verified_at="2026-10-16T10:00:00Z",
    ),
]


@dataclass
class PitchClaimItem:
    claim_text: str
    domain: str
    evidence_pointer_id: Optional[str] = None
    metric_key: Optional[str] = None
    claimed_value: Optional[Any] = None
    is_quantitative: bool = True
    truth_tier: str = "OBSERVED"  # OBSERVED, HYPOTHESIS, FORECAST


@dataclass
class PitchClaimAuditFinding:
    claim_text: str
    domain: str
    evidence_pointer_id: Optional[str]
    status: str  # RbpcPitchClaimStatus enum value
    is_grounded: bool
    discrepancy_notes: Optional[str] = None
    verified_metric_value: Optional[Any] = None
    claimed_metric_value: Optional[Any] = None


@dataclass
class PitchReviewReport:
    audit_ref: str
    pitch_deck_title: str
    deck_version: str
    total_claims_audited: int
    verified_claims_count: int
    ungrounded_claims_count: int
    pitch_readiness: str  # RbpcPitchReadiness enum value
    findings: List[PitchClaimAuditFinding]
    summary_notes: str
    reviewed_at: str

    def to_dict(self) -> dict:
        return {
            "audit_ref": self.audit_ref,
            "pitch_deck_title": self.pitch_deck_title,
            "deck_version": self.deck_version,
            "total_claims_audited": self.total_claims_audited,
            "verified_claims_count": self.verified_claims_count,
            "ungrounded_claims_count": self.ungrounded_claims_count,
            "pitch_readiness": self.pitch_readiness,
            "findings": [asdict(f) for f in self.findings],
            "summary_notes": self.summary_notes,
            "reviewed_at": self.reviewed_at,
        }


class StartupEvidenceRoomService:
    """Manages versioned evidence room pointers and evaluates pitch claim grounding."""

    def __init__(self, canonical_pointers: Optional[Sequence[CanonicalEvidencePointer]] = None):
        self._pointers: Dict[str, CanonicalEvidencePointer] = {}
        for p in (canonical_pointers or CANONICAL_EVIDENCE_POINTERS):
            self._pointers[p.pointer_id] = p

    def get_all_pointers(
        self,
        domain: Optional[Union[str, RbpcEvidenceDomain]] = None,
        status: Optional[Union[str, RbpcEvidencePointerStatus]] = None,
    ) -> List[CanonicalEvidencePointer]:
        """Query evidence room pointers with optional domain or status filter."""
        results = list(self._pointers.values())
        if domain is not None:
            domain_val = domain.value if isinstance(domain, RbpcEvidenceDomain) else str(domain)
            results = [p for p in results if p.domain.value == domain_val]
        if status is not None:
            status_val = status.value if isinstance(status, RbpcEvidencePointerStatus) else str(status)
            results = [p for p in results if p.status.value == status_val]
        return sorted(results, key=lambda x: (x.domain.value, x.pointer_id))

    def get_pointer(self, pointer_id: str) -> Optional[CanonicalEvidencePointer]:
        return self._pointers.get(pointer_id)

    def register_pointer(self, pointer: CanonicalEvidencePointer) -> None:
        self._pointers[pointer.pointer_id] = pointer

    def evaluate_pitch_claims(
        self,
        deck_title: str,
        deck_version: str,
        claims: Sequence[Union[PitchClaimItem, Dict[str, Any]]],
        audit_ref: Optional[str] = None,
    ) -> PitchReviewReport:
        """Evaluate pitch claims against evidence pointers under strict negative abuse invariants.

        Negative abuse guardrails:
        1. Every quantitative pitch claim must have an immutable evidence reference and status.
        2. If evidence pointer is missing, invalid, or not active_verified -> UNGROUNDED_FLAGGED.
        3. If metric_key claimed value contradicts verified payload -> UNGROUNDED_FLAGGED.
        4. If ANY claim is ungrounded -> pitch_readiness is FLAGGED_UNREADY.
        5. Approved for pitch ONLY if total_claims > 0 and ungrounded_claims == 0.
        """
        audit_id = audit_ref or f"AUDIT-PITCH-{uuid.uuid4().hex[:8].upper()}"
        findings: List[PitchClaimAuditFinding] = []
        verified_count = 0
        ungrounded_count = 0

        for raw_c in claims:
            if isinstance(raw_c, dict):
                c = PitchClaimItem(
                    claim_text=raw_c.get("claim_text", ""),
                    domain=raw_c.get("domain", "product"),
                    evidence_pointer_id=raw_c.get("evidence_pointer_id"),
                    metric_key=raw_c.get("metric_key"),
                    claimed_value=raw_c.get("claimed_value"),
                    is_quantitative=raw_c.get("is_quantitative", True),
                    truth_tier=raw_c.get("truth_tier", "OBSERVED"),
                )
            else:
                c = raw_c

            is_grounded = True
            finding_status = RbpcPitchClaimStatus.verified_observed.value
            discrepancy = None
            verified_val = None

            # Negative abuse check 1: Quantitative claim must reference evidence
            if c.is_quantitative and not c.evidence_pointer_id:
                is_grounded = False
                finding_status = RbpcPitchClaimStatus.ungrounded_flagged.value
                discrepancy = "Negative abuse violation: Quantitative claim lacks mandatory evidence pointer reference."

            # Negative abuse check 2: Evidence pointer existence
            elif c.evidence_pointer_id:
                pointer = self.get_pointer(c.evidence_pointer_id)
                if not pointer:
                    is_grounded = False
                    finding_status = RbpcPitchClaimStatus.ungrounded_flagged.value
                    discrepancy = f"Negative abuse violation: Evidence pointer '{c.evidence_pointer_id}' does not exist in evidence room."
                elif pointer.status != RbpcEvidencePointerStatus.active_verified:
                    is_grounded = False
                    finding_status = RbpcPitchClaimStatus.ungrounded_flagged.value
                    discrepancy = (
                        f"Negative abuse violation: Evidence pointer '{c.evidence_pointer_id}' has status "
                        f"'{pointer.status.value}', not active_verified."
                    )
                else:
                    # Pointer is active and verified, check metric value if metric_key given
                    if c.metric_key:
                        if c.metric_key not in pointer.metrics_payload:
                            is_grounded = False
                            finding_status = RbpcPitchClaimStatus.ungrounded_flagged.value
                            discrepancy = (
                                f"Negative abuse violation: Metric key '{c.metric_key}' not found in evidence payload "
                                f"for pointer '{c.evidence_pointer_id}'."
                            )
                        else:
                            verified_val = pointer.metrics_payload[c.metric_key]
                            if c.claimed_value is not None:
                                is_match = self._compare_metric_values(c.claimed_value, verified_val)
                                if not is_match:
                                    is_grounded = False
                                    finding_status = RbpcPitchClaimStatus.ungrounded_flagged.value
                                    discrepancy = (
                                        f"Negative abuse discrepancy: Claimed value '{c.claimed_value}' contradicts "
                                        f"verified evidence '{verified_val}'."
                                    )

                    if is_grounded:
                        # Map truth tier to verified status
                        if c.truth_tier == "HYPOTHESIS":
                            finding_status = RbpcPitchClaimStatus.verified_hypothesis.value
                        elif c.truth_tier == "FORECAST":
                            finding_status = RbpcPitchClaimStatus.verified_projection.value
                        else:
                            finding_status = RbpcPitchClaimStatus.verified_observed.value

            if is_grounded:
                verified_count += 1
            else:
                ungrounded_count += 1

            findings.append(
                PitchClaimAuditFinding(
                    claim_text=c.claim_text,
                    domain=c.domain,
                    evidence_pointer_id=c.evidence_pointer_id,
                    status=finding_status,
                    is_grounded=is_grounded,
                    discrepancy_notes=discrepancy,
                    verified_metric_value=verified_val,
                    claimed_metric_value=c.claimed_value,
                )
            )

        if len(claims) == 0:
            pitch_readiness = RbpcPitchReadiness.flagged_unready.value
            summary_notes = "Audit rejected: Zero claims submitted for pitch review."
        elif ungrounded_count > 0:
            pitch_readiness = RbpcPitchReadiness.flagged_unready.value
            summary_notes = (
                f"FLAGGED UNREADY: Detected {ungrounded_count} ungrounded quantitative assertions "
                f"out of {len(claims)} audited. Correction or evidence submission required before pitch."
            )
        else:
            pitch_readiness = RbpcPitchReadiness.approved_for_pitch.value
            summary_notes = (
                f"APPROVED FOR PITCH: 100% of {len(claims)} quantitative pitch claims are rigorously "
                f"grounded against active verified evidence room pointers."
            )

        return PitchReviewReport(
            audit_ref=audit_id,
            pitch_deck_title=deck_title,
            deck_version=deck_version,
            total_claims_audited=len(claims),
            verified_claims_count=verified_count,
            ungrounded_claims_count=ungrounded_count,
            pitch_readiness=pitch_readiness,
            findings=findings,
            summary_notes=summary_notes,
            reviewed_at=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _compare_metric_values(claimed: Any, verified: Any) -> bool:
        """Compare claimed versus verified values with numeric normalization."""
        if claimed == verified:
            return True
        try:
            # Handle numeric types (int, float)
            num_claimed = float(str(claimed).replace(",", "").replace("VND", "").replace("%", "").strip())
            num_verified = float(str(verified).replace(",", "").replace("VND", "").replace("%", "").strip())
            # Within 0.05% relative tolerance
            if num_verified != 0:
                rel_diff = abs(num_claimed - num_verified) / abs(num_verified)
                return rel_diff <= 0.0005
            return num_claimed == num_verified
        except (ValueError, TypeError):
            # Fall back to string comparison
            return str(claimed).strip().lower() == str(verified).strip().lower()

    # ---------------- Export Utilities ----------------

    def export_evidence_room_json(self) -> str:
        """Export evidence room catalog as formatted JSON."""
        pointers = self.get_all_pointers()
        domains_count: Dict[str, int] = {}
        for p in pointers:
            domains_count[p.domain.value] = domains_count.get(p.domain.value, 0) + 1

        payload = {
            "title": "LƯU NIÊN RBPC 2026 Startup Evidence Room",
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "domains_covered": [d.value for d in RbpcEvidenceDomain],
            "summary": {
                "total_pointers": len(pointers),
                "domain_breakdown": domains_count,
                "verified_active_count": sum(1 for p in pointers if p.status == RbpcEvidencePointerStatus.active_verified),
            },
            "evidence_pointers": [p.to_dict() for p in pointers],
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def export_evidence_room_markdown(self) -> str:
        """Export evidence room catalog as Markdown table."""
        pointers = self.get_all_pointers()
        lines = [
            "# LƯU NIÊN — Startup Evidence Room & Verification Ledger",
            "",
            "**Classification:** RBPC 2026 Due Diligence & Investor Evidence Room  ",
            f"**Last Audited:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}  ",
            f"**Total Registered Pointers:** {len(pointers)}  ",
            "",
            "---",
            "",
            "## 1. Domain Coverage & Invariant Summary",
            "",
            "Every quantitative pitch assertion must trace to an immutable evidence pointer in one of 7 canonical domains:",
            "1. **product** | 2. **customer** | 3. **market** | 4. **finances** | 5. **impact** | 6. **legal** | 7. **team**",
            "",
            "---",
            "",
            "## 2. Master Evidence Pointer Registry",
            "",
            "| Pointer ID | Domain | Title | Doc Ref | Version | Status | Owner | SHA-256 Digest |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for p in pointers:
            short_sha = p.hash_sha256[:12] + "..." if len(p.hash_sha256) > 15 else p.hash_sha256
            lines.append(
                f"| `{p.pointer_id}` | `{p.domain.value}` | {p.title} | `{p.doc_ref}` | v{p.version} | `{p.status.value}` | {p.owner} | `{short_sha}` |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 3. Negative Abuse Guardrail Invariant",
            "",
            "> **Enforced Rule:**",
            "> Any pitch deck slide containing ungrounded numbers, unsupported verbal approximations,",
            "> or metric inflation is marked `UNGROUNDED_FLAGGED` with deck readiness `FLAGGED_UNREADY`.",
            "> Only decks with 100% verified evidence grounding may display the `APPROVED_FOR_PITCH` certification.",
        ])
        return "\n".join(lines)

    def export_pitch_review_markdown(self, report: PitchReviewReport) -> str:
        """Export a pitch review report as a Markdown due diligence audit document."""
        lines = [
            f"# LƯU NIÊN — Pitch Review Audit Report: `{report.audit_ref}`",
            "",
            f"**Deck Title:** {report.pitch_deck_title} (v{report.deck_version})  ",
            f"**Audit Timestamp:** {report.reviewed_at}  ",
            f"**Pitch Readiness:** `{report.pitch_readiness}`  ",
            f"**Score:** {report.verified_claims_count}/{report.total_claims_audited} Grounded Claims  ",
            "",
            "---",
            "",
            f"### Executive Finding: {report.summary_notes}",
            "",
            "### Itemized Claims Audit",
            "",
            "| Status | Domain | Evidence Ref | Pitch Claim Assertion | Discrepancy / Audit Finding |",
            "|---|---|---|---|---|",
        ]
        for f in report.findings:
            ref_badge = f"`{f.evidence_pointer_id}`" if f.evidence_pointer_id else "❌ NONE"
            disc = f.discrepancy_notes or "✅ Verified against evidence room"
            lines.append(f"| `{f.status}` | `{f.domain}` | {ref_badge} | {f.claim_text} | {disc} |")

        return "\n".join(lines)

    # ---------------- Database Persistence Helpers ----------------

    def seed_db(self, db: Session) -> int:
        """Seed canonical pointers into PostgreSQL rbpc_evidence_room_pointers table."""
        count = 0
        now = datetime.now(timezone.utc)
        for cp in self.get_all_pointers():
            existing = db.scalar(
                select(RbpcEvidencePointer).where(RbpcEvidencePointer.pointer_id == cp.pointer_id)
            )
            parsed_dt = datetime.fromisoformat(cp.verified_at.replace("Z", "+00:00"))
            if not existing:
                row = RbpcEvidencePointer(
                    pointer_id=cp.pointer_id,
                    domain=cp.domain.value,
                    title=cp.title,
                    doc_ref=cp.doc_ref,
                    version=cp.version,
                    status=cp.status.value,
                    hash_sha256=cp.hash_sha256,
                    metrics_payload=cp.metrics_payload,
                    summary=cp.summary,
                    owner=cp.owner,
                    verified_at=parsed_dt,
                    created_at=now,
                    updated_at=now,
                )
                db.add(row)
                count += 1
            else:
                existing.title = cp.title
                existing.doc_ref = cp.doc_ref
                existing.version = cp.version
                existing.status = cp.status.value
                existing.hash_sha256 = cp.hash_sha256
                existing.metrics_payload = cp.metrics_payload
                existing.summary = cp.summary
                existing.owner = cp.owner
                existing.verified_at = parsed_dt
                existing.updated_at = now
        db.commit()
        return count

    def persist_pitch_review(
        self,
        db: Session,
        report: PitchReviewReport,
        reviewed_by_id: Optional[uuid.UUID] = None,
    ) -> RbpcPitchReview:
        """Persist pitch review report into rbpc_pitch_reviews table."""
        now = datetime.now(timezone.utc)
        review_row = RbpcPitchReview(
            audit_ref=report.audit_ref,
            pitch_deck_title=report.pitch_deck_title,
            deck_version=report.deck_version,
            total_claims_audited=report.total_claims_audited,
            verified_claims_count=report.verified_claims_count,
            ungrounded_claims_count=report.ungrounded_claims_count,
            pitch_readiness=report.pitch_readiness,
            claims_payload=[asdict(f) for f in report.findings],
            audit_findings={
                "summary_notes": report.summary_notes,
                "findings_count": len(report.findings),
            },
            reviewed_by_id=reviewed_by_id,
            reviewed_at=datetime.fromisoformat(report.reviewed_at.replace("Z", "+00:00")),
            created_at=now,
            updated_at=now,
        )
        db.add(review_row)
        db.commit()
        db.refresh(review_row)
        return review_row


# Global default service instance
default_evidence_room_service = StartupEvidenceRoomService()
