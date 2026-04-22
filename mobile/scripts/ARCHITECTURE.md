# 🗺️ Architecture & Workflow Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Model Compression Solution                    │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
        ┌───────▼────────┐            ┌────────▼────────┐
        │   User Layer   │            │  Server Layer   │
        └───────┬────────┘            └────────┬────────┘
                │                               │
    ┌───────────┴──────────┐        ┌──────────┴─────────┐
    │                      │        │                    │
┌───▼────┐         ┌──────▼──┐  ┌──▼────┐      ┌───────▼─────┐
│ Shell  │         │  Node   │  │Deploy │      │   Models    │
│Wrapper │◄────────┤ Script  │  │Script │─────►│  Storage    │
└────────┘         └─────────┘  └───────┘      └─────────────┘
    │                   │            │
    │              ┌────▼────┐       │
    │              │ gltf-   │       │
    │              │pipeline │       │
    │              └────┬────┘       │
    │                   │            │
    │              ┌────▼────┐       │
    │              │  Draco  │       │
    │              │Compress │       │
    │              └─────────┘       │
    │                                │
    └────────────────┬───────────────┘
                     │
              ┌──────▼──────┐
              │   Output    │
              │ Compressed  │
              │   Models    │
              └─────────────┘
```

## Compression Workflow

```
START
  │
  ├─► 1. User runs script
  │      └─► ./compress-models.sh
  │
  ├─► 2. Check prerequisites
  │      ├─► Node.js installed? ──No──► Exit with error
  │      ├─► npm installed?     ──No──► Exit with error
  │      └─► Yes ──────────────────────► Continue
  │
  ├─► 3. Install dependencies
  │      ├─► Check if installed
  │      ├─► If not: npm install gltf-pipeline
  │      ├─► If not: npm install fs-extra
  │      └─► Verify installation
  │
  ├─► 4. Validate directories
  │      ├─► Input directory exists? ──No──► Exit with error
  │      ├─► Has GLB files?          ──No──► Exit (nothing to do)
  │      └─► Yes ───────────────────────────► Continue
  │
  ├─► 5. FOR EACH GLB file:
  │      │
  │      ├─► Read GLB file
  │      ├─► Get original size
  │      │
  │      ├─► Process with gltf-pipeline
  │      │      ├─► Apply Draco compression
  │      │      ├─► Compression level: 7
  │      │      ├─► Quantize geometry
  │      │      └─► Optimize meshes
  │      │
  │      ├─► Write compressed file
  │      ├─► Get compressed size
  │      ├─► Calculate reduction %
  │      └─► Display progress
  │
  ├─► 6. Generate statistics
  │      ├─► Total files processed
  │      ├─► Total original size
  │      ├─► Total compressed size
  │      ├─► Overall reduction %
  │      └─► Processing time
  │
  └─► 7. Display summary & EXIT
```

## File Processing Pipeline

```
Input: model.glb (75 MB)
         │
         ├─► Read binary data
         │      └─► Buffer in memory
         │
         ├─► Parse glTF structure
         │      ├─► Extract meshes
         │      ├─► Extract materials
         │      └─► Extract textures
         │
         ├─► Apply Draco compression
         │      ├─► Compress vertex positions
         │      ├─► Compress normals
         │      ├─► Compress texture coords
         │      └─► Compress indices
         │
         ├─► Quantize attributes
         │      ├─► Position: 14 bits
         │      ├─► Normals: 10 bits
         │      └─► TexCoords: 12 bits
         │
         ├─► Rebuild glTF binary
         │      ├─► Update headers
         │      ├─► Update chunk sizes
         │      └─► Embed compressed data
         │
         └─► Write output
                └─► model.compressed.glb (36 MB)

Result: 52% size reduction
```

## Deployment Workflow

```
Local Development
      │
      ├─► 1. Compress models locally
      │      └─► ./compress-models.sh
      │
      ├─► 2. Test compressed models
      │      ├─► Load in app
      │      ├─► Verify quality
      │      └─► Measure performance
      │
      ├─► 3. Run deployment script
      │      └─► ./deploy-compressed-models.sh
      │            │
      │            ├─► Connect to server (SSH)
      │            │
      │            ├─► Create backup
      │            │      └─► models.backup.20250113_1234/
      │            │
      │            ├─► Upload compressed files
      │            │      └─► /tmp/models.temp.xyz/
      │            │
      │            ├─► User choice:
      │            │      ├─► Keep .compressed suffix
      │            │      └─► Replace originals
      │            │
      │            └─► Move files to production
      │                   └─► /srv/assets/models/
      │
      └─► 4. Production ready
             └─► App uses compressed models
