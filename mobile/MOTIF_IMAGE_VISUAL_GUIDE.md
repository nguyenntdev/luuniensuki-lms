# Motif Image Loading - Visual Debug Reference

## 🎨 Visual Guide to Image Loading States

### Normal Flow

```
┌─────────────────────────────────────────────────┐
│ 1. API Response                                 │
│    Backend returns: "/assets/motifs/..."       │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 2. DTO Mapping (if using mapper)                │
│    _toFullUrl() converts to full URL            │
│    OR widget does conversion                    │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 3. Widget - UrlUtils.getImageUrl()              │
│    Converts: /assets/... → https://lms.../...  │
│    [MOTIF_IMAGE] Converting relative URL: ...   │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 4. CachedNetworkImage                           │
│    - Shows placeholder (shimmer/spinner)        │
│    - Downloads image                            │
│    - Caches locally                             │
│    - Displays image                             │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 5. Success State                                │
│    ✅ Image displayed                           │
│    ✅ Cached for future loads                   │
└─────────────────────────────────────────────────┘
```

### Error Flow

```
┌─────────────────────────────────────────────────┐
│ Image Load Attempt                              │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Error Occurs                                     │
│ • Network error                                  │
│ • 404 not found                                  │
│ • Invalid image format                           │
│ • Timeout                                        │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Error Logging                                    │
│ [MOTIF_IMAGE] Failed to load: URL - Error       │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Error Widget Displayed                           │
│ 🖼️ Icon(Icons.image_not_supported)             │
│ OR Icon(Icons.broken_image)                     │
└─────────────────────────────────────────────────┘
```

## 📊 Widget State Diagram

### URN Card (Explore Screen)

```
╔═════════════════════════════════════╗
║  URN Card                           ║
║  ┌───────────────────────────────┐  ║
║  │                               │  ║
║  │   [Thumbnail Image Area]      │  ║  ← CachedNetworkImage
║  │                               │  ║
║  │   State:                      │  ║
║  │   • Loading → Shimmer         │  ║
║  │   • Success → Image           │  ║
║  │   • Error → Placeholder       │  ║
║  └───────────────────────────────┘  ║
║  ┌───────────────────────────────┐  ║
║  │  Urn Name                     │  ║
║  │  Progress Bar                 │  ║
║  │  📊 Stats Row                 │  ║
║  └───────────────────────────────┘  ║
╚═════════════════════════════════════╝
```

### Motif Sidebar (URN Viewer)

```
╔═══════════════════════════════════════╗
║  Motif Sidebar                        ║
║  ┌─────────────────────────────────┐  ║
║  │  [Close Button]                 │  ║
║  └─────────────────────────────────┘  ║
║  ┌─────────────────────────────────┐  ║
║  │                                 │  ║
║  │  [Motif Thumbnail 16:10]        │  ║ ← CachedNetworkImage
║  │                                 │  ║
║  │  Aspect Ratio: 16/10            │  ║
║  │  Border Radius: 12px            │  ║
║  └─────────────────────────────────┘  ║
║  ┌─────────────────────────────────┐  ║
║  │  Motif Name                     │  ║
║  │  English Name (if exists)       │  ║
║  │  [Category] [Rarity]            │  ║
║  │  Progress Stepper               │  ║
║  │  XP Info                        │  ║
║  │  Description                    │  ║
║  └─────────────────────────────────┘  ║
╚═══════════════════════════════════════╝
```

### Motif Detail Hero Image

```
╔═══════════════════════════════════════╗
║  SliverAppBar (Expanded)              ║
║  ┌─────────────────────────────────┐  ║
║  │ [Back] [Top Bar] [Share]        │  ║
║  │                                 │  ║
║  │                                 │  ║
║  │   [Hero Image - Full Width]     │  ║ ← CachedNetworkImage
║  │                                 │  ║
║  │   Gradient Overlay ↓            │  ║
║  │                                 │  ║
║  │   [Motif Name]                  │  ║
║  │   [English Name]                │  ║
║  │   [Category] [Rarity]           │  ║
║  └─────────────────────────────────┘  ║
╚═══════════════════════════════════════╝
```

## 🔍 Debug Log Visual Flow

### Successful Load Sequence

