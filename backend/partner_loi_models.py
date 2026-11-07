# -*- coding: utf-8 -*-
"""SQLAlchemy models for Partner Discovery and LOI Vault (Ticket V5-T113 / Wave W11 Slot A03).

Features:
- Secure partner evidence register with consent, expiration dates, scope, and agreement checksums
- SHA-256 cryptographic digests of signed LOIs/charters (strictly prohibiting raw signatures/PII in public repo)
- Negative abuse invariant: Revoked or expired partnerships are never displayed as active partners
- Public active discovery filtering against status, consent, revocation, and expiration dates
"""
from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Optional
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .base_model import Base


class RbpcPartnerCategory(str, Enum):
    craft_guild = "craft_guild"
    educational_institution = "educational_institution"
    cultural_association = "cultural_association"
    tourism_operator = "tourism_operator"


class RbpcLoiConsentType(str, Enum):
    written_loi = "written_loi"
    bilateral_charter = "bilateral_charter"
    signed_mou = "signed_mou"
    framework_agreement = "framework_agreement"


class RbpcPartnerLoiStatus(str, Enum):
    active = "active"
    expired = "expired"
    revoked = "revoked"
    pending_review = "pending_review"


def _validate_enum_val(enum_cls: type[Enum], key: str, val: Any) -> str:
    if isinstance(val, enum_cls):
        return str(val.value)
    if isinstance(val, str):
        allowed = {e.value for e in enum_cls}
        if val in allowed:
            return val
        raise ValueError(f"Invalid {key}: '{val}'. Must be one of {sorted(allowed)}")
    raise ValueError(f"Invalid {key}: expected {enum_cls.__name__} or str, got {type(val).__name__}")


class RbpcPartnerLoiVault(Base):
    """Authoritative evidence register for partner discovery and Letters of Intent (LOIs)."""

    __tablename__ = "rbpc_partner_loi_vault"
    __table_args__ = (
        UniqueConstraint("loi_id", name="uq_rbpc_partner_loi_id"),
        UniqueConstraint("slug", name="uq_rbpc_partner_slug"),
        CheckConstraint(
            "status IN ('active','expired','revoked','pending_review')",
            name="ck_rbpc_partner_loi_status",
        ),
        CheckConstraint(
            "consent_status IN ('consented','verified_written_consent','pending_review','revoked','expired')",
            name="ck_rbpc_partner_loi_consent_status",
        ),
        Index("idx_rbpc_partner_loi_id", "loi_id"),
        Index("idx_rbpc_partner_partner_id", "partner_id"),
        Index("idx_rbpc_partner_status", "status"),
        Index("idx_rbpc_partner_category", "category"),
        Index("idx_rbpc_partner_expiration", "expiration_date"),
        Index("idx_rbpc_partner_active_query", "status", "consent_status", "expiration_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    loi_id: Mapped[str] = mapped_column(String(64), nullable=False)
    partner_id: Mapped[str] = mapped_column(String(64), nullable=False)
    partner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_name_en: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    institution_type: Mapped[str] = mapped_column(String(64), nullable=False)
    region: Mapped[str] = mapped_column(String(128), nullable=False, default="Huế")
    scope_of_partnership: Mapped[str] = mapped_column(Text, nullable=False)
    scope_details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    consent_type: Mapped[str] = mapped_column(
        String(64), nullable=False, default=RbpcLoiConsentType.written_loi.value
    )
    consent_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="consented"
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=RbpcPartnerLoiStatus.active.value
    )
    effective_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    expiration_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    agreement_checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    dignity_charter_binding: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    commercial_terms: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    lead_artisan_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_role: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rbpc_creators.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verified_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    revoked_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revocation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    @property
    def is_currently_active(self) -> bool:
        """Negative abuse invariant: Expired or revoked partnerships are never active."""
        today = datetime.date.today()
        if self.status != RbpcPartnerLoiStatus.active.value:
            return False
        if self.consent_status not in ("consented", "verified_written_consent"):
            return False
        if self.revoked_at is not None:
            return False
        if self.expiration_date < today:
            return False
        return True

    @property
    def is_expired(self) -> bool:
        """Return True if agreement reached expiration date or marked expired."""
        today = datetime.date.today()
        return self.expiration_date < today or self.status == RbpcPartnerLoiStatus.expired.value

    @validates("category")
    def validate_category(self, key: str, value: Any) -> str:
        return _validate_enum_val(RbpcPartnerCategory, key, value)

    @validates("consent_type")
    def validate_consent_type(self, key: str, value: Any) -> str:
        return _validate_enum_val(RbpcLoiConsentType, key, value)

    @validates("status")
    def validate_status(self, key: str, value: Any) -> str:
        return _validate_enum_val(RbpcPartnerLoiStatus, key, value)

    @validates("agreement_checksum_sha256")
    def validate_checksum(self, key: str, value: str) -> str:
        """Verify checksum is a valid 64-char hex SHA-256 and strictly bar raw signatures or PII."""
        if not value or not isinstance(value, str):
            raise ValueError("agreement_checksum_sha256 is required and must be a string.")
        stripped = value.strip().lower()
        # Bar raw signatures, data URIs, or URLs in checksum field
        if "data:image" in stripped or "http://" in stripped or "https://" in stripped or "base64" in stripped:
            raise ValueError(
                "Negative abuse: Raw signatures, document URLs, or base64 data cannot be stored as agreement checksum."
            )
        if len(stripped) != 64 or not all(c in "0123456789abcdef" for c in stripped):
            raise ValueError(
                "agreement_checksum_sha256 must be a valid 64-character hexadecimal SHA-256 hash."
            )
        return stripped
