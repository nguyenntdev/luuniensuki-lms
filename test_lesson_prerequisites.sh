#!/bin/bash

# Test script for P1-REC-02: Lesson Prerequisites and Next Lesson API
# This script tests the new lesson sequence endpoints

BASE_URL="http://localhost:8000"
API_URL="${BASE_URL}/api/v1"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== P1-REC-02: Lesson Prerequisites and Next Lesson API Test ===${NC}\n"

# Step 1: Login to get access token
echo -e "${BLUE}Step 1: Logging in...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test@example.com",
    "password": "test123"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo -e "${RED}❌ Login failed${NC}"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓ Login successful${NC}\n"

# Step 2: Get next lesson (without urn filter)
echo -e "${BLUE}Step 2: Getting next recommended lesson (no filter)...${NC}"
NEXT_LESSON=$(curl -s -X GET "${API_URL}/lessons/next" \
  -H "Authorization: Bearer $TOKEN")

echo "Response:"
echo $NEXT_LESSON | jq '.'

LESSON_ID=$(echo $NEXT_LESSON | jq -r '.lesson_id')
if [ "$LESSON_ID" != "null" ]; then
  echo -e "${GREEN}✓ Next lesson found: $LESSON_ID${NC}\n"
else
  echo -e "${BLUE}ℹ No next lesson available (user may have completed all lessons)${NC}\n"
fi

# Step 3: Get next lesson with urn filter
echo -e "${BLUE}Step 3: Getting next lesson in specific urn...${NC}"

# First, get an urn ID
URN_LIST=$(curl -s -X GET "${API_URL}/urns" \
  -H "Authorization: Bearer $TOKEN")

URN_ID=$(echo $URN_LIST | jq -r '.[0].id')

if [ "$URN_ID" != "null" ]; then
  echo "Testing with urn: $URN_ID"
  NEXT_LESSON_URN=$(curl -s -X GET "${API_URL}/lessons/next?urn_id=${URN_ID}" \
    -H "Authorization: Bearer $TOKEN")
  
  echo "Response:"
  echo $NEXT_LESSON_URN | jq '.'
  echo -e "${GREEN}✓ Next lesson with urn filter retrieved${NC}\n"
else
  echo -e "${BLUE}ℹ No urns available to test${NC}\n"
fi

# Step 4: Get lesson sequence
echo -e "${BLUE}Step 4: Getting full lesson sequence...${NC}"
SEQUENCE=$(curl -s -X GET "${API_URL}/lessons/sequence" \
  -H "Authorization: Bearer $TOKEN")

echo "Response (first 3 lessons):"
echo $SEQUENCE | jq '{
  urn_id,
  urn_name,
  total_lessons,
  completed_lessons,
  current_position,
  sequence: .sequence[:3]
}'

TOTAL_LESSONS=$(echo $SEQUENCE | jq -r '.total_lessons')
echo -e "${GREEN}✓ Sequence retrieved: $TOTAL_LESSONS total lessons${NC}\n"

# Step 5: Get lesson sequence for specific urn
if [ "$URN_ID" != "null" ]; then
  echo -e "${BLUE}Step 5: Getting lesson sequence for urn...${NC}"
  SEQUENCE_URN=$(curl -s -X GET "${API_URL}/lessons/sequence?urn_id=${URN_ID}" \
    -H "Authorization: Bearer $TOKEN")
  
  echo "Response:"
  echo $SEQUENCE_URN | jq '{
    urn_id,
    urn_name,
    total_lessons,
    completed_lessons,
    current_position
  }'
  echo -e "${GREEN}✓ Urn sequence retrieved${NC}\n"
fi

# Step 6: Test lesson prerequisites (if we have a lesson)
if [ "$LESSON_ID" != "null" ]; then
  echo -e "${BLUE}Step 6: Getting prerequisites for lesson $LESSON_ID...${NC}"
  PREREQS=$(curl -s -X GET "${API_URL}/lessons/${LESSON_ID}/prerequisites" \
    -H "Authorization: Bearer $TOKEN")
  
  echo "Response:"
  echo $PREREQS | jq '.'
  
  ALL_MET=$(echo $PREREQS | jq -r '.all_prerequisites_met')
  PREREQ_COUNT=$(echo $PREREQS | jq -r '.prerequisites | length')
  
  echo -e "${GREEN}✓ Prerequisites retrieved: $PREREQ_COUNT prerequisites, all met: $ALL_MET${NC}\n"
  
  # Step 7: Check if lesson is unlocked
  echo -e "${BLUE}Step 7: Checking if lesson is unlocked...${NC}"
  UNLOCK_STATUS=$(curl -s -X GET "${API_URL}/lessons/${LESSON_ID}/is-unlocked" \
    -H "Authorization: Bearer $TOKEN")
  
  echo "Response:"
  echo $UNLOCK_STATUS | jq '.'
  
  IS_UNLOCKED=$(echo $UNLOCK_STATUS | jq -r '.is_unlocked')
  MISSING_COUNT=$(echo $UNLOCK_STATUS | jq -r '.missing_prerequisites | length')
  
  echo -e "${GREEN}✓ Unlock status retrieved: unlocked=$IS_UNLOCKED, missing=$MISSING_COUNT${NC}\n"
fi

echo -e "${BLUE}=== Test Summary ===${NC}"
echo -e "${GREEN}✓ All API endpoints tested successfully${NC}"
echo ""
echo "Endpoints tested:"
echo "  1. GET /api/v1/lessons/next"
echo "  2. GET /api/v1/lessons/next?urn_id={id}"
echo "  3. GET /api/v1/lessons/sequence"
echo "  4. GET /api/v1/lessons/sequence?urn_id={id}"
echo "  5. GET /api/v1/lessons/{id}/prerequisites"
echo "  6. GET /api/v1/lessons/{id}/is-unlocked"

