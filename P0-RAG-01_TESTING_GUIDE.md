# P0-RAG-01 Testing Guide

## Prerequisites

1. Backend running on `http://localhost:8000`
2. Admin user credentials
3. Tool for API testing (curl, Postman, or browser dev tools)

## Step 1: Get Admin Token

```bash
# Login as admin
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "your-admin-password"
  }'

# Save the access_token from response
export ADMIN_TOKEN="<access_token_from_response>"
```

## Step 2: Test GET Endpoint

### Test 2.1: Get Current Settings (Success)

```bash
curl -X GET "http://localhost:8000/api/v1/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Response (200 OK):**
```json
{
  "system_instruction": "You are a helpful assistant...",
  "prompt_prefix": "Based on the following context...",
  "model_override": null,
  "temperature": 0.7,
  "max_documents": 6,
  "embedding_enabled": true,
  "hybrid_alpha": 0.6
}
```

### Test 2.2: Get Settings Without Auth (Failure)

```bash
curl -X GET "http://localhost:8000/api/v1/admin/rag/settings"
```

**Expected Response (401 Unauthorized):**
```json
{
  "detail": "Not authenticated"
}
```

### Test 2.3: Get Settings as Non-Admin (Failure)

Use a learner/teacher token instead of admin token.

**Expected Response (403 Forbidden):**
```json
{
  "detail": "Not authorized"
}
```

## Step 3: Test PUT Endpoint

### Test 3.1: Update Single Field (Success)

```bash
curl -X PUT "http://localhost:8000/api/v1/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"temperature": 0.8}'
```

**Expected Response (200 OK):**
```json
{
  "system_instruction": "You are a helpful assistant...",
  "prompt_prefix": "Based on the following context...",
  "model_override": null,
  "temperature": 0.8,
  "max_documents": 6,
  "embedding_enabled": true,
  "hybrid_alpha": 0.6
}
```

**Verify:** Temperature changed to 0.8

### Test 3.2: Update Multiple Fields (Success)

```bash
curl -X PUT "http://localhost:8000/api/v1/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 1.0,
    "max_documents": 10,
    "hybrid_alpha": 0.7
  }'
```

**Verify:** All three fields updated

### Test 3.3: Update System Instruction (Success)

```bash
curl -X PUT "http://localhost:8000/api/v1/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "system_instruction": "You are a test assistant."
  }'
```

**Verify:** system_instruction updated

### Test 3.4: Temperature Too High (Validation Error)

```bash
curl -X PUT "http://localhost:8000/api/v1/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"temperature": 3.0}'
```

**Expected Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "loc": ["body", "temperature"],
      "msg": "ensure this value is less than or equal to 2.0",
      "type": "value_error.number.not_le"
    }
  ]
}
```

### Test 3.5: Temperature Too Low (Validation Error)

```bash
curl -X PUT "http://localhost:8000/api/v1/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"temperature": -0.5}'
```

**Expected Response (422):** Validation error for minimum value

### Test 3.6: Max Documents Too High (Validation Error)

```bash
curl -X PUT "http://localhost:8000/api/v1/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"max_documents": 25}'
```

**Expected Response (422):** Validation error (max is 20)

### Test 3.7: Max Documents Too Low (Validation Error)

```bash
curl -X PUT "http://localhost:8000/api/v1/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"max_documents": 0}'
```

**Expected Response (422):** Validation error (min is 1)

### Test 3.8: Hybrid Alpha Out of Range (Validation Error)

```bash
curl -X PUT "http://localhost:8000/api/v1/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hybrid_alpha": 1.5}'
```

**Expected Response (422):** Validation error (max is 1.0)

### Test 3.9: System Instruction Too Long (Validation Error)

```bash
# Create a string longer than 5000 characters
python3 << 'EOF'
import requests
long_text = "x" * 5001
response = requests.put(
    "http://localhost:8000/api/v1/admin/rag/settings",
    headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
    json={"system_instruction": long_text}
)
print(response.status_code, response.json())
EOF
```

