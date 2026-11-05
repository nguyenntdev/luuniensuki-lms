"""Add rbpc_customer_reviews and rbpc_review_disputes tables

Revision ID: 0083_rbpc_verified_reviews_disputes
Revises: 0082_rbpc_availability_inventory_calendar
Create Date: 2026-11-06 08:00:00.000000

V5-T107 / W10-A07: Verified customer reviews and disputes.
Only customers with verified completed experience inquiries can submit reviews; anti-fraud checking and moderation queue.
Negative abuse: Uncompleted, fake, or cancelled inquiries cannot post ratings or reviews.

Strictly additive:
- Creates rbpc_customer_reviews table with indexes and constraints
- Creates rbpc_review_disputes table with indexes and constraints
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0083_rbpc_verified_reviews_disputes"
down_revision: Union[str, Sequence[str], None] = "0082_rbpc_availability_inventory_calendar"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- 1. Create rbpc_customer_reviews table
        CREATE TABLE IF NOT EXISTS rbpc_customer_reviews (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            inquiry_id UUID NOT NULL UNIQUE REFERENCES rbpc_inquiries(id) ON DELETE CASCADE,
            experience_id UUID NOT NULL REFERENCES rbpc_experiences(id) ON DELETE RESTRICT,
            author_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            author_display_name TEXT NOT NULL,
            rating INTEGER NOT NULL,
            title TEXT NOT NULL,
            comment TEXT NOT NULL,
            verified_completed BOOLEAN NOT NULL DEFAULT TRUE,
            status TEXT NOT NULL DEFAULT 'pending_moderation',
            fraud_flags JSONB NOT NULL DEFAULT '{}'::jsonb,
            moderated_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            moderated_at TIMESTAMPTZ,
            moderation_notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_rbpc_review_rating_range CHECK (rating >= 1 AND rating <= 5),
            CONSTRAINT ck_rbpc_review_status CHECK (status IN ('pending_moderation','published','rejected','disputed','archived'))
        );

        -- 2. Indexes for rbpc_customer_reviews
        CREATE INDEX IF NOT EXISTS idx_rbpc_review_exp ON rbpc_customer_reviews(experience_id);
        CREATE INDEX IF NOT EXISTS idx_rbpc_review_status ON rbpc_customer_reviews(status);
        CREATE INDEX IF NOT EXISTS idx_rbpc_review_created ON rbpc_customer_reviews(created_at);

        -- 3. Create rbpc_review_disputes table
        CREATE TABLE IF NOT EXISTS rbpc_review_disputes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            review_id UUID NOT NULL REFERENCES rbpc_customer_reviews(id) ON DELETE CASCADE,
            disputant_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            reason TEXT NOT NULL,
            evidence_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            status TEXT NOT NULL DEFAULT 'opened',
            resolved_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            resolution_notes TEXT,
            resolved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_rbpc_dispute_status CHECK (status IN ('opened','under_review','resolved_upheld','resolved_overturned','dismissed'))
        );

        -- 4. Indexes for rbpc_review_disputes
        CREATE INDEX IF NOT EXISTS idx_rbpc_dispute_review ON rbpc_review_disputes(review_id);
        CREATE INDEX IF NOT EXISTS idx_rbpc_dispute_status ON rbpc_review_disputes(status);
        CREATE INDEX IF NOT EXISTS idx_rbpc_dispute_created ON rbpc_review_disputes(created_at);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS rbpc_review_disputes;
        DROP TABLE IF EXISTS rbpc_customer_reviews;
        """
    )
