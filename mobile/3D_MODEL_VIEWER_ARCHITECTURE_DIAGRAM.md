# 3D Model Viewer Fix - Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        3D MODEL VIEWER FIX                              │
│                     Complete Solution Overview                          │
└─────────────────────────────────────────────────────────────────────────┘

                              USER JOURNEY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────┐
│   USER TAP   │
│  Urn Card    │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│  UrnViewerScreen                     │
│  ─────────────────                   │
│  initState():                        │
│  - _isLoading = true                 │
│  - Start 10s timeout timer           │
│  - Load ModelViewer                  │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  LOADING STATE                       │
│  ═══════════════                     │
│  ⏳ Đang tải mô hình 3D...           │
│  Vui lòng chờ trong giây lát         │
└──────────────┬───────────────────────┘
               │
               ▼
       ┌───────┴────────┐
       │                │
       ▼                ▼
 ╔═══════════╗    ╔═══════════╗
 ║  SUCCESS  ║    ║   ERROR   ║
 ╚═══════════╝    ╚═══════════╝
       │                │
       │                │
       ▼                ▼
┌──────────┐    ┌─────────────────┐
│ 3D Model │    │  Error Overlay  │
│  Loaded  │    │  ⚠️ Message     │
│ Hotspots │    │  [Retry] [Back] │
│ Visible  │    │  Tips shown     │
└──────────┘    └────────┬────────┘
                         │
                         ▼
                   User taps Retry
                         │
                         └──────┐
                                │
                        (Loop back to Loading)


                        TECHNICAL ARCHITECTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────────┐
│                         MOBILE APP (Flutter)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  urn_viewer_screen.dart                                         │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  State Management                                      │     │
│  │  ─────────────────                                     │     │
│  │  • _isLoading: bool                                    │     │
│  │  • _modelLoadError: bool                               │     │
│  │  • _errorMessage: String?                              │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  ModelViewer Widget                                    │     │
│  │  ─────────────────────                                 │     │
│  │  src: urnDetail.urn.effectiveModelUrl                  │     │
│  │  innerModelViewerHtml: _generateHotspotHtml()          │     │
│  │  relatedJs: _generateHotspotJs()                       │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  JavaScript Event Handlers                             │     │
│  │  ────────────────────────────                          │     │
│  │  modelViewer.addEventListener('load', ...)             │     │
│  │  modelViewer.addEventListener('error', ...)            │     │
│  │  modelViewer.addEventListener('progress', ...)         │     │
│  │                                                         │     │
│  │  Communicates via:                                     │     │
│  │  window.flutter_inappwebview.callHandler(...)          │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ HTTPS Request
                     │ GET /assets/models/URN.glb
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NGINX SERVER (lms.histolab.icu)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  /etc/nginx/sites-enabled/nginx-lms-histolab.conf              │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  location ^~ /assets/models/ {                        │     │
│  │                                                         │     │
│  │    proxy_pass https://store.histolab.icu/;            │     │
│  │                                                         │     │
│  │    # Caching                                           │     │
│  │    expires 30d;                                        │     │
│  │    add_header Cache-Control "...";                    │     │
│  │                                                         │     │
│  │    # ✅ CORS FIX (ADD THIS)                            │     │
│  │    add_header 'Access-Control-Allow-Origin' '*';      │     │
│  │  }                                                      │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ Proxies to CDN
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CDN (store.histolab.icu)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  • Stores 3D model files (.glb)                                 │
│  • Serves models with high availability                         │
│  • CORS headers added by nginx proxy                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘


                          ERROR HANDLING FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCENARIO 1: CORS ERROR (No server fix yet)
────────────────────────────────────────────

Mobile App                        Server                  Browser
    │                               │                        │
    ├──GET /assets/models/URN.glb──→│                        │
    │                               ├─Response (no CORS)────→│
    │                               │                        ├─BLOCK!
    │                               │                        │
    │←──────────────────JavaScript 'error' event─────────────┤
    │                                                         │
    ├─Update State:                                          │
    │  _isLoading = false                                    │
    │  _modelLoadError = true                                │
    │  _errorMessage = "CORS error..."                       │
    │                                                         │
    ├─Show Error Overlay:                                    │
    │  ⚠️ Không thể tải mô hình 3D                           │
    │  [Retry Button]                                        │
    │  [Back Button]                                         │
    │  [Troubleshooting Tips]                                │
    │                                                         │
    └─User taps Retry ──┐                                    │
                        │                                    │
                    (Loop back to GET request)               │


