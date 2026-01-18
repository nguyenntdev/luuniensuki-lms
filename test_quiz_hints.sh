#!/bin/bash
# Test script for P1-AI-02 Quiz Hints API
# Usage: ./test_quiz_hints.sh <base_url> <token> <question_id>

set -e

BASE_URL="${1:-http://localhost:8000}"
TOKEN="${2}"
QUESTION_ID="${3}"

if [ -z "$TOKEN" ] || [ -z "$QUESTION_ID" ]; then
    echo "Usage: $0 <base_url> <token> <question_id>"
    echo "Example: $0 http://localhost:8000 eyJhbGc... abc-123-def"
    exit 1
fi

echo "==================================="
echo "Testing Quiz Hints API"
echo "==================================="
echo "Base URL: $BASE_URL"
echo "Question ID: $QUESTION_ID"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1: Request explain hint (free)
echo -e "${BLUE}Test 1: Request EXPLAIN hint (0 hearts)${NC}"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/quiz/questions/$QUESTION_ID/hint" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hint_type": "explain"}')

echo "$RESPONSE" | jq '.'
HEART_COST=$(echo "$RESPONSE" | jq -r '.heart_cost // "error"')
if [ "$HEART_COST" == "0" ]; then
    echo -e "${GREEN}✓ PASS: Explain hint costs 0 hearts${NC}"
else
    echo -e "${RED}✗ FAIL: Expected cost 0, got $HEART_COST${NC}"
fi
echo ""

# Test 2: Request clue hint (1 heart)
echo -e "${BLUE}Test 2: Request CLUE hint (1 heart)${NC}"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/quiz/questions/$QUESTION_ID/hint" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hint_type": "clue"}')

echo "$RESPONSE" | jq '.'
HEART_COST=$(echo "$RESPONSE" | jq -r '.heart_cost // "error"')
if [ "$HEART_COST" == "1" ]; then
    echo -e "${GREEN}✓ PASS: Clue hint costs 1 heart${NC}"
else
    echo -e "${RED}✗ FAIL: Expected cost 1, got $HEART_COST${NC}"
fi
echo ""

# Test 3: Request elimination hint (2 hearts)
echo -e "${BLUE}Test 3: Request ELIMINATION hint (2 hearts)${NC}"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/quiz/questions/$QUESTION_ID/hint" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hint_type": "elimination"}')

echo "$RESPONSE" | jq '.'
HEART_COST=$(echo "$RESPONSE" | jq -r '.heart_cost // "error"')
if [ "$HEART_COST" == "2" ]; then
    echo -e "${GREEN}✓ PASS: Elimination hint costs 2 hearts${NC}"
else
    echo -e "${RED}✗ FAIL: Expected cost 2, got $HEART_COST${NC}"
fi
echo ""

# Test 4: Try to request duplicate hint (should fail)
echo -e "${BLUE}Test 4: Request duplicate EXPLAIN hint (should fail)${NC}"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/quiz/questions/$QUESTION_ID/hint" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hint_type": "explain"}')

echo "$RESPONSE" | jq '.'
ERROR=$(echo "$RESPONSE" | jq -r '.detail // ""')
if [[ "$ERROR" == *"already used"* ]]; then
    echo -e "${GREEN}✓ PASS: Duplicate hint rejected${NC}"
else
    echo -e "${RED}✗ FAIL: Should reject duplicate hint${NC}"
fi
echo ""

# Test 5: Get hint history
echo -e "${BLUE}Test 5: Get hint history${NC}"
RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/quiz/questions/$QUESTION_ID/hints" \
  -H "Authorization: Bearer $TOKEN")

echo "$RESPONSE" | jq '.'
TOTAL=$(echo "$RESPONSE" | jq -r '.total // 0')
if [ "$TOTAL" -ge "3" ]; then
    echo -e "${GREEN}✓ PASS: Hint history retrieved (total: $TOTAL)${NC}"
else
    echo -e "${RED}✗ FAIL: Expected at least 3 hints, got $TOTAL${NC}"
fi
echo ""

# Test 6: Invalid hint type
echo -e "${BLUE}Test 6: Request invalid hint type${NC}"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/quiz/questions/$QUESTION_ID/hint" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hint_type": "invalid"}')

echo "$RESPONSE" | jq '.'
ERROR=$(echo "$RESPONSE" | jq -r '.detail // ""')
if [[ "$ERROR" == *"Invalid hint_type"* ]]; then
    echo -e "${GREEN}✓ PASS: Invalid hint type rejected${NC}"
else
    echo -e "${RED}✗ FAIL: Should reject invalid hint type${NC}"
fi
echo ""

# Test 7: Invalid question ID
echo -e "${BLUE}Test 7: Request hint for invalid question${NC}"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/quiz/questions/00000000-0000-0000-0000-000000000000/hint" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hint_type": "explain"}')

echo "$RESPONSE" | jq '.'
ERROR=$(echo "$RESPONSE" | jq -r '.detail // ""')
if [[ "$ERROR" == *"not found"* ]]; then
    echo -e "${GREEN}✓ PASS: Invalid question rejected${NC}"
else
    echo -e "${RED}✗ FAIL: Should reject invalid question${NC}"
fi
echo ""

echo "==================================="
echo "All tests completed!"
echo "==================================="

