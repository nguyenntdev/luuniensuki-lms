# Share Image Caption Burn - Testing Guide

## Quick Test Checklist

### ✅ Basic Functionality
- [ ] Open any motif detail screen
- [ ] Tap the share button (top-right)
- [ ] Loading indicator shows "Đang tạo ảnh chia sẻ..."
- [ ] Share dialog opens after processing
- [ ] Image has caption burned at bottom
- [ ] Share completes successfully

### ✅ Caption Content
- [ ] Line 1 shows: `🏛️ {motif.name}`
- [ ] Line 2 shows: `📍 {urn.name} • Lưu Niên Sử Kí`
- [ ] Text is centered and readable
- [ ] Emoji icons display correctly

### ✅ Visual Quality
- [ ] Original image is clear (not blurry)
- [ ] Overlay bar is semi-transparent black
- [ ] Text is white and sharp
- [ ] Bar height looks proportional (120px)
- [ ] No text cutoff or overflow

### ✅ Error Handling
- [ ] Works when image URL is available
- [ ] Fallback to text share when no image
- [ ] Error message shows if download fails
- [ ] Loading indicator hides on error

---

## Detailed Test Cases

### Test Case 1: Standard Share
**Steps:**
1. Navigate to any motif (e.g., "Chim công")
2. Tap share button
3. Wait for processing
4. Check the image in share preview

**Expected:**
- Loading shows for 2-5 seconds
- Share dialog opens
- Image shows with caption at bottom
- Caption text is clear and centered

---

### Test Case 2: Long Motif Name
**Steps:**
1. Find a motif with long name (>20 characters)
2. Tap share button
3. Check caption rendering

**Expected:**
- Long name wraps properly or uses ellipsis
- Text stays within overlay bar
- Still readable

---

### Test Case 3: No Image Available
**Steps:**
1. Find a motif without image URL
2. Tap share button

**Expected:**
- Quick fallback to text-only share
- Message: "🏛️ {name} - Khám phá tại ứng dụng Lưu Niên Sử Kí!"

---

### Test Case 4: Network Error
**Steps:**
1. Turn off WiFi/mobile data
2. Try to share a motif
3. Check error handling

**Expected:**
- Error message displays
- Loading indicator hides
- User can retry

---

### Test Case 5: Different Image Sizes

**Small Image (< 500px):**
- [ ] Caption bar scales appropriately
- [ ] Text size looks good

**Medium Image (500-1500px):**
- [ ] Standard case - should work perfectly
- [ ] 120px bar is proportional

**Large Image (> 1500px):**
- [ ] Processing may take longer
- [ ] Final image quality is good
- [ ] File size is reasonable

---

## Platform Testing

### Test on Facebook
1. Share to Facebook
2. Check preview in Facebook app
3. Post and verify final appearance

**Expected:**
- Caption is visible in image
- Image displays at full size
- Text is readable

### Test on Instagram Stories
1. Share to Instagram Stories
2. Check image appearance
3. Verify text readability

**Expected:**
- Image fits properly
- Caption is clearly visible
- No cropping of caption area

### Test on WhatsApp
1. Share to WhatsApp contact
2. Send the image
3. Check received image

**Expected:**
- Full resolution maintained
- Caption is part of image
- Displays correctly on recipient's device

---

## Performance Testing

### Timing Benchmarks
- **Download**: 1-3 seconds (varies by connection)
- **Processing**: < 1 second
- **Total**: 2-5 seconds typical

### Memory Usage
- Monitor app memory during share
- Should not spike excessively
- Temp files cleaned up after share

---

## Visual Verification Checklist

```
Check these aspects of the final image:

┌─────────────────────────────────┐
│                                 │
│  [ ] Original image quality    │ ← No compression artifacts
│  [ ] Colors accurate            │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ [ ] Bar opacity (87%)       │ │ ← Semi-transparent
│ │ [ ] Bar height (120px)      │ │
│ │                             │ │
│ │ [ ] Line 1 bold & white     │ │ ← Motif name
│ │ [ ] Size: 42px              │ │
│ │                             │ │
│ │ [ ] Line 2 lighter white    │ │ ← Location
│ │ [ ] Size: 32px              │ │
│ │                             │ │
│ │ [ ] 20px padding sides      │ │
│ │ [ ] Text centered           │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

---

## Regression Testing

Make sure these still work:

- [ ] Share button is visible
- [ ] Share button is tappable
- [ ] Other screen functions not affected
- [ ] Navigation still works
- [ ] Back button works after share

---

## Edge Cases to Test

1. **Very small image** (< 300px)
   - Caption may be too large proportionally
   - Text might overflow

2. **Very wide image** (panorama)
   - Bar should span full width
   - Text should center properly

3. **Very tall image** (portrait)
   - Bar at bottom may be far from visible area
   - Consider scrolling to see caption

4. **Special characters in name**
   - Vietnamese diacritics
   - Emoji in motif name
   - Parentheses, quotes

5. **Rapid repeated shares**
   - Tap share multiple times quickly
   - Should handle gracefully
   - No crashes or hangs

---

## How to Report Issues

If you find a problem, provide:

1. **Device info**: Model, OS version
2. **Screenshot**: Of the shared image
3. **Motif name**: Which motif you tested
4. **Steps**: What you did
5. **Expected vs Actual**: What should happen vs what happened
6. **Console logs**: Any error messages

---

## Success Criteria

✅ All test cases pass
✅ Images look professional
✅ Caption is always readable
✅ No crashes or errors
✅ Works on all major platforms
✅ Performance is acceptable (< 5 sec)

