"""Add research factory core tables and distributed leasing

Revision ID: 0070_research_factory_core
Revises: 0069_ai_privacy_child_protections
Create Date: 2026-11-05 20:00:00.000000

V5-T071 / V5-T073: Research factory run/phase/job tables and distributed leasing with semaphores.
Strictly additive:
- research_runs
- research_phases
- research_agent_jobs
- research_job_attempts
- research_job_leases
- research_budgets
- research_evidence_results
- provider_semaphore_leases
- provider_concurrency_configs
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0070_research_factory_core"
down_revision: Union[str, Sequence[str], None] = "0069_ai_privacy_child_protections"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS research_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            scope_id VARCHAR(100) NOT NULL DEFAULT 'cuu_dinh_162_motifs',
            content_scope VARCHAR(64) NOT NULL DEFAULT 'NINE_URNS',
            subject_type VARCHAR(64) NOT NULL DEFAULT 'RELIEF',
            subject_id VARCHAR(255) NOT NULL DEFAULT '',
            subject_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            source_release_id UUID,
            status VARCHAR(50) NOT NULL DEFAULT 'QUEUED',
            current_phase VARCHAR(16) NOT NULL DEFAULT 'P00',
            mode VARCHAR(50) NOT NULL DEFAULT 'standard',
            config_hash VARCHAR(64) NOT NULL DEFAULT '',
            run_manifest_sha256 VARCHAR(64),
            idempotency_key VARCHAR(255) UNIQUE,
            cost_budget FLOAT NOT NULL DEFAULT 100.0,
            worker_slots_per_phase INTEGER NOT NULL DEFAULT 10,
            max_active_phases_per_run INTEGER NOT NULL DEFAULT 1,
            human_approval_required BOOLEAN NOT NULL DEFAULT TRUE,
            metadata_payload JSONB,
            created_by UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS research_phases (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            run_id UUID NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
            phase_code VARCHAR(16) NOT NULL,
            phase_order INTEGER NOT NULL DEFAULT 0,
            wave INTEGER NOT NULL DEFAULT 1,
            status VARCHAR(64) NOT NULL DEFAULT 'QUEUED',
            state VARCHAR(50) NOT NULL DEFAULT 'QUEUED',
            input_sha256 VARCHAR(64) NOT NULL DEFAULT '',
            input_manifest_sha256 VARCHAR(64),
            output_snapshot_sha256 VARCHAR(64),
            gate_manifest_sha256 VARCHAR(64),
            barrier_passed BOOLEAN NOT NULL DEFAULT FALSE,
            gate_checks JSONB,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_research_phase_run_wave UNIQUE (run_id, phase_code, wave)
        );
        CREATE INDEX IF NOT EXISTS idx_research_phase_run_id ON research_phases(run_id);
        CREATE INDEX IF NOT EXISTS idx_research_phase_code ON research_phases(phase_code);

        CREATE TABLE IF NOT EXISTS research_agent_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            phase_id UUID NOT NULL REFERENCES research_phases(id) ON DELETE CASCADE,
            slot_number INTEGER NOT NULL,
            agent_index INTEGER NOT NULL DEFAULT 1,
            role_key VARCHAR(100) NOT NULL,
            agent_role VARCHAR(128) NOT NULL DEFAULT '',
            idempotency_key VARCHAR(255) NOT NULL UNIQUE,
            status VARCHAR(64) NOT NULL DEFAULT 'QUEUED',
            state VARCHAR(50) NOT NULL DEFAULT 'QUEUED',
            model_identifier VARCHAR(128),
            prompt_template_sha256 VARCHAR(64),
            tool_manifest_sha256 VARCHAR(64),
            input_payload JSONB,
            output_schema_version VARCHAR(64) NOT NULL DEFAULT 'v1',
            attempts_count INTEGER NOT NULL DEFAULT 0,
            attempt INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 3,
            max_retries INTEGER NOT NULL DEFAULT 3,
            priority INTEGER NOT NULL DEFAULT 0,
            available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            lease_owner VARCHAR(255),
            lease_token VARCHAR(64),
            lease_until TIMESTAMPTZ,
            last_heartbeat_at TIMESTAMPTZ,
            provider VARCHAR(100),
            estimated_tokens INTEGER NOT NULL DEFAULT 0,
            payload JSONB,
            output_sha256 VARCHAR(64),
            result_envelope JSONB,
            error_message TEXT,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_research_job_phase_slot UNIQUE (phase_id, slot_number),
            CONSTRAINT chk_research_job_slot_range CHECK (slot_number BETWEEN 1 AND 10)
        );
        CREATE INDEX IF NOT EXISTS idx_research_job_phase_id ON research_agent_jobs(phase_id);
        CREATE INDEX IF NOT EXISTS idx_research_job_idempotency ON research_agent_jobs(idempotency_key);
        CREATE INDEX IF NOT EXISTS research_job_leases_idx ON research_agent_jobs(state, lease_until);
        CREATE INDEX IF NOT EXISTS research_job_queue_idx ON research_agent_jobs(state, available_at, priority);

        CREATE TABLE IF NOT EXISTS research_job_attempts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID NOT NULL REFERENCES research_agent_jobs(id) ON DELETE CASCADE,
            attempt_number INTEGER NOT NULL,
            worker_id VARCHAR(255) NOT NULL,
            status VARCHAR(64) NOT NULL DEFAULT 'RUNNING',
            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            ended_at TIMESTAMPTZ,
            finished_at TIMESTAMPTZ,
            duration_ms INTEGER,
            input_tokens INTEGER NOT NULL DEFAULT 0,
            output_tokens INTEGER NOT NULL DEFAULT 0,
            cost_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            error_code VARCHAR(64),
            error_message TEXT,
            error_details JSONB,
            retryable BOOLEAN NOT NULL DEFAULT FALSE
        );
        CREATE INDEX IF NOT EXISTS idx_research_attempt_job_id ON research_job_attempts(job_id);

        CREATE TABLE IF NOT EXISTS research_job_leases (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID NOT NULL REFERENCES research_agent_jobs(id) ON DELETE CASCADE,
            worker_id VARCHAR(255) NOT NULL,
            lease_token VARCHAR(64) NOT NULL,
            fence_token BIGINT NOT NULL DEFAULT 1,
            status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
            acquired_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at TIMESTAMPTZ NOT NULL,
            released_at TIMESTAMPTZ
        );
        CREATE INDEX IF NOT EXISTS idx_research_lease_job_id ON research_job_leases(job_id);

        CREATE TABLE IF NOT EXISTS research_budgets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            run_id UUID NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
            phase_code VARCHAR(16),
            provider VARCHAR(100) NOT NULL,
            total_budget FLOAT NOT NULL DEFAULT 50.0,
            allocated FLOAT NOT NULL DEFAULT 0.0,
            spent FLOAT NOT NULL DEFAULT 0.0,
            max_tokens BIGINT NOT NULL DEFAULT 500000,
            tokens_consumed BIGINT NOT NULL DEFAULT 0,
            max_cost_usd DOUBLE PRECISION NOT NULL DEFAULT 25.0,
            cost_consumed_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            max_api_calls INTEGER NOT NULL DEFAULT 1000,
            api_calls_consumed INTEGER NOT NULL DEFAULT 0,
            is_exhausted BOOLEAN NOT NULL DEFAULT FALSE,
            exhausted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_research_budget_run_id ON research_budgets(run_id);

        CREATE TABLE IF NOT EXISTS research_evidence_results (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID NOT NULL REFERENCES research_agent_jobs(id) ON DELETE CASCADE,
            schema_version VARCHAR(50) NOT NULL DEFAULT 'research-agent-result/v1',
            output_schema VARCHAR(64) NOT NULL DEFAULT 'default/v1',
            input_manifest_sha256 VARCHAR(64) NOT NULL DEFAULT '',
            artifact_sha256 VARCHAR(64) NOT NULL,
            artifact_uri VARCHAR(500) NOT NULL DEFAULT '',
            model_identifier VARCHAR(100) NOT NULL DEFAULT 'default',
            status VARCHAR(64) NOT NULL DEFAULT 'SUCCEEDED',
            source_ids JSONB,
            claim_ids JSONB,
            evidence_locator_ids JSONB,
            metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
            usage_metrics JSONB,
            warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
            failures JSONB NOT NULL DEFAULT '[]'::jsonb,
            raw_envelope JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_research_evidence_job_id ON research_evidence_results(job_id);

        CREATE TABLE IF NOT EXISTS provider_semaphore_leases (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            provider VARCHAR(100) NOT NULL,
            holder_id VARCHAR(255) NOT NULL,
            lease_token VARCHAR(64) NOT NULL,
            weight INTEGER NOT NULL DEFAULT 1,
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_provider_semaphore_expires ON provider_semaphore_leases(provider, expires_at);

        CREATE TABLE IF NOT EXISTS provider_concurrency_configs (
            provider VARCHAR(100) PRIMARY KEY,
            max_concurrency INTEGER NOT NULL DEFAULT 10,
            rate_limit_per_minute INTEGER NOT NULL DEFAULT 60,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )


def downgrade() -> None:
    pass
