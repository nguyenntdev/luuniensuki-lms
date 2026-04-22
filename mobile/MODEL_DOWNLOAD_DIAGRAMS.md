# Model Download System - Architecture Diagrams

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐        ┌──────────────────────────────┐      │
│  │ UrnViewerScreen  │        │  ModelDownloadProgress      │      │
│  │                  │───────▶│                              │      │
│  │ - Shows 3D Model │        │ - Progress UI                │      │
│  │ - Handles State  │        │ - Cancel/Retry buttons       │      │
│  └────────┬─────────┘        └──────────────────────────────┘      │
│           │                                                         │
│           │ ref.watch(modelDownloadNotifierProvider)               │
│           ▼                                                         │
├─────────────────────────────────────────────────────────────────────┤
│                      STATE MANAGEMENT LAYER                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────────────────────────────────────┐        │
│  │         ModelDownloadNotifier (Riverpod)               │        │
│  │                                                         │        │
│  │  State:                        Methods:                │        │
│  │  • ModelDownloadState          • downloadModel()       │        │
│  │  • progress (0.0 - 1.0)        • cancelDownload()      │        │
│  │  • localPath                   • retry()               │        │
│  │  • error                       • _checkCache()         │        │
│  └────────────────────┬───────────────────────────────────┘        │
│                       │                                             │
│                       │ uses                                        │
│                       ▼                                             │
├─────────────────────────────────────────────────────────────────────┤
│                         SERVICE LAYER                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │         ModelPreloader (Singleton)                      │       │
│  │                                                          │       │
│  │  Private:                      Public Methods:          │       │
│  │  • Dio _dio                    • getModelPath()         │       │
│  │  • Map<String, CancelToken>    • isCached()             │       │
│  │  • Map<String, double>         • preloadModels()        │       │
│  │                                • cancelDownload()       │       │
│  │  Helpers:                      • clearCache()           │       │
│  │  • _getCacheKey() (SHA256)     • getCacheSize()         │       │
│  │  • _getCachedFile()                                     │       │
│  │  • _formatBytes()                                       │       │
│  └────────┬──────────────────────┬────────────────────────┘       │
│           │                      │                                 │
│           │                      │                                 │
├───────────┼──────────────────────┼─────────────────────────────────┤
│           │                      │         EXTERNAL LAYER          │
├───────────┼──────────────────────┼─────────────────────────────────┤
│           ▼                      ▼                                 │
│  ┌──────────────┐      ┌──────────────────┐                       │
│  │ path_provider│      │       Dio        │                       │
│  │              │      │                  │                       │
│  │ • App Docs   │      │ • HTTP Download  │                       │
│  │   Directory  │      │ • Progress       │                       │
│  │ • Cache Dir  │      │ • Cancellation   │                       │
│  └──────────────┘      └──────────────────┘                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
User Taps Screen
       │
       ▼
┌─────────────────┐
│ Widget builds   │
│ with ref.watch  │
└────────┬────────┘
         │
         ▼
┌──────────────────────┐      ┌─────────────┐
│ Check download state │─────▶│ Is Cached?  │
└──────────────────────┘      └──────┬──────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
              ┌─────────┐      ┌─────────┐     ┌──────────┐
              │  YES    │      │   NO    │     │  ERROR   │
              │ CACHED  │      │  IDLE   │     │          │
              └────┬────┘      └────┬────┘     └────┬─────┘
                   │                │                │
                   │                │                │
                   ▼                ▼                ▼
           ┌──────────────┐  ┌──────────────┐  ┌──────────┐
           │ Show Model   │  │ Show Download│  │  Show    │
           │ Instantly    │  │    Button    │  │  Retry   │
           └──────────────┘  └──────┬───────┘  └────┬─────┘
                                    │                │
                         User Taps  │                │ User Taps
                                    ▼                ▼
                           ┌─────────────────────────────┐
                           │ downloadModel() called      │
                           └──────────────┬──────────────┘
                                          │
                                          ▼
                           ┌─────────────────────────────┐
                           │ ModelPreloader.getModelPath │
                           └──────────────┬──────────────┘
                                          │
                                          ▼
                           ┌─────────────────────────────┐
                           │ Dio.download() with progress│
                           └──────────────┬──────────────┘
                                          │
                   ┌──────────────────────┼──────────────────────┐
                   │                      │                      │
                   ▼                      ▼                      ▼
            ┌──────────┐          ┌──────────┐          ┌──────────┐
            │ Progress │          │ Complete │          │  Error   │
            │ Callback │          │          │          │          │
            └─────┬────┘          └─────┬────┘          └─────┬────┘
                  │                     │                      │
                  ▼                     ▼                      ▼
         ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
         │ Update State │      │ Save to Cache│      │ Show Error   │
         │ progress %   │      │ Return Path  │      │ UI           │
         └──────────────┘      └──────────────┘      └──────────────┘
