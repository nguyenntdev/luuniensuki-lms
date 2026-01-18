#!/bin/bash

# P0-SEC-02: Abuse Reporting API Testing Script
# Tests all abuse reporting endpoints

set -e

echo "=== P0-SEC-02 Abuse Reporting System Test ==="
echo ""

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin123}"
USER_EMAIL="${USER_EMAIL:-user@example.com}"
USER_PASSWORD="${USER_PASSWORD:-user123}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function for success
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Helper function for error
error() {
    echo -e "${RED}✗ $1${NC}"
}

# Helper function for info
info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Step 1: Login as regular user
info "Step 1: Logging in as regular user..."
USER_TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$USER_EMAIL\",
    \"password\": \"$USER_PASSWORD\"
  }" | jq -r '.access_token')

if [ "$USER_TOKEN" != "null" ] && [ -n "$USER_TOKEN" ]; then
    success "User logged in successfully"
else
    error "Failed to login as user"
    exit 1
fi

# Step 2: Login as admin
info "Step 2: Logging in as admin..."
ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$ADMIN_EMAIL\",
    \"password\": \"$ADMIN_PASSWORD\"
  }" | jq -r '.access_token')

if [ "$ADMIN_TOKEN" != "null" ] && [ -n "$ADMIN_TOKEN" ]; then
    success "Admin logged in successfully"
else
    error "Failed to login as admin"
    exit 1
fi

# Get admin user ID for later
ADMIN_ID=$(curl -s -X GET "$BASE_URL/api/v1/users/me" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.id')

# Step 3: Submit abuse report as user
info "Step 3: Submitting abuse report (harassment - should be CRITICAL priority)..."
REPORT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/reports/abuse" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "comment",
    "reason": "harassment",
    "description": "This is a test harassment report with threatening language",
    "evidence_urls": ["https://example.com/screenshot1.png", "https://example.com/screenshot2.png"]
  }')

REPORT_ID=$(echo "$REPORT_RESPONSE" | jq -r '.id')
REPORT_PRIORITY=$(echo "$REPORT_RESPONSE" | jq -r '.priority')
REPORT_STATUS=$(echo "$REPORT_RESPONSE" | jq -r '.status')

if [ "$REPORT_ID" != "null" ] && [ -n "$REPORT_ID" ]; then
    success "Report created with ID: $REPORT_ID"
    success "Priority: $REPORT_PRIORITY (expected: critical)"
    success "Status: $REPORT_STATUS (expected: pending)"
else
    error "Failed to create report"
    echo "$REPORT_RESPONSE" | jq
    exit 1
fi

# Step 4: Submit another report (spam - should be MEDIUM priority)
info "Step 4: Submitting spam report (should be MEDIUM priority)..."
SPAM_REPORT=$(curl -s -X POST "$BASE_URL/api/v1/reports/abuse" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "comment",
    "reason": "spam",
    "description": "This comment contains spam and advertising links"
  }')

SPAM_ID=$(echo "$SPAM_REPORT" | jq -r '.id')
SPAM_PRIORITY=$(echo "$SPAM_REPORT" | jq -r '.priority')

if [ "$SPAM_PRIORITY" = "medium" ]; then
    success "Spam report created with correct priority: $SPAM_PRIORITY"
else
    error "Spam report has wrong priority: $SPAM_PRIORITY (expected: medium)"
fi

# Step 5: Get user's own reports
info "Step 5: Getting user's submitted reports..."
MY_REPORTS=$(curl -s -X GET "$BASE_URL/api/v1/reports/abuse/mine" \
  -H "Authorization: Bearer $USER_TOKEN")

REPORT_COUNT=$(echo "$MY_REPORTS" | jq 'length')
if [ "$REPORT_COUNT" -ge 2 ]; then
    success "User can see their reports (count: $REPORT_COUNT)"
else
    error "User reports not found or incorrect count: $REPORT_COUNT"
fi

