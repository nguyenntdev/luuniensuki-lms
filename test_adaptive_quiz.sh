#!/bin/bash

# P1-ADAP-02 Adaptive Quiz Testing Script
# This script tests the adaptive quiz endpoints

set -e

# Configuration
BASE_URL="${API_BASE_URL:-http://localhost:8000}"
TOKEN="${API_TOKEN:-}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function to print colored output
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if token is set
if [ -z "$TOKEN" ]; then
    print_error "API_TOKEN environment variable is not set"
    echo "Usage: API_TOKEN=<your-jwt-token> ./test_adaptive_quiz.sh"
    exit 1
fi

# Test 1: Get User Skills (Initial State)
print_header "TEST 1: Get User Skills (Initial State)"
response=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    "$BASE_URL/api/v1/skills")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    print_success "User skills retrieved successfully"
    echo "$body" | jq '.'
else
    print_error "Failed to get user skills (HTTP $http_code)"
    echo "$body"
fi

# Test 2: Get Adaptive Quiz (No filters)
print_header "TEST 2: Get Adaptive Quiz (No Filters)"
response=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    "$BASE_URL/api/v1/quiz/adaptive?limit=5")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    print_success "Adaptive quiz retrieved successfully"
    question_count=$(echo "$body" | jq '.questions | length')
    recommended_difficulty=$(echo "$body" | jq '.recommended_difficulty')
    print_info "Questions returned: $question_count"
    print_info "Recommended difficulty: $recommended_difficulty"
    echo "$body" | jq '.'
else
    print_error "Failed to get adaptive quiz (HTTP $http_code)"
    echo "$body"
fi

# Test 3: Get Adaptive Quiz (Motif Recognition)
print_header "TEST 3: Get Adaptive Quiz (Motif Recognition)"
response=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    "$BASE_URL/api/v1/quiz/adaptive?skill_type=motif_recognition&limit=3")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    print_success "Adaptive quiz for motif_recognition retrieved"
    echo "$body" | jq '.'
elif [ "$http_code" -eq 404 ]; then
    print_info "No questions found for motif_recognition (this is OK if no questions are tagged)"
    echo "$body" | jq '.'
else
    print_error "Failed to get adaptive quiz (HTTP $http_code)"
    echo "$body"
fi

# Test 4: Get Adaptive Quiz (History Knowledge)
print_header "TEST 4: Get Adaptive Quiz (History Knowledge)"
response=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    "$BASE_URL/api/v1/quiz/adaptive?skill_type=history_knowledge&limit=3")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    print_success "Adaptive quiz for history_knowledge retrieved"
    echo "$body" | jq '.'
elif [ "$http_code" -eq 404 ]; then
    print_info "No questions found for history_knowledge (this is OK if no questions are tagged)"
    echo "$body" | jq '.'
else
    print_error "Failed to get adaptive quiz (HTTP $http_code)"
    echo "$body"
fi

# Test 5: Get Adaptive Quiz (Invalid Skill Type)
print_header "TEST 5: Get Adaptive Quiz (Invalid Skill Type)"
response=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    "$BASE_URL/api/v1/quiz/adaptive?skill_type=invalid_type&limit=3")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 400 ]; then
    print_success "Correctly rejected invalid skill type"
    echo "$body" | jq '.'
else
    print_error "Expected 400 for invalid skill type, got HTTP $http_code"
    echo "$body"
fi

# Test 6: Recalculate User Skills
print_header "TEST 6: Recalculate User Skills"
response=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$BASE_URL/api/v1/skills/recalculate")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    print_success "Skills recalculated successfully"
    echo "$body" | jq '.'
else
    print_error "Failed to recalculate skills (HTTP $http_code)"
    echo "$body"
fi

# Test 7: Get User Skills (After Recalculation)
print_header "TEST 7: Get User Skills (After Recalculation)"
response=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    "$BASE_URL/api/v1/skills")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    print_success "User skills retrieved successfully"
    overall_level=$(echo "$body" | jq '.overall_level')
    print_info "Overall skill level: $overall_level"
    echo "$body" | jq '.'
else
    print_error "Failed to get user skills (HTTP $http_code)"
    echo "$body"
fi

# Summary
print_header "TEST SUMMARY"
echo -e "${GREEN}All tests completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Check that skill levels are created with default value 0.5"
echo "2. Submit some quizzes to test skill level updates"
echo "3. Verify that adaptive quiz questions match user skill level"
echo "4. Monitor skill progression over time"


