#!/bin/bash

# P1-EXP-01: A/B Testing Framework - API Testing Script
# This script tests all feature flag and experiment endpoints

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API base URL
BASE_URL="${API_URL:-http://localhost:8000}"

# Get tokens from environment or prompt
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin123}"
USER_EMAIL="${USER_EMAIL:-user@example.com}"
USER_PASSWORD="${USER_PASSWORD:-password123}"

echo -e "${BLUE}=== P1-EXP-01: A/B Testing Framework - API Testing ===${NC}\n"

# Function to print test header
test_header() {
    echo -e "\n${BLUE}TEST: $1${NC}"
}

# Function to print success
test_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
test_error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

# Login as admin
test_header "1. Login as Admin"
ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}" \
    | jq -r '.access_token')

if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" = "null" ]; then
    test_error "Failed to get admin token"
fi
test_success "Admin login successful"

# Login as regular user
test_header "2. Login as Regular User"
USER_TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$USER_PASSWORD\"}" \
    | jq -r '.access_token')

if [ -z "$USER_TOKEN" ] || [ "$USER_TOKEN" = "null" ]; then
    test_error "Failed to get user token"
fi
test_success "User login successful"

# Test 1: Create Boolean Feature Flag
test_header "3. Create Boolean Feature Flag"
BOOLEAN_FLAG=$(curl -s -X POST "$BASE_URL/api/v1/admin/feature-flags" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "key": "test_boolean_feature",
        "name": "Test Boolean Feature",
        "description": "A test boolean feature flag",
        "flag_type": "boolean",
        "is_enabled": true
    }')

FLAG_ID=$(echo "$BOOLEAN_FLAG" | jq -r '.id')
if [ -z "$FLAG_ID" ] || [ "$FLAG_ID" = "null" ]; then
    test_error "Failed to create boolean flag"
fi
test_success "Boolean flag created: $FLAG_ID"

# Test 2: Create Percentage Feature Flag
test_header "4. Create Percentage Feature Flag"
PERCENTAGE_FLAG=$(curl -s -X POST "$BASE_URL/api/v1/admin/feature-flags" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "key": "test_percentage_feature",
        "name": "Test Percentage Feature",
        "flag_type": "percentage",
        "is_enabled": true,
        "percentage": 50
    }')

PERCENTAGE_FLAG_ID=$(echo "$PERCENTAGE_FLAG" | jq -r '.id')
if [ -z "$PERCENTAGE_FLAG_ID" ] || [ "$PERCENTAGE_FLAG_ID" = "null" ]; then
    test_error "Failed to create percentage flag"
fi
test_success "Percentage flag created: $PERCENTAGE_FLAG_ID"

# Test 3: List All Feature Flags
test_header "5. List All Feature Flags"
FLAGS=$(curl -s "$BASE_URL/api/v1/admin/feature-flags" \
    -H "Authorization: Bearer $ADMIN_TOKEN")

FLAG_COUNT=$(echo "$FLAGS" | jq 'length')
if [ "$FLAG_COUNT" -lt 2 ]; then
    test_error "Expected at least 2 flags, got $FLAG_COUNT"
fi
test_success "Found $FLAG_COUNT feature flags"

# Test 4: Update Feature Flag
test_header "6. Update Feature Flag"
UPDATE_RESULT=$(curl -s -X PUT "$BASE_URL/api/v1/admin/feature-flags/$FLAG_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "is_enabled": false
    }')

IS_ENABLED=$(echo "$UPDATE_RESULT" | jq -r '.is_enabled')
if [ "$IS_ENABLED" != "false" ]; then
    test_error "Failed to update flag"
fi
test_success "Flag updated successfully"

# Test 5: Check Feature as User
test_header "7. Check Feature as User"
CHECK_RESULT=$(curl -s "$BASE_URL/api/v1/features/test_boolean_feature" \
    -H "Authorization: Bearer $USER_TOKEN")

ENABLED=$(echo "$CHECK_RESULT" | jq -r '.enabled')
if [ "$ENABLED" != "false" ]; then
    test_error "Expected feature to be disabled"
