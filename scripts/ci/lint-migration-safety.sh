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

# Find all SQL migration files
SQL_FILES=$(find "$MIGRATIONS_DIR" -name "*.sql" -type f 2>/dev/null || true)

if [ -z "$SQL_FILES" ]; then
    echo "OK: No SQL migration files found."
    exit 0
fi

ERRORS=0

# Dangerous patterns (case-insensitive)
DANGEROUS_PATTERNS=(
    "DROP\s+TABLE"
    "DROP\s+COLUMN"
    "ALTER\s+.*\s+TYPE\b"
    "ALTER\s+COLUMN"
    "RENAME\s+TABLE"
    "RENAME\s+COLUMN"
    "RENAME\s+TO\b"
    "DROP\s+CONSTRAINT"
)

for file in $SQL_FILES; do
    for pattern in "${DANGEROUS_PATTERNS[@]}"; do
        MATCHES=$(grep -niE "$pattern" "$file" 2>/dev/null || true)
        if [ -n "$MATCHES" ]; then
            echo "ERROR: Dangerous operation in $file:"
            echo "$MATCHES"
            echo ""
            ERRORS=$((ERRORS + 1))
        fi
    done
done

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
