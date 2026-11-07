# -*- coding: utf-8 -*-
"""Pydantic schemas for Partner Discovery and LOI Vault (Ticket V5-T113 / Wave W11 Slot A03)."""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RbpcPartnerDiscoveryOut(BaseModel):
    """Public discovery summary for verified, active partner institutions."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    loi_id: str
    partner_id: str
    partner_name: str
    partner_name_en: Optional[str] = None
    slug: str
    category: str
    institution_type: str
    region: str
    scope_of_partnership: str
    consent_type: str
    effective_date: datetime.date
    expiration_date: datetime.date
    is_active: bool = True
    dignity_charter_binding: bool = True
    lead_artisan_title: Optional[str] = None
    contact_role: Optional[str] = None
    verified_at: Optional[datetime.datetime] = None


class RbpcPartnerDiscoveryListOut(BaseModel):
    """Paginated list of active partners for public discovery."""

    items: List[RbpcPartnerDiscoveryOut]
    total: int
    as_of_date: str


class RbpcLoiVaultItemOut(BaseModel):
    """Detailed evidence record for Letter of Intent (LOI) Vault."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    loi_id: str
    partner_id: str
    partner_name: str
    partner_name_en: Optional[str] = None
    slug: str
    category: str
    institution_type: str
    region: str
    scope_of_partnership: str
    scope_details: Dict[str, Any] = Field(default_factory=dict)
    consent_type: str
    consent_status: str
    status: str
    effective_date: datetime.date
    expiration_date: datetime.date
    agreement_checksum_sha256: str
    dignity_charter_binding: bool = True
    commercial_terms: Dict[str, Any] = Field(default_factory=dict)
    is_expired: bool
    is_currently_active: bool
    lead_artisan_title: Optional[str] = None
    contact_role: Optional[str] = None
    is_verified: bool
    verified_at: Optional[datetime.datetime] = None
    revoked_at: Optional[datetime.datetime] = None
    revocation_reason: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class RbpcLoiVaultListOut(BaseModel):
    """Vault evidence registry list with status aggregates."""

    items: List[RbpcLoiVaultItemOut]
    total: int
    active_count: int
    expired_count: int
    revoked_count: int
    as_of_date: str


class RbpcLoiRegisterIn(BaseModel):
    """Payload to register a new verified LOI agreement into the vault."""

    loi_id: str = Field(..., min_length=3, max_length=64, description="Unique LOI reference e.g. LOI-HUE-BRONZE-001")
    partner_id: str = Field(..., min_length=3, max_length=64, description="Partner entity ID e.g. PARTNER-BRONZE-001")
    partner_name: str = Field(..., min_length=2, max_length=255)
    partner_name_en: Optional[str] = Field(None, max_length=255)
    slug: str = Field(..., min_length=2, max_length=128)
    category: str = Field(..., description="craft_guild, educational_institution, cultural_association, tourism_operator")
    institution_type: str = Field(..., max_length=64)
    region: str = Field("Huế", max_length=128)
    scope_of_partnership: str = Field(..., min_length=10)
    scope_details: Optional[Dict[str, Any]] = None
    consent_type: str = Field("written_loi", description="written_loi, bilateral_charter, signed_mou, framework_agreement")
    effective_date: datetime.date
    expiration_date: datetime.date
    agreement_checksum_sha256: str = Field(..., min_length=64, max_length=64)
    dignity_charter_binding: bool = True
    commercial_terms: Optional[Dict[str, Any]] = None
    lead_artisan_title: Optional[str] = None
    contact_role: Optional[str] = None

    @field_validator("expiration_date")
    @classmethod
    def validate_expiration_after_effective(cls, v: datetime.date, info) -> datetime.date:
        eff = info.data.get("effective_date")
        if eff and v <= eff:
            raise ValueError("expiration_date must be strictly after effective_date.")
        return v

    @field_validator("agreement_checksum_sha256")
    @classmethod
    def validate_checksum_format(cls, v: str) -> str:
        s = v.strip().lower()
        if len(s) != 64 or not all(c in "0123456789abcdef" for c in s):
            raise ValueError("agreement_checksum_sha256 must be a 64-character hexadecimal SHA-256 hash.")
        if "data:image" in s or "http://" in s or "https://" in s:
            raise ValueError("Negative abuse: Raw signatures or external URLs cannot be stored as agreement checksum.")
        return s


class RbpcLoiRevokeIn(BaseModel):
    """Payload to revoke an active partnership / LOI."""

    reason: str = Field(..., min_length=5, max_length=1000, description="Reason for agreement revocation")


class RbpcLoiChecksumVerifyIn(BaseModel):
    """Payload to verify document text or bytes against stored SHA-256 agreement digest."""

    document_content: str = Field(..., min_length=1, description="Raw document text content to hash and compare")


class RbpcLoiChecksumVerifyOut(BaseModel):
    """Result of SHA-256 checksum comparison."""

    loi_id: str
    expected_checksum: str
    computed_checksum: str
    is_match: bool


class RbpcLoiExportOut(BaseModel):
    """Export package for pitch review due diligence."""

    format: str
    total_records: int
    exported_at: str
    content: str
