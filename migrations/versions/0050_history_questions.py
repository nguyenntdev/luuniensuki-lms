"""historical learning engine V2 — question model columns + question type registry

History-First Phase 8 (docs/specs/HISTORY_FIRST_MASTER_SPEC.md sections 32-34):

- Extends ``quiz_questions`` with the V2 common fields (32.1):
  - ``skill_dimensions`` JSONB  — mastery skill tags this question trains
  - ``entity_id`` UUID          — FK to ``historical_entities(id)``
  - ``claim_ids`` JSONB         — claim UUIDs the answer depends on
  - ``source_ids`` JSONB        — source UUIDs surfaced to the learner
  - ``answer_contract`` JSONB   — typed answer rubric per question type (33)
- Extends ``user_skill_levels`` with ``skill_dimensions`` JSONB for the V2
  mastery dimensions (34).
- Adds ``history_question_types`` — registry of the V2 question type enum keys
  (chronology_order, image_identification, map_location, urn_hotspot,
  evidence_match, entity_match, compare_two, source_interpretation,
  short_response, multi_select, relationship_chain) with bilingual labels and
  sort order, seeded with the 11 V2 keys.

NOTE: the Postgres ``question_type`` enum on ``quiz_questions`` is intentionally
NOT altered here (enum ADD VALUE cannot run inside an Alembic transaction on
PG < 12 and the prod enum predates V2). Fresh databases built via
``Base.metadata.create_all`` (test suite) derive the full enum from the Python
``QuestionType`` enum. On prod, V2 inserts require an out-of-transaction
``ALTER TYPE question_type ADD VALUE ...`` before seeding V2 questions.

All additive and reversible.

Revision ID: 0050_history_questions
Revises: 0049_content_validation_status
Create Date: 2026-08-17
"""
from __future__ import annotations

from alembic import op

revision = "0050_history_questions"
down_revision = "0049_content_validation_status"
branch_labels = None
depends_on = None


V2_QUESTION_TYPES = [
    ("chronology_order", "Sắp xếp theo trình tự thời gian", "Chronology order"),
    ("image_identification", "Nhận diện hình ảnh", "Image identification"),
    ("map_location", "Xác định vị trí trên bản đồ", "Map location"),
    ("urn_hotspot", "Điểm nóng trên đỉnh", "Urn hotspot"),
    ("evidence_match", "Ghép nối bằng chứng", "Evidence match"),
    ("entity_match", "Khớp thực thể", "Entity match"),
    ("compare_two", "So sánh hai thực thể", "Compare two"),
    ("source_interpretation", "Diễn giải nguồn tư liệu", "Source interpretation"),
    ("short_response", "Trả lời ngắn", "Short response"),
    ("multi_select", "Chọn nhiều đáp án", "Multi select"),
    ("relationship_chain", "Chuỗi quan hệ", "Relationship chain"),
]


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE quiz_questions
            ADD COLUMN IF NOT EXISTS skill_dimensions JSONB,
            ADD COLUMN IF NOT EXISTS entity_id UUID REFERENCES historical_entities(id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS claim_ids JSONB,
            ADD COLUMN IF NOT EXISTS source_ids JSONB,
            ADD COLUMN IF NOT EXISTS answer_contract JSONB
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_quiz_questions_entity_id "
        "ON quiz_questions(entity_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_quiz_questions_skill_dims "
        "ON quiz_questions USING gin (skill_dimensions jsonb_path_ops)"
    )

    op.execute(
        """
        ALTER TABLE user_skill_levels
            ADD COLUMN IF NOT EXISTS skill_dimensions JSONB
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS history_question_types (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            key         VARCHAR(50) NOT NULL,
            label_vi    VARCHAR(255) NOT NULL,
            label_en    VARCHAR(255),
            sort_order  INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_history_question_types_key "
        "ON history_question_types(key)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_history_question_types_sort "
        "ON history_question_types(sort_order)"
    )
    # The table may already exist (e.g. tests build the schema via
    # Base.metadata.create_all without server-side defaults); guarantee the id
    # default exists so the plain-SQL seed inserts below are portable.
    op.execute(
        "ALTER TABLE history_question_types ALTER COLUMN id SET DEFAULT gen_random_uuid()"
    )

    for sort_order, (key, label_vi, label_en) in enumerate(V2_QUESTION_TYPES):
        op.execute(
            "INSERT INTO history_question_types (key, label_vi, label_en, sort_order) "
            f"VALUES ('{key}', '{label_vi}', '{label_en}', {sort_order}) "
            "ON CONFLICT (key) DO NOTHING"
        )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS history_question_types")
    op.execute("ALTER TABLE user_skill_levels DROP COLUMN IF EXISTS skill_dimensions")
    op.execute("DROP INDEX IF EXISTS idx_quiz_questions_skill_dims")
    op.execute("DROP INDEX IF EXISTS idx_quiz_questions_entity_id")
    op.execute(
        """
        ALTER TABLE quiz_questions
            DROP COLUMN IF EXISTS answer_contract,
            DROP COLUMN IF EXISTS source_ids,
            DROP COLUMN IF EXISTS claim_ids,
            DROP COLUMN IF EXISTS entity_id,
            DROP COLUMN IF EXISTS skill_dimensions
        """
    )