```

## State Transition Diagram

```
                    ┌──────────────────────────────────┐
                    │    INITIAL LOAD                  │
                    │                                  │
                    │  Build → _checkCache()           │
                    └────────────┬─────────────────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   │                           │
                   ▼                           ▼
            ┌──────────┐                ┌──────────┐
            │  CACHED  │                │   IDLE   │
            └────┬─────┘                └─────┬────┘
                 │                            │
                 │                            │ downloadModel()
                 │                            ▼
                 │                      ┌────────────┐
                 │                      │DOWNLOADING │◄──┐
                 │                      └──────┬─────┘   │
                 │                             │         │
                 │              ┌──────────────┼─────────┘
                 │              │              │         retry()
                 │              │              │
                 │       cancelDownload()      │
                 │              │              │
                 │              ▼              │
                 │         ┌────────┐   ┌──────────┐
                 │         │  IDLE  │   │COMPLETED │
                 │         └────────┘   └────┬─────┘
                 │              ▲             │
                 │              │             │
                 │              │             ▼
                 │              │      ┌──────────┐
                 │              │      │  CACHED  │
                 │              │      └──────────┘
                 │              │
                 │         ┌────┴────┐
                 └────────▶│  ERROR  │
                           └─────────┘
```

## Cache Directory Structure

```
{Application Documents Directory}
│
└── model_cache/
    │
    ├── a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.glb    (SHA256 hash of URL 1)
    │   └── Size: 78.5 MB
    │
    ├── q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2.glb    (SHA256 hash of URL 2)
    │   └── Size: 65.2 MB
    │
    └── g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8.gltf   (SHA256 hash of URL 3)
        └── Size: 72.1 MB

Total Cache Size: 215.8 MB
```

## Component Interaction Sequence

```
UrnViewerScreen          ModelDownloadNotifier       ModelPreloader           Dio
      │                           │                         │                  │
      │  watch(provider)          │                         │                  │
      ├──────────────────────────▶│                         │                  │
      │                           │                         │                  │
      │                           │  isCached(url)?         │                  │
      │                           ├────────────────────────▶│                  │
      │                           │                         │                  │
      │                           │  ◄── false ─────────────┤                  │
      │                           │                         │                  │
      │  ModelDownloadInfo        │                         │                  │
      │  (state: idle)            │                         │                  │
      │◄──────────────────────────┤                         │                  │
      │                           │                         │                  │
      │  Show Download Button     │                         │                  │
      │                           │                         │                  │
      │  User Taps                │                         │                  │
      │  downloadModel()          │                         │                  │
      ├──────────────────────────▶│                         │                  │
      │                           │                         │                  │
      │                           │  getModelPath(url)      │                  │
      │                           ├────────────────────────▶│                  │
      │                           │                         │                  │
      │                           │                         │  download(url)   │
      │                           │                         ├─────────────────▶│
      │                           │                         │                  │
      │                           │                         │  Progress: 25%   │
      │                           │  onProgress(0.25)       │◄─────────────────┤
      │                           │◄────────────────────────┤                  │
      │  ModelDownloadInfo        │                         │                  │
      │  (progress: 0.25)         │                         │                  │
      │◄──────────────────────────┤                         │                  │
      │                           │                         │                  │
      │  Update UI (25%)          │                         │  Progress: 100%  │
      │                           │  onProgress(1.0)        │◄─────────────────┤
      │                           │◄────────────────────────┤                  │
      │                           │                         │                  │
      │                           │  localPath              │                  │
      │                           │◄────────────────────────┤                  │
      │                           │                         │                  │
      │  ModelDownloadInfo        │                         │                  │
      │  (state: completed,       │                         │                  │
      │   localPath: "/...")      │                         │                  │
      │◄──────────────────────────┤                         │                  │
      │                           │                         │                  │
      │  Show ModelViewer         │                         │                  │
      │  with local path          │                         │                  │
      │                           │                         │                  │
```

## File Size Progression

```
Download Progress Over Time (80 MB model on 10 Mbps connection)

  80 MB │                                        ▓▓▓▓▓
        │                                  ▓▓▓▓▓▓
  60 MB │                             ▓▓▓▓▓
        │                        ▓▓▓▓▓
  40 MB │                   ▓▓▓▓▓
        │              ▓▓▓▓▓
  20 MB │         ▓▓▓▓▓
        │    ▓▓▓▓▓
   0 MB │▓▓▓▓
        └───────────────────────────────────────────▶
        0s  10s  20s  30s  40s  50s  60s  70s

Legend:
▓ Downloaded data
Timeline shows typical download on 10 Mbps connection
```

## Memory Usage During Download

```
Memory Footprint

High │
     │
     │                        ┌─── Peak during model render
     │                        │
Med  │        ┌──────────────┐│
     │        │   Streaming  ││  Model in GPU
     │        │   Download   ││  Memory
Low  │───────┐│              │└──────────────
     │  Idle ││              │
     └───────┴┴──────────────┴───────────────▶
            Start         Download    Render
           Download       Complete    Complete

Note: Streaming download keeps memory usage minimal
Only small chunks (8KB) buffered at a time
```

