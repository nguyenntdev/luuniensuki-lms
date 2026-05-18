# Example Debug Log Output

## Successful Model Load

```
[URN_VIEWER] ═══════════════════════════════════════
[URN_VIEWER] === 3D VIEWER DEBUG START ===
[URN_VIEWER] Screen initializing for slug: urn-dong-son
[URN_VIEWER] Timestamp: 2024-01-15T10:30:45.123456
[URN_VIEWER] ═══════════════════════════════════════

[URN_VIEWER] Network connectivity check: ✅ Online

[URN_VIEWER] ───────────────────────────────────────
[URN_VIEWER] Building viewer content
[URN_VIEWER] Urn ID: 123
[URN_VIEWER] Urn Name: Chum Đông Sơn
[URN_VIEWER] Urn Slug: urn-dong-son
[URN_VIEWER] Model URL from API: https://storage.googleapis.com/museum/models/urn-dong-son.glb
[URN_VIEWER] Effective Model URL: https://storage.googleapis.com/museum/models/urn-dong-son.glb
[URN_VIEWER] Motif count: 5
[URN_VIEWER] Discovered count: 2
[URN_VIEWER] Network status: Online
[URN_VIEWER] ───────────────────────────────────────

[URN_VIEWER] 🔍 Model URL Verification:
[URN_VIEWER]   Raw model URL: https://storage.googleapis.com/museum/models/urn-dong-son.glb
[URN_VIEWER]   Effective URL: https://storage.googleapis.com/museum/models/urn-dong-son.glb
[URN_VIEWER]   ✅ URL is valid
[URN_VIEWER]   Scheme: https
[URN_VIEWER]   Host: storage.googleapis.com
[URN_VIEWER]   Path: /museum/models/urn-dong-son.glb
[URN_VIEWER]   Extension: glb

[URN_VIEWER] ┌─────────────────────────────────────
[URN_VIEWER] │ Starting 3D Model Load
[URN_VIEWER] │ Model URL: https://storage.googleapis.com/museum/models/urn-dong-son.glb
[URN_VIEWER] │ URL is valid: true
[URN_VIEWER] │ Loading state: true
[URN_VIEWER] │ Error state: false
[URN_VIEWER] │ Progress: 0%
[URN_VIEWER] └─────────────────────────────────────

[MODEL_VIEWER_JS] ═══════════════════════════════════
[MODEL_VIEWER_JS] Initializing model viewer JavaScript
[MODEL_VIEWER_JS] Timestamp: 2024-01-15T10:30:46.000Z
[MODEL_VIEWER_JS] ✅ Flutter WebView bridge available
[MODEL_VIEWER_JS] Found 5 hotspots
[MODEL_VIEWER_JS] Registering hotspot 0 - Motif ID: 1
[MODEL_VIEWER_JS] Registering hotspot 1 - Motif ID: 2
[MODEL_VIEWER_JS] Registering hotspot 2 - Motif ID: 3
[MODEL_VIEWER_JS] Registering hotspot 3 - Motif ID: 4
[MODEL_VIEWER_JS] Registering hotspot 4 - Motif ID: 5
[MODEL_VIEWER_JS] ✅ model-viewer element found
[MODEL_VIEWER_JS] Model src: https://storage.googleapis.com/museum/models/urn-dong-son.glb
[MODEL_VIEWER_JS] 🔄 Starting model load...
[MODEL_VIEWER_JS] 📊 Loading progress: 10.5%
[MODEL_VIEWER_JS] 📊 Loading progress: 25.3%
[MODEL_VIEWER_JS] 📊 Loading progress: 45.7%
[MODEL_VIEWER_JS] 📊 Loading progress: 68.2%
[MODEL_VIEWER_JS] 📊 Loading progress: 89.4%
[MODEL_VIEWER_JS] 📊 Loading progress: 100.0%
[MODEL_VIEWER_JS] ✅ Model loaded successfully!
[MODEL_VIEWER_JS] Load time: 3245.67 ms
[MODEL_VIEWER_JS] Notified Flutter of successful load
[MODEL_VIEWER_JS] ✅ All event listeners registered
[MODEL_VIEWER_JS] ═══════════════════════════════════

[MODEL_VIEWER_JS] 🎯 Hotspot clicked: 1
[MODEL_VIEWER_JS] ✅ Sent hotspot click to Flutter

[URN_VIEWER] Screen disposing for slug: urn-dong-son
[URN_VIEWER] === 3D VIEWER DEBUG END ===
```

