# Gesture Hints Overlay Implementation

## Overview
Added a first-time user gesture hints overlay to the 3D URN viewer to help users understand how to interact with the 3D model.

## Implementation Details

### Modified File
- `/lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart`

### Key Features
1. **One-time display**: Shows only on first visit, tracked via Hive storage
2. **Auto-dismiss**: Automatically dismisses after 4 seconds
3. **Manual dismiss**: User can tap anywhere to dismiss
4. **Glass morphism design**: Uses existing `TrueGlassContainer` for consistent styling
5. **Vietnamese text**: All hints in Vietnamese for target audience

### Technical Implementation

#### State Variables Added (Lines 90-92)
```dart
// Gesture hints
bool _showGestureHints = false;
Timer? _gestureHintsTimer;
```

#### Storage Key
- Key: `'urn_viewer_gesture_hints_shown'`
- Type: Boolean
- Stored in: Hive `settingsBox`

#### Core Methods

**1. _checkGestureHints() (Lines 200-215)**
- Called in `initState()`
- Reads from Hive storage
- If never shown, displays overlay and starts 4-second timer

**2. _dismissGestureHints() (Lines 217-223)**
- Cancels auto-dismiss timer
- Hides overlay
- Persists flag to Hive storage

**3. _buildGestureHintsOverlay() (Lines 1758-1813)**
- Returns full-screen overlay with semi-transparent backdrop
- Centers a glass container with hints
- Uses `BackdropFilter` for blur effect

**4. _buildHintRow() (Lines 1815-1843)**
- Renders individual hint with icon and text
- Consistent layout for each gesture type

### Gesture Hints Shown

1. **One-finger drag** (rotate model)
   - Icon: `Icons.touch_app`
   - Text: "Kéo một ngón tay để xoay mô hình 3D"

2. **Two-finger pinch** (zoom in/out)
   - Icon: `Icons.zoom_out_map`
   - Text: "Chụm hai ngón để phóng to/thu nhỏ"

3. **Tap hotspot** (explore)
   - Icon: `Icons.ads_click`
   - Text: "Chạm điểm nóng để khám phá"

### Visual Design

- **Backdrop**: Black 54% opacity with 10px blur
- **Container**: `TrueGlassContainer` with 20px blur, 15% opacity
- **Border radius**: 24px for modern rounded look
- **Icon design**: Circular badges with primary color
- **Spacing**: Consistent 16-24px spacing between elements
- **Title**: "Hướng dẫn thao tác" in bold white

### Integration

The overlay is positioned in the widget Stack (Lines 672-676):
```dart
// Gesture hints overlay (shows only on first use)
if (_showGestureHints)
  Positioned.fill(
    child: _buildGestureHintsOverlay(),
  ),
```

Placed after discovery animation to ensure it's on top when shown.

### Cleanup

Timer is properly disposed in `dispose()` method (Line 255):
```dart
_gestureHintsTimer?.cancel();
```

## Testing Checklist

- [ ] First-time user sees gesture hints overlay
- [ ] Overlay auto-dismisses after 4 seconds
- [ ] Tapping anywhere dismisses the overlay
- [ ] Subsequent visits do NOT show the overlay
- [ ] Glass morphism styling matches app design
- [ ] Vietnamese text displays correctly
- [ ] Icons are properly themed with primary color
- [ ] No memory leaks (timer properly disposed)

## How to Test

1. **Clear app data** or delete Hive storage file
2. **Navigate to 3D viewer** for any urn
3. **Verify overlay appears** with all three hints
4. **Wait 4 seconds** - overlay should auto-dismiss
5. **Restart app and revisit** - overlay should NOT appear again

### Manual Testing Reset
To test again, clear the Hive setting:
```dart
final hiveStorage = ref.read(hiveStorageProvider);
await hiveStorage.setSetting('urn_viewer_gesture_hints_shown', false);
```

## Code Quality

- ✅ No hardcoded strings (Vietnamese is intentional)
- ✅ Proper state management
- ✅ Memory leak prevention (timer disposal)
- ✅ Consistent with existing glass styling patterns
- ✅ Uses existing Hive infrastructure
- ✅ Self-documenting code with clear method names
- ✅ No redundant comments

## What's Next?

1. **Analytics tracking** (optional): Track how many users see/dismiss the hints
2. **A/B testing** (optional): Test different hint durations or wording
3. **Localization** (optional): Add English/other language support
4. **Advanced hints** (optional): Add hints for AR mode, camera reset, etc.

## File Changes Summary

- **Lines added**: ~115 lines
- **State variables**: 2
- **New methods**: 4
- **Hive storage keys**: 1
- **Dependencies**: No new dependencies (uses existing Hive, glass widgets)

