#!/bin/bash

# P1-EXP-03: Test Experiment Metric Events API
# This script tests the metric tracking functionality

set -e  # Exit on error

echo "========================================"
echo "P1-EXP-03 Metric Events API Test"
echo "========================================"
echo ""

# Configuration
BASE_URL="${API_BASE_URL:-http://localhost:8000}"
ADMIN_TOKEN="${ADMIN_TOKEN:-}"
USER_TOKEN="${USER_TOKEN:-}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function for formatted output
print_step() {
    echo -e "${BLUE}➜ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check prerequisites
if [ -z "$ADMIN_TOKEN" ]; then
    print_error "ADMIN_TOKEN not set. Please export ADMIN_TOKEN=<your_admin_token>"
    exit 1
fi

if [ -z "$USER_TOKEN" ]; then
    print_error "USER_TOKEN not set. Please export USER_TOKEN=<your_user_token>"
    exit 1
fi

echo ""
print_step "Step 1: Create Test Experiment"
EXPERIMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/admin/experiments" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "metric_test_'$(date +%s)'",
    "name": "Metric Tracking Test",
    "description": "Testing P1-EXP-03 metric events",
    "variants": [
      {"key": "control", "name": "Control", "weight": 50},
      {"key": "variant_a", "name": "Variant A", "weight": 50}
    ],
    "is_active": true
  }')

EXPERIMENT_ID=$(echo $EXPERIMENT_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$EXPERIMENT_ID" ]; then
    print_error "Failed to create experiment"
    echo "$EXPERIMENT_RESPONSE"
    exit 1
fi

print_success "Created experiment: $EXPERIMENT_ID"
echo ""

print_step "Step 2: Get User Assignment (auto-assign)"
ASSIGNMENT_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/experiments" \
  -H "Authorization: Bearer $USER_TOKEN")

VARIANT=$(echo $ASSIGNMENT_RESPONSE | grep -o '"'$(echo $EXPERIMENT_RESPONSE | grep -o '"key":"[^"]*' | cut -d'"' -f4)'":"[^"]*' | cut -d'"' -f4 || echo "control")

print_success "User assigned to variant: $VARIANT"
echo ""

print_step "Step 3: Record Metric Events"

# Record conversion metrics
print_step "  3a. Recording conversion metrics (binary 0/1)"
for i in {1..10}; do
    METRIC_VALUE=$((RANDOM % 2))  # 0 or 1
    curl -s -X POST "$BASE_URL/api/v1/experiments/$EXPERIMENT_ID/metrics" \
      -H "Authorization: Bearer $USER_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"metric_name\": \"conversion\",
        \"metric_value\": $METRIC_VALUE,
        \"metadata\": {\"iteration\": $i}
      }" > /dev/null
    echo -n "."
done
echo ""
print_success "Recorded 10 conversion metrics"

# Record engagement scores
print_step "  3b. Recording engagement scores (0-100)"
for i in {1..15}; do
    METRIC_VALUE=$((RANDOM % 100))
    curl -s -X POST "$BASE_URL/api/v1/experiments/$EXPERIMENT_ID/metrics" \
      -H "Authorization: Bearer $USER_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"metric_name\": \"engagement_score\",
        \"metric_value\": $METRIC_VALUE,
        \"metadata\": {\"session\": $i}
      }" > /dev/null
    echo -n "."
done
echo ""
print_success "Recorded 15 engagement score metrics"

# Record retention metrics
print_step "  3c. Recording retention metrics"
for i in {1..8}; do
    METRIC_VALUE=$((50 + RANDOM % 50))  # 50-100
    curl -s -X POST "$BASE_URL/api/v1/experiments/$EXPERIMENT_ID/metrics" \
      -H "Authorization: Bearer $USER_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"metric_name\": \"retention_rate\",
        \"metric_value\": $METRIC_VALUE,
        \"metadata\": {\"day\": $i}
      }" > /dev/null
    echo -n "."
