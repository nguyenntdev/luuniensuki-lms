"""Add AI telemetry logs and budget caps tables

Revision ID: 0068_ai_observability_budgeting
Revises: 0067_hotspot_claim_entity_binding
Create Date: 2026-11-05 18:00:00.000000

V5-T069: AI observability and budgeting.
Strictly additive:
- Creates ai_telemetry_logs table for zero-PII token, latency, cost, and citation tracking.
- Creates ai_budget_caps table for user and classroom daily budget limits.
- Creates indexes on foreign keys, timestamps, operation, model, and status.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0068_ai_observability_budgeting"
down_revision: Union[str, Sequence[str], None] = "0067_hotspot_claim_entity_binding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create ai_telemetry_logs table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_telemetry_logs (
            id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id                UUID REFERENCES users(id) ON DELETE SET NULL,
            classroom_id           UUID REFERENCES classes(id) ON DELETE SET NULL,
            session_id             VARCHAR(100),
            operation              VARCHAR(100) NOT NULL DEFAULT 'tutor',
            model                  VARCHAR(100) NOT NULL DEFAULT 'gemini-3.8-flash-tiered',
            provider               VARCHAR(50) NOT NULL DEFAULT 'clara',
            prompt_tokens          INTEGER NOT NULL DEFAULT 0,
            completion_tokens      INTEGER NOT NULL DEFAULT 0,
            total_tokens           INTEGER NOT NULL DEFAULT 0,
            latency_ms             FLOAT NOT NULL DEFAULT 0.0,
            cost_usd               FLOAT NOT NULL DEFAULT 0.0,
            citation_valid_count   INTEGER NOT NULL DEFAULT 0,
            citation_invalid_count INTEGER NOT NULL DEFAULT 0,
            citation_validity_rate FLOAT NOT NULL DEFAULT 1.0,
            status                 VARCHAR(50) NOT NULL DEFAULT 'success',
            error_code             VARCHAR(50),
            prompt_sha256          VARCHAR(64),
            created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )

    # Indexes on ai_telemetry_logs
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ai_telemetry_user_created ON ai_telemetry_logs(user_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_ai_telemetry_classroom_created ON ai_telemetry_logs(classroom_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_ai_telemetry_operation ON ai_telemetry_logs(operation);
        CREATE INDEX IF NOT EXISTS idx_ai_telemetry_created_at ON ai_telemetry_logs(created_at);
        CREATE INDEX IF NOT EXISTS idx_ai_telemetry_status ON ai_telemetry_logs(status);
        CREATE INDEX IF NOT EXISTS idx_ai_telemetry_model ON ai_telemetry_logs(model);
        """
    )

    # 2. Create ai_budget_caps table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_budget_caps (
            id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entity_type            VARCHAR(20) NOT NULL,
            entity_id              UUID NOT NULL,
            daily_token_limit      INTEGER NOT NULL DEFAULT 500000,
            daily_cost_limit_usd   FLOAT NOT NULL DEFAULT 5.0,
            max_tokens_per_request INTEGER NOT NULL DEFAULT 4096,
            is_active              BOOLEAN NOT NULL DEFAULT TRUE,
            created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_ai_budget_caps_entity UNIQUE (entity_type, entity_id)
        );
        """
    )

    # Indexes on ai_budget_caps
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ai_budget_caps_entity ON ai_budget_caps(entity_type, entity_id);
        """
    )


def downgrade() -> None:
    # Strictly additive migration per repository policy.
    pass
