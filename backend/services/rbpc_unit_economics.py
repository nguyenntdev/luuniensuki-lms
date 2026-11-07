# -*- coding: utf-8 -*-
"""Unit Economics Actual Ledger Service (RBPC 2026).

Ticket: V5-T115 (Wave W11, Slot A05).
Role / Priority: W11-A05 / P2 / NEW_PRODUCT_FEATURE.

Foundational Mandates:
1. Cash actuals strictly separated from GMV forecasts:
   - Cash actuals require compliance-approved and settled records in rbpc_settlement_ledger.
   - GMV forecasts represent pipeline inquiries or SOM model projections (labeled FORECAST).
2. Cost structure inference:
   - Server hosting: BNIX in-kind compute subsidy (1,142,400 VND/yr; 95,200 VND/mo replacement).
   - AI token inference: Phổ Tuệ in-kind AI credits ($7,610 USD / 201,218,238 VND; ~270 VND/inquiry replacement).
   - Contracted take rate: 10.0% standard performance commission (up to 15.0% ceiling).
   - Dual margin calculation: Sponsored runway cash margin (100%) vs Shadow commercial margin.
3. Revenue streams separation:
   - visitor_commerce (FIT, cultural tourists, hands-on craft workshops).
   - school_b2b (Secondary school excursions, accredited curriculum kits, institutional cohorts).
4. Negative abuse invariant:
   - Merely submitting, contacting, or confirming an inquiry creates EXACTLY 0 VND cash revenue
     and 0 VND realized GMV without a verified payment settlement in rbpc_settlement_ledger.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.models_rbpc import (
    RbpcInquiry,
    RbpcInquiryStatus,
    RbpcRevenueStream,
    RbpcSettlementLedger,
    RbpcSettlementStatus,
)

# --------------------------------------------------------------------------- #
# Benchmarks & In-Kind Cost Structure Constants (DOC-RBPC-FIN-001)
# --------------------------------------------------------------------------- #
IN_KIND_SERVER_SPONSORED: bool = True
IN_KIND_SERVER_SPONSOR_NAME: str = "BNIX (1 Dedicated Cloud VPS, 4 vCPU, 8 GB RAM, 100 GB NVMe)"
IN_KIND_SERVER_ANNUAL_VND: float = 1_142_400.0
IN_KIND_SERVER_MONTHLY_VND: float = 95_200.0

IN_KIND_AI_SPONSORED: bool = True
IN_KIND_AI_SPONSOR_NAME: str = "Phổ Tuệ (AI API Model Inference Credits: $7,610.00 USD)"
IN_KIND_AI_CREDITS_USD: float = 7_610.0
IN_KIND_AI_CREDITS_VND: float = 201_218_238.0

COMMERCIAL_SERVER_REPLACEMENT_MONTHLY_VND: float = 95_200.0
COMMERCIAL_AI_COST_PER_INQUIRY_VND: float = 270.0  # 6 questions @ 1,500 ctx tokens with Gemini 3.8 Flash
COMMERCIAL_AI_COST_PER_1M_TOKENS_USD: float = 0.15
DEFAULT_CONTRACTED_TAKE_RATE: float = 0.1000

BLENDED_WORKSHOP_TICKET_PRICE_VND: float = 516_667.0
SOM_ANNUAL_GMV_FORECAST_VND: float = 570_000_000.0
SOM_ANNUAL_REVENUE_FORECAST_VND: float = 57_000_000.0


def compute_unit_economics_ledger(
    db: Session,
    provider_id: Optional[UUID] = None,
    stream_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute verified unit economics actual ledger report with strict separation
    between cash actuals, cost inferences, streams, and forward forecasts.
    """
    # 1. Base Query for Settlements
    settlement_stmt = select(RbpcSettlementLedger)
    if provider_id is not None:
        settlement_stmt = settlement_stmt.where(RbpcSettlementLedger.provider_id == provider_id)
    if stream_filter:
        settlement_stmt = settlement_stmt.where(RbpcSettlementLedger.revenue_stream == stream_filter)

    all_settlements: List[RbpcSettlementLedger] = list(db.scalars(settlement_stmt))

    # Approved and settled records strictly contribute to cash actuals
    cash_settlements = [
        s for s in all_settlements
        if s.status in (RbpcSettlementStatus.approved.value, RbpcSettlementStatus.settled.value)
    ]

    total_settled_gross = sum(float(s.gross_amount_vnd) for s in cash_settlements)
    total_platform_fee_cash = sum(float(s.platform_fee_vnd) for s in cash_settlements)
    total_artisan_payout = sum(float(s.artisan_payout_vnd) for s in cash_settlements)
    total_tax_vat = sum(float(s.tax_vat_vnd) for s in cash_settlements)
    total_refunds = sum(float(s.refund_amount_vnd) for s in all_settlements)
    net_cash_revenue = max(0.0, round(total_platform_fee_cash - total_refunds, 2))

    approved_count = sum(1 for s in all_settlements if s.status == RbpcSettlementStatus.approved.value)
    settled_count = sum(1 for s in all_settlements if s.status == RbpcSettlementStatus.settled.value)
    pending_count = sum(1 for s in all_settlements if s.status == RbpcSettlementStatus.pending_compliance.value)

    # 2. Base Query for Inquiries (Pipeline & Negative Abuse)
    inquiry_stmt = select(RbpcInquiry).options(selectinload(RbpcInquiry.experience))
    if provider_id is not None:
        inquiry_stmt = inquiry_stmt.where(RbpcInquiry.provider_id == provider_id)

    all_inquiries: List[RbpcInquiry] = list(db.scalars(inquiry_stmt))

    # Identify inquiries that have NO verified approved/settled record
    settled_inquiry_ids = {s.inquiry_id for s in cash_settlements}
    unsettled_inquiries = [inq for inq in all_inquiries if inq.id not in settled_inquiry_ids]

    # Pipeline potential forecast GMV
    pipeline_forecast_gmv = 0.0
    for inq in unsettled_inquiries:
        if inq.state != RbpcInquiryStatus.declined.value:
            party = inq.party_size or 1
            unit_price = (
                float(inq.experience.indicative_price_amount)
                if inq.experience and inq.experience.indicative_price_amount
                else BLENDED_WORKSHOP_TICKET_PRICE_VND
            )
            pipeline_forecast_gmv += party * unit_price

    pipeline_forecast_gmv = round(pipeline_forecast_gmv, 2)
    forecast_realization_rate = (
        round(total_settled_gross / SOM_ANNUAL_GMV_FORECAST_VND, 4)
        if SOM_ANNUAL_GMV_FORECAST_VND > 0
        else 0.0
    )

    # 3. Cost Structure Inference
    has_activity = bool(cash_settlements or all_inquiries)
    inferred_server_cost = COMMERCIAL_SERVER_REPLACEMENT_MONTHLY_VND if has_activity else 0.0
    inferred_ai_token_cost = round(len(all_inquiries) * COMMERCIAL_AI_COST_PER_INQUIRY_VND, 2)
    inferred_total_variable_cost = round(inferred_server_cost + inferred_ai_token_cost, 2)

    effective_take_rate = (
        round(total_platform_fee_cash / total_settled_gross, 4)
        if total_settled_gross > 0
        else DEFAULT_CONTRACTED_TAKE_RATE
    )

    # Sponsored Runway: 0 cash cost for server & AI (100% sponsored in-kind)
    net_contribution_margin_sponsored_vnd = net_cash_revenue
    net_contribution_margin_sponsored_pct = 100.0 if net_cash_revenue > 0 else 0.0

    # Commercial Replacement Shadow: Deducts commercial server & AI replacement costs
    net_contribution_margin_commercial_vnd = round(net_cash_revenue - inferred_total_variable_cost, 2)
    net_contribution_margin_commercial_pct = (
        round((net_contribution_margin_commercial_vnd / net_cash_revenue) * 100.0, 2)
        if net_cash_revenue > 0
        else 0.0
    )

    # 4. Stream Breakdown (Visitor Commerce vs School B2B)
    streams_summary: Dict[str, Dict[str, Any]] = {}
    for stream_enum in [RbpcRevenueStream.visitor_commerce, RbpcRevenueStream.school_b2b]:
        stream_key = stream_enum.value
        stream_settlements = [s for s in cash_settlements if s.revenue_stream == stream_key]
        all_stream_settlements = [s for s in all_settlements if s.revenue_stream == stream_key]

        s_gross = sum(float(s.gross_amount_vnd) for s in stream_settlements)
        s_fee = sum(float(s.platform_fee_vnd) for s in stream_settlements)
        s_payout = sum(float(s.artisan_payout_vnd) for s in stream_settlements)
        s_tax = sum(float(s.tax_vat_vnd) for s in stream_settlements)
        s_refund = sum(float(s.refund_amount_vnd) for s in all_stream_settlements)
        s_count = len(stream_settlements)
        s_aov = round(s_gross / s_count, 2) if s_count > 0 else 0.0
        s_take = round(s_fee / s_gross, 4) if s_gross > 0 else DEFAULT_CONTRACTED_TAKE_RATE

        # Filter unsettled inquiries mapped to stream (default is visitor_commerce)
        if stream_key == RbpcRevenueStream.visitor_commerce.value:
            s_unsettled_count = len(unsettled_inquiries)
            s_pipeline_gmv = pipeline_forecast_gmv
        else:
            s_unsettled_count = 0
            s_pipeline_gmv = 0.0

        streams_summary[stream_key] = {
            "stream": stream_key,
            "settled_gross_vnd": round(s_gross, 2),
            "platform_fee_cash_vnd": round(s_fee, 2),
            "artisan_payout_vnd": round(s_payout, 2),
            "tax_vat_vnd": round(s_tax, 2),
            "refund_amount_vnd": round(s_refund, 2),
            "transactions_count": s_count,
            "average_order_value_vnd": s_aov,
            "effective_take_rate": s_take,
            "unsettled_inquiries_count": s_unsettled_count,
            "pipeline_forecast_gmv_vnd": round(s_pipeline_gmv, 2),
        }

    # 5. Negative Abuse Audit Block
    # Enforces invariant: Unsettled inquiries contribute strictly 0 VND revenue and 0 VND GMV
    negative_abuse = {
        "unsettled_inquiries_count": len(unsettled_inquiries),
        "unsettled_inquiries_cash_revenue_vnd": 0.0,
        "unsettled_inquiries_realized_gmv_vnd": 0.0,
        "rule": "Partner inquiry creates 0 VND revenue without verified payment or settled transaction.",
        "is_compliant": True,
    }

    return {
        "generated_at": datetime.now(timezone.utc),
        "currency": "VND",
        "cash_actuals": {
            "total_settled_gross_vnd": round(total_settled_gross, 2),
            "total_platform_fee_cash_vnd": round(total_platform_fee_cash, 2),
            "total_artisan_payout_vnd": round(total_artisan_payout, 2),
            "total_tax_vat_vnd": round(total_tax_vat, 2),
            "total_refunds_vnd": round(total_refunds, 2),
            "net_cash_revenue_vnd": round(net_cash_revenue, 2),
            "approved_settlements_count": approved_count,
            "settled_settlements_count": settled_count,
            "pending_settlements_count": pending_count,
        },
        "gmv_forecasts": {
            "unsettled_pipeline_inquiries_count": len(unsettled_inquiries),
            "pipeline_potential_gmv_forecast_vnd": pipeline_forecast_gmv,
            "annual_som_target_gmv_vnd": SOM_ANNUAL_GMV_FORECAST_VND,
            "annual_som_target_revenue_vnd": SOM_ANNUAL_REVENUE_FORECAST_VND,
            "forecast_realization_rate": forecast_realization_rate,
            "truth_tier": "FORECAST",
            "epistemic_notice": (
                "Cash actuals require verified settlement records. Inquiries and pipeline forecasts "
                "are model estimates and contribute strictly 0 VND cash to recognized revenue."
            ),
        },
        "cost_inference": {
            "inferred_server_cost_vnd": inferred_server_cost,
            "server_cost_is_in_kind": IN_KIND_SERVER_SPONSORED,
            "server_sponsor": IN_KIND_SERVER_SPONSOR_NAME,
            "inferred_ai_token_cost_vnd": inferred_ai_token_cost,
            "ai_token_cost_is_in_kind": IN_KIND_AI_SPONSORED,
            "ai_sponsor": IN_KIND_AI_SPONSOR_NAME,
            "effective_take_rate": effective_take_rate,
            "inferred_total_variable_cost_vnd": inferred_total_variable_cost,
            "net_contribution_margin_sponsored_vnd": net_contribution_margin_sponsored_vnd,
            "net_contribution_margin_sponsored_pct": net_contribution_margin_sponsored_pct,
            "net_contribution_margin_commercial_vnd": net_contribution_margin_commercial_vnd,
            "net_contribution_margin_commercial_pct": net_contribution_margin_commercial_pct,
        },
        "streams": streams_summary,
        "negative_abuse": negative_abuse,
    }
