#!/bin/bash

# Migration Verification Script for P1-TEACH-01

echo "=== P1-TEACH-01: Migration Verification ==="
echo ""

# Check if running in docker or locally
if [ -f /.dockerenv ]; then
    echo "Running inside Docker container"
    ALEMBIC_CMD="alembic"
else
    echo "Running locally - will use docker-compose"
    ALEMBIC_CMD="docker-compose exec -T backend alembic"
fi

# Step 1: Check current migration status
echo "Step 1: Checking current migration status..."
$ALEMBIC_CMD current
echo ""

# Step 2: Show migration history
echo "Step 2: Migration history..."
$ALEMBIC_CMD history | tail -20
echo ""

# Step 3: Check if our migration is in the list
echo "Step 3: Checking for 0021_classroom_enhancements..."
if $ALEMBIC_CMD history | grep -q "0021_classroom_enhancements"; then
    echo "✅ Migration file found in history"
else
    echo "❌ Migration file NOT found"
    exit 1
fi
echo ""

# Step 4: Perform dry run (show what would happen)
echo "Step 4: Showing SQL that will be executed..."
echo "(This is a dry run - no changes will be made)"
$ALEMBIC_CMD upgrade head --sql
echo ""

# Step 5: Ask for confirmation
read -p "Do you want to apply the migration? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Step 6: Applying migration..."
    $ALEMBIC_CMD upgrade head
    
    if [ $? -eq 0 ]; then
        echo "✅ Migration applied successfully!"
        echo ""
        echo "Step 7: Verifying migration..."
        $ALEMBIC_CMD current
        echo ""
        
        # Step 8: Check if new columns exist
        echo "Step 8: Checking if new columns exist..."
        if [ -f /.dockerenv ]; then
            PSQL_CMD="psql -U \$POSTGRES_USER -d \$POSTGRES_DB"
        else
            PSQL_CMD="docker-compose exec -T db psql -U postgres -d luuniensuki"
        fi
        
        echo "Checking classes table structure..."
        $PSQL_CMD -c "\d classes" | grep -E "class_code|max_students|is_archived|settings|updated_at"
        
        if [ $? -eq 0 ]; then
            echo "✅ New columns verified!"
        else
            echo "⚠️  Could not verify columns (might need manual check)"
        fi
        echo ""
        
        echo "=== Migration completed successfully! ==="
        echo ""
        echo "Next steps:"
        echo "1. Restart the backend service: docker-compose restart backend"
        echo "2. Run the API tests: ./test_classroom_api.sh"
    else
        echo "❌ Migration failed!"
        exit 1
    fi
else
    echo "Migration cancelled."
    echo ""
    echo "To apply the migration later, run:"
    echo "  alembic upgrade head"
fi

