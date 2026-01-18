#!/bin/bash
# P1-ADAP-01: Spaced Repetition API Testing Script
# 
# This script tests all spaced repetition endpoints
# Make sure the backend is running on localhost:8000

set -e

# Configuration
API_BASE="http://localhost:8000/api/v1"
AUTH_TOKEN=""  # Set this to a valid JWT token

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================="
echo "Spaced Repetition API Testing"
echo "=================================="
echo ""

# Check if token is set
if [ -z "$AUTH_TOKEN" ]; then
    echo -e "${RED}Error: AUTH_TOKEN not set${NC}"
    echo "Please set AUTH_TOKEN to a valid JWT token"
    echo "Example: AUTH_TOKEN=\"your_token_here\" ./test_spaced_repetition.sh"
    exit 1
fi

# Helper function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ -z "$data" ]; then
        curl -s -X "$method" "$API_BASE$endpoint" \
            -H "Authorization: Bearer $AUTH_TOKEN" \
            -H "Content-Type: application/json"
    else
        curl -s -X "$method" "$API_BASE$endpoint" \
            -H "Authorization: Bearer $AUTH_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data"
    fi
}

# Test 1: Get Review Stats (initial state)
echo -e "${YELLOW}Test 1: Get initial review statistics${NC}"
STATS=$(api_call GET "/review/stats")
echo "$STATS" | jq '.'
TOTAL_CARDS=$(echo "$STATS" | jq -r '.total_cards')
echo -e "${GREEN}✓ Initial total cards: $TOTAL_CARDS${NC}"
echo ""

# Test 2: Get Due Cards (should be empty or show existing)
echo -e "${YELLOW}Test 2: Get due cards${NC}"
DUE_CARDS=$(api_call GET "/review/due?limit=10")
echo "$DUE_CARDS" | jq '.'
DUE_COUNT=$(echo "$DUE_CARDS" | jq -r '.total_due')
echo -e "${GREEN}✓ Due cards count: $DUE_COUNT${NC}"
echo ""

# Test 3: Get a motif ID to add
echo -e "${YELLOW}Test 3: Get a motif to add to review deck${NC}"
MOTIFS=$(curl -s "$API_BASE/motifs" \
    -H "Authorization: Bearer $AUTH_TOKEN")
MOTIF_ID=$(echo "$MOTIFS" | jq -r '.motifs[0].id')
MOTIF_NAME=$(echo "$MOTIFS" | jq -r '.motifs[0].name')
echo "Selected motif: $MOTIF_NAME ($MOTIF_ID)"
echo ""

