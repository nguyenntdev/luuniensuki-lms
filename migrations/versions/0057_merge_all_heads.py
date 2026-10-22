"""merge all migration heads into single baseline head

Revision ID: 0057_merge_all_heads
Revises: 0012_analytics_taxonomy, 0012_onboarding_fields, 0013_content_tagging, 0013_weekly_quests, 0014, 0014_crash_reports, 0019_app_versions, 0021_classroom_enhancements, 0024, 0024_user_learning_paths, 0031_user_shares, 0032_email_scheduling, 0033_feature_flags_experiments, 0054_rbpc_heritage_schema, 0056_imperial_sources_claims_scope
Create Date: 2026-10-21 00:00:00.000000

V5-T004 Baseline: Unifies the 15 concurrent development migration branches
into a single unambiguous head for deterministic deployment and zero drift.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0057_merge_all_heads'
down_revision: Union[str, Sequence[str], None] = (
    '0012_analytics_taxonomy',
    '0012_onboarding_fields',
    '0013_content_tagging',
    '0013_weekly_quests',
    '0014',
    '0014_crash_reports',
    '0019_app_versions',
    '0021_classroom_enhancements',
    '0024',
    '0024_user_learning_paths',
    '0031_user_shares',
    '0032_email_scheduling',
    '0033_feature_flags_experiments',
    '0054_rbpc_heritage_schema',
    '0056_imperial_sources_claims_scope',
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
