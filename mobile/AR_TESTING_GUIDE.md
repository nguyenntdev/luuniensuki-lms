# AR Functionality Testing Guide

## Quick Test Steps

### 1. Basic AR Button Test
1. Open the app and navigate to any URN detail screen
2. Verify AR button shows tooltip "Xem AR" (not "Xem AR (Sắp ra mắt)")
3. Tap the AR button in the bottom toolbar
4. Verify SnackBar appears with message: "Nhấn vào nút AR trên mô hình 3D để xem trong không gian thực"

### 2. Model Viewer AR Test
1. Look at the 3D model viewer
2. Wait for model to load completely
3. Locate the AR button on the model viewer (usually bottom-right corner)
4. Tap the AR button on the model
5. Grant camera permissions if prompted
6. Device should launch native AR viewer

### 3. AR Viewing Test (Android)
1. Point camera at flat surface (floor, table)
2. Model should appear with placement indicator
3. Tap to place model in space
4. Test interactions:
   - Move around model to view from different angles
   - Pinch to scale
   - Two-finger rotation
   - Tap and drag to reposition

### 4. AR Viewing Test (iOS)
1. Point camera at flat surface
2. Model appears with AR Quick Look interface
3. Tap to place model
4. Test interactions similar to Android

## Device Requirements

### Android
- Android 7.0 (Nougat) or higher
- ARCore support required
- Check device compatibility: https://developers.google.com/ar/devices

### iOS
- iOS 12 or higher
- A9 processor or newer (iPhone 6s and later)
- AR Quick Look support

## Expected Behavior

### ✅ Success Indicators
- [ ] AR button visible and labeled correctly
- [ ] SnackBar message appears when tapping toolbar AR button
- [ ] AR button appears on model viewer
- [ ] Tapping model AR button launches native AR
- [ ] Model displays correctly in AR space
- [ ] Can interact with model in AR

### ❌ Failure Indicators
- AR button missing on model viewer → Check if model loaded successfully
- AR button disabled/grayed out → Device may not support AR
- Camera permission denied → Need to grant permissions
- Model not appearing in AR → Check model format (should be GLB/GLTF)

## Troubleshooting

### AR Button Not Appearing on Model
**Possible Causes:**
1. Model hasn't finished loading
2. Device doesn't support AR
3. AR not enabled in CustomModelViewer

**Solution:** Verify `ar: true` is set in urn_viewer_screen.dart line 657

### AR Not Launching
**Possible Causes:**
1. Missing camera permissions
2. Device doesn't support ARCore/AR Quick Look
3. Browser WebView doesn't have AR capabilities

**Solution:** 
- Check device AR support
- Grant camera permissions
- Update Google Play Services (Android)

### Model Not Visible in AR
**Possible Causes:**
1. Model file format incompatible
2. Model scale too large/small
3. Lighting conditions poor

**Solution:**
- Ensure model is in GLB format
- Test in well-lit environment
- Try different placement surfaces

## Code Verification

### Check AR is Enabled
```dart
// File: urn_viewer_screen.dart, around line 657
return CustomModelViewer(
  modelUrl: modelPath,
  alt: urnDetail.urn.name,
  ar: true,  // ← Should be true
  // ...
);
```

### Check AR Parameters Passed to ModelViewer
```dart
// File: custom_model_viewer.dart, around line 464
ar: widget.ar,
arModes: widget.arModes ?? const ['scene-viewer', 'webxr', 'quick-look'],
iosSrc: widget.iosSrc,
```

## Testing Devices

### Recommended Test Devices
- **Android**: Pixel 4/5/6/7/8, Samsung Galaxy S20+
- **iOS**: iPhone 12/13/14/15 (any variant)

### Minimum Test Configuration
- At least one ARCore-compatible Android device
- At least one iOS device with AR Quick Look support

## Notes
- AR testing requires physical devices (emulators don't support AR)
- Test in various lighting conditions
- Test on different surface types (horizontal and vertical if supported)

