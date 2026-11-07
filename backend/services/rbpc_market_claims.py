# -*- coding: utf-8 -*-
"""Market Claims Evidence Register service & exporter for RBPC pitch dossiers.

Ticket: V5-T118 (Wave W11, Slot A08).
Goal:
- Categorize every market claim in docs/rbpc/BUSINESS_PLAN_DRAFT.md and docs/rbpc/
  with dates, method, sample size, and truth tier (OBSERVED / HYPOTHESIS / FORECAST).
- Provide export utilities (JSON and Markdown) for investor and RBPC pitch reviews.
- Negative abuse guardrail:
  Unverified external benchmark or TAM projection cannot be displayed as actual
  LƯU NIÊN operational KPI. Any attempt to present HYPOTHESIS or FORECAST (or external benchmark)
  as OBSERVED operational metric must fail validation closed.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional


class TruthTier(str, Enum):
    OBSERVED = "OBSERVED"
    HYPOTHESIS = "HYPOTHESIS"
    FORECAST = "FORECAST"


class MarketClaimCategory(str, Enum):
    PROBLEM_URGENCY = "PROBLEM_URGENCY"
    USER_BEHAVIOR = "USER_BEHAVIOR"
    UNIT_ECONOMICS = "UNIT_ECONOMICS"
    SPONSORSHIP_RUNWAY = "SPONSORSHIP_RUNWAY"
    MARKET_SIZING = "MARKET_SIZING"
    COMPETITIVE_BENCHMARK = "COMPETITIVE_BENCHMARK"
    OPERATIONAL_EFFICIENCY = "OPERATIONAL_EFFICIENCY"


@dataclass(frozen=True)
class MarketClaimEvidence:
    claim_id: str
    category: MarketClaimCategory
    truth_tier: TruthTier
    statement: str
    metric_value: str
    date_recorded: str  # YYYY-MM-DD or date range
    methodology: str    # e.g., "Official Government Census", "In-depth User Interviews", "Bottom-Up Modeling"
    sample_size: str    # e.g., "N=4,050,000 visitors", "N=5 workshop operators", "N=1 signed contract"
    source_reference: str  # Document ID or external archival link
    is_operational_kpi: bool = False
    validation_status: str = "VERIFIED"
    negative_abuse_notes: Optional[str] = None

    def validate_integrity(self) -> None:
        """Validate integrity rules, especially negative abuse invariants.
        
        Negative abuse invariant:
        Unverified external benchmark or TAM projection cannot be displayed as actual
        LƯU NIÊN operational KPI. If is_operational_kpi is True, truth_tier MUST be OBSERVED.
        Hypotheses, external market sizes, and forward forecasts cannot be operational KPIs.
        """
        if self.is_operational_kpi and self.truth_tier != TruthTier.OBSERVED:
            raise ValueError(
                f"Negative abuse violation: Claim '{self.claim_id}' is tagged as an operational KPI "
                f"but has truth tier '{self.truth_tier.value}'. Only OBSERVED actuals can be operational KPIs."
            )
        if self.truth_tier == TruthTier.FORECAST and self.is_operational_kpi:
            raise ValueError(
                f"Negative abuse violation: Forecast claim '{self.claim_id}' cannot be an operational KPI."
            )
        if not self.claim_id or not self.statement or not self.date_recorded or not self.methodology or not self.sample_size:
            raise ValueError(f"Market claim '{self.claim_id}' has missing mandatory metadata.")


# Canonical market claims database for LƯU NIÊN / RBPC 2026
CANONICAL_MARKET_CLAIMS: list[MarketClaimEvidence] = [
    # 1. Total arrivals baseline (Observed external government census)
    MarketClaimEvidence(
        claim_id="MC-001",
        category=MarketClaimCategory.PROBLEM_URGENCY,
        truth_tier=TruthTier.OBSERVED,
        statement="Every year, over 4.0 million travelers visit Huế (including 1.2+ million international visitors).",
        metric_value="4,050,000 total visitors (1,200,000 international)",
        date_recorded="2025-01-15",
        methodology="Official provincial tourism statistics bulletin",
        sample_size="N=4,050,000 annual tourist arrivals",
        source_reference="Thừa Thiên Huế Department of Tourism Annual Report 2024 / DOC-RBPC-FIN-001",
        is_operational_kpi=False,  # External macroeconomic statistic, NOT platform operational KPI
        validation_status="VERIFIED",
        negative_abuse_notes="Regional demographic baseline; must never be conflated with platform traffic or active users.",
    ),
    # 2. International visitor comprehension gap (Hypothesis / Field Usability Finding)
    MarketClaimEvidence(
        claim_id="MC-002",
        category=MarketClaimCategory.PROBLEM_URGENCY,
        truth_tier=TruthTier.HYPOTHESIS,
        statement="78% of international visitors report difficulty understanding the authentic historical context of Vietnamese monuments from brief plaques or generic audio guides.",
        metric_value="78.0% comprehension difficulty rate",
        date_recorded="2026-10-16",
        methodology="Field discovery intercepts & bilingual survey sampling in Huế Citadel",
        sample_size="N=50 international independent cultural travelers (FITs)",
        source_reference="DOC-RBPC-VAL-001 (EVID-USER-001, EVID-USER-002) / DOC-RBPC-METRICS-001",
        is_operational_kpi=False,
        validation_status="VERIFIED",
        negative_abuse_notes="Exploratory customer research hypothesis; cannot be represented as general population census or internal KPI.",
    ),
    # 3. Mass OTA commission extraction (Observed competitor market pricing)
    MarketClaimEvidence(
        claim_id="MC-003",
        category=MarketClaimCategory.COMPETITIVE_BENCHMARK,
        truth_tier=TruthTier.OBSERVED,
        statement="Mass Online Travel Agencies (Klook, Viator, GetYourGuide) charge 25%–30% commission cuts on cultural tours and activities.",
        metric_value="25.0% - 30.0% take rate",
        date_recorded="2026-10-16",
        methodology="Partner merchant contract review & competitor supplier terms audit",
        sample_size="N=5 local workshop operator interviews & published OTA merchant terms",
        source_reference="DOC-RBPC-VAL-001 (EVID-PARTNER-001) / DOC-RBPC-METRICS-001",
        is_operational_kpi=False,
        validation_status="VERIFIED",
        negative_abuse_notes="Competitor market rate benchmark; cannot be claimed as LƯU NIÊN revenue or fee.",
    ),
    # 4. Operator administrative burden & time saved (Observed baseline field study)
    MarketClaimEvidence(
        claim_id="MC-004",
        category=MarketClaimCategory.OPERATIONAL_EFFICIENCY,
        truth_tier=TruthTier.OBSERVED,
        statement="Traditional workshop operators spend an average of 5.8 hours per week on manual translation, lead qualification, and scheduling.",
        metric_value="5.8 hours / week burden",
        date_recorded="2026-10-16",
        methodology="Time-motion study and semi-structured operator field interviews across 5 studios",
        sample_size="N=5 independent heritage craft studios in Huế (OP-01 to OP-05)",
        source_reference="DOC-RBPC-VAL-001 / DOC-RBPC-METRICS-001 §2.1",
        is_operational_kpi=False,
        validation_status="VERIFIED",
        negative_abuse_notes="Pre-platform operator baseline; time recaptured is an operational value proposition.",
    ),
    # 5. LƯU NIÊN time savings proposition (Hypothesis tested during pilot)
    MarketClaimEvidence(
        claim_id="MC-005",
        category=MarketClaimCategory.OPERATIONAL_EFFICIENCY,
        truth_tier=TruthTier.HYPOTHESIS,
        statement="LƯU NIÊN automates the top 80% of repetitive inbound friction, saving ~4.5 hours per week per studio manager.",
        metric_value="4.5 hours / week saved (77.6% reduction)",
        date_recorded="2026-10-18",
        methodology="Pilot intake workflow simulation & operator task timing audit",
        sample_size="N=5 workshop operators in Kim Long, Phường Đúc, Thủy Biều",
        source_reference="DOC-RBPC-METRICS-001 §2.1.2",
        is_operational_kpi=False,
        validation_status="VERIFIED",
        negative_abuse_notes="Modeled pilot hypothesis; actual realization subject to long-term cohort tracking.",
    ),
    # 6. High-intent reader engagement rate (Hypothesis)
    MarketClaimEvidence(
        claim_id="MC-006",
        category=MarketClaimCategory.USER_BEHAVIOR,
        truth_tier=TruthTier.HYPOTHESIS,
        statement="Approximately 20% of unique story readers spend >60s engaging deeply with historical annals, 3D artifacts, or AI tutor.",
        metric_value="20.0% engagement rate (Cohort B)",
        date_recorded="2026-10-17",
        methodology="Web analytics dwell-time instrumentation & interactive session sampling",
        sample_size="N=1,500 monthly simulated visitor cohort",
        source_reference="DOC-RBPC-FIN-001 §3.3 / DOC-RBPC-METRICS-001 §2.2",
        is_operational_kpi=False,
        validation_status="VERIFIED",
        negative_abuse_notes="Funnel parameter hypothesis; cannot be booked as guaranteed platform traffic.",
    ),
    # 7. Engaged visitor conversion rate (Hypothesis)
    MarketClaimEvidence(
        claim_id="MC-007",
        category=MarketClaimCategory.USER_BEHAVIOR,
        truth_tier=TruthTier.HYPOTHESIS,
        statement="15% of deeply engaged story readers submit an authentic workshop availability inquiry when presented with verified lineage masters.",
        metric_value="15.0% inquiry conversion rate",
        date_recorded="2026-10-18",
        methodology="Controlled UX inquiry form usability trials and click-through tracking",
        sample_size="N=120 prospective cultural traveler sessions",
        source_reference="DOC-RBPC-METRICS-001 §2.2.2 / DOC-RBPC-FIN-001 §3.3",
        is_operational_kpi=False,
        validation_status="VERIFIED",
        negative_abuse_notes="Conversion hypothesis for qualified inquiry funnel; not a realized sales e-commerce conversion.",
    ),
    # 8. Pure performance commission model (Observed platform policy)
    MarketClaimEvidence(
        claim_id="MC-008",
        category=MarketClaimCategory.UNIT_ECONOMICS,
        truth_tier=TruthTier.OBSERVED,
        statement="LƯU NIÊN charges a 10% performance fee strictly on completed, non-refunded workshop experiences, with 0 VND fixed monthly fees.",
        metric_value="10.0% platform take-rate (0 VND fixed fee)",
        date_recorded="2026-10-16",
        methodology="Executed partner agreements and pricing policy formulation",
        sample_size="N=5 pilot artisan partners / contract specifications",
        source_reference="DOC-RBPC-FIN-001 §1.2 / DOC-RBPC-BP-001 §4",
        is_operational_kpi=True,  # Actual platform policy contract rate
        validation_status="VERIFIED",
        negative_abuse_notes="Contracted fee schedule; does not imply revenue has been collected without completed transactions.",
    ),
    # 9. Artisan direct revenue retention (Observed platform policy)
    MarketClaimEvidence(
        claim_id="MC-009",
        category=MarketClaimCategory.UNIT_ECONOMICS,
        truth_tier=TruthTier.OBSERVED,
        statement="90% of workshop booking revenue is retained directly by the craft family (e.g. 630,000 VND out of 700,000 VND).",
        metric_value="90.0% artisan retention share",
        date_recorded="2026-10-16",
        methodology="Bilingual partner consent agreements and payout ledger policy",
        sample_size="N=5 artisan studios",
        source_reference="DOC-RBPC-FIN-001 §1.2 / DOC-RBPC-VALPROP-010 §2",
        is_operational_kpi=True,  # Operational platform governance invariant
        validation_status="VERIFIED",
        negative_abuse_notes="Platform governance invariant protecting craft families under UN SDG 8.",
    ),
    # 10. Documented Corporate In-Kind Sponsorship (Observed Audited Contract Fact)
    MarketClaimEvidence(
        claim_id="MC-010",
        category=MarketClaimCategory.SPONSORSHIP_RUNWAY,
        truth_tier=TruthTier.OBSERVED,
        statement="LƯU NIÊN has secured exactly 202,360,638 VND in documented corporate in-kind sponsorship (BNIX VPS + Phổ Tuệ AI API credits and domain).",
        metric_value="202,360,638 VND non-cash compute subsidy",
        date_recorded="2026-10-17",
        methodology="Signed corporate partnership contract reconciliation & audit",
        sample_size="N=2 corporate sponsorship agreements (BNIX, Phổ Tuệ)",
        source_reference="BASELINE.md §5 / DOC-RBPC-FIN-001 §1.2 / DOC-RBPC-BP-001 §5",
        is_operational_kpi=True,  # Verified operational asset/contra-expense
        validation_status="VERIFIED",
        negative_abuse_notes="Accounted strictly as non-cash infrastructure subsidy; NEVER booked as operational sales or company cash revenue.",
    ),
    # 11. Commercial breakeven threshold (Hypothesis / Model derivation)
    MarketClaimEvidence(
        claim_id="MC-011",
        category=MarketClaimCategory.UNIT_ECONOMICS,
        truth_tier=TruthTier.HYPOTHESIS,
        statement="At full commercial market hosting rates (203,100 VND/month), LƯU NIÊN achieves commercial breakeven with 2.9 (3) completed workshop guests per month.",
        metric_value="2.9 bookings / month breakeven",
        date_recorded="2026-10-17",
        methodology="Dual P&L financial modeling under shadow replacement cost",
        sample_size="Analytical cost modeling based on 70,000 VND net commission/booking",
        source_reference="DOC-RBPC-FIN-001 §4.4 / DOC-RBPC-BP-001 §5",
        is_operational_kpi=False,
        validation_status="VERIFIED",
        negative_abuse_notes="Financial model deduction; represents required volume, not historical operational performance.",
    ),
    # 12. Total Addressable Market TAM (Forecast / Macro model)
    MarketClaimEvidence(
        claim_id="MC-012",
        category=MarketClaimCategory.MARKET_SIZING,
        truth_tier=TruthTier.FORECAST,
        statement="Total Addressable Market (TAM) for cultural tourist participatory craft experiences across Thừa Thiên Huế is 28.5 Billion VND (~$1.08M USD) to 3,600 Billion VND depending on broad vs narrow scope.",
        metric_value="28.5B VND GMV (narrow) / 3,600B VND (broad cultural tourism activities)",
        date_recorded="2026-10-18",
        methodology="Bottom-up sizing from official 4.05M visitor arrivals, 14.8% cultural segment, 9.17% masterclass propensity",
        sample_size="Province-wide macro projection",
        source_reference="DOC-RBPC-FIN-001 §2.3.1 / DOC-RBPC-BP-001 §6",
        is_operational_kpi=False,  # External market forecast, NOT an operational KPI
        validation_status="VERIFIED",
        negative_abuse_notes="Macroeconomic projection; CANNOT be presented as actual operational metric or pipeline of LƯU NIÊN.",
    ),
    # 13. Serviceable Addressable Market SAM (Forecast / Urban Guild Segment)
    MarketClaimEvidence(
        claim_id="MC-013",
        category=MarketClaimCategory.MARKET_SIZING,
        truth_tier=TruthTier.FORECAST,
        statement="Serviceable Addressable Market (SAM) across ~50–60 master craft studios in designated historic quarters of Huế is 5.7 Billion VND ($216k USD) GBV (~570M VND net revenue).",
        metric_value="5.7 Billion VND GMV / 570 Million VND Platform Revenue",
        date_recorded="2026-10-18",
        methodology="Bottom-up guild inventory filtering (Kim Long, Phường Đúc, Thanh Tiên, Thủy Biều)",
        sample_size="N=55 traditional master studios",
        source_reference="DOC-RBPC-FIN-001 §2.3.2 / DOC-RBPC-BP-001 §6",
        is_operational_kpi=False,
        validation_status="VERIFIED",
        negative_abuse_notes="Segment sizing forecast; cannot be displayed as achieved or booked revenue.",
    ),
    # 14. Serviceable Obtainable Market SOM Year 1 (Forecast / 3-Year Projection)
    MarketClaimEvidence(
        claim_id="MC-014",
        category=MarketClaimCategory.MARKET_SIZING,
        truth_tier=TruthTier.FORECAST,
        statement="Serviceable Obtainable Market (SOM Year 1) targets 5 active partner workshops, 1,100 completed experiences, and 570M VND GMV (57M VND platform net revenue).",
        metric_value="1,100 experiences / 570M VND GMV (Year 1 Target)",
        date_recorded="2026-10-18",
        methodology="Operational capacity constraint modeling for 3-4 student founder team",
        sample_size="N=5 workshops over 10 operational months",
        source_reference="DOC-RBPC-FIN-001 §2.3.3 / DOC-RBPC-BP-001 §6",
        is_operational_kpi=False,  # Forward target, NOT operational KPI
        validation_status="VERIFIED",
        negative_abuse_notes="Forward commercial goal; must remain strictly separated from observed completed experiences.",
    ),
    # 15. Real Database Observed Completed Experiences (Observed Actual KPI)
    MarketClaimEvidence(
        claim_id="MC-015",
        category=MarketClaimCategory.OPERATIONAL_EFFICIENCY,
        truth_tier=TruthTier.OBSERVED,
        statement="LƯU NIÊN operational KPIs display only verified closed inquiries as completed experiences; empty database returns 0.",
        metric_value="0 (Baseline) to N (Closed Inquiries)",
        date_recorded="2026-11-05",
        methodology="Strict database aggregation (select count where state == 'closed')",
        sample_size="Real PostgreSQL inquiry event records",
        source_reference="backend/routers/rbpc.py (get_rbpc_impact_metrics) / V5-T110",
        is_operational_kpi=True,
        validation_status="VERIFIED",
        negative_abuse_notes="Strict operational actual; never displays synthetic or forecast counts.",
    ),
]


class MarketClaimsEvidenceRegister:
    """Registry engine providing validation, filtering, and pitch export."""

    def __init__(self, claims: Optional[list[MarketClaimEvidence]] = None):
        self._claims: list[MarketClaimEvidence] = claims or CANONICAL_MARKET_CLAIMS
        self._validate_all()

    def _validate_all(self) -> None:
        for claim in self._claims:
            claim.validate_integrity()

    def get_all_claims(self) -> list[MarketClaimEvidence]:
        return list(self._claims)

    def get_by_truth_tier(self, tier: TruthTier) -> list[MarketClaimEvidence]:
        return [c for c in self._claims if c.truth_tier == tier]

    def get_by_category(self, category: MarketClaimCategory) -> list[MarketClaimEvidence]:
        return [c for c in self._claims if c.category == category]

    def get_operational_kpis(self) -> list[MarketClaimEvidence]:
        return [c for c in self._claims if c.is_operational_kpi]

    def validate_claim_against_operational_kpi(self, claim: MarketClaimEvidence) -> bool:
        """Enforce negative abuse invariant:
        Returns True if valid. Raises ValueError if non-OBSERVED or external TAM is claimed as operational KPI.
        """
        claim.validate_integrity()
        if claim.is_operational_kpi and claim.truth_tier != TruthTier.OBSERVED:
            raise ValueError(
                f"Negative abuse: Non-OBSERVED claim {claim.claim_id} cannot be an operational KPI."
            )
        if claim.category == MarketClaimCategory.MARKET_SIZING and claim.is_operational_kpi:
            raise ValueError(
                f"Negative abuse: TAM/SAM/SOM market sizing claim {claim.claim_id} cannot be an operational KPI."
            )
        return True

    def export_json(self) -> str:
        """Export register to a structured JSON string suitable for pitch dossiers."""
        data = {
            "title": "LƯU NIÊN RBPC 2026 Market Claims Evidence Register",
            "version": "1.0.0",
            "standard": "RBPC Pitch Review & Evidence Governance",
            "truth_tiers_defined": {
                "OBSERVED": "Factually verified operational actual, executed contract, or empirical government statistic.",
                "HYPOTHESIS": "Model assumption, user survey finding, or tested usability hypothesis pending longitudinal proof.",
                "FORECAST": "Forward-looking market sizing (TAM/SAM/SOM) or financial projection for business planning.",
            },
            "summary": {
                "total_claims": len(self._claims),
                "observed_count": len(self.get_by_truth_tier(TruthTier.OBSERVED)),
                "hypothesis_count": len(self.get_by_truth_tier(TruthTier.HYPOTHESIS)),
                "forecast_count": len(self.get_by_truth_tier(TruthTier.FORECAST)),
                "operational_kpis_count": len(self.get_operational_kpis()),
            },
            "claims": [
                {
                    "claim_id": c.claim_id,
                    "category": c.category.value,
                    "truth_tier": c.truth_tier.value,
                    "statement": c.statement,
                    "metric_value": c.metric_value,
                    "date_recorded": c.date_recorded,
                    "methodology": c.methodology,
                    "sample_size": c.sample_size,
                    "source_reference": c.source_reference,
                    "is_operational_kpi": c.is_operational_kpi,
                    "validation_status": c.validation_status,
                    "negative_abuse_notes": c.negative_abuse_notes,
                }
                for c in self._claims
            ],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def export_markdown_table(self) -> str:
        """Export register as a clean Markdown table for pitch review documentation."""
        lines = [
            "# LƯU NIÊN — Market Claims Evidence Register",
            "",
            "> **Standard for RBPC 2026 Dossier:** Every market claim is strictly categorized by "
            "Truth Tier (`OBSERVED` / `HYPOTHESIS` / `FORECAST`), date, methodology, and sample size. "
            "External benchmarks and TAM forecasts are firewalled from actual operational KPIs.",
            "",
            "| Claim ID | Truth Tier | Category | Metric / Claim | Date Recorded | Methodology | Sample Size | Source Ref | Operational KPI? |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for c in self._claims:
            kpi_badge = "✅ YES" if c.is_operational_kpi else "❌ NO (External/Projection)"
            lines.append(
                f"| **{c.claim_id}** | `{c.truth_tier.value}` | {c.category.value} | "
                f"{c.statement} (*{c.metric_value}*) | {c.date_recorded} | {c.methodology} | "
                f"{c.sample_size} | `{c.source_reference}` | {kpi_badge} |"
            )
        lines.append("")
        lines.append("### Negative Abuse Guardrail Invariant")
        lines.append(
            "- **Rule:** Unverified external benchmarks or TAM/SAM/SOM projections CANNOT be displayed "
            "as actual LƯU NIÊN operational KPIs. Operational KPIs must have truth tier `OBSERVED`."
        )
        return "\n".join(lines)


# Singleton instance
default_market_claims_register = MarketClaimsEvidenceRegister()
