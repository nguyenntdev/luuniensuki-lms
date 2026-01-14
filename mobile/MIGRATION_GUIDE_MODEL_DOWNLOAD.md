# Migration Guide: Adding Model Download to Other Screens

This guide shows how to integrate the model download system into other screens that use 3D models.

## Quick Start (5 minutes)

### 1. Import Required Providers

```dart
import '../providers/model_download_provider.dart';
import '../widgets/model_download_progress.dart';
```

### 2. Wrap Your ModelViewer with Consumer

**Before:**
```dart
Widget build(BuildContext context) {
  return ModelViewer(
    src: 'https://example.com/model.glb',
    // ... other properties
  );
}
```

**After:**
```dart
Widget build(BuildContext context, WidgetRef ref) {
  final modelUrl = 'https://example.com/model.glb';
  final downloadInfo = ref.watch(modelDownloadNotifierProvider(modelUrl));
  
  // Show download UI if not cached
  if (downloadInfo.state != ModelDownloadState.cached &&
      downloadInfo.state != ModelDownloadState.completed) {
    return ModelDownloadProgress(
      modelUrl: modelUrl,
      onCancel: () => Navigator.pop(context),
    );
  }
  
  // Show 3D viewer with local cached path
  return ModelViewer(
    src: downloadInfo.localPath ?? modelUrl,
    // ... other properties
  );
}
```

### 3. Change StatelessWidget to ConsumerWidget

**Before:**
```dart
class MyScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    // ...
  }
}
```

**After:**
```dart
class MyScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // ...
  }
}
```

Or for StatefulWidget:

**Before:**
```dart
class MyScreen extends StatefulWidget {
  @override
  State<MyScreen> createState() => _MyScreenState();
}

class _MyScreenState extends State<MyScreen> {
  @override
  Widget build(BuildContext context) {
    // ...
  }
}
```

**After:**
```dart
class MyScreen extends ConsumerStatefulWidget {
  @override
  ConsumerState<MyScreen> createState() => _MyScreenState();
}

class _MyScreenState extends ConsumerState<MyScreen> {
  @override
  Widget build(BuildContext context) {
    // ...
  }
}
```

## Advanced Usage

### Manual Download Trigger

```dart
ElevatedButton(
  onPressed: () async {
    final notifier = ref.read(
      modelDownloadNotifierProvider(modelUrl).notifier,
    );
    await notifier.downloadModel();
  },
  child: Text('Download Now'),
)
```

### Show Custom Loading While Downloading

```dart
final downloadInfo = ref.watch(modelDownloadNotifierProvider(modelUrl));

switch (downloadInfo.state) {
  case ModelDownloadState.downloading:
    return MyCustomProgressBar(progress: downloadInfo.progress);
    
  case ModelDownloadState.error:
    return ErrorWidget(message: downloadInfo.error);
    
  case ModelDownloadState.cached:
  case ModelDownloadState.completed:
    return ModelViewer(src: downloadInfo.localPath);
    
  case ModelDownloadState.idle:
    return DownloadButton(
      onTap: () => ref.read(
        modelDownloadNotifierProvider(modelUrl).notifier
      ).downloadModel(),
    );
}
```

### Background Preload Adjacent Models

```dart
@override
void initState() {
  super.initState();
  
  // Preload next 3 models in background
  Future.microtask(() {
    final preloader = ref.read(modelPreloadNotifierProvider.notifier);
    preloader.preloadUrns([nextUrn1, nextUrn2, nextUrn3]);
  });
}
```

## Complete Example

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:model_viewer_plus/model_viewer_plus.dart';
import '../providers/model_download_provider.dart';
import '../widgets/model_download_progress.dart';

class My3DModelScreen extends ConsumerWidget {
  final String modelUrl;

  const My3DModelScreen({
    super.key,
    required this.modelUrl,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final downloadInfo = ref.watch(modelDownloadNotifierProvider(modelUrl));

    return Scaffold(
      appBar: AppBar(title: Text('3D Model Viewer')),
      body: _buildBody(downloadInfo),
    );
  }

  Widget _buildBody(ModelDownloadInfo downloadInfo) {
    // Show download progress if not cached
    if (downloadInfo.state == ModelDownloadState.idle ||
        downloadInfo.state == ModelDownloadState.downloading ||
        downloadInfo.state == ModelDownloadState.error) {
      return ModelDownloadProgress(
        modelUrl: modelUrl,
        onCancel: () => Navigator.pop(context),
      );
    }

    // Show 3D viewer once model is ready
    return ModelViewer(
      src: downloadInfo.localPath ?? modelUrl,
      alt: 'My 3D Model',
      ar: true,
      autoRotate: true,
      cameraControls: true,
    );
  }
}
```

## Testing Your Integration

### 1. First Launch (No Cache)
- ✅ Should show download button
- ✅ Tapping button should start download
- ✅ Should show progress percentage
- ✅ Should transition to 3D viewer when complete

### 2. Second Launch (Cached)
- ✅ Should skip download UI
- ✅ Should load instantly from cache
- ✅ Model should render correctly

### 3. Error Handling
- ✅ Disconnect WiFi and try downloading
- ✅ Should show error message
- ✅ Retry button should work

### 4. Cancellation
- ✅ Start download
- ✅ Tap cancel
- ✅ Should return to previous screen

## Troubleshooting

### Model re-downloads every time
**Problem**: Not checking cached state correctly
**Solution**: Make sure you're using the downloadInfo.localPath when state is cached

```dart
// WRONG
ModelViewer(src: modelUrl)  // Always uses remote URL

// RIGHT
ModelViewer(src: downloadInfo.localPath ?? modelUrl)
```

### Progress stuck at 0%
**Problem**: Server doesn't send Content-Length header
**Solution**: This is a server-side issue. Contact backend team.

### Download never completes
**Problem**: Timeout too short for large files
**Solution**: Already configured in ModelPreloader (5min timeout)

### State not updating
**Problem**: Not watching the provider correctly
**Solution**: Use `ref.watch()`, not `ref.read()`

```dart
// WRONG - won't rebuild
final downloadInfo = ref.read(modelDownloadNotifierProvider(url));

// RIGHT - rebuilds on state change
final downloadInfo = ref.watch(modelDownloadNotifierProvider(url));
```

## Performance Tips

1. **Preload on List Screen**: Preload models when user scrolls through list
2. **Smart Caching**: Check cache status before rendering
3. **Progress Throttling**: UI already handles this
4. **Cancel on Exit**: Download cancels automatically when provider disposes

## Need Help?

Check the comprehensive documentation:
- `README_MODEL_DOWNLOAD.md` - Full system docs
- `model_download_example.dart` - Working examples
- `model_download_test.dart` - Test patterns

## Checklist

- [ ] Imported model_download_provider
- [ ] Changed to ConsumerWidget/ConsumerStatefulWidget
- [ ] Added WidgetRef ref parameter to build method
- [ ] Wrapped ModelViewer with download state check
- [ ] Used downloadInfo.localPath for cached models
- [ ] Added ModelDownloadProgress for download UI
- [ ] Tested first launch (download flow)
- [ ] Tested second launch (cached flow)
- [ ] Tested error handling
- [ ] Tested cancel functionality

