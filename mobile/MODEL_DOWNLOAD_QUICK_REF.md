# Model Download System - Quick Reference Card

## 📦 Core Components

### ModelPreloader (Singleton Service)
```dart
final preloader = ModelPreloader();
```

| Method | Purpose | Returns |
|--------|---------|---------|
| `getModelPath(url, {onProgress})` | Download or get cached model | `Future<String>` (local path) |
| `isCached(url)` | Check if model is cached | `Future<bool>` |
| `preloadModels(urls)` | Background download multiple | `Future<void>` |
| `cancelDownload(url)` | Cancel active download | `void` |
| `clearCache()` | Remove all cached models | `Future<void>` |
| `getCacheSize()` | Get total cache size in bytes | `Future<int>` |

### ModelDownloadNotifier (Riverpod Provider)
```dart
ref.watch(modelDownloadNotifierProvider(modelUrl))
```

| Property | Type | Description |
|----------|------|-------------|
| `state` | `ModelDownloadState` | Current download state |
| `progress` | `double` | Download progress (0.0 - 1.0) |
| `localPath` | `String?` | Local file path when cached |
| `error` | `String?` | Error message if failed |

| Method | Purpose |
|--------|---------|
| `downloadModel()` | Start download |
| `cancelDownload()` | Cancel download |
| `retry()` | Retry after error |

### ModelDownloadState (Enum)
```dart
enum ModelDownloadState {
  idle,        // Not started
  downloading, // In progress
  completed,   // Just finished
  error,       // Failed
  cached,      // Already cached
}
```

## 🎨 UI Component

### ModelDownloadProgress Widget
```dart
ModelDownloadProgress(
  modelUrl: 'https://example.com/model.glb',
  onCancel: () => Navigator.pop(context),
)
```

**Shows:**
- Download button (idle)
- Circular progress with % (downloading)
- Error message with retry (error)
- Success checkmark (completed)

## 🚀 Common Patterns

### Pattern 1: Basic Integration
```dart
final downloadInfo = ref.watch(modelDownloadNotifierProvider(modelUrl));

if (downloadInfo.state == ModelDownloadState.cached ||
    downloadInfo.state == ModelDownloadState.completed) {
  return ModelViewer(src: downloadInfo.localPath);
} else {
  return ModelDownloadProgress(modelUrl: modelUrl);
}
```

### Pattern 2: Manual Control
```dart
// Start download
ref.read(modelDownloadNotifierProvider(url).notifier).downloadModel();

// Cancel
ref.read(modelDownloadNotifierProvider(url).notifier).cancelDownload();

// Check cache first
if (await ModelPreloader().isCached(url)) {
  // Use cached
} else {
  // Download
}
```

### Pattern 3: Background Preload
```dart
ref.read(modelPreloadNotifierProvider.notifier).preloadUrns(urnList);
```

### Pattern 4: Cache Management
```dart
// Get size
final size = await ModelPreloader().getCacheSize();

// Clear all
await ModelPreloader().clearCache();

// Format size
final formatted = await ModelPreloader().getCacheSizeFormatted(); // "145.2 MB"
```

## 📊 State Flow Diagram

```
     ┌─────┐
     │IDLE │ ◄─── Initial state
     └──┬──┘
        │ downloadModel()
        ▼
   ┌────────────┐
   │DOWNLOADING │ ◄─── Shows progress
   └─────┬──────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐  ┌─────┐
│ ERROR │  │DONE │
└───┬───┘  └──┬──┘
    │         │
    │retry()  │
    │         ▼
    │    ┌────────┐
    └───►│ CACHED │ ◄─── Next launch
         └────────┘
```

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Re-downloads every time | Use `downloadInfo.localPath` not `modelUrl` |
| Progress stuck at 0% | Server needs Content-Length header |
| State not updating | Use `ref.watch()` not `ref.read()` |
| Out of storage | Call `clearCache()` |
| Slow download | Normal for 60-80MB models |

## 📝 Imports Needed

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/model_download_provider.dart';
import '../widgets/model_download_progress.dart';
import '../../../../core/services/model_preloader.dart';
```

## ✅ Quick Checklist

- [ ] Widget extends `ConsumerWidget` or `ConsumerStatefulWidget`
- [ ] Build method has `WidgetRef ref` parameter
- [ ] Using `ref.watch()` for download state
- [ ] Using `downloadInfo.localPath` when cached
- [ ] Showing `ModelDownloadProgress` when not cached
- [ ] Handling all download states
- [ ] Tested with no internet
- [ ] Tested with cached model

## 🎯 Best Practices

1. **Always check cache first** - Instant loading for cached models
2. **Use background preload** - Preload next models while viewing current
3. **Handle errors gracefully** - Show retry button, don't crash
4. **Cancel on navigation** - Cleanup happens automatically
5. **Show progress** - Users expect feedback for 60-80MB downloads

## 📱 File Sizes Reference

| Model Type | Typical Size | Download Time (10 Mbps) |
|------------|--------------|-------------------------|
| Low detail | 20-30 MB | 16-24 seconds |
| Medium detail | 40-60 MB | 32-48 seconds |
| High detail | 60-80 MB | 48-64 seconds |

## 🔐 Cache Location

```
{app_documents}/model_cache/{sha256(url)}.{extension}
```

Example:
```
/data/user/0/com.example.app/app_flutter/model_cache/
  ├── a1b2c3d4e5f6g7h8.glb  (80 MB)
  ├── 9i8h7g6f5e4d3c2b.glb  (65 MB)
  └── 1a2b3c4d5e6f7g8h.gltf (72 MB)
```

## 💡 Pro Tips

- Cache survives app restarts
- Downloads continue in background
- Multiple concurrent downloads supported
- Progress callbacks throttled for performance
- SHA256 ensures no URL collisions
- File extensions preserved for compatibility

## 📚 Full Documentation

See `README_MODEL_DOWNLOAD.md` for complete documentation.

