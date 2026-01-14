# On-Demand Model Download System

This system provides efficient downloading and caching of 3D models with progress indication for the Luuniensuki LMS mobile app.

## Architecture

### Core Components

1. **ModelPreloader Service** (`mobile/lib/core/services/model_preloader.dart`)
   - Singleton pattern for global model management
   - Downloads models using Dio with progress callbacks
   - Caches models in app's documents directory using SHA256 URL hashing
   - Supports concurrent downloads, cancellation, and cache management

2. **ModelDownloadNotifier** (`mobile/lib/features/urn_viewer/presentation/providers/model_download_provider.dart`)
   - Riverpod provider for tracking download state per model URL
   - States: idle, downloading, completed, error, cached
   - Integrates with ModelPreloader service
   - Auto-detects cached models on initialization

3. **ModelDownloadProgress Widget** (`mobile/lib/features/urn_viewer/presentation/widgets/model_download_progress.dart`)
   - Beautiful glass-morphism UI matching app design
   - Shows circular progress with percentage
   - Displays download size (received/total)
   - Cancel and retry functionality
   - Responsive error handling

4. **UrnViewerScreen Integration** (`mobile/lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart`)
   - Checks cache status before loading model
   - Shows download progress UI when model not cached
   - Seamlessly transitions to 3D viewer once downloaded
   - Uses local file path for cached models

## Features

### Download Management
- **Progress Tracking**: Real-time progress updates (0-100%)
- **File Size Display**: Shows downloaded/total size in human-readable format
- **Cancellation**: Users can cancel in-progress downloads
- **Error Handling**: Graceful error messages with retry option
- **Network Timeouts**: Configurable timeouts (30s connect, 5min receive)

### Caching System
- **Persistent Storage**: Models cached in app documents directory
- **SHA256 Hashing**: URL-based cache keys prevent collisions
- **Extension Preservation**: Maintains original file extensions (.glb, .gltf)
- **Cache Management**: Query cache size, clear cache
- **Auto-Detection**: Instantly loads cached models without redownload

### Background Preloading
- **Adjacent Urn Preloading**: Preload nearby urns in the background
- **Silent Failures**: Background downloads fail silently to not disrupt UX
- **Smart Caching**: Only downloads if not already cached

### User Experience
- **Glass Morphism UI**: Consistent with app's visual style
- **Smooth Transitions**: Animated state changes
- **Clear Status**: Visual feedback for all states
- **Responsive**: Works on all screen sizes

## Usage

### Basic Download Flow

```dart
// In UrnViewerScreen
Consumer(
  builder: (context, ref, child) {
    final downloadInfo = ref.watch(modelDownloadNotifierProvider(modelUrl));
    
    switch (downloadInfo.state) {
      case ModelDownloadState.cached:
      case ModelDownloadState.completed:
        // Show 3D viewer with local path
        return ModelViewer(src: downloadInfo.localPath);
        
      case ModelDownloadState.downloading:
      case ModelDownloadState.idle:
      case ModelDownloadState.error:
        // Show download progress UI
        return ModelDownloadProgress(modelUrl: modelUrl);
    }
  },
)
```

### Manual Download Trigger

```dart
final notifier = ref.read(modelDownloadNotifierProvider(modelUrl).notifier);
await notifier.downloadModel();
```

### Background Preloading

```dart
// Preload adjacent urns
final preloader = ref.read(modelPreloadNotifierProvider.notifier);
await preloader.preloadUrns([urn1, urn2, urn3]);
```

### Cache Management

```dart
// Get cache size
final cacheManager = ref.watch(cacheManagerProvider);
cacheManager.when(
  data: (sizeInBytes) => Text('Cache: ${formatBytes(sizeInBytes)}'),
  loading: () => CircularProgressIndicator(),
  error: (err, _) => Text('Error'),
);

// Clear cache
await ref.read(cacheManagerProvider.notifier).clearCache();
```

## File Structure

```
mobile/lib/
├── core/
│   └── services/
│       └── model_preloader.dart          # Core download service
└── features/
    └── urn_viewer/
        ├── presentation/
        │   ├── providers/
        │   │   ├── model_download_provider.dart     # Download state management
        │   │   └── model_download_provider.g.dart   # Generated Riverpod code
        │   ├── screens/
        │   │   └── urn_viewer_screen.dart           # Updated with download UI
        │   └── widgets/
        │       └── model_download_progress.dart     # Progress UI widget
```

## State Diagram

```
[idle] → [downloading] → [completed]
   ↓           ↓              ↓
   →      [error]       [cached]
              ↓
         [downloading] (retry)
```

## Dependencies

```yaml
dependencies:
  dio: ^5.4.0              # HTTP client with progress
  path_provider: ^2.1.1    # Platform-specific directories
  crypto: ^3.0.3           # SHA256 hashing
  riverpod: ^2.4.9         # State management
```

## Performance Considerations

- **Model Size**: Typical models are 60-80 MB
- **Memory**: Uses streaming download, minimal memory footprint
- **Network**: Respects connection timeouts, handles network errors
- **Storage**: Models persist across app restarts
- **Concurrent Downloads**: Supports multiple simultaneous downloads

## Error Handling

1. **Connection Timeout**: Clear message, suggests checking internet
2. **Network Error**: Detects no connection state
3. **Server Error**: Shows HTTP status code
4. **Download Failure**: Cleans up partial files
5. **Cancellation**: Graceful cleanup of in-progress downloads

## Future Enhancements

- [ ] Download queue with priority
- [ ] Automatic cache cleanup (LRU eviction)
- [ ] Download pause/resume
- [ ] Wi-Fi only download option
- [ ] Bandwidth throttling
- [ ] Download analytics
- [ ] Offline mode indicator
- [ ] Pre-download all models option

## Testing

### Manual Testing Checklist
- [ ] First download shows progress correctly
- [ ] Subsequent loads use cache (instant)
- [ ] Cancel button works during download
- [ ] Retry works after error
- [ ] No internet shows appropriate error
- [ ] Cache persists across app restarts
- [ ] Multiple concurrent downloads work
- [ ] File extensions preserved correctly

### Test Cases
```dart
// Check if model is cached
final isCached = await ModelPreloader().isCached(modelUrl);

// Get cache size
final size = await ModelPreloader().getCacheSize();

// Clear cache
await ModelPreloader().clearCache();
```

## Troubleshooting

**Model won't download**
- Check internet connection
- Verify model URL is accessible
- Check available storage space
- Review Dio error logs

**Cache not persisting**
- Verify path_provider returns correct directory
- Check file permissions
- Ensure files aren't being deleted by OS

**Progress stuck at 0%**
- Check server supports content-length header
- Verify Dio receive progress callback
- Check for network throttling

## Credits

Implemented for Luuniensuki LMS - Vietnamese Cultural Heritage Learning Platform

