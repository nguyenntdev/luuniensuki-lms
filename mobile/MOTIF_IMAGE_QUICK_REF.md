# Motif Image Loading - Quick Reference

## 🚀 Quick Fix Checklist

When adding a new widget that displays motif/urn images:

1. ✅ Import UrlUtils
```dart
import '../../../../core/utils/url_utils.dart';
```

2. ✅ Import CachedNetworkImage
```dart
import 'package:cached_network_image/cached_network_image.dart';
```

3. ✅ Convert URL before using
```dart
final imageUrl = UrlUtils.getImageUrl(motif.thumbnailUrl);
```

4. ✅ Use CachedNetworkImage with proper error handling
```dart
CachedNetworkImage(
  imageUrl: imageUrl,
  fit: BoxFit.cover,
  placeholder: (context, url) => LoadingWidget(),
  errorWidget: (context, url, error) {
    debugPrint('[MOTIF_IMAGE] Failed: $imageUrl - $error');
    return ErrorWidget();
  },
)
```

## 🔍 Debug Commands

### View Image Loading Logs
```bash
# Android
adb logcat | grep MOTIF_IMAGE

# View all together
adb logcat | grep -E "MOTIF_IMAGE|API"
```

### Test Image URL
```bash
# Replace with actual URL from logs
curl -I "https://lms.histolab.icu/assets/motifs/URN-DONG-SON/rong-phung.jpg"
```

## 📦 API Response Structure

### URN Response
```json
{
  "id": "urn-123",
  "slug": "urn-dong-son",
  "name": "Chum Đông Sơn",
  "thumbnail_url": "/assets/urns/urn-dong-son.jpg"
}
```

### Motif Response
```json
{
  "id": "motif-123",
  "name": "Rồng Phượng",
  "thumbnail_url": "/assets/motifs/URN-DONG-SON/rong-phung.jpg",
  "image_url": "/assets/motifs/URN-DONG-SON/rong-phung-detail.jpg"
}
```

## 🛠️ UrlUtils Methods

### toFullUrl()
```dart
// Converts relative to full URL
String? fullUrl = UrlUtils.toFullUrl('/assets/motifs/image.jpg');
// Result: 'https://lms.histolab.icu/assets/motifs/image.jpg'
```

### getImageUrl()
```dart
// With fallback
String url = UrlUtils.getImageUrl(motif.thumbnailUrl, fallback: '');
// Returns empty string if null
```

### getAssetUrl()
```dart
// For asset-specific paths
String url = UrlUtils.getAssetUrl('motifs/urn/image.jpg');
// Result: 'https://lms.histolab.icu/motifs/urn/image.jpg'
```

### isValidUrl()
```dart
// Validate URL format
bool valid = UrlUtils.isValidUrl(someUrl);
```

## 📋 Common Patterns

### Pattern 1: Simple Thumbnail
```dart
Widget _buildThumbnail() {
  final imageUrl = UrlUtils.getImageUrl(item.thumbnailUrl);
  
  if (imageUrl.isEmpty) {
    return PlaceholderWidget();
  }
  
  return CachedNetworkImage(
    imageUrl: imageUrl,
    fit: BoxFit.cover,
    placeholder: (_, __) => ShimmerSkeleton(),
    errorWidget: (_, __, ___) => ErrorIcon(),
  );
}
```

### Pattern 2: With Fallback Image
```dart
Widget _buildImage() {
  // Try main image, fallback to thumbnail
  final imageUrl = UrlUtils.getImageUrl(
    item.imageUrl ?? item.thumbnailUrl,
  );
  
  return CachedNetworkImage(imageUrl: imageUrl, ...);
}
```

### Pattern 3: Conditional Display
```dart
Widget _buildContent() {
  return Column(
    children: [
      // Only show if URL exists
      if (item.thumbnailUrl != null && item.thumbnailUrl!.isNotEmpty)
        _buildThumbnail(item.thumbnailUrl!),
      
      // Other content...
    ],
  );
}
```

## ⚠️ Common Mistakes

### ❌ DON'T: Use URL directly
```dart
CachedNetworkImage(
  imageUrl: motif.thumbnailUrl!, // May be relative!
)
```

### ✅ DO: Convert first
```dart
final imageUrl = UrlUtils.getImageUrl(motif.thumbnailUrl);
CachedNetworkImage(imageUrl: imageUrl)
```

### ❌ DON'T: Use Image.network
```dart
Image.network(url) // No caching, poor error handling
```

### ✅ DO: Use CachedNetworkImage
```dart
CachedNetworkImage(
  imageUrl: url,
  placeholder: ...,
  errorWidget: ...,
)
```

### ❌ DON'T: Silent failures
```dart
errorWidget: (_, __, ___) => Icon(Icons.error)
// No logging!
```

### ✅ DO: Log errors
```dart
errorWidget: (context, url, error) {
  debugPrint('[MOTIF_IMAGE] Failed: $url - $error');
  return Icon(Icons.error);
}
```

## 🎯 Where Images Are Used

| Screen | Widget | Image Type | Status |
|--------|--------|------------|--------|
| Explore | UrnCard | URN thumbnail | ✅ Fixed |
| URN Viewer | MotifSidebar | Motif thumbnail | ✅ Fixed |
| Collection | CollectionScreen | Motif thumbnail | ✅ Fixed |
| Motif Detail | Hero Image | Motif image/thumbnail | ✅ Fixed |
| Lesson | LessonTab | Lesson images | ✅ Fixed |

## 📞 Troubleshooting

### Images showing placeholder/error icon
1. Check logs: `adb logcat | grep MOTIF_IMAGE`
2. Verify URL format in logs
3. Test URL in browser
4. Check network connectivity

### Slow loading
- CachedNetworkImage handles caching automatically
- First load may be slow, subsequent loads are cached
- Check network speed

### Vietnamese characters issue
- Backend should handle URL encoding
- If issues persist, check server logs

## 🔗 Related Files

- `lib/core/utils/url_utils.dart` - URL utilities
- `lib/core/constants/api_constants.dart` - Base URLs
- `MOTIF_IMAGE_LOADING_FIX.md` - Full documentation