fi
test_success "Feature check returned correct status"

# Test 6: Get All Features for User
test_header "8. Get All Features for User"
USER_FEATURES=$(curl -s "$BASE_URL/api/v1/features" \
    -H "Authorization: Bearer $USER_TOKEN")

HAS_FEATURES=$(echo "$USER_FEATURES" | jq -r '.features | keys | length')
if [ "$HAS_FEATURES" -lt 1 ]; then
    test_error "Expected at least 1 feature"
fi
test_success "Retrieved $HAS_FEATURES features for user"

# Test 7: Create Experiment
test_header "9. Create Experiment"
EXPERIMENT=$(curl -s -X POST "$BASE_URL/api/v1/admin/experiments" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "key": "test_ab_experiment",
        "name": "Test A/B Experiment",
        "description": "A test experiment",
        "variants": [
            {"key": "control", "name": "Control", "weight": 50},
            {"key": "variant_a", "name": "Variant A", "weight": 50}
        ],
        "is_active": true
    }')

EXPERIMENT_ID=$(echo "$EXPERIMENT" | jq -r '.id')
if [ -z "$EXPERIMENT_ID" ] || [ "$EXPERIMENT_ID" = "null" ]; then
    test_error "Failed to create experiment"
fi
test_success "Experiment created: $EXPERIMENT_ID"

# Test 8: List All Experiments
test_header "10. List All Experiments"
EXPERIMENTS=$(curl -s "$BASE_URL/api/v1/admin/experiments" \
    -H "Authorization: Bearer $ADMIN_TOKEN")

EXPERIMENT_COUNT=$(echo "$EXPERIMENTS" | jq 'length')
if [ "$EXPERIMENT_COUNT" -lt 1 ]; then
    test_error "Expected at least 1 experiment"
fi
test_success "Found $EXPERIMENT_COUNT experiments"

# Test 9: Get Experiment Assignments for User
test_header "11. Get Experiment Assignments for User"
USER_EXPERIMENTS=$(curl -s "$BASE_URL/api/v1/experiments" \
    -H "Authorization: Bearer $USER_TOKEN")

ASSIGNED_VARIANT=$(echo "$USER_EXPERIMENTS" | jq -r '.experiments.test_ab_experiment')
if [ -z "$ASSIGNED_VARIANT" ] || [ "$ASSIGNED_VARIANT" = "null" ]; then
    test_error "User should be assigned to experiment"
fi
test_success "User assigned to variant: $ASSIGNED_VARIANT"

# Test 10: Verify Assignment Persistence
test_header "12. Verify Assignment Persistence"
USER_EXPERIMENTS_2=$(curl -s "$BASE_URL/api/v1/experiments" \
    -H "Authorization: Bearer $USER_TOKEN")

ASSIGNED_VARIANT_2=$(echo "$USER_EXPERIMENTS_2" | jq -r '.experiments.test_ab_experiment')
if [ "$ASSIGNED_VARIANT" != "$ASSIGNED_VARIANT_2" ]; then
    test_error "Variant assignment should be persistent"
fi
test_success "Assignment is persistent"

# Test 11: Get Experiment Assignments (Admin)
test_header "13. Get Experiment Assignments (Admin)"
ASSIGNMENTS=$(curl -s "$BASE_URL/api/v1/admin/experiments/$EXPERIMENT_ID/assignments?page=1&page_size=10" \
    -H "Authorization: Bearer $ADMIN_TOKEN")

ASSIGNMENT_COUNT=$(echo "$ASSIGNMENTS" | jq 'length')
if [ "$ASSIGNMENT_COUNT" -lt 1 ]; then
    test_error "Expected at least 1 assignment"
fi
test_success "Found $ASSIGNMENT_COUNT assignments"

# Test 12: Update Experiment (Deactivate)
test_header "14. Update Experiment (Deactivate)"
UPDATE_EXP=$(curl -s -X PUT "$BASE_URL/api/v1/admin/experiments/$EXPERIMENT_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "is_active": false
    }')

IS_ACTIVE=$(echo "$UPDATE_EXP" | jq -r '.is_active')
if [ "$IS_ACTIVE" != "false" ]; then
    test_error "Failed to deactivate experiment"
