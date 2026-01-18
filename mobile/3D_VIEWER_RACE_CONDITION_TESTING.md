# 3D Viewer Race Condition Fix - Testing Checklist

## ✅ Pre-Testing Setup

- [ ] Ensure you have the latest code with the race condition fix
- [ ] Build the app in debug mode for detailed logging
- [ ] Have a 3D model ready (e.g., Cao Đỉnh urn)
- [ ] Enable console logging in the app

## 🧪 Test Cases

### Test 1: Fast Network Loading (Primary Fix)

**Scenario:** Model loads quickly from fast network

**Steps:**
1. [ ] Connect to fast WiFi (>10 Mbps)
2. [ ] Clear app cache/data
3. [ ] Navigate to URN viewer
4. [ ] Select any 3D model (e.g., Cao Đỉnh)
5. [ ] Observe loading behavior

**Expected Result:**
- ✅ Model loads smoothly
- ✅ Loading overlay disappears after model loads
- ✅ No infinite spinner
- ✅ Console shows: `[MODEL_VIEWER_JS] Model already loaded (immediate check)` OR `[MODEL_VIEWER_JS] Model loaded event fired`

**Pass/Fail:** ____

---

### Test 2: Cached Model Loading (Critical)

**Scenario:** Model loads from cache (returning user)

**Steps:**
1. [ ] Load a 3D model once (let it fully load)
2. [ ] Navigate away from the viewer
3. [ ] Return to the same model viewer
4. [ ] Observe loading behavior

**Expected Result:**
- ✅ Model loads almost instantly
- ✅ Loading overlay appears briefly and disappears
- ✅ No infinite spinner
- ✅ Console shows: `[MODEL_VIEWER_JS] Model already loaded (immediate check)`

**Pass/Fail:** ____

---

### Test 3: Normal Slow Loading

**Scenario:** Model loads normally on slower connection

**Steps:**
1. [ ] Throttle network to 3G/4G speed
2. [ ] Clear app cache
3. [ ] Navigate to URN viewer
4. [ ] Select a 3D model
5. [ ] Observe loading behavior

**Expected Result:**
- ✅ Loading overlay shows with progress percentage
- ✅ Progress increments (0% → 100%)
- ✅ Loading overlay disappears when complete
- ✅ Model displays correctly
- ✅ Console shows: `[MODEL_VIEWER_JS] Model loaded event fired`

**Pass/Fail:** ____

---

### Test 4: Timeout Handling (60 Second Fallback)

**Scenario:** Model fails to load within 60 seconds

**Steps:**
1. [ ] Start loading a large 3D model
2. [ ] Disable network after loading starts
3. [ ] Wait 60 seconds
4. [ ] Observe behavior

**Expected Result:**
- ✅ After 60 seconds, error message appears
- ✅ Shows "Model loading timed out" error
- ✅ "Retry" button is available
- ✅ Console shows: `[MODEL_VIEWER_JS] Fallback check: model not loaded - timeout`

**Pass/Fail:** ____

---

### Test 5: Retry After Timeout

**Scenario:** User retries after timeout error

**Steps:**
1. [ ] Trigger a timeout error (from Test 4)
2. [ ] Re-enable network
3. [ ] Tap "Retry" button
4. [ ] Observe loading behavior

**Expected Result:**
- ✅ Loading overlay reappears
- ✅ Model loads successfully
- ✅ Error clears and model displays

**Pass/Fail:** ____

---

### Test 6: Multiple Models Sequential Loading

**Scenario:** Load multiple different models one after another

**Steps:**
1. [ ] Load first 3D model (wait for complete)
2. [ ] Navigate to second 3D model
3. [ ] Navigate to third 3D model
4. [ ] Go back to first model
5. [ ] Observe all load correctly

**Expected Result:**
- ✅ Each model loads correctly
- ✅ No infinite spinners on any model
- ✅ Previously loaded models load instantly (cached)
- ✅ New models show progress and load normally

**Pass/Fail:** ____

---

### Test 7: Background/Foreground Transition

**Scenario:** App goes to background and returns while loading

**Steps:**
1. [ ] Start loading a 3D model
2. [ ] Before it completes, put app in background
3. [ ] Wait 5 seconds
4. [ ] Return to foreground
5. [ ] Observe loading behavior

**Expected Result:**
- ✅ Loading continues or restarts appropriately
- ✅ No crash or freeze
- ✅ Model eventually loads or shows error

**Pass/Fail:** ____

---

## 📊 Console Log Verification

Check for these key log messages:

### Successful Load (Fast/Cached):
```
[MODEL_VIEWER_JS] Initializing JavaScript bridge...
[MODEL_VIEWER_JS] Model viewer element found
[MODEL_VIEWER_JS] Model already loaded (immediate check)
[CUSTOM_MODEL_VIEWER] ✅ Model loaded successfully - hiding loading overlay
```

### Successful Load (Normal):
```
[MODEL_VIEWER_JS] Initializing JavaScript bridge...
[MODEL_VIEWER_JS] Model viewer element found
[MODEL_VIEWER_JS] Progress: 25
[MODEL_VIEWER_JS] Progress: 50
[MODEL_VIEWER_JS] Progress: 75
[MODEL_VIEWER_JS] Model loaded event fired
[CUSTOM_MODEL_VIEWER] ✅ Model loaded successfully - hiding loading overlay
```

### Timeout Error:
```
[MODEL_VIEWER_JS] Initializing JavaScript bridge...
[MODEL_VIEWER_JS] Model viewer element found
[MODEL_VIEWER_JS] Fallback check: model not loaded - timeout
[CUSTOM_MODEL_VIEWER] ❌ Model load error: Model loading timed out
```

## 🎯 Success Criteria

**All tests must pass:**
- [ ] Test 1: Fast Network Loading
- [ ] Test 2: Cached Model Loading (CRITICAL)
- [ ] Test 3: Normal Slow Loading
- [ ] Test 4: Timeout Handling
- [ ] Test 5: Retry After Timeout
- [ ] Test 6: Multiple Models Sequential
- [ ] Test 7: Background/Foreground Transition

**No regressions:**
- [ ] Existing functionality works as before
- [ ] No new crashes introduced
- [ ] Performance is same or better

## 📝 Notes Section

Add any observations or issues found during testing:

```
Date: __________
Tester: __________
Device: __________
OS Version: __________

Notes:




```

## ✍️ Sign-off

- [ ] All tests completed
- [ ] All tests passed
- [ ] No critical issues found
- [ ] Ready for production deployment

**Tester Signature:** ___________________  
**Date:** ___________________

