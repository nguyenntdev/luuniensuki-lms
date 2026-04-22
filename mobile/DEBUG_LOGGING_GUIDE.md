# URN Viewer Debug Logging Guide

## Overview
Comprehensive debug logging has been added to the 3D model viewer to help diagnose loading issues and track model loading performance.

## Debug Features Added

### 1. **Enhanced Debug Logging**

#### Screen Initialization
- Logs when the screen initializes with urn details
- Timestamps for tracking session duration
- Network connectivity check on startup

```dart
[URN_VIEWER] ═══════════════════════════════════════
[URN_VIEWER] === 3D VIEWER DEBUG START ===
[URN_VIEWER] Screen initializing for slug: {slug}
[URN_VIEWER] Timestamp: {ISO8601 timestamp}
```

#### Model Loading
- Logs the exact model URL being used
- Verifies URL format and structure
- Tracks loading progress percentage
- Logs loading start/completion/error events

```dart
[URN_VIEWER] ┌─────────────────────────────────────
[URN_VIEWER] │ Starting 3D Model Load
[URN_VIEWER] │ Model URL: {url}
[URN_VIEWER] │ URL is valid: {true/false}
[URN_VIEWER] │ Loading state: {loading}
[URN_VIEWER] │ Progress: {percentage}%
```

#### URN Details
- Logs all URN metadata when content builds
- Shows motif count and discovery status
- Displays both raw and effective model URLs

```dart
[URN_VIEWER] Urn ID: {id}
[URN_VIEWER] Urn Slug: {slug}
[URN_VIEWER] Model URL from API: {modelUrl}
[URN_VIEWER] Effective Model URL: {effectiveModelUrl}
[URN_VIEWER] Motif count: {count}
```

### 2. **Network Connectivity Check**

- Performs connectivity check before loading model
- Shows warning if device is offline
- Uses simple DNS lookup (google.com) with 5-second timeout
- Logs connectivity status clearly

```dart
[URN_VIEWER] Network connectivity check: ✅ Online
// or
[URN_VIEWER] ❌ Network connectivity check failed: {error}
```

### 3. **JavaScript Console Logging**

Enhanced JavaScript in the WebView with extensive logging:

```javascript
[MODEL_VIEWER_JS] ═══════════════════════════════════
[MODEL_VIEWER_JS] Initializing model viewer JavaScript
[MODEL_VIEWER_JS] ✅ Flutter WebView bridge available
[MODEL_VIEWER_JS] Found {n} hotspots
[MODEL_VIEWER_JS] 🔄 Starting model load...
[MODEL_VIEWER_JS] 📊 Loading progress: {percentage}%
[MODEL_VIEWER_JS] ✅ Model loaded successfully!
```

#### Error Logging
```javascript
[MODEL_VIEWER_JS] ❌ Error loading model!
[MODEL_VIEWER_JS] Error event: {event}
[MODEL_VIEWER_JS] Model src: {url}
```

### 4. **Improved Error Display**

#### Debug Info Section
- Shows comprehensive debug information in error overlay
- Includes all URN details, URLs, network status, and timing
- Only shown when error occurs (production-safe)

#### Copy Debug Info Button
- Allows users to copy debug information to clipboard
- Helpful for reporting issues to support
- Includes full system context

Debug info includes:
- Timestamp
- URN ID, Slug, Name
- Model URLs (raw and effective)
- Motif count and discovery stats
- Network status
- Loading state and progress
- Error messages
- Time elapsed since load start
- Platform and OS version

### 5. **Progress Tracking**

- Visual progress indicator in loading overlay
- Shows percentage when available
- Offline warning during loading
- Extended timeout (60 seconds) with logging

### 6. **Model URL Verification**

Comprehensive URL verification logs:
- Raw model URL from API
- Effective URL being used
- URL validity check
- URL scheme, host, path
- File extension

```dart
[URN_VIEWER] 🔍 Model URL Verification:
[URN_VIEWER]   Raw model URL: {url}
[URN_VIEWER]   Effective URL: {url}
[URN_VIEWER]   ✅ URL is valid
[URN_VIEWER]   Scheme: https
[URN_VIEWER]   Host: {hostname}
[URN_VIEWER]   Path: {path}
[URN_VIEWER]   Extension: glb
```

## Viewing Logs

### Android (via adb logcat)
```bash
# View all URN_VIEWER logs
adb logcat | grep URN_VIEWER

# View JavaScript console logs
adb logcat | grep MODEL_VIEWER_JS

# View combined logs
adb logcat | grep -E "URN_VIEWER|MODEL_VIEWER_JS"
```

### iOS (via Console.app)
1. Open Console.app on macOS
2. Connect iOS device
3. Filter by "URN_VIEWER" or "MODEL_VIEWER"

### Flutter DevTools
- All `debugPrint()` statements appear in the Debug Console
- Can be filtered by "[URN_VIEWER]" prefix

## Troubleshooting with Logs

### Model Not Loading
1. Check network status in logs
2. Verify model URL format
3. Check loading progress (stuck at 0%?)
4. Look for JavaScript errors

### Hotspots Not Appearing
1. Check motif count in logs
2. Verify hotspot registration in JavaScript
3. Check for Flutter WebView bridge availability

### Performance Issues
1. Check time elapsed logs
2. Monitor loading progress increments
3. Look for timeout warnings

## Debug Info Format

When error occurs, users can copy this information:

```
=== URN VIEWER DEBUG INFO ===
Timestamp: 2024-01-15T10:30:45.123Z
Urn ID: 123
Urn Slug: urn-dong-son
Urn Name: Chum Đông Sơn
Model URL: https://example.com/models/urn.glb
Effective URL: https://example.com/models/urn.glb
Motif Count: 5
Discovered: 2
Network: Online
Loading: false
Error: true
Progress: 45%
Error Message: Failed to load 3D model
Time Elapsed: 12s
Platform: android 13
===========================
```

## Code Changes Summary

### New Imports
- `import 'dart:io';` - For network connectivity check

### New State Variables
- `_modelLoadProgress` - Track loading percentage (0.0 - 1.0)
- `_debugInfo` - Full debug information string
- `_isOnline` - Network connectivity status
- `_loadStartTime` - Track when loading started

### New Methods
1. `_checkConnectivity()` - Check internet connection before loading
2. `_verifyModelUrl()` - Verify and log model URL details
3. `_buildDebugInfoString()` - Build comprehensive debug info for copying

### Enhanced Methods
1. `initState()` - Added debug logging and connectivity check
2. `dispose()` - Added cleanup logging
3. `_buildViewerContent()` - Added URN details logging
4. `_build3DViewer()` - Enhanced model loading logs
5. `_generateHotspotJs()` - Comprehensive JavaScript logging
6. `_buildLoadingOverlay()` - Shows progress percentage and offline warning
7. `_buildModelErrorOverlay()` - Shows debug info and copy button

## Testing the Debug Logging

### Test Scenarios

1. **Normal Load**
   - Watch for initialization logs
   - Monitor progress updates
   - Verify successful load message

2. **Network Error**
   - Disable network
   - Check offline detection
   - Verify error message

3. **Invalid URL**
   - Provide invalid model URL
   - Check URL verification logs
   - Verify error handling

4. **Slow Connection**
   - Use network throttling
   - Monitor progress percentage
   - Check timeout behavior

## Performance Impact

- Logging is production-safe (uses `debugPrint`)
- No logging in release builds (Flutter strips debug prints)
- Minimal memory overhead
- Network check adds ~5 seconds max at startup

## Future Enhancements

- Add analytics event tracking
- Implement retry with exponential backoff
- Add model caching status logs
- Track WebView memory usage