## Model Load Error

```
[URN_VIEWER] ═══════════════════════════════════════
[URN_VIEWER] === 3D VIEWER DEBUG START ===
[URN_VIEWER] Screen initializing for slug: urn-dong-son
[URN_VIEWER] Timestamp: 2024-01-15T10:30:45.123456
[URN_VIEWER] ═══════════════════════════════════════

[URN_VIEWER] ❌ Network connectivity check failed: SocketException: Failed host lookup: 'google.com'

[URN_VIEWER] ───────────────────────────────────────
[URN_VIEWER] Building viewer content
[URN_VIEWER] Urn ID: 123
[URN_VIEWER] Urn Name: Chum Đông Sơn
[URN_VIEWER] Urn Slug: urn-dong-son
[URN_VIEWER] Model URL from API: https://storage.googleapis.com/museum/models/urn-dong-son.glb
[URN_VIEWER] Effective Model URL: https://storage.googleapis.com/museum/models/urn-dong-son.glb
[URN_VIEWER] Motif count: 5
[URN_VIEWER] Discovered count: 2
[URN_VIEWER] Network status: Offline
[URN_VIEWER] ───────────────────────────────────────

[MODEL_VIEWER_JS] ═══════════════════════════════════
[MODEL_VIEWER_JS] Initializing model viewer JavaScript
[MODEL_VIEWER_JS] Timestamp: 2024-01-15T10:30:46.000Z
[MODEL_VIEWER_JS] ✅ Flutter WebView bridge available
[MODEL_VIEWER_JS] Found 5 hotspots
[MODEL_VIEWER_JS] ✅ model-viewer element found
[MODEL_VIEWER_JS] 🔄 Starting model load...
[MODEL_VIEWER_JS] ❌ Error loading model!
[MODEL_VIEWER_JS] Error event: [object Event]
[MODEL_VIEWER_JS] Error detail: NetworkError
[MODEL_VIEWER_JS] Model src: https://storage.googleapis.com/museum/models/urn-dong-son.glb
[MODEL_VIEWER_JS] Notified Flutter of error
[MODEL_VIEWER_JS] ═══════════════════════════════════
```

## Invalid URL Error

```
[URN_VIEWER] 🔍 Model URL Verification:
[URN_VIEWER]   Raw model URL: invalid-url
[URN_VIEWER]   Effective URL: invalid-url
[URN_VIEWER]   ❌ URL is INVALID!

[URN_VIEWER] ┌─────────────────────────────────────
[URN_VIEWER] │ Starting 3D Model Load
[URN_VIEWER] │ Model URL: invalid-url
[URN_VIEWER] │ URL is valid: false
[URN_VIEWER] │ Loading state: true
[URN_VIEWER] │ Error state: false
[URN_VIEWER] │ Progress: 0%
[URN_VIEWER] └─────────────────────────────────────
```

## Timeout Warning

```
[URN_VIEWER] ⚠️ Model loading timeout after 60 seconds - continuing in background
[URN_VIEWER] Last progress: 45%
```

## Debug Info Copy

```
When user clicks "Copy Debug Info" button:

=== URN VIEWER DEBUG INFO ===
Timestamp: 2024-01-15T10:31:50.123456
Urn ID: 123
Urn Slug: urn-dong-son
Urn Name: Chum Đông Sơn
Model URL: https://storage.googleapis.com/museum/models/urn-dong-son.glb
Effective URL: https://storage.googleapis.com/museum/models/urn-dong-son.glb
Motif Count: 5
Discovered: 2
Network: Offline
Loading: false
Error: true
Progress: 45%
Error Message: Failed to load 3D model. Check network connection or CORS settings.
Time Elapsed: 65s
Platform: android 13
===========================

[URN_VIEWER] 📋 Debug info copied to clipboard
```

## How to Filter Logs

### View only URN_VIEWER logs
```bash
adb logcat | grep URN_VIEWER
```

### View only JavaScript logs
```bash
adb logcat | grep MODEL_VIEWER_JS
```

### View both combined
```bash
adb logcat | grep -E "URN_VIEWER|MODEL_VIEWER_JS"
```

### Save logs to file
```bash
adb logcat | grep -E "URN_VIEWER|MODEL_VIEWER_JS" > debug_log.txt
```

### Live monitoring with timestamps
```bash
adb logcat -v time | grep -E "URN_VIEWER|MODEL_VIEWER_JS"
```

