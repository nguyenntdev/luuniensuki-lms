# Quick Start Guide - Testing Custom Model Viewer

## Setup (5 minutes)

### 1. Install Dependencies
```bash
cd mobile
flutter pub get
```

### 2. Clean Build
```bash
flutter clean
flutter pub get
```

### 3. Run the App
```bash
# For Android
flutter run

# For iOS
flutter run -d ios

# For a specific device
flutter devices
flutter run -d <device-id>
```

## Testing the Custom Model Viewer (10 minutes)

### Test Case 1: Successful Model Load
**Steps:**
1. Launch the app
2. Navigate to any urn (e.g., "Đỉnh Cao")
3. Tap to view the urn

**Expected Results:**
- ✅ Loading overlay appears with progress percentage
- ✅ Progress increases from 0% to 100%
- ✅ 3D model loads and displays
- ✅ Hotspots are visible on the model
- ✅ Model can be rotated with touch
- ✅ Console shows: `[CUSTOM_MODEL_VIEWER] ✅ Model loaded successfully`

**Test Duration:** ~30 seconds

### Test Case 2: Error Handling
**Steps:**
1. Turn off WiFi/mobile data
2. Navigate to an urn viewer
3. Observe error handling

**Expected Results:**
- ✅ Loading starts normally
- ✅ Error overlay appears after timeout
- ✅ Error message is displayed
- ✅ "Thử lại" (Retry) button is visible
- ✅ Console shows: `[CUSTOM_MODEL_VIEWER] ❌ Model load error`

**Test Duration:** ~15 seconds

### Test Case 3: Retry Functionality
**Steps:**
1. Start with no network (from Test Case 2)
2. Turn on WiFi/mobile data
3. Tap "Thử lại" button

**Expected Results:**
- ✅ Error overlay dismisses
- ✅ Loading overlay appears
- ✅ Model loads successfully
- ✅ Hotspots appear

**Test Duration:** ~20 seconds

### Test Case 4: Hotspot Interaction
**Steps:**
1. With model loaded successfully
2. Tap on any hotspot (glowing circle on model)
3. Observe the response

**Expected Results:**
- ✅ Hotspot is clickable
- ✅ Console shows: `[CUSTOM_MODEL_VIEWER] 🎯 Hotspot tapped: <motif-id>`
- ✅ Console shows: `[URN_VIEWER] 🎯 Hotspot tapped: <motif-id>`
- ✅ Motif detail sidebar appears (or appropriate action)
- ✅ Correct motif information is displayed

**Test Duration:** ~15 seconds

### Test Case 5: Progress Tracking
**Steps:**
1. Clear app cache/data
2. Navigate to urn viewer with slow network
3. Watch loading progress

**Expected Results:**
- ✅ Progress starts at 0%
- ✅ Progress updates smoothly
- ✅ Progress reaches 100%
- ✅ Console shows progress logs: `[MODEL_VIEWER] Loading progress: X%`

**Test Duration:** ~30 seconds

## Console Log Verification

### Expected Logs on Success
```
[CUSTOM_MODEL_VIEWER] Initializing for model: https://...
[CUSTOM_MODEL_VIEWER] WebView created
[CUSTOM_MODEL_VIEWER] JavaScript handlers registered
[MODEL_VIEWER] Initializing...
[MODEL_VIEWER] Loading progress: 0.0%
[MODEL_VIEWER] Loading progress: 25.0%
[MODEL_VIEWER] Loading progress: 50.0%
[MODEL_VIEWER] Loading progress: 75.0%
[MODEL_VIEWER] Loading progress: 100.0%
[MODEL_VIEWER] ✅ Model loaded successfully
[CUSTOM_MODEL_VIEWER] ✅ Model loaded successfully
```

### Expected Logs on Hotspot Tap
```
[MODEL_VIEWER] 🎯 Hotspot tapped: <motif-id>
[CUSTOM_MODEL_VIEWER] 🎯 Hotspot tapped: <motif-id>
[URN_VIEWER] 🎯 Hotspot tapped: <motif-id>
```

### Expected Logs on Error
```
[CUSTOM_MODEL_VIEWER] Initializing for model: https://...
[MODEL_VIEWER] ❌ Model load error: ...
[CUSTOM_MODEL_VIEWER] ❌ Model load error: ...
```

## Quick Debug Commands

### View Logs
```bash
# Android
adb logcat | grep -E "CUSTOM_MODEL_VIEWER|MODEL_VIEWER|URN_VIEWER"

# iOS (with device connected)
idevicesyslog | grep -E "CUSTOM_MODEL_VIEWER|MODEL_VIEWER|URN_VIEWER"

# Flutter logs (all platforms)
flutter logs | grep -E "CUSTOM_MODEL_VIEWER|MODEL_VIEWER|URN_VIEWER"
```

### Clear Cache
```bash
# Android
adb shell pm clear com.histolab.luuniensuki_lms

# iOS
# Settings > General > iPhone Storage > App > Delete App
```

### Reload App
```bash
# Hot reload (r)
r

# Hot restart (R)
R

# Full restart
# Stop app and run again
```

## Troubleshooting

### Issue: Model Not Loading
**Solutions:**
1. Check network connection
2. Verify model URL in console logs
3. Check CORS headers on server
4. Try with different model URL

### Issue: Hotspots Not Appearing
**Solutions:**
1. Check if motifs have valid positions
2. Verify hotspots HTML in console
3. Check model scale vs hotspot positions
4. Try zooming out

### Issue: JavaScript Handlers Not Firing
**Solutions:**
1. Verify `flutter_inappwebview` is installed
2. Check WebView initialization logs
3. Verify JavaScript console logs
4. Check for JavaScript errors

### Issue: App Crashes
**Solutions:**
1. Check memory usage
2. Verify device compatibility
3. Check crash logs
4. Test with smaller model file

## Performance Benchmarks

### Load Times (3G Network)
- Small model (<5MB): 3-5 seconds
- Medium model (5-10MB): 5-10 seconds
- Large model (>10MB): 10-20 seconds

### Memory Usage
- Idle: ~100-150 MB
- Model loaded: ~150-250 MB
- Multiple models: ~250-400 MB

### Frame Rate
- Target: 60 FPS
- Acceptable: 30-60 FPS
- Poor: <30 FPS

## Quick Reference

### Files Modified
- `mobile/pubspec.yaml` - Added flutter_inappwebview
- `mobile/lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart` - Uses CustomModelViewer
- `mobile/lib/features/urn_viewer/presentation/widgets/custom_model_viewer.dart` - New widget

### Key Classes
- `CustomModelViewer` - Main widget
- `InAppWebView` - WebView component
- `InAppWebViewController` - WebView controller

### Key Methods
- `_generateHtml()` - Creates HTML content
- `_registerJavaScriptHandlers()` - Sets up JS handlers
- `onModelLoaded()` - Success callback
- `onModelError()` - Error callback
- `onProgress()` - Progress callback
- `onHotspotTap()` - Hotspot tap callback

## Support

### Documentation
- `mobile/CUSTOM_MODEL_VIEWER_INTEGRATION.md` - Full integration guide
- `mobile/lib/features/urn_viewer/presentation/widgets/CUSTOM_MODEL_VIEWER_README.md` - API reference
- `mobile/3D_VIEWER_HANDLER_FIX_SUMMARY.md` - Implementation summary

### Contact
- Create an issue in the repository
- Check existing documentation
- Review console logs for clues

## Next Steps After Testing

1. ✅ All tests pass → Ready for staging
2. ❌ Tests fail → Review logs, fix issues, retest
3. ⚠️ Some tests fail → Document issues, decide priority

