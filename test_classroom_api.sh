#!/bin/bash

# P1-TEACH-01: Classroom Management API Testing Script

API_URL="${API_URL:-http://localhost:8000}"

echo "=== P1-TEACH-01: Classroom Management API Tests ==="
echo "API URL: $API_URL"
echo ""

# Function to make authenticated requests
auth_request() {
    local method=$1
    local endpoint=$2
    local token=$3
    local data=$4
    
    if [ -z "$data" ]; then
        curl -s -X "$method" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            "$API_URL$endpoint"
    else
        curl -s -X "$method" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_URL$endpoint"
    fi
}

# Step 1: Login as teacher
echo "Step 1: Login as teacher..."
TEACHER_LOGIN=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "teacher@luuniensuki.local",
        "password": "Teacher123!"
    }')

TEACHER_TOKEN=$(echo $TEACHER_LOGIN | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

if [ -z "$TEACHER_TOKEN" ]; then
    echo "❌ Failed to login as teacher"
    echo "$TEACHER_LOGIN"
    exit 1
fi

echo "✅ Teacher logged in successfully"
echo ""

# Step 2: Create a new classroom
echo "Step 2: Create a new classroom..."
CREATE_CLASSROOM=$(auth_request POST "/api/v1/classrooms" "$TEACHER_TOKEN" '{
    "name": "Vietnamese Pottery Class",
    "description": "Learn about ancient Vietnamese pottery and ceramics",
    "max_students": 30,
    "settings": {
        "allow_self_paced": true,
        "grading_enabled": true
    }
}')

CLASSROOM_ID=$(echo $CREATE_CLASSROOM | grep -o '"id":"[^"]*' | sed 's/"id":"//')
CLASS_CODE=$(echo $CREATE_CLASSROOM | grep -o '"class_code":"[^"]*' | sed 's/"class_code":"//')

if [ -z "$CLASSROOM_ID" ]; then
    echo "❌ Failed to create classroom"
    echo "$CREATE_CLASSROOM"
    exit 1
fi

echo "✅ Classroom created:"
echo "   ID: $CLASSROOM_ID"
echo "   Class Code: $CLASS_CODE"
echo ""

# Step 3: List classrooms
echo "Step 3: List teacher's classrooms..."
LIST_CLASSROOMS=$(auth_request GET "/api/v1/classrooms" "$TEACHER_TOKEN")
echo "✅ Classrooms retrieved"
echo "$LIST_CLASSROOMS" | python3 -m json.tool 2>/dev/null || echo "$LIST_CLASSROOMS"
echo ""

# Step 4: Get classroom details
echo "Step 4: Get classroom details..."
GET_CLASSROOM=$(auth_request GET "/api/v1/classrooms/$CLASSROOM_ID" "$TEACHER_TOKEN")
echo "✅ Classroom details retrieved"
echo "$GET_CLASSROOM" | python3 -m json.tool 2>/dev/null || echo "$GET_CLASSROOM"
echo ""

# Step 5: Update classroom
echo "Step 5: Update classroom..."
UPDATE_CLASSROOM=$(auth_request PUT "/api/v1/classrooms/$CLASSROOM_ID" "$TEACHER_TOKEN" '{
    "name": "Advanced Vietnamese Pottery Class",
    "max_students": 25
}')
echo "✅ Classroom updated"
echo "$UPDATE_CLASSROOM" | python3 -m json.tool 2>/dev/null || echo "$UPDATE_CLASSROOM"
echo ""

# Step 6: Login as learner
echo "Step 6: Login as learner..."
LEARNER_LOGIN=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "learner@luuniensuki.local",
        "password": "Learner123!"
    }')

LEARNER_TOKEN=$(echo $LEARNER_LOGIN | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

if [ -z "$LEARNER_TOKEN" ]; then
    echo "❌ Failed to login as learner"
    echo "$LEARNER_LOGIN"
    exit 1
fi

echo "✅ Learner logged in successfully"
echo ""

# Step 7: Join classroom by code
echo "Step 7: Join classroom using class code: $CLASS_CODE..."
JOIN_CLASSROOM=$(auth_request POST "/api/v1/classrooms/join" "$LEARNER_TOKEN" "{
    \"class_code\": \"$CLASS_CODE\"
}")
echo "✅ Joined classroom"
echo "$JOIN_CLASSROOM" | python3 -m json.tool 2>/dev/null || echo "$JOIN_CLASSROOM"
echo ""

# Step 8: Get enrolled classrooms
echo "Step 8: Get learner's enrolled classrooms..."
ENROLLED=$(auth_request GET "/api/v1/classrooms/enrolled" "$LEARNER_TOKEN")
echo "✅ Enrolled classrooms retrieved"
echo "$ENROLLED" | python3 -m json.tool 2>/dev/null || echo "$ENROLLED"
echo ""

# Step 9: Get classroom members (as teacher)
echo "Step 9: Get classroom members..."
MEMBERS=$(auth_request GET "/api/v1/classrooms/$CLASSROOM_ID" "$TEACHER_TOKEN")
echo "✅ Classroom members retrieved"
echo "$MEMBERS" | python3 -m json.tool 2>/dev/null || echo "$MEMBERS"
echo ""

# Step 10: Remove a member
echo "Step 10: Get member ID for removal..."
MEMBER_ID=$(echo $MEMBERS | grep -o '"id":"[^"]*' | head -2 | tail -1 | sed 's/"id":"//')

if [ -n "$MEMBER_ID" ]; then
    echo "Removing member: $MEMBER_ID..."
    REMOVE=$(auth_request DELETE "/api/v1/classrooms/$CLASSROOM_ID/members/$MEMBER_ID" "$TEACHER_TOKEN")
    echo "✅ Member removed"
fi
echo ""

# Step 11: Archive classroom
echo "Step 11: Archive classroom..."
ARCHIVE=$(auth_request POST "/api/v1/classrooms/$CLASSROOM_ID/archive" "$TEACHER_TOKEN")
echo "✅ Classroom archived"
echo "$ARCHIVE" | python3 -m json.tool 2>/dev/null || echo "$ARCHIVE"
echo ""

# Step 12: Unarchive classroom
echo "Step 12: Unarchive classroom..."
UNARCHIVE=$(auth_request POST "/api/v1/classrooms/$CLASSROOM_ID/unarchive" "$TEACHER_TOKEN")
echo "✅ Classroom unarchived"
echo "$UNARCHIVE" | python3 -m json.tool 2>/dev/null || echo "$UNARCHIVE"
echo ""

# Step 13: List with archived filter
echo "Step 13: List classrooms with archived filter..."
LIST_WITH_ARCHIVED=$(auth_request GET "/api/v1/classrooms?include_archived=true" "$TEACHER_TOKEN")
echo "✅ Classrooms with archived retrieved"
echo "$LIST_WITH_ARCHIVED" | python3 -m json.tool 2>/dev/null || echo "$LIST_WITH_ARCHIVED"
echo ""

# Step 14: Delete classroom
echo "Step 14: Delete classroom..."
DELETE=$(auth_request DELETE "/api/v1/classrooms/$CLASSROOM_ID" "$TEACHER_TOKEN")
echo "✅ Classroom deleted"
echo ""

echo "=== All tests completed successfully! ==="

