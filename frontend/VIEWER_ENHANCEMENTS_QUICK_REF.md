# 3D Viewer Enhancements - Quick Reference

## 🚀 Quick Start

### Import
```jsx
import {
  GestureHintsOverlay,
  ZoomIndicator,
  CameraResetButton,
  ViewerControls,
} from '@/components/viewer'
```

### Basic Usage
```jsx
// 1. First-time hints
<GestureHintsOverlay onDismiss={() => console.log('dismissed')} />

// 2. Zoom indicator
const controlsRef = useRef()
<ZoomIndicator controlsRef={controlsRef} />

// 3. Camera reset
<CameraResetButton onClick={() => camera.reset()} />

// 4. Viewer controls
<ViewerControls
  onZoomIn={() => camera.zoomIn()}
  onZoomOut={() => camera.zoomOut()}
  onFitView={() => camera.fit()}
/>
```

---

## 📋 Component Props

| Component | Props | Type | Required |
|-----------|-------|------|----------|
| GestureHintsOverlay | `onDismiss` | `() => void` | No |
| ZoomIndicator | `controlsRef` | `RefObject` | Yes |
| CameraResetButton | `onClick` | `() => void` | Yes |
| | `className` | `string` | No |
| ViewerControls | `onZoomIn` | `() => void` | Yes |
| | `onZoomOut` | `() => void` | Yes |
| | `onFitView` | `() => void` | Yes |
| | `className` | `string` | No |

---

## 💾 localStorage Integration

### Check & Set
```jsx
// Check if hints shown
const hasSeenHints = localStorage.getItem('3d-viewer-hints-shown')

// Mark as shown
localStorage.setItem('3d-viewer-hints-shown', 'true')

// Reset (for testing)
localStorage.removeItem('3d-viewer-hints-shown')
```

---

## 🎨 Positioning Examples

```jsx
// Top right
<div className="absolute top-4 right-4 z-20">
  <CameraResetButton onClick={reset} />
</div>

// Bottom left
<div className="absolute bottom-4 left-4 z-20">
  <ViewerControls {...props} />
</div>

// Bottom right
<CameraResetButton
  onClick={reset}
  className="absolute bottom-4 right-4 z-20"
/>
```

---

## 🔧 Camera Control Handlers

```jsx
// Zoom In (move camera closer)
const handleZoomIn = () => {
  const camera = controlsRef.current.object
  const target = controlsRef.current.target
  const direction = camera.position.clone().sub(target).normalize()
  camera.position.addScaledVector(direction, -0.5)
}

// Zoom Out (move camera away)
const handleZoomOut = () => {
  const camera = controlsRef.current.object
  const target = controlsRef.current.target
  const direction = camera.position.clone().sub(target).normalize()
  camera.position.addScaledVector(direction, 0.5)
}

// Fit View (reset to initial)
const handleFitView = () => {
  const camera = controlsRef.current.object
  camera.position.set(0, 1.4, 3.6)
  controlsRef.current.target.set(0, 0, 0)
  controlsRef.current.update()
}
```

---

## 🎯 Common Patterns

### Pattern 1: First-time user hints
```jsx
const [showHints, setShowHints] = useState(false)

useEffect(() => {
  const shown = localStorage.getItem('3d-viewer-hints-shown')
  if (!shown) setShowHints(true)
}, [])

const dismiss = () => {
  localStorage.setItem('3d-viewer-hints-shown', 'true')
  setShowHints(false)
}

return showHints && <GestureHintsOverlay onDismiss={dismiss} />
```

### Pattern 2: Full control suite
```jsx
<div className="relative h-full w-full">
  <UrnViewer {...props} />
  <ZoomIndicator controlsRef={controlsRef} />
  <CameraResetButton onClick={reset} className="absolute bottom-4 right-4 z-20" />
  <ViewerControls {...handlers} className="absolute bottom-4 left-4 z-20" />
</div>
```

---

## 📝 Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `GestureHintsOverlay.jsx` | First-time hints | 51 |
| `ZoomIndicator.jsx` | Zoom level display | 46 |
| `CameraResetButton.jsx` | Reset button | 15 |
| `ViewerControls.jsx` | Control panel | 34 |
| `index.js` | Exports | 5 |
| `Example.jsx` | Integration demo | 95 |
| `README.md` | Documentation | - |

---

## ⚙️ Customization Tips

### Change auto-dismiss timing
```jsx
// In GestureHintsOverlay.jsx, line 11
setTimeout(() => { ... }, 4000)  // Change 4000 to desired ms
```

### Change zoom calculation
```jsx
// In ZoomIndicator.jsx, line 18
const initialDistance = 3.6  // Adjust base distance
const zoom = Math.round((initialDistance / distance) * 100)
```

### Modify z-index layers
- Hints overlay: `z-10`
- Controls: `z-20`
- Zoom indicator: `z-20`

---

## 🧪 Testing Checklist

- [ ] First-time hints appear on first load
- [ ] Hints dismiss after 4 seconds
- [ ] Hints dismiss on click/tap
- [ ] Zoom indicator shows on scroll
- [ ] Zoom percentage is accurate
- [ ] Reset button works
- [ ] Zoom in/out buttons work
- [ ] Fit view button works
- [ ] All tooltips show correctly
- [ ] Mobile touch works
- [ ] localStorage persists

---

## 🔗 See Full Details

- **Complete integration:** `Example.jsx`
- **Full documentation:** `README.md`
- **Implementation summary:** `VIEWER_ENHANCEMENTS_SUMMARY.md`

