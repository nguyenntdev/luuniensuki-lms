#!/bin/bash

# P0-ANA-04: Retention Analytics API Testing Script
# Tests all three retention endpoints

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
API_BASE="${API_BASE:-http://localhost:8000}"
ADMIN_TOKEN="${ADMIN_TOKEN:-}"

if [ -z "$ADMIN_TOKEN" ]; then
    echo -e "${RED}Error: ADMIN_TOKEN environment variable not set${NC}"
    echo "Usage: ADMIN_TOKEN=your_token ./test_retention_api.sh"
    exit 1
fi

echo -e "${YELLOW}=== P0-ANA-04: Retention Analytics API Tests ===${NC}\n"

# Test 1: Overall Retention Metrics
echo -e "${GREEN}Test 1: Overall Retention Metrics${NC}"
echo "GET /api/v1/admin/analytics/retention"
curl -s -X GET "$API_BASE/api/v1/admin/analytics/retention" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

# Test 2: Overall Retention with days_ago filter
echo -e "${GREEN}Test 2: Overall Retention (last 30 days)${NC}"
echo "GET /api/v1/admin/analytics/retention?days_ago=30"
curl -s -X GET "$API_BASE/api/v1/admin/analytics/retention?days_ago=30" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

# Test 3: Cohort Retention (Weekly)
echo -e "${GREEN}Test 3: Cohort Retention (Weekly)${NC}"
echo "GET /api/v1/admin/analytics/retention/cohorts"
curl -s -X GET "$API_BASE/api/v1/admin/analytics/retention/cohorts" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

# Test 4: Cohort Retention (Monthly)
echo -e "${GREEN}Test 4: Cohort Retention (Monthly, limit 6)${NC}"
echo "GET /api/v1/admin/analytics/retention/cohorts?period=month&limit=6"
curl -s -X GET "$API_BASE/api/v1/admin/analytics/retention/cohorts?period=month&limit=6" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

# Test 5: Retention Curve (Default 30 days)
echo -e "${GREEN}Test 5: Retention Curve (30 days)${NC}"
echo "GET /api/v1/admin/analytics/retention/curve"
curl -s -X GET "$API_BASE/api/v1/admin/analytics/retention/curve" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

# Test 6: Retention Curve (60 days, 180-day cohort)
echo -e "${GREEN}Test 6: Retention Curve (60 days, 180-day cohort)${NC}"
echo "GET /api/v1/admin/analytics/retention/curve?days=60&cohort_days_ago=180"
curl -s -X GET "$API_BASE/api/v1/admin/analytics/retention/curve?days=60&cohort_days_ago=180" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

# Test 7: Permission Check (should fail without admin token)
echo -e "${YELLOW}Test 7: Permission Check (should fail)${NC}"
echo "GET /api/v1/admin/analytics/retention (without auth)"
curl -s -X GET "$API_BASE/api/v1/admin/analytics/retention" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

# Test 8: Invalid period parameter
echo -e "${YELLOW}Test 8: Invalid period parameter (should fail)${NC}"
echo "GET /api/v1/admin/analytics/retention/cohorts?period=invalid"
curl -s -X GET "$API_BASE/api/v1/admin/analytics/retention/cohorts?period=invalid" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" | jq '.'
echo -e "\n"

echo -e "${GREEN}=== Testing Complete ===${NC}"
echo -e "\nAll endpoints tested. Check responses above for correctness."
echo -e "Expected behavior:"
echo -e "  - Tests 1-6: Should return JSON with retention data"
echo -e "  - Test 7: Should return 401 Unauthorized"
echo -e "  - Test 8: Should return 422 Validation Error"

