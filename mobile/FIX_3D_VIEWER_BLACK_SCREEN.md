# Fix for 3D Viewer Black Screen Issue

## Issue Description
The 3D viewer in the Flutter app was showing a black screen when trying to load urn models.

## Root Cause
The `effectiveModelUrl` getter in the Urn entity was returning a local asset path (`assets/models/...`) that doesn't work correctly with the `model_viewer_plus` package. Additionally, only one GLB model file (`CAO-DINH-v1.glb`) exists locally, while the other 8 urn models are missing.

## Solution
Changed the `effectiveModelUrl` getter to use remote URLs instead of local asset paths, ensuring all 9 urn models can be loaded from the remote server at `https://lms.histolab.icu/assets/models/`.

## Files Modified

### 1. `mobile/lib/features/urn_viewer/domain/entities/urn.dart`
**Changed:**
- Updated `effectiveModelUrl` getter to return `remoteModelUrl` instead of local asset path
- Updated comments to reflect the change from local assets to remote URLs

**Before:**
```dart
/// Get the effective model URL - prefers local assets over remote
String get effectiveModelUrl {
  // Always try local asset first for better performance
  // The app will have models bundled in assets/models/
  return 'assets/models/${slug.toUpperCase()}-v1.glb';
}
```

**After:**
```dart
/// Get the effective model URL - uses remote URL for reliable loading
String get effectiveModelUrl {
  // Use remote URL since local assets have path issues with model_viewer_plus
  // The remote server has all 9 urn models available
  return remoteModelUrl;
}
```

### 2. `mobile/lib/features/explore/domain/entities/urn.dart`
**Added:**
- Added `effectiveModelUrl` and `remoteModelUrl` getters for consistency across the app
- Both Urn entities now have the same URL handling logic

**New code:**
```dart
/// Get the effective model URL - uses remote URL for reliable loading
String get effectiveModelUrl {
  // Use remote URL for model_viewer_plus compatibility
  // All 9 urn models are available on the remote server
  return remoteModelUrl;
}

/// Get the remote model URL
String get remoteModelUrl {
  if (modelUrl != null && modelUrl!.isNotEmpty) {
    return modelUrl!;
  }
  // Fallback to constructed URL
  return 'https://lms.histolab.icu/assets/models/${slug.toUpperCase()}-v1.glb';
}
```

### 3. `mobile/lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart`
**Changed:**
- Updated comment in `_build3DViewer` method to reflect use of remote URLs

**Before:**
```dart
// Use local asset path for better performance
```

**After:**
```dart
// Use remote URL for reliable model loading
```

## How It Works
1. The `effectiveModelUrl` getter now returns the remote URL from the server
2. If `modelUrl` is provided by the API, it uses that
3. If not, it falls back to constructing the URL using the urn's slug: `https://lms.histolab.icu/assets/models/{SLUG}-v1.glb`
4. The ModelViewer widget in the screen loads the model from the remote URL
5. All 9 urn models are now accessible from the remote server

## Testing
To verify the fix:
1. Run the Flutter app
2. Navigate to any urn in the explore screen
3. Tap on an urn to open the 3D viewer
4. The 3D model should now load correctly from the remote server
5. Test with different urns to ensure all models load properly

## Benefits
- ✅ All 9 urn models are now accessible
- ✅ No need to bundle large GLB files in the app
- ✅ Easier to update models on the server without app updates
- ✅ Consistent behavior across both Urn entity implementations
- ✅ Proper fallback URL construction when API doesn't provide model_url

## Notes
- The ModelViewer widget already has proper configuration with `loading: Loading.eager` for fast loading
- Error handling is in place in the UrnViewerScreen
- The remote server at `https://lms.histolab.icu` has all 9 GLB model files available

