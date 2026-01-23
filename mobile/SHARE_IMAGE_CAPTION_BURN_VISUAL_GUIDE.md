# Share Image Caption Burn - Visual Guide

## Before vs After

### BEFORE: Separate Text Caption
```
┌─────────────────────────────────┐
│                                 │
│     [MOTIF IMAGE]              │
│                                 │
│                                 │
└─────────────────────────────────┘
                ↓
      Text sent separately:
      🏛️ Chim công (Peacock)
      📍 Trống đồng Ngọc Lũ
      🎨 Động vật • ⭐ Hiếm
      ✨ Khám phá văn hóa...
```

**Issues:**
- Caption appears below image in share dialog
- Different apps display it differently
- Easy to lose or ignore
- Not part of the image itself

---

### AFTER: Caption Burned Into Image
```
┌─────────────────────────────────┐
│                                 │
│                                 │
│     [MOTIF IMAGE]              │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │ │  ← Semi-transparent
│ │                             │ │     black overlay
│ │  🏛️ Chim công              │ │     (87% opacity)
│ │                             │ │
│ │  📍 Trống đồng Ngọc Lũ •   │ │
│ │      Lưu Niên Sử Kí        │ │
│ │                             │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

**Benefits:**
✅ Caption is permanent part of image
✅ Consistent across all platforms
✅ Professional watermark style
✅ Better branding and recognition

---

## Technical Layout

```
Image Dimensions: [width] × [height]

┌──────────────────────────────────────┐
│                                      │
│                                      │  ← Original image area
│         Original Image               │
│                                      │
│──────────────────────────────────────│ ← height - 120px
│  [20px padding]                      │
│                                      │
│  🏛️ {motif.name}                    │ ← +15px from bar top
│     Font: 42px, Bold, White          │
│                                      │
│  📍 {urn.name} • Lưu Niên Sử Kí     │ ← +65px from bar top
│     Font: 32px, Regular, 80% White   │
│                                      │
│  [20px padding]                      │
└──────────────────────────────────────┘
         ↑
    120px bar height
```

---

## Processing Flow Diagram

```
START
  │
  ├─→ Show loading indicator
  │   "Đang tạo ảnh chia sẻ..."
  │
  ├─→ Check if image URL exists
  │   │
  │   ├─ No → Share text only
  │   │        (fallback)
  │   │
  │   └─ Yes → Continue
  │
  ├─→ Download original image
  │   from server to temp file
  │
  ├─→ Decode image to ui.Image
  │   (get width, height, pixels)
  │
  ├─→ Create canvas & recorder
  │
  ├─→ Draw original image
  │   at (0, 0)
  │
  ├─→ Draw black overlay bar
  │   at bottom (height - 120px)
  │   with 87% opacity
  │
  ├─→ Render caption line 1
  │   (motif name, bold, 42px)
  │   centered, 15px from bar top
  │
  ├─→ Render caption line 2
  │   (location, regular, 32px)
  │   centered, 65px from bar top
  │
  ├─→ Convert canvas to PNG image
  │
  ├─→ Save to temp file
  │   "share_{motif_id}.png"
  │
  ├─→ Hide loading indicator
  │
  ├─→ Open share dialog
  │   with the processed image
  │
END
```

---

## Color Specifications

### Overlay Bar
- **Color**: Black (`#000000`)
- **Opacity**: 87% (`0xDD` in hex)
- **Full ARGB**: `0xDD000000`

### Caption Line 1 (Motif Name)
- **Color**: White (`#FFFFFF`)
- **Opacity**: 100%
- **Full ARGB**: `0xFFFFFFFF`
- **Font Size**: 42px
- **Font Weight**: Bold

### Caption Line 2 (Location)
- **Color**: White (`#FFFFFF`)
- **Opacity**: 80% (`0xCC` in hex)
- **Full ARGB**: `0xCCFFFFFF`
- **Font Size**: 32px
- **Font Weight**: Regular

---

## Example Output

### Example 1: Chim công (Peacock)
```
┌─────────────────────────────────┐
│  [Beautiful peacock image       │
│   from Ngọc Lũ bronze drum]     │
│                                 │
│ ╔═══════════════════════════╗   │
│ ║ ████████████████████████ ║   │
│ ║                           ║   │
│ ║  🏛️ Chim công            ║   │
│ ║                           ║   │
│ ║  📍 Trống đồng Ngọc Lũ • ║   │
│ ║      Lưu Niên Sử Kí      ║   │
│ ║                           ║   │
│ ╚═══════════════════════════╝   │
└─────────────────────────────────┘
```

### Example 2: Long văn (Dragon Pattern)
```
┌─────────────────────────────────┐
│  [Intricate dragon pattern      │
│   artwork]                      │
│                                 │
│ ╔═══════════════════════════╗   │
│ ║ ████████████████████████ ║   │
│ ║                           ║   │
│ ║  🏛️ Long văn             ║   │
│ ║                           ║   │
│ ║  📍 Trống đồng Hoàng Hạ •║   │
│ ║      Lưu Niên Sử Kí      ║   │
│ ║                           ║   │
│ ╚═══════════════════════════╝   │
└─────────────────────────────────┘
```

---

## File Size Comparison

| Format | Typical Size | Quality |
|--------|-------------|---------|
| Original JPEG | 100-300 KB | Good |
| PNG with caption | 200-500 KB | Excellent |

**Note**: PNG format is used to preserve transparency and ensure high quality text rendering.

---

## Platform Compatibility

✅ **Works on all platforms:**
- Facebook
- Instagram  
- WhatsApp
- Zalo
- Messenger
- Email
- File managers
- Any app that accepts images

The caption is permanently part of the image, so it displays correctly everywhere!

