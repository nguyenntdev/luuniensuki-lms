# AR Button Testing Guide

## Quick Visual Reference

### What Changed
```
BEFORE                          AFTER
┌──────────────────┐           ┌──────────────────┐
│  Tap AR Button   │           │  Tap AR Button   │
└────────┬─────────┘           └────────┬─────────┘
         │                              │
         ▼                              ▼
┌──────────────────┐           ┌──────────────────┐
│ Show SnackBar:   │           │ Check if model   │
│ "Tap AR button   │           │ controller ready │
│  on 3D model"    │           └────────┬─────────┘
└──────────────────┘                    │
                                        ▼
                              ┌──────────────────┐
                              │   Yes: Activate  │
                              │   AR via JS      │
                              └──────────────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │ No: Show message │
                              │ "Wait for model  │
                              │  to load"        │
                              └──────────────────┘
```

## Testing Steps

### Test 1: Normal AR Activation ✓
1. Open URN viewer screen
2. Wait for 3D model to fully load
3. Tap AR button in bottom toolbar
4. **Expected**: AR mode activates immediately

### Test 2: Early Button Tap ✓
1. Open URN viewer screen
2. Immediately tap AR button (before model loads)
3. **Expected**: See message "Vui lòng đợi mô hình 3D tải xong"
4. Wait for model to load
5. Tap AR button again
6. **Expected**: AR mode activates

### Test 3: AR Not Supported ⚠️
1. Test on device without AR support
2. Tap AR button
3. **Expected**: See message "Không thể kích hoạt AR. Thiết bị có thể không hỗ trợ."

### Test 4: Multiple Taps 🔄
1. Wait for model to load
2. Tap AR button multiple times quickly
3. **Expected**: Should handle gracefully without crashes

## Code Flow

### 1. Controller Setup
```dart
// In CustomModelViewer
onWebViewCreated: (controller) {
  _webViewController = controller;
  widget.onControllerReady?.call(controller); // ← Exposes controller
},
```

### 2. Controller Storage
```dart
// In UrnViewerScreen
onControllerReady: (controller) {
  _modelViewerController = controller; // ← Stores reference
},
```

### 3. AR Activation
```dart
void _launchAR(UrnDetail urnDetail) {
  if (_modelViewerController == null) {
    // Show "wait for model" message
    return;
  }
  
  // Inject JavaScript to activate AR
  _modelViewerController.runJavaScript('''
    const modelViewer = document.querySelector('model-viewer');
    if (modelViewer && modelViewer.canActivateAR) {
      modelViewer.activateAR();
    }
  ''');
}
```

## Error Handling

### Case 1: Model Not Loaded
```
User Action: Tap AR button
Condition: _modelViewerController == null
Response: SnackBar "Vui lòng đợi mô hình 3D tải xong"
```

### Case 2: AR Not Available
```
User Action: Tap AR button
Condition: AR not supported on device
Response: SnackBar "Không thể kích hoạt AR. Thiết bị có thể không hỗ trợ."
```

### Case 3: JavaScript Error
```
User Action: Tap AR button
Condition: JS execution fails
Response: Debug log + SnackBar error message
```

## Visual States

### State 1: Loading
```
┌─────────────────────────────┐
│         🔄 Loading...       │
│                             │
│  [AR Button - Disabled]     │ ← Tapping shows wait message
└─────────────────────────────┘
```

### State 2: Ready
```
┌─────────────────────────────┐
│      3D Model Loaded ✓      │
│                             │
│   [AR Button - Active]      │ ← Tapping activates AR
└─────────────────────────────┘
```

### State 3: AR Activated
```
┌─────────────────────────────┐
│    AR View Active 🎯        │
│                             │
│  (Camera view with model)   │
└─────────────────────────────┘
```

## Success Criteria

✅ AR activates immediately when button tapped (model loaded)
✅ Helpful message when tapped too early
✅ Error handling for unsupported devices
✅ No crashes on multiple taps
✅ Debug logging for troubleshooting

## Files Modified
- `custom_model_viewer.dart` - Added onControllerReady callback
- `urn_viewer_screen.dart` - Implemented AR activation logic

## Related Documentation
- AR_BUTTON_PROGRAMMATIC_ACTIVATION.md - Full implementation details
- AR_FUNCTIONALITY_IMPLEMENTATION.md - Original AR setup
- AR_TESTING_GUIDE.md - Comprehensive testing guide

