"""Add rbpc_pilot_go_no_go_evaluations table

Revision ID: 0091_rbpc_pilot_go_no_go_board
Revises: 0090_research_results_truth_gate
Create Date: 2026-11-07 15:00:00.000000

V5-T129 / W12-A09: Pilot go/no-go board.
Evaluates production release readiness across 5 domain owner decisions,
blocking issue register (P0-P3), feature flag plan, rollback triggers, and support contacts.
Negative abuse invariant: Launch is strictly BLOCKED if any P0 issue remains unresolved.

Strictly additive:
- Creates rbpc_pilot_go_no_go_evaluations table with indexes and constraints
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0091_rbpc_pilot_go_no_go_board"
down_revision: Union[str, Sequence[str], None] = "0090_research_results_truth_gate"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- Create rbpc_pilot_go_no_go_evaluations table
        CREATE TABLE IF NOT EXISTS rbpc_pilot_go_no_go_evaluations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            board_ref VARCHAR(64) NOT NULL UNIQUE,
            release_version VARCHAR(64) NOT NULL DEFAULT 'v2026.1.0-rbpc',
            target_environment VARCHAR(64) NOT NULL DEFAULT 'staging',
            verdict VARCHAR(32) NOT NULL DEFAULT 'BLOCKED',
            open_p0_count INTEGER NOT NULL DEFAULT 0,
            open_p1_count INTEGER NOT NULL DEFAULT 0,
            open_p2_count INTEGER NOT NULL DEFAULT 0,
            signed_owners_count INTEGER NOT NULL DEFAULT 0,
            is_launch_blocked BOOLEAN NOT NULL DEFAULT true,
            blocking_reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
            owner_decisions JSONB NOT NULL DEFAULT '[]'::jsonb,
            blocking_issues JSONB NOT NULL DEFAULT '[]'::jsonb,
            feature_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
            rollback_triggers JSONB NOT NULL DEFAULT '[]'::jsonb,
            support_contacts JSONB NOT NULL DEFAULT '[]'::jsonb,
            evaluated_by VARCHAR(255) NOT NULL,
            evaluated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_rbpc_go_no_go_verdict CHECK (verdict IN ('GO','BLOCKED','NO_GO','CONDITIONAL_GO'))
        );

        CREATE INDEX IF NOT EXISTS idx_rbpc_go_no_go_ref ON rbpc_pilot_go_no_go_evaluations(board_ref);
        CREATE INDEX IF NOT EXISTS idx_rbpc_go_no_go_verdict ON rbpc_pilot_go_no_go_evaluations(verdict);
        CREATE INDEX IF NOT EXISTS idx_rbpc_go_no_go_env ON rbpc_pilot_go_no_go_evaluations(target_environment);
        CREATE INDEX IF NOT EXISTS idx_rbpc_go_no_go_eval_at ON rbpc_pilot_go_no_go_evaluations(evaluated_at);
        CREATE INDEX IF NOT EXISTS idx_rbpc_go_no_go_blocked ON rbpc_pilot_go_no_go_evaluations(is_launch_blocked);
        """
    )


def downgrade() -> None:
    # Strictly additive migration policy
    pass
