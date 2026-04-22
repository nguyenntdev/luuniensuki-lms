# 3D Viewer Enhancements - Visual Testing Guide

## 🎨 Component Visual Reference

### 1. GestureHintsOverlay
```
┌─────────────────────────────────────────┐
│                                         │
│  ┌───────────────────────────────┐     │
│  │  👆        🔍                  │     │
│  │  Kéo để    Cuộn để             │     │
│  │  xoay      thu/phóng           │     │
│  │                                │     │
│  │  Nhấp vào bất kỳ đâu để tiếp tục │  │
│  └───────────────────────────────┘     │
│                                         │
└─────────────────────────────────────────┘
         Semi-transparent overlay
         White card with backdrop blur
         Auto-dismisses after 4s
```

### 2. ZoomIndicator
```
┌─────────────────────────┐
│               ┌───────┐ │
│               │ 150%  │ │  ← Top right corner
│               └───────┘ │     Black/70 with blur
└─────────────────────────┘     Auto-hides after 1.5s
```

### 3. CameraResetButton
```
┌─────────────────────────┐
│                         │
│                         │
│                    ⟲   │  ← Bottom right
│                   ───  │     Circular button
└─────────────────────────┘     White/80 with blur
```

### 4. ViewerControls
```
┌─────────────────────────┐
│  ⊕                      │  ← Zoom In
│  ⊝                      │  ← Zoom Out
│  ⛶                      │  ← Fit View
│                         │
│                         │
└─────────────────────────┘
   Bottom left
   Vertical stack
   White/80 with blur
```

---

## 🧪 Testing Steps

### Test 1: First-Time Hints
```bash
# 1. Open browser DevTools (F12)
# 2. Go to Application > Local Storage
# 3. Delete key: '3d-viewer-hints-shown'
# 4. Reload page
# 5. Expected: Hints appear immediately
# 6. Expected: Auto-dismiss after 4 seconds
# 7. OR: Click anywhere to dismiss
```

**Visual Check:**
- ✅ Semi-transparent black overlay
- ✅ White card centered
- ✅ Two icons with text
- ✅ Smooth fade-in
- ✅ Smooth fade-out

### Test 2: Zoom Indicator
```bash
# 1. Load viewer
# 2. Scroll mouse wheel up (zoom in)
# 3. Expected: "XXX%" appears top-right
# 4. Wait 1.5 seconds
# 5. Expected: Indicator fades out
# 6. Scroll again
# 7. Expected: Indicator reappears
```

**Visual Check:**
- ✅ Shows percentage (10-500%)
- ✅ Top-right position
- ✅ Black background with white text
- ✅ Smooth transitions
- ✅ Updates in real-time

### Test 3: Camera Reset
```bash
# 1. Rotate/zoom the 3D model
# 2. Click reset button (bottom-right)
# 3. Expected: Camera smoothly returns to initial position
```

**Visual Check:**
- ✅ Circular button visible
- ✅ RotateCcw icon centered
- ✅ Hover effect works
- ✅ Tooltip shows on hover
- ✅ Position: bottom-right

### Test 4: Viewer Controls
```bash
# 1. Click zoom in (+) button
# Expected: Camera moves closer

# 2. Click zoom out (-) button
# Expected: Camera moves away

# 3. Click fit view (⛶) button
# Expected: Camera resets to show full model
```

**Visual Check:**
- ✅ Three buttons stacked vertically
- ✅ Bottom-left position
- ✅ Icons visible and clear
- ✅ Hover effects work
- ✅ Tooltips show on hover
- ✅ All buttons clickable

---

## 📱 Mobile Testing

### Touch Gestures
```bash
# 1. Open on mobile device or use DevTools mobile emulation
# 2. Expected: Hints show "tap" instead of "click"
# 3. Touch and drag to rotate
# 4. Pinch to zoom
# 5. Tap any control button
```

**Visual Check:**
- ✅ Buttons large enough to tap (44x44px minimum)
- ✅ Hints dismiss on first touch
- ✅ Controls don't overlap content
- ✅ Text is readable on small screen

