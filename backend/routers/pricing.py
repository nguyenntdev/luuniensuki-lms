# -*- coding: utf-8 -*-
"""API Router for Pricing Experiment Instrumentation (Ticket V5-T117 / W11-A07)."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ..apischemas.pricing import (
    PricingCalculatorIn,
    PricingCalculatorOut,
    PricingContractCreateIn,
    PricingContractOut,
    PricingContractSignAcceptIn,
    PricingExperimentConfigOut,
    PricingExperimentConsentIn,
    PricingExperimentEventCreateIn,
    PricingExperimentEventOut,
    PricingExperimentMetricsSummaryOut,
)
from ..db import get_db
from ..deps import get_current_user, get_current_user_optional
from ..models import User
from ..services import pricing as pricing_service

router = APIRouter(prefix="/api/v1/pricing", tags=["pricing_experiment"])


@router.get("/config", response_model=PricingExperimentConfigOut)
def get_pricing_experiment_config(
    variant: str = Query("control", description="Experiment variant key (e.g. control, annual_flat, per_student_metered)"),
) -> PricingExperimentConfigOut:
    """Retrieve pricing experiment configuration, transparent tiers, and anti-dark-pattern notices."""
    return pricing_service.get_pricing_experiment_config(variant_key=variant)


@router.post("/calculator", response_model=PricingCalculatorOut)
def calculate_pricing_estimate(
    payload: PricingCalculatorIn,
) -> PricingCalculatorOut:
    """Compute non-binding estimate for school or institution with strict 0 VND recognized revenue invariant."""
    return pricing_service.calculate_pricing_quote(payload)


@router.post(
    "/events",
    response_model=PricingExperimentEventOut,
    status_code=status.HTTP_201_CREATED,
)
def record_pricing_interest_event(
    payload: PricingExperimentEventCreateIn,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> PricingExperimentEventOut:
    """Record pricing interest telemetry with user consent.
    
    Negative abuse invariant:
    Tier clicks and calculator interactions produce is_paying_customer=False and 0 VND revenue.
    """
    user_id = current_user.id if current_user else None
    try:
        event = pricing_service.record_pricing_event(db=db, payload=payload, user_id=user_id)
        return PricingExperimentEventOut.model_validate(event)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/contracts",
    response_model=PricingContractOut,
    status_code=status.HTTP_201_CREATED,
)
def create_institutional_contract(
    payload: PricingContractCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PricingContractOut:
    """Draft an institutional contract for school or district partner."""
    contract = pricing_service.create_draft_contract(
        db=db, payload=payload, signer_user=current_user
    )
    return PricingContractOut.model_validate(contract)


@router.post(
    "/contracts/{contract_id}/accept",
    response_model=PricingContractOut,
)
def accept_and_sign_contract(
    contract_id: UUID,
    payload: PricingContractSignAcceptIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PricingContractOut:
    """Real contract acceptance and execution with cryptographic verification.
    
    Only this action transitions contract to signed_and_executed and establishes paying customer status.
    """
    try:
        contract = pricing_service.accept_and_execute_contract(
            db=db,
            contract_id=contract_id,
            payload=payload,
            current_user=current_user,
        )
        return PricingContractOut.model_validate(contract)
    except ValueError as e:
        err_msg = str(e)
        if "CONTRACT_NOT_FOUND" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contract not found: {err_msg}",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg,
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to sign this contract: {str(e)}",
        )


@router.get(
    "/metrics/summary",
    response_model=PricingExperimentMetricsSummaryOut,
)
def get_pricing_metrics_summary(
    experiment_key: str = Query("school_pricing_v1"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> PricingExperimentMetricsSummaryOut:
    """Get aggregated metrics verifying anti-abuse: tier views & calculator clicks = 0 revenue."""
    return pricing_service.get_pricing_metrics_summary(
        db=db, experiment_key=experiment_key
    )
