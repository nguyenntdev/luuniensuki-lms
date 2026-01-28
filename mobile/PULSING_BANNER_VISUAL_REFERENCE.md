# 🎬 Pulsing Due Reviews Banner - Visual Reference

## Animation Timeline (2-second loop)

```
Time:    0s -------- 1s -------- 2s -------- (repeat)
         ↓          ↓          ↓
Scale:   1.0 -----> 1.02 -----> 1.0 -----> 1.02
Border:  0.3 -----> 0.7  -----> 0.3 -----> 0.7
Shadow:  8px -----> 15px -----> 8px -----> 15px
Icon:    0° -> +5.7° -> -5.7° -> 0° (wobble)
```

## Animation States

### State 1: Rest (0s)
```
┌─────────────────────────────────┐
│  🔔 CẦN ÔN TẬP: 8 họa tiết      │  Scale: 1.0
│  Kế tiếp trong 2 giờ            │  Border: 0.3 opacity
└─────────────────────────────────┘  Shadow: 8px blur
     ↑ Icon at 0°
```

### State 2: Peak (1s)
```
┌───────────────────────────────────┐
│   🔔 CẦN ÔN TẬP: 8 họa tiết       │  Scale: 1.02 ✨
│   Kế tiếp trong 2 giờ             │  Border: 0.7 opacity 🌟
└───────────────────────────────────┘  Shadow: 15px blur ☄️
      ↑ Icon wobbling +5.7°
```

### State 3: Rest (2s)
```
┌─────────────────────────────────┐
│  🔔 CẦN ÔN TẬP: 8 họa tiết      │  Scale: 1.0
│  Kế tiếp trong 2 giờ            │  Border: 0.3 opacity
└─────────────────────────────────┘  Shadow: 8px blur
     ↑ Icon back to 0°
```

## Icon Animation Detail

```
Bell Wobble Pattern (over 2 seconds):
      
  0°  →  +5.7°  →  -5.7°  →  0°
  🔔     🔔      🔔      🔔
  |      /      \      |
  |     /        \     |
  |    /          \    |
Start  Peak1    Peak2  End

Duration: 500ms → 1000ms → 500ms
Weights:  25%   →  50%   →  25%
```

## Color Scheme

```
Primary Color: AppColors.warning (#F59E0B)
├── Background Gradient: 
│   ├── Top-left: warning at 20% opacity
│   └── Bottom-right: warning at 10% opacity
├── Border: warning at 30-70% opacity (animated)
├── Shadow: warning at 30% opacity (blur 8-15px)
├── Icon Background: warning at 30% opacity
└── Icon: warning at 100% opacity
```

## Layout Variants

### Desktop/Tablet (width ≥ 340px)
```
┌─────────────────────────────────────────────┐
│  ┌────┐                              →     │
│  │ 🔔 │  CẦN ÔN TẬP: 8 họa tiết            │
│  └────┘  Kế tiếp trong 2 giờ               │
└─────────────────────────────────────────────┘
   Icon    Text Content              Arrow
```

### Mobile/Compact (width < 340px)
```
┌───────────────────────┐
│  ┌────┐               │
│  │ 🔔 │               │
│  └────┘               │
│                       │
│  CẦN ÔN TẬP: 8 họa tiết│
│  Kế tiếp trong 2 giờ  │
└───────────────────────┘
```

## Animation Curves

All animations use `Curves.easeInOut` for smooth, natural motion:

```
Value
  ^
1 │      ╱────╲
  │    ╱        ╲
  │  ╱            ╲
0 │╱                ╲
  └────────────────────> Time
  0s      1s      2s
  
  Smooth acceleration and deceleration
```

## Performance Notes

- **Frame Rate**: 60 FPS
- **Memory**: Minimal (single AnimationController)
- **CPU**: Low (native Flutter animations)
- **Battery**: Negligible impact

## User Experience

**Attention Level**: ⭐⭐⭐☆☆ (3/5)
- Noticeable but not intrusive
- Gentle pulsing catches eye
- Bell wobble reinforces urgency
- 2s cycle prevents fatigue

**Accessibility**:
- ✅ No rapid flashing (WCAG compliant)
- ✅ Smooth animations (motion-sickness safe)
- ✅ Clear visual hierarchy maintained

