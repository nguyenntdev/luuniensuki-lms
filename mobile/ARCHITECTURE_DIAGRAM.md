# Architecture Overview - Custom Model Viewer

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Flutter Application                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         UrnViewerScreen (Stateful Widget)              │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  - Manages overall viewer state                        │ │
│  │  - Coordinates UI components                           │ │
│  │  - Handles user interactions                           │ │
│  └────────────┬───────────────────────────────────────────┘ │
│               │                                               │
│               │ Uses                                          │
│               ▼                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │      CustomModelViewer (Stateful Widget)               │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  Properties:                                           │ │
│  │   • modelUrl: String                                   │ │
│  │   • hotspots: List<Motif>                              │ │
│  │   • onModelLoaded: () => void                          │ │
│  │   • onModelError: (error) => void                      │ │
│  │   • onProgress: (progress) => void                     │ │
│  │   • onHotspotTap: (motifId) => void                    │ │
│  │                                                         │ │
│  │  Internal State:                                       │ │
│  │   • _isLoading: bool                                   │ │
│  │   • _errorMessage: String?                             │ │
│  │   • _loadProgress: double                              │ │
│  │   • _webViewController: InAppWebViewController?        │ │
│  └────────────┬───────────────────────────────────────────┘ │
│               │                                               │
│               │ Embeds                                        │
│               ▼                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           InAppWebView (from flutter_inappwebview)     │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  - Loads HTML with model-viewer component              │ │
│  │  - Manages JavaScript execution context                │ │
│  │  - Bridges JS ↔ Dart communication                     │ │
│  └────────────┬───────────────────────────────────────────┘ │
└───────────────┼───────────────────────────────────────────────┘
                │
                │ Renders
                ▼
┌─────────────────────────────────────────────────────────────┐
│                    HTML Content                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  <!DOCTYPE html>                                              │
│  <html>                                                       │
│  <head>                                                       │
│    <script type="module"                                      │
│      src="https://unpkg.com/@google/model-viewer/...">       │
│    </script>                                                  │
│  </head>                                                      │
│  <body>                                                       │
│    <model-viewer src="..." camera-orbit="...">               │
│      <!-- Hotspot buttons -->                                │
│    </model-viewer>                                            │
│    <script>                                                   │
│      // Event listeners                                       │
│      // JavaScript handlers                                   │
│    </script>                                                  │
│  </body>                                                      │
│  </html>                                                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Model Load Flow
```
User Opens Viewer
        │
        ▼
UrnViewerScreen._build3DViewer()
        │
        ▼
CustomModelViewer(modelUrl, hotspots, callbacks)
        │
        ▼
_generateHtml() → Creates HTML string
        │
        ▼
InAppWebView loads HTML
        │
        ▼
<model-viewer> starts loading GLB
        │
        ├─→ progress event → JS: onProgress handler
        │                     │
        │                     ▼
        │                window.flutter_inappwebview.callHandler('onProgress', {progress})
        │                     │
        │                     ▼
        │                Dart: onProgress callback
        │                     │
        │                     ▼
        │                Flutter: Update UI (_loadProgress)
        │
        ├─→ load event → JS: onLoad handler
        │                │
        │                ▼
        │           window.flutter_inappwebview.callHandler('onModelLoad', {success: true})
        │                │
        │                ▼
        │           Dart: onModelLoad callback
        │                │
        │                ▼
        │           Flutter: setState({_isLoading: false})
        │
        └─→ error event → JS: onError handler
                         │
                         ▼
                    window.flutter_inappwebview.callHandler('onModelError', {error})
                         │
                         ▼
                    Dart: onModelError callback
                         │
                         ▼
                    Flutter: setState({_errorMessage: error})
```

### 2. Hotspot Tap Flow
```
User Taps Hotspot
        │
        ▼
HTML: <button class="hotspot" onclick="...">
        │
        ▼
JavaScript: click event listener
        │
        ▼
Extract motifId from data-motif-id attribute
        │
        ▼
window.flutter_inappwebview.callHandler('onHotspotTap', {motifId})
        │
        ▼
Dart: onHotspotTap callback in CustomModelViewer
        │
        ▼
widget.onHotspotTap?.call(motifId)
        │
        ▼
UrnViewerScreen._handleHotspotTap(motif)
        │
        ▼
Show motif details / trigger discovery
```

## Component Responsibilities

