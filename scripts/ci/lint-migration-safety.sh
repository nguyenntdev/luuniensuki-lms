#!/usr/bin/env bash
# CI lint: Migration safety lint
#
# Task 1.21: Rejects new SQL migrations containing destructive operations
# against existing tables. The Rust migration MUST NOT alter the existing
# schema (Requirement 6.2).
#
# Blocked patterns:
#   - DROP TABLE / DROP COLUMN
#   - ALTER COLUMN (type change, rename)
#   - RENAME TABLE / RENAME COLUMN
#
# Additive operations (CREATE TABLE, CREATE INDEX, ADD COLUMN) are allowed.
#
# Validates: Req 6.2

set -euo pipefail

MIGRATIONS_DIR="${1:-migrations}"

if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo "OK: No migrations directory found at $MIGRATIONS_DIR — nothing to check."
    exit 0
fi

echo "Checking migration safety in $MIGRATIONS_DIR..."

# Find all SQL and Python migration files
MIGRATION_FILES=$(find "$MIGRATIONS_DIR" \( -name "*.sql" -o -name "*.py" \) -type f 2>/dev/null | sort || true)

if [ -z "$MIGRATION_FILES" ]; then
    echo "OK: No migration files found."
    exit 0
fi

ERRORS=0

# Check 1: Topology check — ensure exactly 1 head (no diverging heads)
echo "Checking Alembic topology (single head invariant)..."
HEAD_INFO=$(PYTHONPATH=. python3 -c "
import sys
from pathlib import Path
REPO_ROOT = Path('.').resolve()
sys.path.insert(0, str(REPO_ROOT))
from alembic.config import Config
from alembic.script import ScriptDirectory
cfg = Config('alembic.ini')
s = ScriptDirectory.from_config(cfg)
heads = s.get_heads()
print(f'{len(heads)}:{\" \".join(heads)}')
" 2>/dev/null || echo "0:")

HEAD_COUNT="${HEAD_INFO%%:*}"
HEADS="${HEAD_INFO#*:}"

if [ "$HEAD_COUNT" -ne 1 ]; then
    echo "ERROR: Multiple or zero migration heads detected! Found $HEAD_COUNT heads ($HEADS)."
    ERRORS=$((ERRORS + 1))
else
    echo "OK: Single Alembic migration head verified: $HEADS"
fi

# Check 2: Dangerous patterns in migration files
DANGEROUS_PATTERNS=(
    "DROP\s+TABLE"
    "DROP\s+COLUMN"
    "ALTER\s+.*\s+TYPE\b"
    "ALTER\s+COLUMN\s+.*\s+TYPE\b"
    "RENAME\s+TABLE"
    "RENAME\s+COLUMN"
    "RENAME\s+TO\b"
    "DROP\s+CONSTRAINT"
    "op\.drop_table"
    "op\.drop_column"
    "op\.drop_constraint"
)

for file in $MIGRATION_FILES; do
    # Skip non-migration helper files
    if [[ "$(basename "$file")" == "env.py" ]] || [[ "$(basename "$file")" == "script.py.mako" ]]; then
        continue
    fi
    # Skip legacy migrations created before schema freeze
    if [[ "$(basename "$file")" == "0037_update_feature_flags_fields.py" ]]; then
        continue
    fi

    # For Python files, extract only the upgrade() function body to avoid flagging downgrade()
    if [[ "$file" == *.py ]]; then
        CONTENT=$(awk '/def upgrade\(/,/def downgrade\(/' "$file" | sed '$d')
        if [ -z "$CONTENT" ]; then
            CONTENT=$(cat "$file")
        fi
    else
        CONTENT=$(cat "$file")
    fi

    for pattern in "${DANGEROUS_PATTERNS[@]}"; do
        MATCHES=$(echo "$CONTENT" | grep -niE "$pattern" || true)
        if [ -n "$MATCHES" ]; then
            echo "ERROR: Dangerous operation in $file (pattern: $pattern):"
            echo "$MATCHES"
            echo ""
            ERRORS=$((ERRORS + 1))
        fi
    done
done

# Check 3: Full migration preflight dry run (offline SQL generation)
if [ -f "scripts/dev/migration_preflight.py" ]; then
    echo "Running migration preflight dry-run validator..."
    if ! PYTHONPATH=. python3 scripts/dev/migration_preflight.py --strict; then
        echo "ERROR: Migration preflight validation failed."
        ERRORS=$((ERRORS + 1))
    fi
fi

if [ $ERRORS -gt 0 ]; then
    echo "FAILED: Found $ERRORS dangerous migration operations."
    echo ""
    echo "The Rust backend migration MUST NOT alter the existing PostgreSQL schema"
    echo "(Requirement 6.2). Destructive operations (DROP, ALTER TYPE, RENAME) are"
    echo "blocked. Only additive operations (CREATE TABLE, CREATE INDEX, ADD COLUMN)"
    echo "are permitted."
    exit 1
fi

echo "OK: All migrations are safe (no destructive operations found)."
