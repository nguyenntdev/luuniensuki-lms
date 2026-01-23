# Share Image Functionality - Testing Visual Guide

## How to Test the Share Feature

### Step 1: Navigate to a Motif Detail Screen
- Open any motif from the collection
- Look for the **share button** (share icon) in the top-right corner

### Step 2: Tap the Share Button
You should see:
```
┌─────────────────────────────────────┐
│  ⭕ Đang chuẩn bị ảnh...             │
└─────────────────────────────────────┘
```

### Step 3: Share Dialog Opens
After the image downloads, you'll see the system share sheet with:

**Image Preview:**
- The actual motif image (high quality)

**Caption Text:**
```
🏛️ [Motif Name] (English Name)
📍 [URN/Artifact Name]
🎨 [Category] • ⭐ [Rarity]

Khám phá tại: Lưu Niên Sử Kí
```

### Example Caption:
```
🏛️ Rồng Thăng Long (Dragon of Thang Long)
📍 Chuông chùa Phổ Minh
🎨 Thần thoại • ⭐ Huyền thoại

Khám phá tại: Lưu Niên Sử Kí
```

## Expected Behavior

### ✅ Success Cases

1. **Motif with imageUrl**
   - Should download and share the full-resolution image
   - Loading indicator shows for a few seconds
   - Share dialog opens with image + caption

2. **Motif with only thumbnailUrl**
   - Should download and share the thumbnail image
   - Same behavior as above

3. **Motif with no images**
   - Shows minimal text: "🏛️ [Motif Name] - Khám phá tại ứng dụng Lưu Niên Sử Kí!"
   - No loading delay

### ❌ Error Cases

If download fails, you'll see:
```
┌─────────────────────────────────────┐
│  Không thể chia sẻ ảnh: [error]    │
└─────────────────────────────────────┘
```

## Visual Flow Diagram

```
User taps Share Button
        ↓
Show Loading Snackbar
"Đang chuẩn bị ảnh..."
        ↓
Check for image URL
        ↓
   ┌────┴────┐
   │         │
No Image   Has Image
   │         │
   │         ↓
   │    Download Image
   │    (with progress)
   │         │
   ↓         ↓
Share     Share
Text      Image + Caption
Only      
```

## Where Images Are Stored

Temporary location:
```
/tmp/share_motif_[motif_id].[extension]
```

Example:
```
/tmp/share_motif_123.jpg
/tmp/share_motif_456.png
/tmp/share_motif_789.webp
```

## Supported Image Formats

- ✅ JPEG (.jpg, .jpeg)
- ✅ PNG (.png)
- ✅ GIF (.gif)
- ✅ WebP (.webp)

## Testing Checklist

### Basic Functionality
- [ ] Share button appears in motif detail screen
- [ ] Loading indicator shows when tapping share
- [ ] Image downloads successfully
- [ ] Share dialog opens with image

### Image Quality
- [ ] Shared image is clear and high quality
- [ ] Image matches what's shown in the detail screen
- [ ] Correct aspect ratio maintained

### Caption Text
- [ ] Motif name is correct
- [ ] English name appears (if available)
- [ ] URN/artifact name is correct
- [ ] Category is translated to Vietnamese
- [ ] Rarity is translated to Vietnamese
- [ ] App branding is present

### Different Platforms
- [ ] Share to Messages/WhatsApp
- [ ] Share to Facebook
- [ ] Share to Instagram
- [ ] Share to Email
- [ ] Share to Twitter/X

### Edge Cases
- [ ] Share with slow internet
- [ ] Share with no internet (should fail gracefully)
- [ ] Share motif with very long name
- [ ] Share motif with no English name
- [ ] Share when app is in background

### Error Handling
- [ ] Error message appears on network failure
- [ ] Loading indicator dismisses on error
- [ ] Can retry sharing after error
- [ ] No app crash on error

## Debug Output

When testing, check the debug console for:

```
flutter: Sharing image from URL: https://api.example.com/uploads/motifs/dragon.jpg
```

Or errors:
```
flutter: Error sharing motif: [error details]
```

## Common Issues & Solutions

### Issue: "Share text only, no image"
**Solution:** Check that `motif.imageUrl` or `motif.thumbnailUrl` is not null/empty

### Issue: "Download fails"
**Solution:** Verify URL is accessible, check network connection

### Issue: "Wrong file extension"
**Solution:** Code now auto-detects extension from URL

### Issue: "Image quality too low"
**Solution:** Code prioritizes `imageUrl` over `thumbnailUrl`

## Performance Notes

- Image download takes 1-5 seconds depending on size and network
- Temp files are auto-cleaned by OS
- No memory leaks (files are not kept in memory)
- Works offline if image is cached by Dio