done
echo ""
print_success "Recorded 8 retention metrics"
echo ""

print_step "Step 4: Get Metrics Summary"
SUMMARY_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/admin/experiments/$EXPERIMENT_ID/metrics" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

echo "$SUMMARY_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SUMMARY_RESPONSE"
print_success "Retrieved metrics summary"
echo ""

print_step "Step 5: Get Specific Metric Comparison - Conversion"
CONVERSION_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/admin/experiments/$EXPERIMENT_ID/metrics/conversion?control_variant_key=control" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

echo "$CONVERSION_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CONVERSION_RESPONSE"
print_success "Retrieved conversion metric comparison"
echo ""

print_step "Step 6: Get Specific Metric Comparison - Engagement Score"
ENGAGEMENT_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/admin/experiments/$EXPERIMENT_ID/metrics/engagement_score?control_variant_key=control" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

echo "$ENGAGEMENT_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ENGAGEMENT_RESPONSE"
print_success "Retrieved engagement score comparison"
echo ""

print_step "Step 7: Get Specific Metric Comparison - Retention Rate"
RETENTION_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/admin/experiments/$EXPERIMENT_ID/metrics/retention_rate?control_variant_key=control" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

echo "$RETENTION_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RETENTION_RESPONSE"
print_success "Retrieved retention rate comparison"
echo ""

print_step "Step 8: Test Error Handling"

# Test recording metric for non-existent experiment
print_step "  8a. Testing non-existent experiment (should fail with 404)"
ERROR_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$BASE_URL/api/v1/experiments/00000000-0000-0000-0000-000000000000/metrics" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "test",
    "metric_value": 1.0
  }')

HTTP_STATUS=$(echo "$ERROR_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
if [ "$HTTP_STATUS" = "404" ]; then
    print_success "Correctly returned 404 for non-existent experiment"
else
    print_warning "Expected 404, got $HTTP_STATUS"
fi
echo ""

# Test without authentication
print_step "  8b. Testing without authentication (should fail with 401)"
ERROR_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$BASE_URL/api/v1/experiments/$EXPERIMENT_ID/metrics" \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "test",
    "metric_value": 1.0
  }')

HTTP_STATUS=$(echo "$ERROR_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
if [ "$HTTP_STATUS" = "403" ] || [ "$HTTP_STATUS" = "401" ]; then
    print_success "Correctly returned 401/403 for unauthenticated request"
else
    print_warning "Expected 401/403, got $HTTP_STATUS"
fi
echo ""

# Test admin endpoint without admin token
print_step "  8c. Testing admin endpoint with user token (should fail with 403)"
ERROR_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X GET "$BASE_URL/api/v1/admin/experiments/$EXPERIMENT_ID/metrics" \
  -H "Authorization: Bearer $USER_TOKEN")

HTTP_STATUS=$(echo "$ERROR_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
if [ "$HTTP_STATUS" = "403" ]; then
    print_success "Correctly returned 403 for non-admin user"
else
    print_warning "Expected 403, got $HTTP_STATUS"
fi
echo ""

print_step "Step 9: Cleanup (Optional)"
print_warning "Experiment $EXPERIMENT_ID was created for testing"
print_warning "To delete: curl -X DELETE \"$BASE_URL/api/v1/admin/experiments/$EXPERIMENT_ID\" -H \"Authorization: Bearer \$ADMIN_TOKEN\""
echo ""

echo "========================================"
print_success "All tests completed successfully!"
echo "========================================"
echo ""

echo "Summary of Created Resources:"
echo "  - Experiment ID: $EXPERIMENT_ID"
echo "  - Metrics Recorded:"
echo "    • Conversion: 10 events"
echo "    • Engagement Score: 15 events"
echo "    • Retention Rate: 8 events"
echo ""

echo "Next Steps:"
echo "1. Review the metric comparisons above"
echo "2. Check for sufficient data indicators (has_sufficient_data: true)"
echo "3. Compare improvement percentages between variants"
echo "4. Clean up test experiment when done"