# Test 4: Add Card to Review Deck
echo -e "${YELLOW}Test 4: Add motif to review deck${NC}"
ADD_RESPONSE=$(api_call POST "/review/cards" "{\"motif_id\": \"$MOTIF_ID\"}")
echo "$ADD_RESPONSE" | jq '.'
CARD_ID=$(echo "$ADD_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Card added with ID: $CARD_ID${NC}"
echo ""

# Test 5: Verify card appears in due cards
echo -e "${YELLOW}Test 5: Verify card appears in due cards${NC}"
DUE_CARDS=$(api_call GET "/review/due?limit=10")
NEW_DUE_COUNT=$(echo "$DUE_CARDS" | jq -r '.total_due')
echo "Due cards count: $NEW_DUE_COUNT"
if [ "$NEW_DUE_COUNT" -gt "$DUE_COUNT" ]; then
    echo -e "${GREEN}✓ Card successfully added to due cards${NC}"
else
    echo -e "${YELLOW}⚠ Card might already exist${NC}"
fi
echo ""

# Test 6: Submit Review - Perfect (5)
echo -e "${YELLOW}Test 6: Submit review with quality 5 (perfect)${NC}"
REVIEW_RESPONSE=$(api_call POST "/review/$CARD_ID" '{"quality": 5}')
echo "$REVIEW_RESPONSE" | jq '.'
INTERVAL_1=$(echo "$REVIEW_RESPONSE" | jq -r '.interval_days')
REPS_1=$(echo "$REVIEW_RESPONSE" | jq -r '.repetitions')
EASE_1=$(echo "$REVIEW_RESPONSE" | jq -r '.ease_factor')
echo "After review: interval=$INTERVAL_1 days, repetitions=$REPS_1, ease=$EASE_1"
echo -e "${GREEN}✓ First review submitted${NC}"
echo ""

# Test 7: Check updated stats
echo -e "${YELLOW}Test 7: Check updated statistics${NC}"
STATS=$(api_call GET "/review/stats")
echo "$STATS" | jq '.'
REVIEWED_TODAY=$(echo "$STATS" | jq -r '.reviewed_today')
echo -e "${GREEN}✓ Reviewed today: $REVIEWED_TODAY${NC}"
echo ""

# Wait a moment
sleep 1

# Test 8: Try to review again (should work but card won't be due)
echo -e "${YELLOW}Test 8: Submit another review (quality 4)${NC}"
# Note: This will work but the card won't appear in due cards until next_review_at
REVIEW_RESPONSE=$(api_call POST "/review/$CARD_ID" '{"quality": 4}')
echo "$REVIEW_RESPONSE" | jq '.'
INTERVAL_2=$(echo "$REVIEW_RESPONSE" | jq -r '.interval_days')
REPS_2=$(echo "$REVIEW_RESPONSE" | jq -r '.repetitions')
EASE_2=$(echo "$REVIEW_RESPONSE" | jq -r '.ease_factor')
echo "After 2nd review: interval=$INTERVAL_2 days, repetitions=$REPS_2, ease=$EASE_2"
echo -e "${GREEN}✓ Second review submitted${NC}"
echo ""

# Test 9: Submit Failed Review (quality 2)
echo -e "${YELLOW}Test 9: Submit failed review (quality 2)${NC}"
REVIEW_RESPONSE=$(api_call POST "/review/$CARD_ID" '{"quality": 2}')
echo "$REVIEW_RESPONSE" | jq '.'
INTERVAL_3=$(echo "$REVIEW_RESPONSE" | jq -r '.interval_days')
REPS_3=$(echo "$REVIEW_RESPONSE" | jq -r '.repetitions')
echo "After failed review: interval=$INTERVAL_3 days, repetitions=$REPS_3"
if [ "$REPS_3" == "0" ] && [ "$INTERVAL_3" == "1" ]; then
    echo -e "${GREEN}✓ Card correctly reset after failure${NC}"
else
    echo -e "${RED}✗ Card should reset to interval=1, repetitions=0${NC}"
fi
echo ""

# Test 10: Final statistics
echo -e "${YELLOW}Test 10: Get final statistics${NC}"
STATS=$(api_call GET "/review/stats")
echo "$STATS" | jq '.'
echo -e "${GREEN}✓ Final stats retrieved${NC}"
echo ""

# Test 11: Error handling - Invalid quality
echo -e "${YELLOW}Test 11: Error handling - Invalid quality (6)${NC}"
ERROR_RESPONSE=$(api_call POST "/review/$CARD_ID" '{"quality": 6}' 2>&1)
if echo "$ERROR_RESPONSE" | grep -q "error\|detail"; then
    echo -e "${GREEN}✓ Correctly rejected invalid quality${NC}"
else
    echo -e "${RED}✗ Should reject quality > 5${NC}"
fi
echo ""

# Test 12: Error handling - Non-existent card
echo -e "${YELLOW}Test 12: Error handling - Non-existent card${NC}"
FAKE_UUID="00000000-0000-0000-0000-000000000000"
ERROR_RESPONSE=$(api_call POST "/review/$FAKE_UUID" '{"quality": 4}' 2>&1)
if echo "$ERROR_RESPONSE" | grep -q "not found\|Not Found"; then
    echo -e "${GREEN}✓ Correctly returned 404 for non-existent card${NC}"
else
    echo -e "${YELLOW}⚠ Response: $ERROR_RESPONSE${NC}"
fi
echo ""

# Test 13: Get card's review history
echo -e "${YELLOW}Test 13: Verify review history is tracked${NC}"
CARD_DETAILS=$(api_call GET "/review/due?limit=100")
HISTORY_COUNT=$(echo "$CARD_DETAILS" | jq -r ".cards[] | select(.id == \"$CARD_ID\") | .review_history | length")
echo "Review history entries: $HISTORY_COUNT"
if [ "$HISTORY_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Review history is being tracked${NC}"
    echo "History details:"
    echo "$CARD_DETAILS" | jq -r ".cards[] | select(.id == \"$CARD_ID\") | .review_history[]"
else
    echo -e "${YELLOW}⚠ Review history might not be saved yet${NC}"
fi
echo ""

# Summary
echo "=================================="
echo -e "${GREEN}Testing Complete!${NC}"
echo "=================================="
echo ""
echo "Summary:"
echo "- Card ID: $CARD_ID"
echo "- Motif: $MOTIF_NAME"
echo "- Reviews submitted: 3"
echo "- Current interval: $INTERVAL_3 days"
echo "- Current repetitions: $REPS_3"
echo ""
echo "Next steps:"
echo "1. Check the card appears correctly in the mobile app"
echo "2. Verify review workflow in the UI"
echo "3. Test notification system for due cards"
echo "4. Monitor performance with large card decks"
echo ""

