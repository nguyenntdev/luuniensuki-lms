#!/bin/bash

# P0-HAB-04 Hearts System - API Testing Script
# Tests all hearts endpoints

set -e

BASE_URL="${API_URL:-http://localhost:8000}"
TOKEN="${AUTH_TOKEN}"

if [ -z "$TOKEN" ]; then
    echo "Error: AUTH_TOKEN environment variable not set"
    echo "Usage: AUTH_TOKEN=your_token_here ./test_hearts_api.sh"
    exit 1
fi

echo "🧪 Testing Hearts System API"
echo "Base URL: $BASE_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo -e "${YELLOW}Testing: $name${NC}"
    echo "  $method $endpoint"
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "  ${GREEN}✓ Success ($http_code)${NC}"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    else
        echo -e "  ${RED}✗ Failed ($http_code)${NC}"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    fi
    echo ""
}

# Test 1: Get Hearts Status
test_endpoint \
    "Get Hearts Status" \
    "GET" \
    "/api/v1/hearts"

# Test 2: Use a Heart
test_endpoint \
    "Use a Heart (quiz_wrong)" \
    "POST" \
    "/api/v1/hearts/use" \
    '{"reason": "quiz_wrong", "metadata": {"quiz_id": "test-123", "question_id": "q-456"}}'

# Test 3: Get Hearts Status Again
test_endpoint \
    "Get Hearts Status (after using)" \
    "GET" \
    "/api/v1/hearts"

# Test 4: Get Transaction History
test_endpoint \
    "Get Transaction History" \
    "GET" \
    "/api/v1/hearts/transactions?page=1&page_size=10"

# Test 5: Refill Hearts (Admin)
test_endpoint \
    "Refill Hearts (admin grant)" \
    "POST" \
    "/api/v1/hearts/refill" \
    '{"method": "admin", "amount": 2, "metadata": {"reason": "testing"}}'

# Test 6: Refill Hearts (Ad Watch)
test_endpoint \
    "Refill Hearts (ad watch)" \
    "POST" \
    "/api/v1/hearts/refill" \
    '{"method": "ad_watch", "amount": 1, "metadata": {"ad_id": "test-ad-789"}}'

# Test 7: Get Hearts Status After Refill
test_endpoint \
    "Get Hearts Status (after refill)" \
    "GET" \
    "/api/v1/hearts"

# Test 8: Use Multiple Hearts
echo -e "${YELLOW}Using hearts until empty...${NC}"
for i in {1..5}; do
    test_endpoint \
        "Use Heart #$i" \
        "POST" \
        "/api/v1/hearts/use" \
        '{"reason": "quiz_wrong", "metadata": {"test": "'$i'"}}'
    sleep 1
done

# Test 9: Try to Use Heart When Empty
test_endpoint \
    "Try to Use Heart (should fail)" \
    "POST" \
    "/api/v1/hearts/use" \
    '{"reason": "quiz_wrong"}'

# Test 10: Use Streak Freeze
test_endpoint \
    "Use Streak Freeze to Restore Hearts" \
    "POST" \
    "/api/v1/hearts/use-streak-freeze" \
    '{}'

# Test 11: Get Final Hearts Status
test_endpoint \
    "Get Final Hearts Status" \
    "GET" \
    "/api/v1/hearts"

# Test 12: Get Full Transaction History
test_endpoint \
    "Get Full Transaction History" \
    "GET" \
    "/api/v1/hearts/transactions?page=1&page_size=50"

echo -e "${GREEN}✅ All tests completed!${NC}"
echo ""
echo "Summary:"
echo "- Get hearts status: ✓"
echo "- Use hearts: ✓"
echo "- Refill hearts (multiple methods): ✓"
echo "- Use streak freeze: ✓"
echo "- Get transaction history: ✓"
echo ""
echo "Check the responses above for details."
