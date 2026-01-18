# Onboarding API Quick Reference

## Endpoints

### 1. Save Onboarding Goal
**POST** `/api/v1/onboarding/goals`

**Headers:**
- Cookie: `luuniensuki_access=<jwt_token>`

**Request Body:**
```json
{
  "goal": "learn_culture"
}
```

**Valid Goals:**
- `learn_culture` - Learn about Vietnamese culture and history
- `pass_exam` - Pass exams or assessments  
- `curiosity` - General curiosity and exploration
- `professional` - Professional development
- `hobby` - Personal hobby/interest

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Onboarding goal saved successfully",
  "goal": "learn_culture"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": {
    "code": "INVALID_GOAL",
    "message": "Invalid goal. Must be one of: learn_culture, pass_exam, curiosity, professional, hobby"
  }
}
```

---

### 2. Get Onboarding Status
**GET** `/api/v1/onboarding/status`

**Headers:**
- Cookie: `luuniensuki_access=<jwt_token>`

**Response (200 OK):**
```json
{
  "onboarding_completed": false,
  "onboarding_goal": "learn_culture",
  "onboarding_completed_at": null
}
```

**Example (completed):**
```json
{
  "onboarding_completed": true,
  "onboarding_goal": "learn_culture",
  "onboarding_completed_at": "2025-01-16T10:30:00Z"
}
```

---

### 3. Complete Onboarding
**POST** `/api/v1/onboarding/complete`

**Headers:**
- Cookie: `luuniensuki_access=<jwt_token>`

**Request Body:** None (empty)

**Response (200 OK - First time):**
```json
{
  "success": true,
  "message": "Onboarding completed successfully",
  "onboarding_completed": true,
  "onboarding_completed_at": "2025-01-16T10:30:00Z"
}
```

**Response (200 OK - Already completed):**
```json
{
  "success": true,
  "message": "Onboarding already completed",
  "onboarding_completed": true,
  "onboarding_completed_at": "2025-01-15T09:20:00Z"
}
```

---

## Usage Flow

### Typical Onboarding Flow

```
1. User registers/logs in
   ↓
2. Check onboarding status
   GET /api/v1/onboarding/status
   ↓
3. If not completed, show onboarding screens
   ↓
4. User selects goal (Screen 1-2)
   POST /api/v1/onboarding/goals
   ↓
5. User completes remaining onboarding steps
   ↓
6. Mark onboarding as complete
   POST /api/v1/onboarding/complete
   ↓
7. Redirect to main app
```

### Frontend Integration (JavaScript/React)

```javascript
// 1. Check if onboarding is needed
async function checkOnboarding() {
  const res = await fetch('/api/v1/onboarding/status', {
    credentials: 'include'
  });
  const data = await res.json();
  
  if (!data.onboarding_completed) {
    // Show onboarding flow
    showOnboarding();
  } else {
    // Go to main app
    redirectToApp();
  }
}

// 2. Save user's goal selection
async function saveGoal(goal) {
  const res = await fetch('/api/v1/onboarding/goals', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify({ goal })
  });
  
  if (!res.ok) {
    const error = await res.json();
    alert(error.error.message);
    return false;
  }
  
  return true;
}

// 3. Complete onboarding
async function finishOnboarding() {
  const res = await fetch('/api/v1/onboarding/complete', {
    method: 'POST',
    credentials: 'include'
  });
  
  const data = await res.json();
  console.log(data.message);
  redirectToApp();
}
```

### Frontend Integration (TypeScript/React)

```typescript
interface OnboardingStatus {
  onboarding_completed: boolean;
  onboarding_goal: string | null;
  onboarding_completed_at: string | null;
}

interface OnboardingResponse {
  success: boolean;
  message: string;
  onboarding_completed: boolean;
  onboarding_completed_at: string | null;
}

// Check onboarding status
export async function getOnboardingStatus(): Promise<OnboardingStatus> {
  const res = await fetch('/api/v1/onboarding/status', {
    credentials: 'include'
  });
  return res.json();
}

// Save goal
export async function saveOnboardingGoal(goal: string): Promise<void> {
  const res = await fetch('/api/v1/onboarding/goals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ goal })
  });
  
  if (!res.ok) {
    throw new Error('Failed to save goal');
  }
}

// Complete onboarding
export async function completeOnboarding(): Promise<OnboardingResponse> {
  const res = await fetch('/api/v1/onboarding/complete', {
    method: 'POST',
    credentials: 'include'
  });
  return res.json();
}
```

---

## Mobile Integration (Flutter/Dart)

```dart
// Check onboarding status
Future<Map<String, dynamic>> checkOnboardingStatus() async {
  final response = await dio.get('/api/v1/onboarding/status');
  return response.data;
}

// Save goal
Future<void> saveOnboardingGoal(String goal) async {
  await dio.post(
    '/api/v1/onboarding/goals',
    data: {'goal': goal},
  );
}

// Complete onboarding
Future<Map<String, dynamic>> completeOnboarding() async {
  final response = await dio.post('/api/v1/onboarding/complete');
  return response.data;
}
```

---

## Testing with cURL

```bash
# 1. Login first to get cookie
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}' \
  -c cookies.txt

# 2. Check onboarding status
curl -X GET http://localhost:8000/api/v1/onboarding/status \
  -b cookies.txt

# 3. Save goal
curl -X POST http://localhost:8000/api/v1/onboarding/goals \
  -H "Content-Type: application/json" \
  -d '{"goal":"learn_culture"}' \
  -b cookies.txt

# 4. Complete onboarding
curl -X POST http://localhost:8000/api/v1/onboarding/complete \
  -b cookies.txt

# 5. Verify completion
curl -X GET http://localhost:8000/api/v1/onboarding/status \
  -b cookies.txt
```

---

## Notes

- All endpoints require authentication (JWT token via cookie)
- Goal selection is optional - users can complete onboarding without selecting a goal
- Completion is idempotent - can be called multiple times safely
- All timestamps are in UTC with timezone information
- Existing users will have `onboarding_completed=false` by default

