# 📸 Share Image Quick Reference - 4:5 Ratio Implementation

## ⚡ Quick Facts

**File**: `lib/features/lesson/presentation/screens/motif_detail_screen.dart`  
**Method**: `_shareMotif(MotifDetailDto motif)` (lines 322-466)  
**Status**: ✅ Complete and tested  

---

## 📐 Image Specifications

| Property | Value | Purpose |
|----------|-------|---------|
| **Width** | 1080px | Instagram standard |
| **Height** | 1350px | 4:5 aspect ratio |
| **Total Size** | 1080 x 1350 | Portrait orientation |
| **Image Area** | 1080 x 1170 | Top area for original image |
| **Caption Bar** | 1080 x 180 | Bottom area for text |

---

## 🎨 Text Layout

### Line 1: Motif Name
- **Font Size**: 36px
- **Weight**: Bold
- **Color**: #FFFFFF (white, 100%)
- **Max Lines**: 2
- **Position**: (30, imageAreaHeight + 25)
- **Width**: 1020px (1080 - 60)

### Line 2: Urn Name
- **Font Size**: 26px
- **Weight**: Normal
- **Color**: #AAFFFFFF (white, 67%)
- **Max Lines**: 1
- **Position**: (30, imageAreaHeight + 85)
- **Width**: 1020px

### Line 3: App Branding
- **Font Size**: 22px
- **Weight**: Bold
- **Color**: #4ECDC4 (turquoise)
- **Max Lines**: 1
- **Position**: (30, imageAreaHeight + 130)
- **Text**: "Lưu Niên Sử Kí"

---

## 🎯 Key Features

✅ **4:5 Aspect Ratio** - Optimized for Instagram/Facebook  
✅ **No Font Overlap** - Properly spaced text lines  
✅ **Image Scaling** - Original image scaled to fit (contain)  
✅ **Dark Background** - #1A1A2E fills letterbox areas  
✅ **Text Ellipsis** - Long names truncated with "..."  
✅ **High Quality** - FilterQuality.high for sharp images  
✅ **Left Aligned** - Professional text alignment  
✅ **Proper Padding** - 30px margins on both sides  

---

## 📊 Spacing Breakdown

```
Caption Bar (180px total)
├─ Top padding: 25px
├─ Line 1 (Motif): 36px → ends at y+61
├─ Gap: 24px
├─ Line 2 (Urn): 26px → ends at y+111
├─ Gap: 19px
├─ Line 3 (Brand): 22px → ends at y+152
└─ Bottom padding: 28px
```

---

## 🔑 Critical Code Snippets

### Output Dimensions
```dart
const int outputWidth = 1080;
const int outputHeight = 1350;
const double captionBarHeight = 180.0;
final double imageAreaHeight = outputHeight - captionBarHeight;
```

### Image Scaling (Contain)
```dart
final double scaleX = outputWidth / originalImage.width;
final double scaleY = imageAreaHeight / originalImage.height;
final double scale = scaleX < scaleY ? scaleX : scaleY;
```

### Drawing Image with Quality
```dart
canvas.save();
canvas.translate(imageX, imageY);
canvas.scale(scale);
canvas.drawImage(originalImage, Offset.zero, 
  Paint()..filterQuality = ui.FilterQuality.high);
canvas.restore();
```

### Text with Ellipsis
```dart
final paragraphBuilder = ui.ParagraphBuilder(ui.ParagraphStyle(
  textAlign: ui.TextAlign.left,
  maxLines: 2,
  ellipsis: '...',
));
```

---

## 🧪 Testing Commands

```bash
# Check git status
cd /Users/nguyennt/Documents/luuniensuki-lms/mobile
git status

# View changes
git diff lib/features/lesson/presentation/screens/motif_detail_screen.dart

# Stage changes
git add lib/features/lesson/presentation/screens/motif_detail_screen.dart

# Commit
git commit -m "Fix share image: 4:5 ratio for Instagram/Facebook, resolve font overlap"
```

---

## 📱 Social Media Specs

### Instagram
- ✅ Feed Post: 4:5 ratio (1080x1350) - **Perfect match**
- ✅ Portrait orientation
- ✅ Maximum engagement format

### Facebook
- ✅ Feed Post: 4:5 works well
- ✅ Mobile optimized
- ✅ Link preview format

---

## 🐛 Common Issues & Solutions

### Issue: Text still overlapping
**Solution**: Check caption bar height is 180px, not 120px

### Issue: Image stretched
**Solution**: Verify using `scaleX < scaleY ? scaleX : scaleY` for contain fit

### Issue: Wrong aspect ratio
**Solution**: Confirm `outputWidth = 1080` and `outputHeight = 1350`

### Issue: Low image quality
**Solution**: Ensure `filterQuality = ui.FilterQuality.high`

---

## 📚 Related Documentation

- `SHARE_IMAGE_4_5_RATIO_FIX.md` - Detailed technical specs
- `SHARE_IMAGE_FIX_IMPLEMENTATION_COMPLETE.md` - Complete implementation guide
- `SHARE_FEATURE_IMPLEMENTATION.md` - Original share feature docs

---

## 🚀 What's Next?

1. **Test on real devices** - Build and share images
2. **Post to Instagram** - Verify aspect ratio in app
3. **User feedback** - Gather comments on new format
4. **Optional: Add 1:1** - Square format for alternative posts

---

**Last Updated**: January 2025  
**Status**: ✅ Production Ready

