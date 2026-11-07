"""Add pilot onboarding portal tables

Revision ID: 0086_pilot_onboarding_portal
Revises: 0085_pricing_experiment_instrumentation
Create Date: 2026-11-06 14:00:00.000000

V5-T116 / W11-A06: Pilot onboarding portal.
Invitation-gated pilot access for verified teachers/schools and artisan partners,
guided activation, usage health, and support.
Negative abuse: User without invitation or token cannot join private school/partner trial.

Strictly additive:
- Creates pilot_invitations table with indexes and constraints
- Creates pilot_participant_activations table with indexes and constraints
- Creates pilot_usage_health table with indexes and constraints
- Creates pilot_support_requests table with indexes and constraints
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0086_pilot_onboarding_portal"
down_revision: Union[str, Sequence[str], None] = "0085_pricing_experiment_instrumentation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- 1. Create pilot_invitations table
        CREATE TABLE IF NOT EXISTS pilot_invitations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            invitation_code VARCHAR(64) NOT NULL UNIQUE,
            token_hash VARCHAR(128) NOT NULL UNIQUE,
            pilot_name VARCHAR(255) NOT NULL,
            target_role VARCHAR(32) NOT NULL,
            organization_name VARCHAR(255) NOT NULL,
            contact_email VARCHAR(255) NOT NULL,
            school_id UUID REFERENCES schools(id) ON DELETE SET NULL,
            partner_id UUID REFERENCES rbpc_creators(id) ON DELETE SET NULL,
            max_uses INTEGER NOT NULL DEFAULT 1,
            used_count INTEGER NOT NULL DEFAULT 0,
            status VARCHAR(32) NOT NULL DEFAULT 'active',
            invited_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            notes TEXT,
            metadata_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_pilot_invitations_token ON pilot_invitations(token_hash);
        CREATE INDEX IF NOT EXISTS idx_pilot_invitations_code ON pilot_invitations(invitation_code);
        CREATE INDEX IF NOT EXISTS idx_pilot_invitations_status ON pilot_invitations(status);
        CREATE INDEX IF NOT EXISTS idx_pilot_invitations_tenant ON pilot_invitations(target_role, organization_name);

        -- 2. Create pilot_participant_activations table
        CREATE TABLE IF NOT EXISTS pilot_participant_activations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            invitation_id UUID NOT NULL REFERENCES pilot_invitations(id) ON DELETE CASCADE,
            role_type VARCHAR(32) NOT NULL,
            organization_name VARCHAR(255) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'activated',
            current_step VARCHAR(64) NOT NULL DEFAULT 'welcome',
            completed_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
            compliance_accepted BOOLEAN NOT NULL DEFAULT FALSE,
            compliance_accepted_at TIMESTAMPTZ,
            activated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_pilot_activations_user ON pilot_participant_activations(user_id);
        CREATE INDEX IF NOT EXISTS idx_pilot_activations_invitation ON pilot_participant_activations(invitation_id);
        CREATE INDEX IF NOT EXISTS idx_pilot_activations_status ON pilot_participant_activations(status);

        -- 3. Create pilot_usage_health table
        CREATE TABLE IF NOT EXISTS pilot_usage_health (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
            activation_id UUID NOT NULL REFERENCES pilot_participant_activations(id) ON DELETE CASCADE,
            login_count INTEGER NOT NULL DEFAULT 1,
            actions_count INTEGER NOT NULL DEFAULT 0,
            last_action_name VARCHAR(100),
            last_active_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            health_score DOUBLE PRECISION NOT NULL DEFAULT 100.0,
            health_status VARCHAR(32) NOT NULL DEFAULT 'healthy',
            telemetry_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_pilot_health_user ON pilot_usage_health(user_id);
        CREATE INDEX IF NOT EXISTS idx_pilot_health_status ON pilot_usage_health(health_status);

        -- 4. Create pilot_support_requests table
        CREATE TABLE IF NOT EXISTS pilot_support_requests (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ticket_code VARCHAR(32) NOT NULL UNIQUE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            activation_id UUID REFERENCES pilot_participant_activations(id) ON DELETE SET NULL,
            category VARCHAR(50) NOT NULL,
            priority VARCHAR(20) NOT NULL DEFAULT 'normal',
            status VARCHAR(20) NOT NULL DEFAULT 'open',
            subject VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            responses JSONB NOT NULL DEFAULT '[]'::jsonb,
            resolved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_pilot_support_user ON pilot_support_requests(user_id);
        CREATE INDEX IF NOT EXISTS idx_pilot_support_status ON pilot_support_requests(status);
        CREATE INDEX IF NOT EXISTS idx_pilot_support_category ON pilot_support_requests(category);
        """
    )


def downgrade() -> None:
    # Strictly additive migration policy
    pass
