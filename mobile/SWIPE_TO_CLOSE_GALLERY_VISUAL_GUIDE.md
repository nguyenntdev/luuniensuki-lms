# Swipe-to-Close Gallery - Visual Guide

## Before vs After

### BEFORE
```
┌─────────────────────────────────┐
│  [X] Close Button               │
│                                 │
│                                 │
│         📷 Image                │
│                                 │
│                                 │
│                                 │
│         1 / 3                   │
└─────────────────────────────────┘

❌ Only way to close: Tap [X] button
```

### AFTER
```
┌─────────────────────────────────┐
│  [X] Close Button               │
│         ↓ Swipe Down            │
│                                 │
│         📷 Image                │
│         (Opacity Fades)         │
│         (Moves with finger)     │
│                                 │
│         1 / 3                   │
└─────────────────────────────────┘

✅ Close with swipe down gesture
✅ Visual feedback (opacity + movement)
✅ Spring-back if not dragged enough
✅ Close button still works
```

## Gesture Flow

### Drag Start
```
User touches screen
       ↓
Drag begins
       ↓
Image follows finger vertically
Opacity starts fading (1.0 → 0.3)
Background darkens proportionally
```

### Drag Progress
```
Dragging Down ↓
┌─────────────┐
│   [X]       │  ← Close button visible
│             │
│    ⬇️       │  ← User finger moving
│   📷 80%    │  ← Image at 80% opacity
│             │  ← Offset by drag distance
│   1 / 3     │
└─────────────┘
```

### Drag End - Dismiss
```
IF dragOffset > 100px OR velocity > 500px/s
       ↓
Navigator.pop()
       ↓
Gallery closes
       ↓
Returns to lesson tab
```

### Drag End - Spring Back
```
IF dragOffset ≤ 100px AND velocity ≤ 500px/s
       ↓
Reset dragOffset = 0
Reset opacity = 1.0
       ↓
Animated transition (100ms)
       ↓
Image returns to original position
```

## State Transitions

### State Variables
```dart
_dragOffset: double    // Vertical displacement
_opacity: double       // Transparency level
```

### Opacity Calculation
```
_opacity = (1 - (|dragOffset| / 200)).clamp(0.3, 1.0)

Examples:
dragOffset =   0  → opacity = 1.0  (100% opaque)
dragOffset =  50  → opacity = 0.75 (75% opaque)
dragOffset = 100  → opacity = 0.5  (50% opaque)
dragOffset = 200  → opacity = 0.3  (30% opaque - minimum)
dragOffset = 300  → opacity = 0.3  (clamped to minimum)
```

## Widget Hierarchy

### Before
```
Scaffold
└── Stack
    ├── PhotoViewGallery.builder
    ├── Positioned (Close button)
    └── Positioned (Page indicator)
```

### After
```
Scaffold (backgroundColor: Colors.black.withOpacity(_opacity))
└── Stack
    ├── GestureDetector
    │   └── AnimatedOpacity (opacity: _opacity)
    │       └── Transform.translate (offset: Offset(0, _dragOffset))
    │           └── PhotoViewGallery.builder
    │               (backgroundDecoration: transparent)
    ├── Positioned (Close button)
    └── Positioned (Page indicator)
```

## Gesture Thresholds

### Distance Threshold
```
100 pixels = Minimum drag distance to close
├── 0-99px:   Spring back
└── 100+px:   Dismiss
```

### Velocity Threshold
```
500 pixels/second = Minimum swipe velocity to close
├── 0-499px/s:  Spring back (even if >100px)
└── 500+px/s:   Dismiss (even if <100px)
```

### Combined Logic
```
DISMISS if:
  dragOffset.abs() > 100 
  OR 
  velocity.abs() > 500

SPRING BACK if:
  dragOffset.abs() ≤ 100 
  AND 
  velocity.abs() ≤ 500
```

## Animation Timeline

### Drag Phase (Real-time)
```
0ms   - User starts drag
      - _dragOffset = 0
      - _opacity = 1.0
      
...   - During drag
      - _dragOffset updates continuously
      - _opacity updates continuously
      - Image translates in real-time
```

### Release Phase (100ms)
```
0ms   - User releases finger
      - Check dismiss conditions
      
IF DISMISS:
      - Navigator.pop() (instant)
      
IF SPRING BACK:
0ms   - Start animation
100ms - Complete animation
      - _dragOffset = 0
      - _opacity = 1.0
```

## User Experience Benefits

### ✅ Improved UX
1. **Familiarity**: Standard iOS/Android gesture
2. **Efficiency**: Faster than tapping close button
3. **Discoverability**: Visual feedback encourages exploration
4. **Accessibility**: Multiple ways to close (gesture + button)
5. **Natural Feel**: Physics-based spring-back animation

### ✅ Visual Feedback
1. **Opacity Fade**: Clear indication of drag progress
2. **Position Follow**: Image moves with finger
3. **Background Dim**: Context fades with image
4. **Smooth Transition**: No jarring movements

### ✅ No Breaking Changes
1. **Horizontal Swipe**: Still works for page navigation
2. **Pinch Zoom**: Still works for image zoom
3. **Close Button**: Still functional
4. **Page Indicator**: Still visible and accurate