```
Timeline →

T+0ms   [MOTIF_IMAGE] Converting relative URL: /assets/motifs/URN-DONG-SON/rong-phung.jpg
        │
T+1ms   [MOTIF_IMAGE] Full URL: https://lms.histolab.icu/assets/motifs/URN-DONG-SON/rong-phung.jpg
        │
T+2ms   [MOTIF_IMAGE] Image URL: https://lms.histolab.icu/assets/motifs/URN-DONG-SON/rong-phung.jpg
        │
        ├─ Widget: Show placeholder
        │
T+100ms ├─ Network: Request image
        │
T+500ms ├─ Network: Download complete
        │
T+510ms ├─ Widget: Cache image
        │
T+520ms └─ Widget: Display image ✅
```

### Failed Load Sequence

```
Timeline →

T+0ms   [MOTIF_IMAGE] Converting relative URL: /assets/motifs/INVALID/image.jpg
        │
T+1ms   [MOTIF_IMAGE] Full URL: https://lms.histolab.icu/assets/motifs/INVALID/image.jpg
        │
T+2ms   [MOTIF_IMAGE] Image URL: https://lms.histolab.icu/assets/motifs/INVALID/image.jpg
        │
        ├─ Widget: Show placeholder
        │
T+100ms ├─ Network: Request image
        │
T+500ms ├─ Network: 404 Not Found ❌
        │
T+510ms ├─ [MOTIF_IMAGE] Failed to load image: https://... - Error: HttpException
        │
T+520ms └─ Widget: Show error icon 🖼️
```

## 📋 URL Format Examples

### Correct URLs (After Conversion)

```
✅ https://lms.histolab.icu/assets/urns/urn-dong-son.jpg
✅ https://lms.histolab.icu/assets/motifs/URN-DONG-SON/rong-phung.jpg
✅ https://lms.histolab.icu/assets/motifs/URN-DONG-SON/hoa-sen-detail.jpg
✅ https://lms.histolab.icu/assets/models/URN-DONG-SON-v1.glb
```

### Incorrect URLs (Before Conversion)

```
❌ /assets/urns/urn-dong-son.jpg                           → Relative path
❌ assets/motifs/URN-DONG-SON/rong-phung.jpg              → Missing leading /
❌ file:///assets/motifs/image.jpg                         → Wrong scheme
❌ null                                                    → Null value
```

## 🎯 Common UI States

### Loading State
```
┌─────────────────┐
│                 │
│   ⏳ Spinner    │  OR  │ ▓▒░▓▒░ Shimmer │
│                 │
└─────────────────┘
```

### Success State
```
┌─────────────────┐
│                 │
│  🖼️ Beautiful  │
│    Motif Image  │
│                 │
└─────────────────┘
```

### Error State
```
┌─────────────────┐
│                 │
│  🚫 Error Icon  │
│ image_not_      │
│   supported     │
└─────────────────┘
```

### Empty State
```
┌─────────────────┐
│                 │
│  📷 Image Icon  │
│                 │
└─────────────────┘
```

## 🛠️ Debugging Checklist

When debugging image loading issues, check in order:

1. **Check Logs**
   ```bash
   adb logcat | grep MOTIF_IMAGE
   ```
   - ✅ See URL conversion?
   - ✅ See full URL logged?
   - ✅ See any error messages?

2. **Verify URL**
   - Copy URL from logs
   - Test in browser
   - Check if image exists on server

3. **Check Widget**
   - Using UrlUtils? ✅
   - Using CachedNetworkImage? ✅
   - Has error handling? ✅
   - Logs errors? ✅

4. **Network**
   - Device online?
   - Server reachable?
   - CORS configured?
   - Firewall blocking?

## 📱 Screen-by-Screen Visual Guide

Each screen should show:

**Explore Screen:**
- Grid of URN cards
- Each card has thumbnail
- Loading: Shimmer skeleton
- Error: Gradient placeholder with icon

**URN Viewer:**
- 3D model in center
- Motif sidebar on tap
- Sidebar has thumbnail 16:10
- Loading: Spinner
- Error: Image not supported icon

**Collection:**
- 2-column grid of motifs
- Each has thumbnail
- Loading: Shimmer
- Error: Image not supported icon (faded)

**Motif Detail:**
- Large hero image at top
- Scrollable content below
- Loading: Spinner in gray container
- Error: Large error icon

**Lesson Tab:**
- Horizontal image gallery
- 100x100 thumbnails
- Loading: Spinner per image
- Error: Broken image icon

---

**Use this guide** to visually identify which state an image is in and what to expect in logs!

