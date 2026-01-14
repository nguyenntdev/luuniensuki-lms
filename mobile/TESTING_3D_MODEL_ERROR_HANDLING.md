# Testing Guide: 3D Model Viewer Error Handling

## Prerequisites
- Flutter development environment set up
- Mobile app running on device/emulator
- Access to urn viewer screens

## Test Cases

### ✅ Test 1: Successful Model Load
**Purpose:** Verify normal operation when model loads correctly

**Steps:**
1. Open the mobile app
2. Navigate to Collections tab
3. Tap on any urn card
4. Observe the loading process

**Expected Results:**
- ✅ Loading overlay appears with spinner and "Đang tải mô hình 3D..."
- ✅ Model appears within 2-5 seconds
- ✅ Loading overlay disappears
- ✅ Hotspots are visible on the model
- ✅ Model can be rotated, zoomed, and panned
- ✅ No error overlay appears

**Pass/Fail:** ________

---

### ⚠️ Test 2: Network Connection Lost
**Purpose:** Verify error handling when network is unavailable

**Steps:**
1. Enable airplane mode on device
2. Open the mobile app
3. Navigate to Collections tab
4. Tap on any urn card
5. Wait for 10 seconds

**Expected Results:**
- ✅ Loading overlay shows for ~10 seconds
- ✅ After timeout, error overlay appears
- ✅ Error message: "Mô hình tải quá lâu. Vui lòng kiểm tra kết nối mạng và thử lại."
- ✅ Red error icon (⚠️) is visible
- ✅ "Thử lại" (Retry) button is present
- ✅ "Quay lại" (Back) button is present
- ✅ Troubleshooting tips are displayed
- ✅ No hotspots are visible (error state)

**Recovery Test:**
1. Disable airplane mode
2. Tap "Thử lại" button

**Expected Results:**
- ✅ Loading overlay reappears
- ✅ Model loads successfully this time
- ✅ Error overlay disappears
- ✅ Hotspots become visible

**Pass/Fail:** ________

---

### 🌐 Test 3: CORS Error (Server-Side Issue)
**Purpose:** Verify error handling when CORS headers are missing

**Note:** This test is only possible if the nginx CORS fix has NOT been applied yet.

**Steps:**
1. Ensure server CORS headers are NOT configured
2. Open mobile app with good internet connection
3. Navigate to urn viewer
4. Check browser console (for web) or debug logs

**Expected Results:**
- ✅ Loading overlay appears
- ✅ After some time, error overlay appears
- ✅ Debug logs show CORS-related error
- ✅ Error message is user-friendly (no technical jargon)

**Pass/Fail:** ________

---

### 🐌 Test 4: Slow Network Connection
**Purpose:** Verify behavior on slow connections

**Steps (Android Emulator):**
1. Open Android emulator settings
2. Set network speed to "EDGE" or "GPRS" (slow 2G)
3. Open mobile app
4. Navigate to urn viewer

**Steps (iOS Simulator):**
1. Use Network Link Conditioner
2. Set to "3G" or "Edge"
3. Open mobile app
4. Navigate to urn viewer

**Expected Results:**
- ✅ Loading overlay stays visible longer
- ✅ If model loads within 10s, shows successfully
- ✅ If exceeds 10s, shows error overlay
- ✅ Progress indicators work smoothly

**Pass/Fail:** ________

---

### 🔄 Test 5: Retry Functionality
**Purpose:** Verify retry mechanism works correctly

**Steps:**
1. Trigger any error state (e.g., airplane mode)
2. Observe error overlay
3. Tap "Thử lại" button
4. Observe loading process

**Expected Results:**
- ✅ Error overlay disappears immediately
- ✅ Loading overlay appears
- ✅ Timer resets to 10 seconds
- ✅ Model attempts to reload
- ✅ If network restored, model loads successfully

**Pass/Fail:** ________

---

### ⬅️ Test 6: Back Navigation from Error
**Purpose:** Verify user can exit error state

**Steps:**
1. Trigger error state
2. Tap "Quay lại" (Back) button

**Expected Results:**
- ✅ Returns to previous screen (Collections)
- ✅ No crash or freezing
- ✅ Collections screen works normally

**Pass/Fail:** ________

---

### 📱 Test 7: Multiple Urns in Sequence
**Purpose:** Test error handling across multiple urn loads

**Steps:**
1. Open Urn A - wait for successful load
2. Go back to Collections
3. Open Urn B - wait for successful load
4. Go back to Collections
5. Turn on airplane mode
6. Open Urn C - should show error
7. Tap back, turn off airplane mode
8. Open Urn D - should load successfully

**Expected Results:**
- ✅ Each urn loads independently
- ✅ Error state doesn't affect subsequent loads
- ✅ No memory leaks or performance issues
- ✅ State resets properly between urns

**Pass/Fail:** ________

---

### 🐛 Test 8: Debug Logging
**Purpose:** Verify debug logs provide useful information

**Steps:**
1. Open terminal/console
2. Run app in debug mode: `flutter run`
3. Navigate to urn viewer
4. Watch console output

**Expected Log Lines:**
```
[URN_VIEWER] Loading model from: https://...
[URN_VIEWER] Loading state: true, Error state: false
[MODEL_VIEWER] Loading progress: 0.5
[MODEL_VIEWER] Model loaded successfully
```

**OR (on error):**
```
[URN_VIEWER] Loading model from: https://...
[URN_VIEWER] Loading state: true, Error state: false
[URN_VIEWER] Model loading timeout after 10 seconds
```

**Expected Results:**
- ✅ Clear, timestamped log messages
- ✅ URL of model being loaded is logged
- ✅ Loading state transitions are logged
- ✅ Errors are logged with context

**Pass/Fail:** ________

---

## Performance Tests

### 🚀 Test 9: Load Time Measurement
**Purpose:** Ensure error handling doesn't impact load times

**Steps:**
1. Use stopwatch or timer
2. Measure time from tap to model visible
3. Test 5 different urns
4. Calculate average

**Expected Results:**
- ✅ Average load time: 2-5 seconds (good connection)
- ✅ No significant delay from added error handling
- ✅ Consistent performance across multiple loads

**Average Time:** ________ seconds
**Pass/Fail:** ________

---

## Acceptance Criteria

All tests must pass before considering feature complete:

- [ ] Test 1: Successful Model Load
- [ ] Test 2: Network Connection Lost
- [ ] Test 3: CORS Error (if applicable)
- [ ] Test 4: Slow Network Connection
- [ ] Test 5: Retry Functionality
- [ ] Test 6: Back Navigation from Error
- [ ] Test 7: Multiple Urns in Sequence
- [ ] Test 8: Debug Logging
- [ ] Test 9: Load Time Measurement

**Overall Status:** ________

**Tested By:** ________________
**Date:** ________________
**Device/Emulator:** ________________
**OS Version:** ________________

