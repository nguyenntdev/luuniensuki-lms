# Shimmer Component Structure Diagram

## Component Hierarchy

```
shimmer/
├── shimmer_skeleton.dart    (Main implementation)
├── index.dart              (Exports)
├── README.md               (Documentation)
├── EXAMPLES.dart           (Code examples)
└── [Future components...]
```

## ShimmerSkeleton (Base)

```
┌─────────────────────────────────────┐
│  ShimmerSkeleton                    │
│  ┌───────────────────────────────┐  │
│  │ Shimmer.fromColors            │  │
│  │   baseColor: surface          │  │
│  │   highlightColor: surfaceElev │  │
│  │   ┌─────────────────────────┐ │  │
│  │   │ Container               │ │  │
│  │   │  - width                │ │  │
│  │   │  - height               │ │  │
│  │   │  - borderRadius         │ │  │
│  │   │  - margin               │ │  │
│  │   └─────────────────────────┘ │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘

Props:
  • width: double?
  • height: double?
  • borderRadius: BorderRadius?
  • margin: EdgeInsetsGeometry?
```

## ShimmerUrnCard

```
┌──────────────────────────────────────────┐
│  Glass Container (radiusLG)              │
│  gradient: white 0.12 → 0.06             │
│  border: white 0.2, 1.5px                │
│  ┌────────────────────────────────────┐  │
│  │  Thumbnail Area (flex: 3)          │  │
│  │  ┌──────────────────────────────┐  │  │
│  │  │ Shimmer (surface → elevated) │  │  │
│  │  └──────────────────────────────┘  │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  Content Area (flex: 2)            │  │
│  │  gradient: black 0.4 → 0.7         │  │
│  │  padding: md                       │  │
│  │  ┌──────────────────────────────┐  │  │
│  │  │ Title (20h, full width)      │  │  │
│  │  ├──────────────────────────────┤  │  │
│  │  │ Subtitle (14h, 120w)         │  │  │
│  │  ├──────────────────────────────┤  │  │
│  │  │ Progress Bar (6h, full)      │  │  │
│  │  └──────────────────────────────┘  │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘

Layout:
  Column (crossAxisStretch)
    ├─ Thumbnail (Expanded flex: 3)
    └─ Content (Expanded flex: 2)
       ├─ Title shimmer
       ├─ Subtitle shimmer
       └─ Progress bar shimmer
```

## ShimmerMotifCard

```
┌──────────────────────────────────────┐
│  Glass Container (radiusLG)          │
│  gradient: white 0.12 → 0.06         │
│  border: white 0.2, 1.5px            │
│  padding: 12                         │
│  ┌────────────────────────────────┐  │
│  │  Thumbnail (Expanded)          │  │
│  │  ┌──────────────────────────┐  │  │
│  │  │ ShimmerSkeleton          │  │  │
│  │  │ (full size)              │  │  │
│  │  └──────────────────────────┘  │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │ Name (16h, full width)         │  │
│  └────────────────────────────────┘  │
│  ┌─────────────┬─────────────────┐  │
│  │ Badge 1     │ Badge 2         │  │
│  │ (60w, 20h)  │ (50w, 20h)      │  │
│  └─────────────┴─────────────────┘  │
└──────────────────────────────────────┘

Layout:
  Column
    ├─ Thumbnail shimmer (Expanded)
    ├─ SizedBox(12)
    ├─ Name shimmer
    ├─ SizedBox(8)
    └─ Row
       ├─ Badge shimmer 1
       ├─ SizedBox(8)
       └─ Badge shimmer 2
```

## ShimmerListItem

```
┌─────────────────────────────────────────────────┐
│  Glass Container (radiusMD, height: 70)         │
│  gradient: white 0.12 → 0.06                    │
│  border: white 0.2, 1.5px                       │
│  padding: md, margin: md horizontal, xs vertical│
│  ┌─────────────────────────────────────────────┐│
│  │ Row                                         ││
│  │ ┌────┐  ┌──────────────────────┐  ┌────┐  ││
│  │ │Icon│  │ Column               │  │Icon│  ││
│  │ │50x │  │ ┌──────────────────┐ │  │24x │  ││
│  │ │50  │  │ │Title (16h, full) │ │  │24  │  ││
│  │ │    │  │ ├──────────────────┤ │  │    │  ││
│  │ │    │  │ │Subtitle (12h,150)│ │  │    │  ││
│  │ │    │  │ └──────────────────┘ │  │    │  ││
│  │ └────┘  └──────────────────────┘  └────┘  ││
│  └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘

Layout:
  Row
    ├─ Leading shimmer (50x50) [if showLeading]
    ├─ SizedBox(md)
    ├─ Column (Expanded)
    │  ├─ Title shimmer (16h, full width)
    │  ├─ SizedBox(sm)
    │  └─ Subtitle shimmer (12h, 150w)
    ├─ SizedBox(md)
    └─ Trailing shimmer (24x24) [if showTrailing]
```

## Color Scheme

```
Dark Theme Colors:
┌────────────────────────────────────┐
│ Base Color (surface)               │
│ #1A1A2E                           │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   │
└────────────────────────────────────┘
         ↓ shimmer animation ↓
┌────────────────────────────────────┐
│ Highlight Color (surfaceElevated)  │
│ #252543                           │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   │
└────────────────────────────────────┘

Glass Effect:
┌────────────────────────────────────┐
│ Gradient Background                │
│ white.withOpacity(0.12) ┐         │
│                         ↓         │
│ white.withOpacity(0.06) ┘         │
└────────────────────────────────────┘
```

## Usage Flow

```
Screen Loading State
        ↓
   isLoading && !hasData
        ↓
┌─────────────────────┐
│ _buildLoadingState()│
└─────────────────────┘
        ↓
   GridView.builder
        ↓
   ┌──────────┬──────────┐
   │ Shimmer  │ Shimmer  │
   │  Card    │  Card    │
   ├──────────┼──────────┤
   │ Shimmer  │ Shimmer  │
   │  Card    │  Card    │
   └──────────┴──────────┘
        ↓
   Data Loaded
        ↓
   ┌──────────┬──────────┐
   │  Real    │  Real    │
   │  Card    │  Card    │
   ├──────────┼──────────┤
   │  Real    │  Real    │
   │  Card    │  Card    │
   └──────────┴──────────┘
```

## Integration Points

```
explore_screen.dart
├─ _buildLoadingState()
│  └─ GridView.builder
│     └─ ShimmerUrnCard × 9
│
collection_screen.dart
├─ _buildLoadingState()
│  └─ GridView.builder
│     └─ ShimmerMotifCard × 8
└─ _buildMotifCard()
   └─ CachedNetworkImage
      └─ placeholder: ShimmerSkeleton
```

