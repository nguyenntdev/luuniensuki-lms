# Bug Fix: 3D Model Viewer Black Screen Issue

## Issue Summary
The 3D model viewer was showing a black screen due to three main issues:
1. Loading timer logic inside the `build()` method causing multiple callbacks
2. Very dark background color (`Color(0xFF0A0E14)`) making it difficult to distinguish loading from errors
3. Missing `android:usesCleartextTraffic` in AndroidManifest.xml potentially blocking HTTP model loading

## Fixes Applied

### Fix 1: AndroidManifest.xml - Enable Cleartext Traffic
**File:** `mobile/android/app/src/main/AndroidManifest.xml`

**Change:** Added `android:usesCleartextTraffic="true"` to the `<application>` tag.

```xml
<application
    android:label="luuniensuki_lms"
    android:name="${applicationName}"
    android:icon="@mipmap/ic_launcher"
    android:allowBackup="false"
    android:usesCleartextTraffic="true">
```

**Why:** This allows the app to load 3D models over HTTP if needed. While the production server uses HTTPS, this ensures compatibility during development and prevents network-related loading failures.

### Fix 2: Move Loading Logic from build() to initState()
**File:** `mobile/lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart`

**Change:** Moved the `Future.delayed` loading timer from inside the `_build3DViewer()` method to the `initState()` lifecycle method.

**Before:**
```dart
Widget _build3DViewer(UrnDetail urnDetail) {
  // ...
  
  // Set loading to false after model load delay
  if (_isLoading) {
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted && _isLoading) {
        setState(() => _isLoading = false);
      }
    });
  }
  
  return ModelViewer(...);
}
```

**After:**
```dart
@override
void initState() {
  super.initState();
  SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
  
  // Set loading to false after model load delay
  // This is a fallback in case the model doesn't emit a load event
  Future.delayed(const Duration(seconds: 3), () {
    if (mounted && _isLoading) {
      setState(() => _isLoading = false);
    }
  });
}

Widget _build3DViewer(UrnDetail urnDetail) {
  final modelPath = urnDetail.urn.effectiveModelUrl;
  debugPrint('[URN_VIEWER] Loading model from: $modelPath');
  
  return ModelViewer(...);
}
```

**Why:** The `build()` method can be called multiple times (on every rebuild), which would create multiple `Future.delayed` timers. Moving this to `initState()` ensures it runs only once when the widget is initialized, preventing multiple redundant callbacks.

### Fix 3: Lighter Background Color for Debugging
**File:** `mobile/lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart`

**Change:** Changed ModelViewer backgroundColor from `AppColors.background` (`Color(0xFF0A0E14)` - very dark) to `Color(0xFF1A1A2E)` (lighter navy).

**Before:**
```dart
return ModelViewer(
  // ...
  backgroundColor: AppColors.background, // Very dark: Color(0xFF0A0E14)
  // ...
);
```

**After:**
```dart
return ModelViewer(
  // ...
  backgroundColor: const Color(0xFF1A1A2E), // Lighter background for debugging
  // ...
);
```

**Why:** The original `AppColors.background` color (`#0A0E14`) is extremely dark, making it nearly indistinguishable from black. This made it impossible to tell whether the screen was loading, had an error, or was working correctly. The new color (`#1A1A2E`) is still dark but has enough contrast to be visually distinct from pure black, making debugging easier.

## Testing
To verify the fixes:

1. **Clean and rebuild the app:**
   ```bash
   cd mobile
   flutter clean
   flutter pub get
   flutter build apk
   ```

2. **Run on device/emulator:**
   ```bash
   flutter run
   ```

3. **Navigate to any 3D urn viewer**
   - You should see a loading indicator with "Đang tải mô hình 3D..." text
   - After ~3 seconds, the 3D model should load and display
   - The background should be a dark navy color, not pure black
   - You should be able to interact with the model (rotate, zoom, pan)

## Expected Behavior
- Loading overlay appears immediately with gold spinner
- Background changes from loading overlay to dark navy
- 3D model loads and is visible against the navy background
- Hotspots appear after loading completes
- Model is interactive (rotate, zoom, pan)

## If Issues Persist
If the black screen still occurs:
1. Check the debug console for `[URN_VIEWER] Loading model from:` messages
2. Verify the model URL is accessible
3. Check network connectivity
4. Try restarting the app completely
5. Check for any WebView-related errors in logcat

## Related Files
- `mobile/android/app/src/main/AndroidManifest.xml`
- `mobile/lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart`
- `mobile/lib/core/theme/app_colors.dart` (reference for color values)

