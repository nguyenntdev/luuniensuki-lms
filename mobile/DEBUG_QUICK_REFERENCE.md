# URN Viewer Debug Logging - Quick Reference

## Quick Start

### View Logs (Android)
```bash
# All URN viewer logs
adb logcat | grep URN_VIEWER

# JavaScript logs
adb logcat | grep MODEL_VIEWER_JS

# Combined
adb logcat | grep -E "URN_VIEWER|MODEL_VIEWER_JS"

# With color highlighting (requires ccze)
adb logcat | grep -E "URN_VIEWER|MODEL_VIEWER_JS" | ccze -A
```

## Log Prefixes

| Prefix | Source | Description |
|--------|--------|-------------|
| `[URN_VIEWER]` | Dart/Flutter | App-level logging |
| `[MODEL_VIEWER_JS]` | JavaScript | WebView JavaScript console |

## Key Log Messages

### ✅ Success Indicators
- `✅ Online` - Network connected
- `✅ URL is valid` - Model URL format correct
- `✅ model-viewer element found` - WebView initialized
- `✅ Model loaded successfully` - 3D model rendered
- `✅ All event listeners registered` - JS handlers ready

### ⚠️ Warnings
- `⚠️ Model loading timeout` - 60s timeout reached (continues loading)
- `Offline` - No network connectivity

### ❌ Error Indicators
- `❌ Network connectivity check failed` - Can't reach internet
- `❌ URL is INVALID` - Model URL malformed
- `❌ model-viewer element not found` - WebView init failed
- `❌ Error loading model` - Model load failed
- `❌ Flutter WebView bridge NOT available` - Communication broken

### 📊 Progress Indicators
- `🔄 Starting model load...` - Load initiated
- `📊 Loading progress: X%` - Loading percentage
- `🎯 Hotspot clicked` - User interaction
- `🔍 Model URL Verification` - URL validation
- `📋 Debug info copied` - User copied debug info

## Common Issues & Solutions

### Issue: Model Not Loading

**Check:**
```bash
adb logcat | grep "Model URL"
adb logcat | grep "Loading progress"
```

**Look for:**
- Invalid URL format
- Stuck at 0% progress
- Network offline
- CORS errors in JS

### Issue: Hotspots Not Appearing

**Check:**
```bash
adb logcat | grep "Found.*hotspots"
adb logcat | grep "Motif count"
```

**Look for:**
- Hotspot count = 0
- Motif positions invalid
- WebView bridge unavailable

### Issue: Slow Loading

**Check:**
```bash
adb logcat | grep "Time Elapsed"
adb logcat | grep "progress"
```

**Look for:**
- Progress incrementing slowly
- Network quality
- Model file size

## Debug Info Structure

When user clicks "Copy Debug Info":

```
Timestamp: When error occurred
Urn ID: Database ID
Urn Slug: URL-friendly identifier
Model URL: Direct API response
Effective URL: Actually used URL
Network: Online/Offline status
Progress: Last known percentage
Error Message: Specific error text
Time Elapsed: Seconds since start
Platform: OS and version
```

## Testing Commands

### Test Network Detection
```bash
# Disable WiFi, then in app terminal:
adb logcat | grep "Network connectivity"
```

### Test Model URL
```bash
# Check what URL is being loaded:
adb logcat | grep "Effective Model URL"
```

### Test Loading Progress
```bash
# Monitor real-time progress:
adb logcat | grep "Loading progress"
```

### Test Error Handling
```bash
# Trigger error, then check:
adb logcat | grep -A 5 "Error loading model"
```

## Quick Diagnostic Checklist

- [ ] Check initialization logs (═══ 3D VIEWER DEBUG START ═══)
- [ ] Verify network status (Online/Offline)
- [ ] Check model URL validity
- [ ] Monitor loading progress (0% to 100%)
- [ ] Verify WebView bridge availability
- [ ] Check hotspot registration count
- [ ] Look for JavaScript errors
- [ ] Verify model load success/error
- [ ] Check time elapsed vs timeout

## Integration with Error Reporting

Users can now:
1. See error with details
2. Click "Copy Debug Info" button
3. Paste into support ticket/email
4. Developers get full context instantly

## Performance Notes

- Debug prints are stripped in release builds
- Network check adds ~5s max at startup
- No runtime performance impact
- Logs are automatically timestamped

