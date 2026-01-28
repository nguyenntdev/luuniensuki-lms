# Login Screen - Visual Layout Reference

## Decorative Elements Positioning

```
┌──────────────────────────────────────┐
│                                      │ Top: 0
│    ●  (Top Left)                     │
│   150x150                        ●   │ Top: 50
│   primary                       120  │
│   opacity: 0.15              x120    │ Top: 200
│                              secondary│
│                              0.12     │
│                                      │
│                                      │
│   ●  (Middle Left)                   │ Top: 350
│  60x60                               │
│  gemYellow                           │
│  0.12                                │
│                                      │
│          [FORM CONTENT]         ●    │ Top: 450
│       [SafeArea Layer]         90x90 │
│                              secondary│
│                                0.1    │
│                                      │
│                                      │
│ ●  (Bottom Left)                 ●   │ Bottom: 150
│100x100                          80x80│ Bottom: 80
│gemYellow                      primary│
│  0.1                            0.08 │
│                                      │
└──────────────────────────────────────┘

Legend:
● = Circular gradient decorative element
Numbers = Width x Height in pixels
Colors = AppColors reference
Opacity = withOpacity() value
```

## Color Palette

### Primary Color
- **Usage**: Top-left and bottom-right elements
- **Reference**: `AppColors.primary`
- **Opacity**: 0.15 (top-left), 0.08 (bottom-right)
- **Effect**: Main brand color creates subtle framing

### Secondary Color
- **Usage**: Top-right and middle-right elements
- **Reference**: `AppColors.secondary`
- **Opacity**: 0.12 (top-right), 0.1 (middle-right)
- **Effect**: Accent color balances composition

### Gem Yellow
- **Usage**: Bottom-left and middle-left elements
- **Reference**: `AppColors.gemYellow`
- **Opacity**: 0.1 (bottom-left), 0.12 (middle-left)
- **Effect**: Warm highlight adds premium feel

## Visual Hierarchy

```
Layer 1 (Bottom): AnimatedGradientBackground
    ↓
Layer 2: Decorative Elements (Stack Positioned)
    ↓
Layer 3 (Top): Main Content (SafeArea + Form)
```

## Design Principles

1. **Subtle Enhancement**: Low opacity (0.08-0.15) ensures decorations don't overpower content
2. **Balance**: Elements distributed across all corners and sides
3. **Depth**: Varying sizes (60-150px) create visual interest
4. **Harmony**: All colors from existing palette maintain consistency
5. **Breathing Room**: Negative positioning (-10 to -40) extends beyond screen edges

## Gradient Effect

Each element uses `RadialGradient`:
```dart
RadialGradient(
  colors: [
    AppColors.[color].withOpacity([value]),  // Center
    AppColors.[color].withOpacity(0.0),      // Edge (transparent)
  ],
)
```

This creates a soft, glowing effect that fades naturally.

## Responsive Considerations

- Elements positioned using absolute coordinates
- May need adjustment for very small or large screens
- Consider using `MediaQuery` for dynamic positioning in future iterations

## Performance Notes

- Static decorative elements (no animation)
- Minimal render overhead
- GPU-accelerated gradients
- No impact on form performance