### UrnViewerScreen
**Responsibilities:**
- Fetch urn data and motifs
- Manage overall screen state
- Handle hotspot selection
- Show motif sidebar
- Manage discovery animations
- Coordinate UI overlays

**Does NOT:**
- Generate HTML
- Manage WebView
- Handle JavaScript communication

### CustomModelViewer
**Responsibilities:**
- Generate HTML with model-viewer component
- Create hotspot buttons with correct positions
- Register JavaScript handlers
- Manage loading/error states
- Display loading/error overlays
- Bridge JS events to Dart callbacks

**Does NOT:**
- Fetch model data
- Handle motif business logic
- Show discovery animations
- Manage navigation

### InAppWebView
**Responsibilities:**
- Render HTML content
- Execute JavaScript
- Provide JS ↔ Dart bridge
- Manage WebView lifecycle

**Does NOT:**
- Generate HTML
- Business logic
- UI state management

## JavaScript Handler Registration

```dart
// In CustomModelViewer._registerJavaScriptHandlers()

controller.addJavaScriptHandler(
  handlerName: 'onModelLoad',
  callback: (args) {
    // Dart callback
    widget.onModelLoaded?.call();
  },
);

controller.addJavaScriptHandler(
  handlerName: 'onModelError',
  callback: (args) {
    // Dart callback
    final error = args[0]['error'];
    widget.onModelError?.call(error);
  },
);

controller.addJavaScriptHandler(
  handlerName: 'onProgress',
  callback: (args) {
    // Dart callback
    final progress = args[0]['progress'];
    widget.onProgress?.call(progress);
  },
);

controller.addJavaScriptHandler(
  handlerName: 'onHotspotTap',
  callback: (args) {
    // Dart callback
    final motifId = args[0]['motifId'];
    widget.onHotspotTap?.call(motifId);
  },
);
```

## State Management

### Loading State
```
Initial: _isLoading = true, _errorMessage = null
   │
   ├─→ Success: _isLoading = false, _errorMessage = null
   │              (Show 3D model)
   │
   └─→ Error:   _isLoading = false, _errorMessage = "..."
                (Show error overlay)
```

### Progress State
```
0% → 25% → 50% → 75% → 100%
│     │     │     │      │
└─────┴─────┴─────┴──────┘
         Updates UI
```

## Error Handling Flow

```
Model Load Error
        │
        ▼
JavaScript catches error event
        │
        ▼
Call onModelError handler with error details
        │
        ▼
Dart receives error
        │
        ▼
setState({_errorMessage: error, _isLoading: false})
        │
        ▼
UI shows error overlay
        │
        ▼
User taps "Retry" button
        │
        ▼
_webViewController.reload()
        │
        ▼
Back to Model Load Flow
```

## Memory Management

```
Widget Created
        │
        ▼
initState() - Initialize state
        │
        ▼
build() - Create InAppWebView
        │
        ▼
onWebViewCreated() - Store controller, register handlers
        │
        ▼
... Widget in use ...
        │
        ▼
dispose() - Clean up
        │
        ├─→ _webViewController?.dispose()
        └─→ Clear callbacks
```

## Key Design Patterns

1. **Widget Composition**
   - CustomModelViewer is a self-contained component
   - Can be reused in different screens
   - Clear input/output interface

2. **Callback Pattern**
   - Events communicated via callbacks
   - Loose coupling between components
   - Easy to test

3. **State Management**
   - Local state in StatefulWidget
   - No global state dependencies
   - Simple and predictable

4. **Bridge Pattern**
   - JavaScript ↔ Dart communication
   - Abstracts WebView complexity
   - Type-safe interface

## Dependencies Graph

```
CustomModelViewer
    │
    ├─→ flutter (framework)
    ├─→ flutter_inappwebview (WebView)
    ├─→ AppColors (theme)
    └─→ Motif (entity)

UrnViewerScreen
    │
    ├─→ CustomModelViewer (widget)
    ├─→ HotspotOverlay (widget) [optional]
    ├─→ MotifSidebar (widget)
    └─→ DiscoveryAnimation (widget)
```

## Performance Considerations

1. **HTML Generation**
   - Generated once per build
   - Cached in memory
   - No unnecessary regeneration

2. **JavaScript Handlers**
   - Registered once on WebView creation
   - No repeated registrations
   - Proper cleanup on dispose

3. **State Updates**
   - Only update when values change
   - Batch related updates
   - Avoid unnecessary rebuilds

4. **Memory**
   - WebView disposed properly
   - No memory leaks
   - Handlers cleaned up