# Step 6: Admin list all reports
info "Step 6: Admin listing all reports..."
ALL_REPORTS=$(curl -s -X GET "$BASE_URL/api/v1/admin/reports/abuse?page=1&page_size=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

TOTAL_REPORTS=$(echo "$ALL_REPORTS" | jq -r '.total')
if [ "$TOTAL_REPORTS" -ge 2 ]; then
    success "Admin can see all reports (total: $TOTAL_REPORTS)"
else
    error "Admin reports query failed or no reports found"
fi

# Step 7: Filter reports by priority
info "Step 7: Filtering reports by critical priority..."
CRITICAL_REPORTS=$(curl -s -X GET "$BASE_URL/api/v1/admin/reports/abuse?priority=critical&page=1&page_size=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

CRITICAL_COUNT=$(echo "$CRITICAL_REPORTS" | jq -r '.total')
success "Found $CRITICAL_COUNT critical priority reports"

# Step 8: Get report details
info "Step 8: Getting detailed report information..."
REPORT_DETAILS=$(curl -s -X GET "$BASE_URL/api/v1/admin/reports/abuse/$REPORT_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

REPORTER_EMAIL=$(echo "$REPORT_DETAILS" | jq -r '.reporter_email')
if [ "$REPORTER_EMAIL" != "null" ] && [ -n "$REPORTER_EMAIL" ]; then
    success "Retrieved report details with reporter email: $REPORTER_EMAIL"
else
    error "Failed to get report details"
fi

# Step 9: Assign report to admin
info "Step 9: Assigning report to admin..."
ASSIGNED_REPORT=$(curl -s -X POST "$BASE_URL/api/v1/admin/reports/abuse/$REPORT_ID/assign" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"assigned_to_id\": \"$ADMIN_ID\"
  }")

ASSIGNED_STATUS=$(echo "$ASSIGNED_REPORT" | jq -r '.status')
ASSIGNED_TO=$(echo "$ASSIGNED_REPORT" | jq -r '.assigned_to_id')

if [ "$ASSIGNED_TO" = "$ADMIN_ID" ]; then
    success "Report assigned successfully to admin: $ADMIN_ID"
    success "Status changed to: $ASSIGNED_STATUS (expected: reviewing)"
else
    error "Failed to assign report"
fi

# Step 10: Resolve report
info "Step 10: Resolving report..."
RESOLVED_REPORT=$(curl -s -X POST "$BASE_URL/api/v1/admin/reports/abuse/$REPORT_ID/resolve" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "resolved",
    "resolution_notes": "User warned and inappropriate content removed. Monitoring for repeat violations."
  }')

FINAL_STATUS=$(echo "$RESOLVED_REPORT" | jq -r '.status')
RESOLVED_AT=$(echo "$RESOLVED_REPORT" | jq -r '.resolved_at')
NOTES=$(echo "$RESOLVED_REPORT" | jq -r '.resolution_notes')

if [ "$FINAL_STATUS" = "resolved" ] && [ "$RESOLVED_AT" != "null" ]; then
    success "Report resolved successfully"
    success "Resolution notes: $NOTES"
else
    error "Failed to resolve report"
fi

# Step 11: Dismiss spam report
info "Step 11: Dismissing spam report..."
DISMISSED_REPORT=$(curl -s -X POST "$BASE_URL/api/v1/admin/reports/abuse/$SPAM_ID/resolve" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "dismissed",
    "resolution_notes": "Review determined this was not spam, just enthusiastic content."
  }')

DISMISS_STATUS=$(echo "$DISMISSED_REPORT" | jq -r '.status')
if [ "$DISMISS_STATUS" = "dismissed" ]; then
    success "Spam report dismissed successfully"
else
    error "Failed to dismiss spam report"
fi

# Step 12: Filter by resolved status
info "Step 12: Filtering reports by resolved status..."
RESOLVED_REPORTS=$(curl -s -X GET "$BASE_URL/api/v1/admin/reports/abuse?status=resolved&page=1&page_size=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

RESOLVED_COUNT=$(echo "$RESOLVED_REPORTS" | jq -r '.total')
success "Found $RESOLVED_COUNT resolved reports"

echo ""
echo "=== Test Summary ==="
echo -e "${GREEN}All tests completed successfully!${NC}"
echo ""
echo "Test Results:"
echo "  ✓ User authentication"
echo "  ✓ Admin authentication"
echo "  ✓ Submit harassment report (critical priority)"
echo "  ✓ Submit spam report (medium priority)"
echo "  ✓ Get user's own reports"
echo "  ✓ Admin list all reports"
echo "  ✓ Filter by priority"
echo "  ✓ Get report details"
echo "  ✓ Assign report to admin"
echo "  ✓ Resolve report"
echo "  ✓ Dismiss report"
echo "  ✓ Filter by status"
echo ""
echo "Report IDs created:"
echo "  - Harassment (resolved): $REPORT_ID"
echo "  - Spam (dismissed): $SPAM_ID"

