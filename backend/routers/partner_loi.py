# -*- coding: utf-8 -*-
"""API router for Partner Discovery & LOI Vault (Ticket V5-T113 / Wave W11 Slot A03).

Endpoints:
- GET  /api/v1/rbpc/partners (Public: list verified active partners)
- GET  /api/v1/rbpc/partners/{identifier} (Public: get active partner details)
- GET  /api/v1/rbpc/loi-vault (Vault: list all LOI records with status totals)
- GET  /api/v1/rbpc/loi-vault/{loi_id} (Vault: get detailed LOI record)
- POST /api/v1/rbpc/admin/loi-vault (Staff: register new verified LOI into vault)
- POST /api/v1/rbpc/admin/loi-vault/{loi_id}/revoke (Staff: revoke active LOI)
- POST /api/v1/rbpc/admin/loi-vault/{loi_id}/verify-checksum (Staff: verify agreement checksum)
- GET  /api/v1/rbpc/admin/loi-vault/export (Staff: export vault as Markdown or JSON)

Negative abuse invariant:
Revoked or expired partnerships are never displayed as active partners.
"""
from __future__ import annotations

import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..apischemas.partner_loi import (
    RbpcLoiChecksumVerifyIn,
    RbpcLoiChecksumVerifyOut,
    RbpcLoiExportOut,
    RbpcLoiRegisterIn,
    RbpcLoiRevokeIn,
    RbpcLoiVaultItemOut,
    RbpcLoiVaultListOut,
    RbpcPartnerDiscoveryListOut,
    RbpcPartnerDiscoveryOut,
)
from ..db import get_db
from ..deps import get_staff_user
from ..models import User
from ..services import partner_loi as partner_service

router = APIRouter(tags=["rbpc_partner_discovery_loi_vault"])


@router.get(
    "/api/v1/rbpc/partners",
    response_model=RbpcPartnerDiscoveryListOut,
)
def list_active_partners(
    category: Optional[str] = Query(None, description="Filter by partner category (craft_guild, educational_institution, cultural_association, tourism_operator)"),
    region: Optional[str] = Query(None, description="Filter by region substring e.g. 'Huế'"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> RbpcPartnerDiscoveryListOut:
    """Public discovery endpoint returning verified, active partner institutions.
    
    NEGATIVE ABUSE INVARIANT:
    Expired and revoked partnerships are strictly excluded and never returned.
    """
    # Ensure seed data exists
    partner_service.seed_canonical_partner_lois(db)

    items, total = partner_service.get_active_partners(
        db, category=category, region=region, limit=limit, offset=offset
    )
    return RbpcPartnerDiscoveryListOut(
        items=[RbpcPartnerDiscoveryOut.model_validate(item) for item in items],
        total=total,
        as_of_date=datetime.date.today().isoformat(),
    )


@router.get(
    "/api/v1/rbpc/partners/{identifier}",
    response_model=RbpcPartnerDiscoveryOut,
)
def get_active_partner(
    identifier: str,
    db: Session = Depends(get_db),
) -> RbpcPartnerDiscoveryOut:
    """Public endpoint retrieving profile of an active verified partner.
    
    NEGATIVE ABUSE INVARIANT:
    If partner agreement is expired or revoked, fails with 404 RBPC_PARTNER_INACTIVE.
    """
    partner_service.seed_canonical_partner_lois(db)
    partner = partner_service.get_active_partner(db, identifier)
    return RbpcPartnerDiscoveryOut.model_validate(partner)


@router.get(
    "/api/v1/rbpc/loi-vault",
    response_model=RbpcLoiVaultListOut,
)
def list_loi_vault(
    status: Optional[str] = Query(None, description="Filter by agreement status (active, expired, revoked, pending_review)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> RbpcLoiVaultListOut:
    """Retrieve full LOI vault records with breakdown counts for due diligence."""
    partner_service.seed_canonical_partner_lois(db)
    items, total, active_c, expired_c, revoked_c = partner_service.list_loi_vault_records(
        db, status_filter=status, category=category, limit=limit, offset=offset
    )
    return RbpcLoiVaultListOut(
        items=[RbpcLoiVaultItemOut.model_validate(i) for i in items],
        total=total,
        active_count=active_c,
        expired_count=expired_c,
        revoked_count=revoked_c,
        as_of_date=datetime.date.today().isoformat(),
    )


@router.get(
    "/api/v1/rbpc/loi-vault/{loi_id}",
    response_model=RbpcLoiVaultItemOut,
)
def get_loi_vault_item(
    loi_id: str,
    db: Session = Depends(get_db),
) -> RbpcLoiVaultItemOut:
    """Retrieve specific LOI vault record by unique ID."""
    partner_service.seed_canonical_partner_lois(db)
    record = partner_service.get_loi_vault_record(db, loi_id)
    return RbpcLoiVaultItemOut.model_validate(record)


@router.post(
    "/api/v1/rbpc/admin/loi-vault",
    response_model=RbpcLoiVaultItemOut,
    status_code=status.HTTP_201_CREATED,
)
def register_loi(
    payload: RbpcLoiRegisterIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
) -> RbpcLoiVaultItemOut:
    """Register a new verified LOI/charter agreement into the evidence vault.
    
    Requires staff or admin role.
    """
    record = partner_service.register_loi_record(db, payload, current_user.id)
    return RbpcLoiVaultItemOut.model_validate(record)


@router.post(
    "/api/v1/rbpc/admin/loi-vault/{loi_id}/revoke",
    response_model=RbpcLoiVaultItemOut,
)
def revoke_loi(
    loi_id: str,
    payload: RbpcLoiRevokeIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
) -> RbpcLoiVaultItemOut:
    """Revoke an active partner agreement.
    
    NEGATIVE ABUSE INVARIANT:
    Partner is immediately excluded from active discovery listings.
    Requires staff or admin role.
    """
    record = partner_service.revoke_loi_record(db, loi_id, payload.reason, current_user.id)
    return RbpcLoiVaultItemOut.model_validate(record)


@router.post(
    "/api/v1/rbpc/admin/loi-vault/{loi_id}/verify-checksum",
    response_model=RbpcLoiChecksumVerifyOut,
)
def verify_agreement_checksum(
    loi_id: str,
    payload: RbpcLoiChecksumVerifyIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
) -> RbpcLoiChecksumVerifyOut:
    """Verify document text or bytes against stored SHA-256 agreement digest.
    
    Requires staff or admin role.
    """
    return partner_service.verify_loi_checksum(db, loi_id, payload.document_content)


@router.get(
    "/api/v1/rbpc/admin/loi-vault/export",
    response_model=RbpcLoiExportOut,
)
def export_loi_vault(
    format: str = Query("markdown", description="Export format: 'markdown' or 'json'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
) -> RbpcLoiExportOut:
    """Export the LOI vault records as Markdown table or JSON string for investor due diligence."""
    partner_service.seed_canonical_partner_lois(db)
    content = partner_service.export_loi_vault(db, export_format=format)
    items, total, _, _, _ = partner_service.list_loi_vault_records(db)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return RbpcLoiExportOut(
        format=format,
        total_records=total,
        exported_at=now,
        content=content,
    )
