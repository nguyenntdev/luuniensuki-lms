#!/bin/bash

# Test script for P1-SOC-01 Social Features
# This script tests all the social endpoints

# Set your API endpoint and token
API_URL="${API_URL:-http://localhost:8000}"
TOKEN="${TOKEN:-your_token_here}"

echo "============================================="
echo "Testing P1-SOC-01: Social Features"
echo "============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1: Get following list
echo -e "${BLUE}Test 1: GET /api/v1/social/following${NC}"
curl -s -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/social/following?page=1&page_size=20" | jq '.'
echo ""

# Test 2: Get followers list
echo -e "${BLUE}Test 2: GET /api/v1/social/followers${NC}"
curl -s -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/social/followers?page=1&page_size=20" | jq '.'
echo ""

# Test 3: Get friends list
echo -e "${BLUE}Test 3: GET /api/v1/social/friends${NC}"
curl -s -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/social/friends" | jq '.'
echo ""

# Test 4: Follow a user (replace USER_ID_TO_FOLLOW)
USER_ID_TO_FOLLOW="${USER_ID_TO_FOLLOW:-00000000-0000-0000-0000-000000000000}"
echo -e "${BLUE}Test 4: POST /api/v1/social/follow/$USER_ID_TO_FOLLOW${NC}"
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/social/follow/$USER_ID_TO_FOLLOW" | jq '.'
echo ""

# Test 5: Get friend requests
echo -e "${BLUE}Test 5: GET /api/v1/social/friend-requests${NC}"
curl -s -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/social/friend-requests" | jq '.'
echo ""

# Test 6: Send a friend request (replace USER_ID)
USER_ID_TO_REQUEST="${USER_ID_TO_REQUEST:-00000000-0000-0000-0000-000000000000}"
echo -e "${BLUE}Test 6: POST /api/v1/social/friend-requests${NC}"
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"to_user_id\":\"$USER_ID_TO_REQUEST\"}" \
  "$API_URL/api/v1/social/friend-requests" | jq '.'
echo ""

# Test 7: Accept a friend request (replace REQUEST_ID)
REQUEST_ID="${REQUEST_ID:-00000000-0000-0000-0000-000000000000}"
echo -e "${BLUE}Test 7: POST /api/v1/social/friend-requests/$REQUEST_ID/accept${NC}"
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/social/friend-requests/$REQUEST_ID/accept" | jq '.'
echo ""

# Test 8: Reject a friend request (replace REQUEST_ID)
echo -e "${BLUE}Test 8: POST /api/v1/social/friend-requests/$REQUEST_ID/reject${NC}"
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/social/friend-requests/$REQUEST_ID/reject" | jq '.'
echo ""

# Test 9: Unfollow a user
echo -e "${BLUE}Test 9: DELETE /api/v1/social/follow/$USER_ID_TO_FOLLOW${NC}"
curl -s -X DELETE -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/social/follow/$USER_ID_TO_FOLLOW"
echo ""

echo ""
echo "============================================="
echo "Tests Complete!"
echo "============================================="
echo ""
echo "Usage:"
echo "  export TOKEN='your_jwt_token'"
echo "  export USER_ID_TO_FOLLOW='user-uuid'"
echo "  export USER_ID_TO_REQUEST='user-uuid'"
echo "  export REQUEST_ID='request-uuid'"
echo "  ./test_social_features.sh"

