# Custom Model Viewer Integration

## Problem
The `model_viewer_plus` package uses WebView internally but doesn't expose the `WebViewController`, making it impossible to properly connect JavaScript handlers to Dart callbacks. This prevented proper communication between the 3D model viewer and the Flutter app for events like:
- Model load success/failure
- Loading progress
- Hotspot tap detection

## Solution
Created a custom wrapper widget using `flutter_inappwebview` to have full control over JavaScript handlers.

## Changes Made

### 1. New Dependencies
Added `flutter_inappwebview: ^6.0.0` to `pubspec.yaml`:

```yaml
dependencies:
  # 3D Rendering
  model_viewer_plus: ^1.6.0
  flutter_inappwebview: ^6.0.0
```

### 2. New Widget: CustomModelViewer
**File:** `mobile/lib/features/urn_viewer/presentation/widgets/custom_model_viewer.dart`

A custom 3D viewer widget that:
- Wraps Google's `<model-viewer>` web component in an InAppWebView
- Provides full JavaScript handler integration
- Handles model loading states and errors
- Detects hotspot taps and communicates back to Flutter

**Features:**
- ✅ Model load callbacks (`onModelLoaded`)
- ✅ Error handling (`onModelError`)
- ✅ Progress tracking (`onProgress`)
- ✅ Hotspot tap detection (`onHotspotTap`)
- ✅ Loading overlay with progress percentage
- ✅ Error overlay with retry button
- ✅ Proper cleanup on dispose

### 3. Updated UrnViewerScreen
**File:** `mobile/lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart`

**Changes:**
- Replaced `ModelViewer` (from model_viewer_plus) with `CustomModelViewer`
- Removed old JavaScript generation methods (`_generateHotspotHtml`, `_generateHotspotJs`)
- Simplified the viewer setup with proper callbacks
- Better error handling and loading state management

## Usage Example

```dart
CustomModelViewer(
  modelUrl: 'https://example.com/model.glb',
  alt: 'My 3D Model',
  hotspots: motifList,
  backgroundColor: const Color(0xFF1A1A2E),
  autoRotate: false,
  cameraControls: true,
  cameraOrbit: '0deg 75deg 5m',
  onModelLoaded: () {
    print('Model loaded successfully');
    setState(() {
      _isLoading = false;
    });
  },
  onModelError: (error) {
    print('Error loading model: $error');
    setState(() {
      _errorMessage = error;
    });
  },
  onProgress: (progress) {
    setState(() {
      _loadProgress = progress;
    });
  },
  onHotspotTap: (motifId) {
    print('Hotspot tapped: $motifId');
    _handleHotspotSelection(motifId);
  },
)
```

## JavaScript Handler Implementation

The widget registers these handlers with the WebView:

### 1. onModelLoad
Called when the 3D model finishes loading successfully.

```javascript
window.flutter_inappwebview.callHandler('onModelLoad', {
  success: true,
  timestamp: Date.now()
});
```

### 2. onModelError
Called when there's an error loading the model.

```javascript
window.flutter_inappwebview.callHandler('onModelError', {
  error: errorMessage,
  detail: errorDetails,
  timestamp: Date.now()
});
```

### 3. onProgress
Called with loading progress (0-100).

```javascript
window.flutter_inappwebview.callHandler('onProgress', {
  progress: percentage,
  timestamp: Date.now()
});
```

### 4. onHotspotTap
Called when user taps a hotspot.

```javascript
window.flutter_inappwebview.callHandler('onHotspotTap', {
  motifId: motifId,
  timestamp: Date.now()
});
```

## Benefits

1. **Better Communication**: Proper JavaScript-to-Dart communication through handlers
2. **Better Error Handling**: Detailed error messages with retry functionality
3. **Progress Tracking**: Real-time loading progress (0-100%)
4. **Hotspot Integration**: Direct hotspot tap detection without overlay positioning hacks
5. **Cleaner Code**: Removed complex JavaScript string generation
6. **More Control**: Full access to WebView lifecycle and configuration

## Testing

To test the implementation:

1. Run `flutter pub get` to install dependencies
2. Build and run the app
3. Navigate to any urn viewer screen
4. Observe:
   - Loading overlay with progress percentage
   - Model loads successfully
   - Hotspots are clickable
   - Error handling with retry button (test by disconnecting internet)

## Migration Notes

If you need to revert or use the old `model_viewer_plus` directly:

1. Change import back to `import 'package:model_viewer_plus/model_viewer_plus.dart';`
2. Replace `CustomModelViewer` with `ModelViewer` in `_build3DViewer`
3. Restore `_generateHotspotHtml` and `_generateHotspotJs` methods
4. Note: JavaScript handlers won't work properly with direct `model_viewer_plus`

## Known Limitations

1. **WebView Overhead**: Slightly more memory usage compared to native rendering
2. **Android 9+**: Requires `android:usesCleartextTraffic="true"` for localhost
3. **iOS**: Requires `io.flutter.embedded_views_preview` in Info.plist
4. **CORS**: Model files must have proper CORS headers for cross-origin loading

## Future Improvements

- [ ] Add camera position tracking
- [ ] Support for animations
- [ ] Screenshot/capture functionality
- [ ] Better AR mode integration
- [ ] Performance optimization for large models
- [ ] Offline model caching

## References

- [flutter_inappwebview Documentation](https://pub.dev/packages/flutter_inappwebview)
- [Google model-viewer](https://modelviewer.dev/)
- [model_viewer_plus](https://pub.dev/packages/model_viewer_plus)

