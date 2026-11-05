"""Add rbpc_settlement_ledger table for fee and revenue settlement tracking

Revision ID: 0079_rbpc_fee_revenue_ledger
Revises: 0078_teacher_onboarding_support
Create Date: 2026-11-06 05:00:00.000000

V5-T108 / W10-A08: Fee/revenue ledger with actual confirmation.
Contracted take rate, actual recorded amounts, refunds, taxes, and artisan payouts after compliance approval.
Negative abuse: Merely changing inquiry status to 'confirmed' produces zero revenue in financial ledger without verified settlement.

Strictly additive:
- Creates rbpc_settlement_ledger table with indexes and constraints
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0079_rbpc_fee_revenue_ledger"
down_revision: Union[str, Sequence[str], None] = "0078_teacher_onboarding_support"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- 1. Create rbpc_settlement_ledger table
        CREATE TABLE IF NOT EXISTS rbpc_settlement_ledger (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            settlement_ref TEXT NOT NULL UNIQUE,
            inquiry_id UUID NOT NULL REFERENCES rbpc_inquiries(id) ON DELETE RESTRICT,
            provider_id UUID REFERENCES users(id) ON DELETE SET NULL,
            creator_id UUID REFERENCES rbpc_creators(id) ON DELETE SET NULL,
            gross_amount_vnd NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
            take_rate NUMERIC(5, 4) NOT NULL DEFAULT 0.1500,
            platform_fee_vnd NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
            tax_vat_vnd NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
            artisan_payout_vnd NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
            refund_amount_vnd NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
            status TEXT NOT NULL DEFAULT 'pending_compliance',
            payout_status TEXT NOT NULL DEFAULT 'pending',
            compliance_approved BOOLEAN NOT NULL DEFAULT FALSE,
            compliance_reviewer_id UUID REFERENCES users(id) ON DELETE SET NULL,
            compliance_reviewed_at TIMESTAMPTZ,
            compliance_notes TEXT,
            transaction_proof_hash TEXT,
            currency TEXT NOT NULL DEFAULT 'VND',
            disbursed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_rbpc_settlement_gross_nonneg CHECK (gross_amount_vnd >= 0.0),
            CONSTRAINT ck_rbpc_settlement_take_rate_range CHECK (take_rate >= 0.0 AND take_rate <= 1.0),
            CONSTRAINT ck_rbpc_settlement_status CHECK (status IN ('pending_compliance','approved','settled','refunded','disputed')),
            CONSTRAINT ck_rbpc_settlement_payout_status CHECK (payout_status IN ('pending','approved','disbursed','withheld','cancelled'))
        );

        -- 2. Create indexes
        CREATE INDEX IF NOT EXISTS idx_rbpc_settlement_inquiry ON rbpc_settlement_ledger(inquiry_id);
        CREATE INDEX IF NOT EXISTS idx_rbpc_settlement_provider ON rbpc_settlement_ledger(provider_id);
        CREATE INDEX IF NOT EXISTS idx_rbpc_settlement_creator ON rbpc_settlement_ledger(creator_id);
        CREATE INDEX IF NOT EXISTS idx_rbpc_settlement_status ON rbpc_settlement_ledger(status);
        CREATE INDEX IF NOT EXISTS idx_rbpc_settlement_payout ON rbpc_settlement_ledger(payout_status);
        CREATE INDEX IF NOT EXISTS idx_rbpc_settlement_created ON rbpc_settlement_ledger(created_at);
        """
    )


def downgrade() -> None:
    # Strictly additive migration discipline
    pass
