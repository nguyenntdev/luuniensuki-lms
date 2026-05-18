# 3D Model Viewer Error Handling - Visual Reference

## Before & After

### BEFORE: Black Screen (No Feedback)
```
┌─────────────────────────────────┐
│ ← Back     [Urn Name]      AR  │
├─────────────────────────────────┤
│                                 │
│                                 │
│                                 │
│         [BLACK SCREEN]          │
│      (No error message)         │
│                                 │
│                                 │
│                                 │
├─────────────────────────────────┤
│ Progress: ▓▓▓░░░░░░░  3/10      │
└─────────────────────────────────┘
User thinks: "Is it loading? Is it broken? 😕"
```

### AFTER: Clear Error State with Actions
```
┌─────────────────────────────────┐
│ ← Back     [Urn Name]      AR  │
├─────────────────────────────────┤
│                                 │
│          ⚠️                      │
│      (Red Circle)               │
│                                 │
│  Không thể tải mô hình 3D       │
│                                 │
│  Đã xảy ra lỗi khi tải mô hình. │
│  Vui lòng kiểm tra kết nối mạng.│
│                                 │
│      [🔄 Thử lại]                │
│      [← Quay lại]                │
│                                 │
│  ┌────────────────────────────┐ │
│  │ Gợi ý khắc phục:           │ │
│  │ • Kiểm tra kết nối         │ │
│  │ • Thử WiFi/4G              │ │
│  │ • Khởi động lại app        │ │
│  └────────────────────────────┘ │
└─────────────────────────────────┘
User knows: "Ah, network issue. Let me retry! 👍"
```

### LOADING State (Enhanced - 10s timeout)
```
┌─────────────────────────────────┐
│ ← Back     [Urn Name]      AR  │
├─────────────────────────────────┤
│                                 │
│                                 │
│                                 │
│          ⏳                      │
│     (Spinning indicator)        │
│                                 │
│   Đang tải mô hình 3D...        │
│   Vui lòng chờ trong giây lát   │
│                                 │
│                                 │
│                                 │
└─────────────────────────────────┘
Timeout: 10 seconds (was 3s)
```

### SUCCESS State (Model Loaded)
```
┌─────────────────────────────────┐
│ ← Back     [Urn Name]      AR  │
├─────────────────────────────────┤
│                                 │
│         ╱╲                      │
│        ╱  ╲    ●               │
│       ╱    ╲  (hotspot)        │
│      ╱ URN  ╲                  │
│     ╱________╲  ●              │
│           (3D Model)            │
│                                 │
│        ● (hotspots)             │
├─────────────────────────────────┤
│ Progress: ▓▓▓▓▓▓▓▓▓▓  10/10    │
└─────────────────────────────────┘
User: "Perfect! I can interact! 🎉"
```

## Code Flow Diagram

### Model Loading Flow
```
┌──────────────────────────────────────────┐
│  User Opens Urn Viewer Screen           │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  initState()                             │
│  - Set _isLoading = true                 │
│  - Start 10s timeout timer               │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  ModelViewer Widget Loads                │
│  - Fetch model from URL                  │
│  - JavaScript event listeners setup      │
└──────────────┬───────────────────────────┘
               │
          ╔════╩════╗
          ║ Success ║
          ║    or   ║
          ║  Error? ║
          ╚════╦════╝
               │
     ┌─────────┴─────────┐
     │                   │
     ▼                   ▼
┌─────────┐         ┌─────────┐
│ SUCCESS │         │  ERROR  │
└────┬────┘         └────┬────┘
     │                   │
     ▼                   ▼
┌─────────────┐    ┌──────────────┐
│ JS 'load'   │    │ JS 'error'   │
│ event fires │    │ event fires  │
└─────┬───────┘    └──────┬───────┘
      │                   │
      ▼                   ▼
┌─────────────┐    ┌──────────────┐
│ Set         │    │ Set          │
│ _isLoading  │    │ _modelLoad   │
│ = false     │    │ Error = true │
└─────┬───────┘    └──────┬───────┘
      │                   │
      ▼                   ▼
┌─────────────┐    ┌──────────────┐
│ Show Model  │    │ Show Error   │
│ + Hotspots  │    │ Overlay with │
│             │    │ Retry button │
└─────────────┘    └──────────────┘
```

## Error States

### 1. Network Timeout (10s)
**Trigger:** Model doesn't load within 10 seconds
**Message:** "Mô hình tải quá lâu. Vui lòng kiểm tra kết nối mạng và thử lại."
**Icon:** ⚠️ Red circle with error outline

### 2. CORS Error (most common)
**Trigger:** Browser blocks model load due to missing CORS headers
**Message:** "Failed to load 3D model. Check network connection or CORS settings."
**Logged:** JavaScript console + Flutter debug print

### 3. Model Parse Error
**Trigger:** Invalid GLB/GLTF file
**Message:** "Không thể tải mô hình 3D"
**Details:** Captured from JS error event

## User Actions

### Retry Button Flow
```
User Taps "Thử lại"
       │
       ▼
Reset State:
- _isLoading = true
- _modelLoadError = false
- _errorMessage = null
       │
       ▼
Invalidate Provider
(Refetch urn data)
       │
       ▼
Restart 10s Timeout
       │
       ▼
ModelViewer Reloads
       │
   ╔═══╩═══╗
   ║Success║
   ║  or   ║
   ║ Error ║
   ╚═══════╝
```

## Debug Logging

### Console Output Examples

**Success:**
```
[URN_VIEWER] Loading model from: https://lms.histolab.icu/assets/models/URN-ABC.glb
[URN_VIEWER] Loading state: true, Error state: false
[MODEL_VIEWER] Loading progress: 0.5
[MODEL_VIEWER] Loading progress: 1.0
[MODEL_VIEWER] Model loaded successfully
```

**Error:**
```
[URN_VIEWER] Loading model from: https://lms.histolab.icu/assets/models/URN-XYZ.glb
[URN_VIEWER] Loading state: true, Error state: false
[MODEL_VIEWER] Error loading model: CORS policy blocked
[URN_VIEWER] Model loading timeout after 10 seconds
```

