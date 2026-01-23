# Share Feature - Testing Guide

## Prerequisites
1. ✅ Run `flutter pub get` to install share_plus package
2. ✅ Test on real device (sharing may not work on simulators)
3. ✅ Ensure device has internet connection (for image download)

---

## Test Scenarios

### ✅ Test 1: Basic Share with Image
**Steps:**
1. Launch the app
2. Navigate to any discovered motif
3. Open motif detail screen
4. Tap the share button (top right, circular icon)
5. Wait for loading indicator "Đang chuẩn bị chia sẻ..."

**Expected Result:**
- Loading snackbar appears for ~2 seconds
- Native share sheet opens
- Image of the motif is visible
- Share text includes motif name, urn, category, rarity
- All text is in Vietnamese with emoji icons

**Pass Criteria:**
- ✅ Share sheet opens
- ✅ Image is visible and correct
- ✅ Text is formatted properly
- ✅ Can share to any app (Messages, WhatsApp, etc.)

---

### ✅ Test 2: Share Without Image
**Steps:**
1. Use a motif that has no imageUrl (if any exist)
2. Or temporarily disable internet to simulate download failure
3. Tap share button

**Expected Result:**
- Loading snackbar appears
- If image download fails, falls back to text-only share
- Share sheet still opens with text content
- No error shown to user (graceful degradation)

**Pass Criteria:**
- ✅ Share sheet opens even without image
- ✅ Text content is still shared
- ✅ No crash or error dialog

---

### ✅ Test 3: Share Cancellation
**Steps:**
1. Tap share button
2. When share sheet appears, tap "Cancel" or back button

**Expected Result:**
- Share sheet closes
- User returns to motif detail screen
- No error or crash

**Pass Criteria:**
- ✅ App remains stable
- ✅ No error messages
- ✅ Can trigger share again

---

### ✅ Test 4: Share to Different Apps
**Test each platform's common share targets:**

**iOS:**
- Messages
- Mail
- Notes
- Copy (to clipboard)
- Save to Files
- AirDrop

**Android:**
- Messages
- Gmail
- WhatsApp
- Facebook
- Copy to clipboard

**Expected Result:**
- Image and text appear correctly in each target app
- Image quality is maintained
- Text formatting is preserved (emojis, line breaks)

**Pass Criteria:**
- ✅ Works with at least 3 different apps
- ✅ Image appears in all apps that support images
- ✅ Text is readable and properly formatted

---

### ✅ Test 5: Translation Accuracy
**Test with different motif types:**

1. **Animal motif** (category: "animal")
   - Expected: "🎨 Thể loại: Động vật"

2. **Mythical motif** (category: "mythical")
   - Expected: "🎨 Thể loại: Thần thoại"

3. **Legendary rarity** (rarity: "legendary")
   - Expected: "⭐ Độ hiếm: Huyền thoại"

4. **Common rarity** (rarity: "common")
   - Expected: "⭐ Độ hiếm: Phổ thông"

**Pass Criteria:**
- ✅ All categories translate correctly
- ✅ All rarity levels translate correctly
- ✅ Unknown values fall back to original code

---

### ✅ Test 6: Performance
**Steps:**
1. Tap share button
2. Measure time until share sheet appears

**Expected Result:**
- Loading appears immediately
- Share sheet opens within 2-3 seconds
- No UI blocking or freezing

**Pass Criteria:**
- ✅ App remains responsive
- ✅ Share completes in < 5 seconds
- ✅ No ANR (Application Not Responding) on Android

---

### ✅ Test 7: Error Handling
**Steps:**
1. Turn off internet connection
2. Tap share button
3. Wait for share attempt

**Expected Result:**
- Falls back to text-only share
- Or shows error: "Không thể chia sẻ. Vui lòng thử lại."
- App doesn't crash

**Pass Criteria:**
- ✅ No crash
- ✅ Error message is user-friendly
- ✅ Can retry after reconnecting

---

## Quick Verification Checklist

**Visual Check:**
- [ ] Share button visible in app bar
- [ ] Loading indicator appears when sharing
- [ ] Image quality is good (not pixelated)
- [ ] Text is readable with proper formatting
- [ ] Emojis display correctly

**Functional Check:**
- [ ] Share sheet opens
- [ ] Can share to multiple apps
- [ ] Can cancel share without issues
- [ ] Works offline (text-only fallback)
- [ ] Error messages are in Vietnamese

**Content Check:**
- [ ] Motif name (Vietnamese + English if available)
- [ ] Urn name is correct
- [ ] Category translates to Vietnamese
- [ ] Rarity translates to Vietnamese
- [ ] Promotion text appears

---

## Common Issues & Solutions

### Issue: Share sheet doesn't open
**Solution:** 
- Ensure testing on real device (not simulator)
- Check share_plus package is installed
- Verify app has necessary permissions

### Issue: Image doesn't appear
**Solution:**
- Check internet connection
- Verify motif has valid imageUrl
- Check device storage (temp files)

### Issue: Text is malformed
**Solution:**
- Check Vietnamese character encoding
- Verify emojis are supported on device
- Test with different motifs

---

## Success Metrics

**Feature is ready for production when:**
- ✅ All 7 test scenarios pass
- ✅ Works on both iOS and Android
- ✅ No crashes in error scenarios
- ✅ User feedback is positive (loading/error messages)
- ✅ Image quality meets standards

