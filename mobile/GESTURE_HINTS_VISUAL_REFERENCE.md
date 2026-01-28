# Gesture Hints Overlay - Visual Reference

## Layout Structure

```
┌─────────────────────────────────────────────────┐
│                                                 │
│              Full Screen Overlay                │
│         (Black 54% + Blur 10px)                │
│                                                 │
│    ┌────────────────────────────────────┐      │
│    │    TrueGlassContainer              │      │
│    │    (Blur 20px, Opacity 15%)        │      │
│    │                                    │      │
│    │    Hướng dẫn thao tác (Title)     │      │
│    │                                    │      │
│    │    ┌──┐  Kéo một ngón tay...      │      │
│    │    │👆│  để xoay mô hình 3D       │      │
│    │    └──┘                            │      │
│    │                                    │      │
│    │    ┌──┐  Chụm hai ngón để         │      │
│    │    │🤏│  phóng to/thu nhỏ         │      │
│    │    └──┘                            │      │
│    │                                    │      │
│    │    ┌──┐  Chạm điểm nóng           │      │
│    │    │👆│  để khám phá               │      │
│    │    └──┘                            │      │
│    │                                    │      │
│    │    Chạm bất kỳ đâu để tiếp tục    │      │
│    │    (Call-to-action badge)         │      │
│    │                                    │      │
│    └────────────────────────────────────┘      │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Backdrop Layer
- **Color**: `Colors.black54` (54% opacity)
- **Blur**: `BackdropFilter` with `sigmaX: 10, sigmaY: 10`
- **Purpose**: Dims 3D viewer, focuses attention on hints

### 2. Glass Container
- **Widget**: `TrueGlassContainer`
- **Blur**: 20px (strong blur for readability)
- **Opacity**: 0.15 (15%)
- **Padding**: 32px all sides
- **Border Radius**: 24px
- **Position**: Centered vertically and horizontally

### 3. Title
- **Text**: "Hướng dẫn thao tác"
- **Font Size**: 20px
- **Font Weight**: Bold
- **Color**: White
- **Margin Bottom**: 24px

### 4. Hint Rows (3 instances)

Each hint row consists of:

```
┌─────────────────────────────────────┐
│  ┌──────┐                           │
│  │ Icon │  Hint Text                │
│  └──────┘                           │
└─────────────────────────────────────┘
```

**Icon Container**:
- Shape: Circle
- Size: 52x52px (12px padding + 28px icon)
- Background: `AppColors.primary.withOpacity(0.2)`
- Border: 2px solid `AppColors.primary.withOpacity(0.5)`
- Icon Size: 28px
- Icon Color: `AppColors.primary`

**Text**:
- Font Size: 16px
- Font Weight: w500 (medium)
- Color: White
- Spacing from icon: 16px
- Layout: Flexible width

**Spacing between rows**: 16px

### 5. Call-to-Action Badge
- **Padding**: 16px horizontal, 8px vertical
- **Background**: `Colors.white.withOpacity(0.1)`
- **Border**: 1px solid `Colors.white.withOpacity(0.3)`
- **Border Radius**: 20px (pill shape)
- **Text**: "Chạm bất kỳ đâu để tiếp tục"
- **Font Size**: 14px
- **Color**: `Colors.white70`
- **Margin Top**: 24px

## Color Palette

| Element | Color | Opacity |
|---------|-------|---------|
| Backdrop | Black | 54% |
| Glass Container | White | 15% |
| Glass Border | White | 30% |
| Title | White | 100% |
| Hint Text | White | 100% |
| Icon Container BG | Primary | 20% |
| Icon Container Border | Primary | 50% |
| Icon | Primary | 100% |
| CTA Badge BG | White | 10% |
| CTA Badge Border | White | 30% |
| CTA Text | White | 70% |

## Icons Used

1. **Touch App** (`Icons.touch_app`) - One finger rotation
2. **Zoom Out Map** (`Icons.zoom_out_map`) - Two finger pinch
3. **Ads Click** (`Icons.ads_click`) - Tap hotspot

## Animation Timeline

```
0s ──────────► Overlay appears (instant)
              User sees hints
              
4s ──────────► Auto-dismiss timer fires
              Overlay fades out
              Flag saved to Hive

OR

0s-4s ────────► User taps anywhere
                Immediate dismiss
                Flag saved to Hive
```

## State Flow

```
App Launch
    │
    ▼
URN Viewer Loads
    │
    ▼
Check Hive Storage
'urn_viewer_gesture_hints_shown'
    │
    ├─► false ──► Show Overlay ──► Start 4s Timer
    │                  │
    │                  ├─► Timer expires ──► Dismiss
    │                  │
    │                  └─► User taps ──────► Dismiss
    │                                        │
    │                                        ▼
    │                              Save flag to Hive
    │
    └─► true ───► Skip Overlay
```

## Responsive Design

- Container width: Auto (fits content with 32px padding)
- Container max width: ~80% of screen width
- Text wrapping: Enabled on hint text
- Icon size: Fixed (doesn't scale)
- Vertical centering: Always centered

## Accessibility

- Large touch target (entire screen) for dismissal
- High contrast white text on dark background
- Clear iconography with text labels
- No time-sensitive interactions (can dismiss anytime)

## Z-Index Layering

From bottom to top:
1. 3D Model Viewer
2. Loading overlays
3. Top bar controls
4. Bottom bar stats
5. Motif sidebar (when open)
6. Discovery animation (when playing)
7. **Gesture hints overlay** ← Highest priority when shown