```

## Component Interaction

```
┌──────────────────────────────────────────────────────────────┐
│                         compress-models.sh                    │
│  ┌────────────────────────────────────────────────────┐      │
│  │ 1. Check Node.js/npm                               │      │
│  │ 2. Install dependencies                            │      │
│  │ 3. Validate directories                            │      │
│  │ 4. Execute Node.js script ──────────┐             │      │
│  └─────────────────────────────────────│─────────────┘      │
└────────────────────────────────────────│──────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────┐
│                       compress-models.js                      │
│  ┌────────────────────────────────────────────────────┐      │
│  │ Import: gltf-pipeline, fs-extra                    │      │
│  │                                                     │      │
│  │ Configuration:                                      │      │
│  │   ├─► Draco options                                │      │
│  │   ├─► Input/output paths                           │      │
│  │   └─► Compression settings                         │      │
│  │                                                     │      │
│  │ Main Process:                                       │      │
│  │   ├─► getGLBFiles(dir) ────────────┐              │      │
│  │   │                                 │              │      │
│  │   ├─► For each file:                │              │      │
│  │   │     └─► compressModel(path) ────┼──────┐      │      │
│  │   │                                 │      │      │      │
│  │   └─► Generate statistics          │      │      │      │
│  └─────────────────────────────────────│──────│──────┘      │
└────────────────────────────────────────│──────│──────────────┘
                                         │      │
                            ┌────────────┘      └────────────┐
                            ▼                                 ▼
                ┌───────────────────┐             ┌──────────────────┐
                │  fs-extra         │             │  gltf-pipeline   │
                │  ┌─────────────┐  │             │  ┌────────────┐  │
                │  │ readdir()   │  │             │  │processGlb()│  │
                │  │ readFile()  │  │             │  │    with    │  │
                │  │ writeFile() │  │             │  │   Draco    │  │
                │  │ ensureDir() │  │             │  └────────────┘  │
                │  └─────────────┘  │             └──────────────────┘
                └───────────────────┘
```

## Data Flow

```
User Input
    │
    └─► Input Directory: /path/to/models/
           │
           ├─► CAO-DINH-v1.glb (75 MB)
           ├─► CHUONG-DINH-v1.glb (72 MB)
           └─► NGHI-DINH-v1.glb (70 MB)
                  │
                  ▼
            Compression Engine
                  │
        ┌─────────┼─────────┐
        │         │         │
        ▼         ▼         ▼
    Process   Process   Process
     File 1    File 2    File 3
        │         │         │
        └─────────┼─────────┘
                  │
                  ▼
        Output Directory: /path/to/output/
           │
           ├─► CAO-DINH-v1.compressed.glb (36 MB) ↓52%
           ├─► CHUONG-DINH-v1.compressed.glb (35 MB) ↓51%
           └─► NGHI-DINH-v1.compressed.glb (34 MB) ↓51%
                  │
                  ▼
            Statistics Report
           ┌──────────────────┐
           │ Total: 217 MB    │
           │ From:  217 MB    │
           │ Saved: 108 MB    │
           │ Ratio: 49.8%     │
           └──────────────────┘
```

## Error Handling Flow

```
Error Occurs
    │
    ├─► File Read Error
    │      └─► Log error → Skip file → Continue
    │
    ├─► Compression Error
    │      └─► Log error → Mark failed → Continue
    │
    ├─► Write Error
    │      └─► Log error → Mark failed → Continue
    │
    ├─► Directory Error
    │      └─► Show error → Exit gracefully
    │
    └─► Dependency Error
           └─► Show install instructions → Exit

All Errors Logged
    │
    ├─► Display in summary
    ├─► Set exit code (1 if errors)
    └─► Provide troubleshooting info
```

## Module Dependencies

```
compress-models.js
    │
    ├─► Requires: gltf-pipeline
    │      └─► Provides: processGlb()
    │             └─► Uses: Draco encoder
    │
    ├─► Requires: fs-extra
    │      ├─► readdir()
    │      ├─► readFile()
    │      ├─► writeFile()
    │      └─► ensureDir()
    │
    └─► Requires: Node.js built-ins
           ├─► path
           ├─► perf_hooks
           └─► require
```

## Configuration Hierarchy

```
Default Settings
    │
    ├─► compressionLevel: 7
    ├─► quantizePositionBits: 14
    ├─► quantizeNormalBits: 10
    ├─► quantizeTexcoordBits: 12
    └─► outputSuffix: '.compressed'
         │
         ├─► Can be overridden in CONFIG object
         │      └─► Edit compress-models.js
         │
         └─► Or via command line
                └─► Input/output directories
```

---

This architecture ensures:
- ✅ **Modularity**: Each component has a single responsibility
- ✅ **Flexibility**: Easy to configure and customize
- ✅ **Reliability**: Comprehensive error handling
- ✅ **Scalability**: Can process any number of files
- ✅ **Maintainability**: Clear structure and flow