**Expected Response (422):** Validation error (max 5000 chars)

### Test 3.10: Prompt Prefix Too Long (Validation Error)

Similar to 3.9, but with 2001 characters for prompt_prefix.

**Expected Response (422):** Validation error (max 2000 chars)

## Step 4: Test POST Reset Endpoint

### Test 4.1: Reset to Defaults (Success)

```bash
# First, modify some settings
curl -X PUT "http://localhost:8000/api/v1/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 1.5,
    "max_documents": 15,
    "system_instruction": "Custom instruction",
    "hybrid_alpha": 0.9
  }'

# Then reset
curl -X POST "http://localhost:8000/api/v1/admin/rag/settings/reset" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Response (200 OK):**
```json
{
  "system_instruction": "You are a helpful assistant for the Lưu Niên Sử Kí...",
  "prompt_prefix": "Based on the following context from the Cửu Đỉnh...",
  "model_override": null,
  "temperature": 0.7,
  "max_documents": 6,
  "embedding_enabled": true,
  "hybrid_alpha": 0.6
}
```

**Verify:** All values back to defaults

### Test 4.2: Reset Without Auth (Failure)

```bash
curl -X POST "http://localhost:8000/api/v1/admin/rag/settings/reset"
```

**Expected Response (401 Unauthorized)**

### Test 4.3: Reset as Non-Admin (Failure)

Use a learner token.

**Expected Response (403 Forbidden)**

## Step 5: Integration Tests

### Test 5.1: Settings Persist Across Requests

```bash
# Update
curl -X PUT "http://localhost:8000/api/v1/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"temperature": 1.2}'

# Verify persisted
curl -X GET "http://localhost:8000/api/v1/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Verify:** Temperature is still 1.2

### Test 5.2: Partial Update Doesn't Overwrite Others

```bash
# Set multiple values
curl -X PUT "http://localhost:8000/api/v1/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 0.9,
    "max_documents": 8
  }'

# Update only temperature
curl -X PUT "http://localhost:8000/api/v1/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"temperature": 1.0}'

# Get settings
curl -X GET "http://localhost:8000/api/v1/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Verify:** temperature is 1.0, max_documents is still 8

## Test Summary Checklist

- [ ] GET returns current settings
- [ ] GET requires authentication
- [ ] GET requires admin role
- [ ] PUT updates single field
- [ ] PUT updates multiple fields
- [ ] PUT validates temperature range (0.0-2.0)
- [ ] PUT validates max_documents range (1-20)
- [ ] PUT validates hybrid_alpha range (0.0-1.0)
- [ ] PUT validates system_instruction length (≤5000)
- [ ] PUT validates prompt_prefix length (≤2000)
- [ ] PUT allows partial updates
- [ ] PUT requires authentication
- [ ] PUT requires admin role
- [ ] POST reset restores all defaults
- [ ] POST reset requires authentication
- [ ] POST reset requires admin role
- [ ] Settings persist across requests
- [ ] Partial updates don't overwrite other fields

## Automated Test Script

Save as `test_rag_settings.sh`:

```bash
#!/bin/bash
set -e

API="http://localhost:8000/api/v1"
ADMIN_EMAIL="admin@example.com"
ADMIN_PASSWORD="admin-password"

# Login
TOKEN=$(curl -s -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}" \
  | jq -r '.access_token')

echo "Token: $TOKEN"

# Test GET
echo "Test 1: GET settings"
curl -s -X GET "$API/admin/rag/settings" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Test PUT
echo "Test 2: UPDATE temperature"
curl -s -X PUT "$API/admin/rag/settings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"temperature": 0.8}' | jq .

# Test RESET
echo "Test 3: RESET to defaults"
curl -s -X POST "$API/admin/rag/settings/reset" \
  -H "Authorization: Bearer $TOKEN" | jq .

echo "All tests passed!"
```

Run with: `chmod +x test_rag_settings.sh && ./test_rag_settings.sh`

