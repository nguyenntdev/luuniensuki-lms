"""Add rbpc_partner_loi_vault table

Revision ID: 0089_rbpc_partner_discovery_loi_vault
Revises: 0088_analytics_taxonomy_ingest
Create Date: 2026-11-07 11:00:00.000000

V5-T113 / W11-A03: Partner discovery and LOI vault.
Secure partner evidence register with consent, expiration dates, scope,
and agreement checksums (not raw signatures in public repo).
Negative abuse invariant: Revoked or expired partnerships are never displayed as active partners.

Strictly additive:
- Creates rbpc_partner_loi_vault table with indexes and constraints
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0089_rbpc_partner_discovery_loi_vault"
down_revision: Union[str, Sequence[str], None] = "0088_analytics_taxonomy_ingest"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- Create rbpc_partner_loi_vault table
        CREATE TABLE IF NOT EXISTS rbpc_partner_loi_vault (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            loi_id VARCHAR(64) NOT NULL UNIQUE,
            partner_id VARCHAR(64) NOT NULL,
            partner_name VARCHAR(255) NOT NULL,
            partner_name_en VARCHAR(255),
            slug VARCHAR(128) NOT NULL UNIQUE,
            category VARCHAR(64) NOT NULL,
            institution_type VARCHAR(64) NOT NULL,
            region VARCHAR(128) NOT NULL DEFAULT 'Huế',
            scope_of_partnership TEXT NOT NULL,
            scope_details JSONB NOT NULL DEFAULT '{}'::jsonb,
            consent_type VARCHAR(64) NOT NULL DEFAULT 'written_loi',
            consent_status VARCHAR(32) NOT NULL DEFAULT 'consented',
            status VARCHAR(32) NOT NULL DEFAULT 'active',
            effective_date DATE NOT NULL,
            expiration_date DATE NOT NULL,
            agreement_checksum_sha256 VARCHAR(64) NOT NULL,
            dignity_charter_binding BOOLEAN NOT NULL DEFAULT true,
            commercial_terms JSONB NOT NULL DEFAULT '{}'::jsonb,
            lead_artisan_title VARCHAR(255),
            contact_role VARCHAR(128),
            is_verified BOOLEAN NOT NULL DEFAULT true,
            creator_id UUID REFERENCES rbpc_creators(id) ON DELETE SET NULL,
            verified_at TIMESTAMPTZ,
            verified_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            revoked_at TIMESTAMPTZ,
            revocation_reason TEXT,
            metadata_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_rbpc_partner_loi_id ON rbpc_partner_loi_vault(loi_id);
        CREATE INDEX IF NOT EXISTS idx_rbpc_partner_partner_id ON rbpc_partner_loi_vault(partner_id);
        CREATE INDEX IF NOT EXISTS idx_rbpc_partner_status ON rbpc_partner_loi_vault(status);
        CREATE INDEX IF NOT EXISTS idx_rbpc_partner_category ON rbpc_partner_loi_vault(category);
        CREATE INDEX IF NOT EXISTS idx_rbpc_partner_expiration ON rbpc_partner_loi_vault(expiration_date);
        CREATE INDEX IF NOT EXISTS idx_rbpc_partner_active_query ON rbpc_partner_loi_vault(status, consent_status, expiration_date);
        """
    )


def downgrade() -> None:
    # Strictly additive migration policy
    pass