fi
test_success "Experiment deactivated"

# Test 13: Verify Inactive Experiment Not Returned to User
test_header "15. Verify Inactive Experiment Not Returned to User"
USER_EXPERIMENTS_3=$(curl -s "$BASE_URL/api/v1/experiments" \
    -H "Authorization: Bearer $USER_TOKEN")

INACTIVE_VARIANT=$(echo "$USER_EXPERIMENTS_3" | jq -r '.experiments.test_ab_experiment')
if [ "$INACTIVE_VARIANT" != "null" ]; then
    test_error "Inactive experiment should not be returned"
fi
test_success "Inactive experiment not returned"

# Test 14: Update Percentage Rollout
test_header "16. Update Percentage Rollout"
UPDATE_PERCENTAGE=$(curl -s -X PUT "$BASE_URL/api/v1/admin/feature-flags/$PERCENTAGE_FLAG_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "percentage": 100
    }')

NEW_PERCENTAGE=$(echo "$UPDATE_PERCENTAGE" | jq -r '.percentage')
if [ "$NEW_PERCENTAGE" != "100" ]; then
    test_error "Failed to update percentage"
fi
test_success "Percentage updated to 100"

# Test 15: Test User List Flag
test_header "17. Create User List Flag"
USER_ID=$(curl -s "$BASE_URL/api/v1/users/me" \
    -H "Authorization: Bearer $USER_TOKEN" \
    | jq -r '.id')

USER_LIST_FLAG=$(curl -s -X POST "$BASE_URL/api/v1/admin/feature-flags" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"key\": \"test_user_list_feature\",
        \"name\": \"Test User List Feature\",
        \"flag_type\": \"user_list\",
        \"is_enabled\": true,
        \"allowed_user_ids\": [\"$USER_ID\"]
    }")

USER_LIST_FLAG_ID=$(echo "$USER_LIST_FLAG" | jq -r '.id')
if [ -z "$USER_LIST_FLAG_ID" ] || [ "$USER_LIST_FLAG_ID" = "null" ]; then
    test_error "Failed to create user list flag"
fi
test_success "User list flag created: $USER_LIST_FLAG_ID"

# Test 16: Verify User in List
test_header "18. Verify User in List"
USER_LIST_CHECK=$(curl -s "$BASE_URL/api/v1/features/test_user_list_feature" \
    -H "Authorization: Bearer $USER_TOKEN")

USER_LIST_ENABLED=$(echo "$USER_LIST_CHECK" | jq -r '.enabled')
if [ "$USER_LIST_ENABLED" != "true" ]; then
    test_error "User should have access to user list feature"
fi
test_success "User has access to user list feature"

# Cleanup
test_header "19. Cleanup - Delete Test Data"

# Delete feature flags
curl -s -X DELETE "$BASE_URL/api/v1/admin/feature-flags/$FLAG_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" > /dev/null
test_success "Deleted boolean flag"

curl -s -X DELETE "$BASE_URL/api/v1/admin/feature-flags/$PERCENTAGE_FLAG_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" > /dev/null
test_success "Deleted percentage flag"

curl -s -X DELETE "$BASE_URL/api/v1/admin/feature-flags/$USER_LIST_FLAG_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" > /dev/null
test_success "Deleted user list flag"

# Delete experiment
curl -s -X DELETE "$BASE_URL/api/v1/admin/experiments/$EXPERIMENT_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" > /dev/null
test_success "Deleted experiment"

# Summary
echo -e "\n${GREEN}=== All Tests Passed! ===${NC}"
echo ""
echo "Summary:"
echo "  ✓ Feature flag creation (boolean, percentage, user_list)"
echo "  ✓ Feature flag updates"
echo "  ✓ User feature checks"
echo "  ✓ Experiment creation and management"
echo "  ✓ Variant assignment (deterministic and persistent)"
echo "  ✓ Admin endpoints"
echo "  ✓ Cleanup"
echo ""
echo -e "${BLUE}P1-EXP-01 implementation verified successfully!${NC}"

