# 3D Viewer Enhancements

Mobile-friendly enhancement components for the 3D viewer.

## Components

### 1. GestureHintsOverlay
First-time user hints that auto-dismiss after 4 seconds or on user interaction.

**Props:**
- `onDismiss?: () => void` - Callback when hints are dismissed

**Features:**
- Auto-dismisses after 4 seconds
- Dismisses on mousedown/touchstart
- Shows drag-to-rotate and scroll-to-zoom hints
- Vietnamese text labels

**Example:**
```jsx
<GestureHintsOverlay onDismiss={() => console.log('Dismissed')} />
```

---

### 2. ZoomIndicator
Displays current zoom level as a percentage when user zooms.

**Props:**
- `controlsRef: RefObject` - Reference to OrbitControls

**Features:**
- Auto-shows on zoom change
- Auto-hides after 1.5 seconds
- Calculates zoom based on camera distance
- Displays 10-500% range

**Example:**
```jsx
const controlsRef = useRef()
<ZoomIndicator controlsRef={controlsRef} />
```

---

### 3. CameraResetButton
Button to reset camera to initial position.

**Props:**
- `onClick: () => void` - Click handler
- `className?: string` - Additional CSS classes

**Features:**
- Circular button with reset icon
- Tooltip: "Đặt lại góc nhìn"
- White background with backdrop blur

**Example:**
```jsx
<CameraResetButton onClick={handleReset} className="absolute bottom-4 right-4" />
```

---

### 4. ViewerControls
Control panel with zoom and fit view buttons.

**Props:**
- `onZoomIn: () => void` - Zoom in handler
- `onZoomOut: () => void` - Zoom out handler
- `onFitView: () => void` - Fit view handler
- `className?: string` - Additional CSS classes

**Features:**
- Vertical button stack
- Zoom in, zoom out, fit view controls
- Accessible with aria-labels
- Vietnamese tooltips

**Example:**
```jsx
<ViewerControls
  onZoomIn={handleZoomIn}
  onZoomOut={handleZoomOut}
  onFitView={handleFitView}
  className="absolute bottom-4 left-4"
/>
```

---

## Integration Example

See `Example.jsx` for full integration with localStorage tracking:

```jsx
import { GestureHintsOverlay, ZoomIndicator, CameraResetButton, ViewerControls } from '@/components/viewer'

// Check localStorage for first-time hints
const hasSeenHints = localStorage.getItem('3d-viewer-hints-shown')
if (!hasSeenHints) {
  setShowHints(true)
}

// Dismiss handler
const handleDismiss = () => {
  localStorage.setItem('3d-viewer-hints-shown', 'true')
  setShowHints(false)
}
```

---

## Styling

All components use:
- Tailwind CSS utility classes
- `backdrop-blur` for glass morphism effect
- `lucide-react` icons
- Responsive design patterns from existing codebase

---

## LocalStorage Keys

- `3d-viewer-hints-shown` - Tracks if gesture hints have been shown

---

## Dependencies

- `react` - useState, useEffect, useRef, useCallback
- `lucide-react` - Icons (MousePointer2, ZoomIn, ZoomOut, RotateCcw, Maximize2)
- `tailwindcss` - Styling