SCENARIO 2: SUCCESS (With server fix)
────────────────────────────────────────────

Mobile App                        Server                  Browser
    │                               │                        │
    ├──GET /assets/models/URN.glb──→│                        │
    │                               ├─Response + CORS ───────→│
    │                               │  Header: Access-       │
    │                               │  Control-Allow-Origin  │
    │                               │                        ├─ALLOW!
    │                               │                        │
    │←──────────────────JavaScript 'load' event──────────────┤
    │                                                         │
    ├─Update State:                                          │
    │  _isLoading = false                                    │
    │  _modelLoadError = false                               │
    │                                                         │
    ├─Render 3D Model                                        │
    ├─Show Hotspots                                          │
    ├─Enable Interactions                                    │
    │                                                         │
    └─User interacts with model ✅                           │


                            STATE DIAGRAM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                        ┌─────────────┐
                        │   INITIAL   │
                        │  (Screen    │
                        │   Opens)    │
                        └──────┬──────┘
                               │
                               │ initState()
                               │ _isLoading = true
                               │ Start 10s timer
                               │
                               ▼
                        ┌─────────────┐
                        │   LOADING   │
                        │             │
                        │ Show spinner│
                        │ & message   │
                        └──────┬──────┘
                               │
                    ┌──────────┼──────────┐
                    │          │          │
         Model loads│          │10s       │Network/CORS
         successfully│          │timeout   │error
                    │          │          │
                    ▼          ▼          ▼
            ┌──────────┐ ┌────────┐ ┌─────────┐
            │ SUCCESS  │ │ TIMEOUT│ │  ERROR  │
            │          │ │        │ │         │
            │ Display  │ │ Show   │ │ Show    │
            │ 3D Model │ │ Error  │ │ Error   │
            └────┬─────┘ └───┬────┘ └────┬────┘
                 │           │           │
                 │           │           │
                 │       [Retry]     [Retry]
                 │           │           │
                 │           └───────────┘
                 │                  │
                 │                  │ Reset state
                 │                  └──────┐
                 │                         │
                 ▼                         ▼
            ┌──────────────────────────────────┐
            │         INTERACTIVE              │
            │  - Rotate model                  │
            │  - Zoom in/out                   │
            │  - Tap hotspots                  │
            │  - Discover motifs               │
            └──────────────────────────────────┘


                        COMPONENT HIERARCHY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UrnViewerScreen
│
├─ Scaffold
│  └─ Stack
│     ├─ ModelViewer (3D model)
│     │  ├─ HTML: Hotspot styling
│     │  └─ JS: Event handlers
│     │
│     ├─ IF _isLoading && !_modelLoadError
│     │  └─ _buildLoadingOverlay()
│     │     └─ Spinner + "Đang tải..."
│     │
│     ├─ IF _modelLoadError
│     │  └─ _buildModelErrorOverlay()
│     │     ├─ Error icon (⚠️)
│     │     ├─ Error message
│     │     ├─ Retry button
│     │     ├─ Back button
│     │     └─ Troubleshooting tips
│     │
│     ├─ TopBar
│     │  ├─ Back button
│     │  ├─ Urn name
│     │  ├─ AR button
│     │  ├─ Toggle hotspots
│     │  └─ Info button
│     │
│     ├─ IF !_isLoading && !_modelLoadError
│     │  └─ HotspotOverlay (for each motif)
│     │     └─ Positioned markers
│     │
│     ├─ BottomBar
│     │  ├─ Progress bar
│     │  └─ Stats (discovered, learned, mastered)
│     │
│     ├─ MotifSidebar (animated)
│     │  └─ Motif details when tapped
│     │
│     └─ DiscoveryAnimation (when unlocking)
```

