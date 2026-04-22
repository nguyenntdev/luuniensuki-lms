# Motif Image Loading - Testing Guide

## Overview
This guide helps you test the motif image loading fixes across all screens in the LMS mobile app.

## Pre-Testing Setup

### 1. Enable Debug Logging
Debug logging is automatically enabled in debug builds. No configuration needed.

### 2. Setup ADB (Android)
```bash
# Connect device
adb devices

# Start log monitoring in a terminal
adb logcat | grep MOTIF_IMAGE
```

### 3. Clear App Cache (Optional)
To test first-time loading:
```bash
# Android
adb shell pm clear com.luuniensuki.lms

# Or manually: Settings → Apps → LMS → Clear Cache
```

## Test Scenarios

### Test 1: Explore Screen - URN Thumbnails

**Steps:**
1. Launch app and navigate to Explore tab
2. Scroll through URN list
3. Observe image loading behavior

**Expected Results:**
- [ ] URN thumbnails load correctly
- [ ] Loading placeholders shown during load
- [ ] No broken image icons (unless image truly missing)
- [ ] Smooth scrolling (images cached after first load)

**Check Logs:**
```bash
adb logcat | grep "MOTIF_IMAGE"
# Should see:
# [MOTIF_IMAGE] Converting relative URL: /assets/urns/...
# [MOTIF_IMAGE] Full URL: https://lms.histolab.icu/assets/urns/...
```

**Screenshot Points:**
- URN grid with all thumbnails loaded
- Loading state (if you can capture it)

---

### Test 2: URN Viewer - Motif Sidebar

**Steps:**
1. Tap on any URN from Explore
2. Wait for 3D model to load
3. Tap on a motif hotspot to open sidebar
4. Observe motif thumbnail in sidebar

**Expected Results:**
- [ ] Motif thumbnail loads in sidebar
- [ ] Loading indicator shown briefly
- [ ] Image fits properly in aspect ratio 16:10
- [ ] Error icon only if image missing

**Check Logs:**
```bash
# Should see URL conversion for motif image
[MOTIF_IMAGE] Converting relative URL: /assets/motifs/...
```

**Screenshot Points:**
- Sidebar with motif thumbnail visible
- Motif details with image

---

### Test 3: Collection Screen - Motif Grid

**Steps:**
1. Navigate to Collection tab (heart icon)
2. Tap "Họa Tiết" tab
3. Scroll through motif grid
4. Observe thumbnail loading

**Expected Results:**
- [ ] All discovered motif thumbnails load
- [ ] Shimmer skeleton shown during load
- [ ] Grid layout maintains proper spacing
- [ ] Images cached on scroll back

**Check Logs:**
```bash
# Multiple image loads
[MOTIF_IMAGE] Image URL: https://lms.histolab.icu/assets/motifs/...
```

**Screenshot Points:**
- Full motif grid with loaded images
- Shimmer loading state (if captured)

---

### Test 4: Motif Detail Screen - Hero Image

**Steps:**
1. From Collection or URN viewer, navigate to a motif detail
2. Observe hero image at top
3. Scroll to see image collapse into app bar

**Expected Results:**
- [ ] Hero image loads in SliverAppBar
- [ ] Image covers full width, maintains aspect ratio
- [ ] Gradient overlay visible for text readability
- [ ] Fallback to thumbnail if main image missing
- [ ] Loading indicator during load

**Check Logs:**
```bash
# Should show URL selection (image_url or thumbnail_url)
[MOTIF_IMAGE] Image URL: https://lms.histolab.icu/...
```

**Screenshot Points:**
- Hero image expanded
- Hero image collapsed in app bar

---

### Test 5: Lesson Tab - Image Gallery

**Steps:**
1. From Motif Detail screen, ensure you're on "Bài Học" tab
2. Scroll down to lesson content
3. Find image gallery (if lesson has images)
4. Tap on images to view full size (if implemented)

**Expected Results:**
- [ ] Lesson images load in horizontal scroll
- [ ] Loading indicators shown for each image
- [ ] CachedNetworkImage used (check for caching on re-scroll)
- [ ] Error icons only for truly missing images
- [ ] "More" indicator if more than 4 images

**Check Logs:**
```bash
# Multiple image loads
[MOTIF_IMAGE] Failed to load lesson image: ... - Error: ...
# (Only if actual error occurs)
```

**Screenshot Points:**
- Lesson image gallery with loaded images

---

## Network Testing

### Test 6: Offline Behavior

**Steps:**
1. Load app with network enabled (cache images)
2. Enable Airplane mode
3. Navigate to different screens
4. Observe cached image behavior

**Expected Results:**
- [ ] Previously loaded images still visible (cached)
- [ ] New images show error state immediately
- [ ] Appropriate error messages

---

### Test 7: Slow Network

**Steps:**
1. Use Android Developer Options → Network Throttling
2. Or use Charles Proxy / similar tool
3. Navigate through app

**Expected Results:**
- [ ] Loading placeholders visible longer
- [ ] Progress indicators work correctly
- [ ] No crashes or timeouts
- [ ] Images eventually load

---

### Test 8: Failed Image Loads

**Steps:**
1. Find a motif/urn with intentionally broken image URL (or modify backend temporarily)
2. Navigate to that item
3. Observe error handling

**Expected Results:**
- [ ] Error icon displayed
- [ ] Error logged with details
- [ ] No app crash
- [ ] Fallback UI shown

**Check Logs:**
```bash
[MOTIF_IMAGE] Failed to load: https://... - Error: NetworkImageLoadException
```

---

## Special Cases

### Test 9: Vietnamese Characters

**Steps:**
1. Find motifs with Vietnamese names (e.g., "Rồng Phượng")
2. Navigate to those motifs
3. Observe image loading

**Expected Results:**
- [ ] Images load correctly despite Vietnamese characters
- [ ] URLs properly encoded in logs
- [ ] No URL encoding errors

---

### Test 10: Large Images

**Steps:**
1. Find motifs with high-resolution detail images
2. Load in Motif Detail screen
3. Monitor memory usage

**Expected Results:**
- [ ] Images load without memory issues
- [ ] CachedNetworkImage handles resizing
- [ ] Smooth scrolling maintained

---

## Regression Testing

After fixes, verify these previously working features still work:

- [ ] 3D model loading in URN viewer
- [ ] Hotspot interaction
- [ ] Navigation between screens
- [ ] User progress updates
- [ ] Quiz functionality
- [ ] Lesson content display

---

## Performance Metrics

Track these metrics during testing:

| Metric | Target | Notes |
|--------|--------|-------|
| Initial image load | < 3s | First time, good network |
| Cached image load | < 100ms | Subsequent loads |
| Memory usage | < 200MB | Normal app usage |
| Scroll FPS | > 50 | Smooth scrolling |

---

## Bug Report Template

If you find issues, use this template:

```markdown
**Screen:** [Explore / URN Viewer / Collection / etc.]
**Issue:** [Brief description]

**Steps to Reproduce:**
1. 
2. 
3. 

**Expected:**
[What should happen]

**Actual:**
[What actually happens]

**Logs:**
```
[Paste relevant MOTIF_IMAGE logs]
```

**Screenshots:**
[Attach if applicable]

**Device Info:**
- OS: Android 13 / iOS 16
- Device: Pixel 6 / iPhone 14
- Network: WiFi / 4G
```

---

## Success Criteria

All tests pass if:
- ✅ All images load correctly with proper URLs
- ✅ Loading states appear appropriately
- ✅ Error states handled gracefully
- ✅ Logs show proper URL conversion
- ✅ No crashes or performance issues
- ✅ Cached images load instantly on re-visit

