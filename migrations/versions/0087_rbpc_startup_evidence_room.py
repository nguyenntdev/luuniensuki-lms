"""Add rbpc_evidence_room_pointers and rbpc_pitch_reviews tables

Revision ID: 0087_rbpc_startup_evidence_room
Revises: 0085_rbpc_unit_economics_actual_ledger, 0086_pilot_onboarding_portal
Create Date: 2026-11-07 10:00:00.000000

V5-T120 / W11-A10: Startup evidence room + pitch review.
Versioned evidence pointers across product, customer, market, finances, impact, legal, and team.
Immutable pitch review audit records verifying quantitative pitch claims against evidence pointers.
Negative abuse invariant: Every quantitative pitch claim must have an immutable evidence reference and status; ungrounded metrics flagged.

Strictly additive:
- Creates rbpc_evidence_room_pointers table with indexes and constraints
- Creates rbpc_pitch_reviews table with indexes and constraints
- Unifies migration graph into single head
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0087_rbpc_startup_evidence_room"
down_revision: Union[str, Sequence[str], None] = (
    "0085_rbpc_unit_economics_actual_ledger",
    "0086_pilot_onboarding_portal",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- 1. Create rbpc_evidence_room_pointers table
        CREATE TABLE IF NOT EXISTS rbpc_evidence_room_pointers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            pointer_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            title TEXT NOT NULL,
            doc_ref TEXT NOT NULL,
            version TEXT NOT NULL DEFAULT '1.0',
            status TEXT NOT NULL DEFAULT 'active_verified',
            hash_sha256 TEXT NOT NULL,
            metrics_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            summary TEXT NOT NULL,
            owner TEXT NOT NULL,
            verified_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_rbpc_evidence_pointer_id UNIQUE (pointer_id),
            CONSTRAINT ck_rbpc_evidence_domain CHECK (domain IN ('product','customer','market','finances','impact','legal','team')),
            CONSTRAINT ck_rbpc_evidence_status CHECK (status IN ('active_verified','archived','needs_review'))
        );

        -- 2. Indexes for rbpc_evidence_room_pointers
        CREATE INDEX IF NOT EXISTS idx_rbpc_evid_domain ON rbpc_evidence_room_pointers(domain);
        CREATE INDEX IF NOT EXISTS idx_rbpc_evid_status ON rbpc_evidence_room_pointers(status);
        CREATE INDEX IF NOT EXISTS idx_rbpc_evid_verified ON rbpc_evidence_room_pointers(verified_at);

        -- 3. Create rbpc_pitch_reviews table
        CREATE TABLE IF NOT EXISTS rbpc_pitch_reviews (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            audit_ref TEXT NOT NULL,
            pitch_deck_title TEXT NOT NULL,
            deck_version TEXT NOT NULL,
            total_claims_audited INTEGER NOT NULL DEFAULT 0,
            verified_claims_count INTEGER NOT NULL DEFAULT 0,
            ungrounded_claims_count INTEGER NOT NULL DEFAULT 0,
            pitch_readiness TEXT NOT NULL DEFAULT 'FLAGGED_UNREADY',
            claims_payload JSONB NOT NULL DEFAULT '[]'::jsonb,
            audit_findings JSONB NOT NULL DEFAULT '{}'::jsonb,
            reviewed_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            reviewed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_rbpc_pitch_audit_ref UNIQUE (audit_ref),
            CONSTRAINT ck_rbpc_pitch_readiness CHECK (pitch_readiness IN ('APPROVED_FOR_PITCH','FLAGGED_UNREADY'))
        );

        -- 4. Indexes for rbpc_pitch_reviews
        CREATE INDEX IF NOT EXISTS idx_rbpc_pitch_readiness ON rbpc_pitch_reviews(pitch_readiness);
        CREATE INDEX IF NOT EXISTS idx_rbpc_pitch_reviewed_at ON rbpc_pitch_reviews(reviewed_at);
        """
    )


def downgrade() -> None:
    pass