---

## 🎨 Visual States

### GestureHintsOverlay States
1. **Hidden** - Not shown (after first time)
2. **Visible** - Showing (first 4 seconds)
3. **Dismissed** - User clicked/tapped

### ZoomIndicator States
1. **Hidden** - No zoom activity
2. **Visible** - User is zooming
3. **Fading** - Auto-hiding after 1.5s

### Buttons States
1. **Default** - White/80 background
2. **Hover** - White/100 background
3. **Active** - Clicked/tapped

---

## 🔍 Detailed Visual Specs

### Colors
- **Overlay background:** `bg-black/30` (black 30% opacity)
- **Hints card:** `bg-white/90` (white 90% opacity)
- **Zoom indicator:** `bg-black/70` (black 70% opacity)
- **Buttons:** `bg-white/80` (white 80% opacity)
- **Buttons hover:** `bg-white` (white 100%)

### Typography
- **Hints title:** `text-xs` (12px)
- **Hints footer:** `text-sm` (14px)
- **Zoom percentage:** `text-sm font-medium` (14px)
- **Icons:** `w-5 h-5` (20px) for buttons
- **Icons:** `w-8 h-8` (32px) for hints

### Spacing
- **Hints padding:** `p-6` (24px)
- **Button padding:** `p-2` (8px)
- **Controls gap:** `gap-2` (8px)
- **Hints icons gap:** `gap-8` (32px)

### Effects
- **Backdrop blur:** `backdrop-blur` / `backdrop-blur-md`
- **Shadows:** `shadow-lg`
- **Rounded corners:** `rounded-lg` / `rounded-full`
- **Transitions:** `transition-colors` / `transition-opacity`

### Z-Index Layers
```
z-30: (future overlays)
z-20: Controls & indicators
z-10: Hints overlay
z-0:  3D Viewer (base)
```

---

## 📸 Screenshot Checklist

Take screenshots for each state:

- [ ] Hints overlay - initial appearance
- [ ] Zoom indicator - showing 100%
- [ ] Zoom indicator - showing 250%
- [ ] Camera reset button - default
- [ ] Camera reset button - hover
- [ ] Viewer controls - default
- [ ] Viewer controls - hover on each button
- [ ] Mobile view - all components
- [ ] Desktop view - all components together

---

## 🐛 Common Issues & Solutions

### Issue: Hints don't appear
**Solution:** Clear localStorage and reload

### Issue: Zoom indicator stuck
**Solution:** Check controlsRef is properly passed

### Issue: Buttons not clickable
**Solution:** Check z-index and pointer-events

### Issue: Tooltips not showing
**Solution:** Ensure title attribute is set

### Issue: Components overlap
**Solution:** Adjust positioning classes

---

## ✅ Final Visual Checklist

### Desktop
- [ ] All components visible
- [ ] No overlap with existing UI
- [ ] Tooltips work on hover
- [ ] Smooth animations
- [ ] Proper spacing

### Mobile
- [ ] Buttons large enough
- [ ] Text readable
- [ ] Touch targets sufficient
- [ ] No horizontal scroll
- [ ] Gestures work smoothly

### Accessibility
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] High contrast readable
- [ ] Focus indicators visible
- [ ] ARIA labels present

---

## 🎯 Expected User Flow

```
1st Visit:
  ┌─────────────────┐
  │ Page Load       │
  └────────┬────────┘
           ▼
  ┌─────────────────┐
  │ Hints Appear    │  (4 seconds)
  └────────┬────────┘
           ▼
  ┌─────────────────┐
  │ Auto Dismiss    │
  └────────┬────────┘
           ▼
  ┌─────────────────┐
  │ Mark as Shown   │
  └─────────────────┘

Subsequent Visits:
  ┌─────────────────┐
  │ Page Load       │
  └────────┬────────┘
           ▼
  ┌─────────────────┐
  │ No Hints        │  (localStorage check)
  └─────────────────┘

During Usage:
  Zoom → Indicator shows → Auto-hides
  Reset → Camera animates → Done
  Controls → Immediate response
```

