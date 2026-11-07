"""Add pricing_experiment_events and pricing_contracts tables

Revision ID: 0085_pricing_experiment_instrumentation
Revises: 0084_rbpc_oral_history_consent_studio
Create Date: 2026-11-06 12:00:00.000000

V5-T117 / W11-A07: Pricing experiment instrumentation with user consent,
anti-abuse safeguards (tier/calc clicks != paying customer / recognized revenue),
and real contract acceptance.

Strictly additive:
- Creates pricing_experiment_events table with indexes and constraints
- Creates pricing_contracts table with indexes and constraints
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0085_pricing_experiment_instrumentation"
down_revision: Union[str, Sequence[str], None] = "0085_rbpc_unit_economics_actual_ledger"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- 1. Create pricing_experiment_events table
        CREATE TABLE IF NOT EXISTS pricing_experiment_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            anonymous_session_id VARCHAR(128),
            experiment_key VARCHAR(100) NOT NULL DEFAULT 'school_pricing_v1',
            variant_key VARCHAR(50) NOT NULL DEFAULT 'control',
            tier_key VARCHAR(50) NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            has_experiment_consent BOOLEAN NOT NULL DEFAULT true,
            consent_version VARCHAR(32) NOT NULL DEFAULT '2026.1-pricing',
            is_paying_customer BOOLEAN NOT NULL DEFAULT false,
            revenue_impact_vnd NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
            calculator_params JSONB,
            client_metadata JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
            CONSTRAINT ck_pricing_exp_event_type CHECK (
                event_type IN ('tier_view', 'calculator_interaction', 'quote_inquiry', 'contract_sign_attempt', 'contract_accepted')
            ),
            CONSTRAINT ck_pricing_exp_revenue_nonneg CHECK (
                revenue_impact_vnd >= 0.0
            )
        );

        CREATE INDEX IF NOT EXISTS idx_pricing_exp_user ON pricing_experiment_events (user_id);
        CREATE INDEX IF NOT EXISTS idx_pricing_exp_experiment ON pricing_experiment_events (experiment_key);
        CREATE INDEX IF NOT EXISTS idx_pricing_exp_type ON pricing_experiment_events (event_type);
        CREATE INDEX IF NOT EXISTS idx_pricing_exp_tier ON pricing_experiment_events (tier_key);
        CREATE INDEX IF NOT EXISTS idx_pricing_exp_created ON pricing_experiment_events (created_at);

        -- 2. Create pricing_contracts table
        CREATE TABLE IF NOT EXISTS pricing_contracts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            contract_number VARCHAR(64) NOT NULL,
            school_id UUID REFERENCES schools(id) ON DELETE SET NULL,
            organization_name VARCHAR(255) NOT NULL,
            signer_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            tier_key VARCHAR(50) NOT NULL,
            variant_key VARCHAR(50) NOT NULL,
            contract_value_vnd NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
            student_seat_capacity NUMERIC(8, 0) NOT NULL DEFAULT 100,
            status VARCHAR(50) NOT NULL DEFAULT 'draft',
            terms_version VARCHAR(32) NOT NULL DEFAULT 'v2026.1-edu',
            signed_at TIMESTAMPTZ,
            signature_ip_hash VARCHAR(64),
            verification_hash VARCHAR(64),
            metadata JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
            CONSTRAINT uq_pricing_contract_number UNIQUE (contract_number),
            CONSTRAINT ck_pricing_contract_status CHECK (
                status IN ('draft', 'pending_signature', 'signed_and_executed', 'cancelled')
            ),
            CONSTRAINT ck_pricing_contract_value_nonneg CHECK (
                contract_value_vnd >= 0.0
            )
        );

        CREATE INDEX IF NOT EXISTS idx_pricing_contract_school ON pricing_contracts (school_id);
        CREATE INDEX IF NOT EXISTS idx_pricing_contract_status ON pricing_contracts (status);
        CREATE INDEX IF NOT EXISTS idx_pricing_contract_signer ON pricing_contracts (signer_user_id);
        """
    )


def downgrade() -> None:
    pass
