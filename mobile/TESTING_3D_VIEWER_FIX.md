# 3D Viewer Black Screen Fix - Test Plan

## Testing Instructions

### Prerequisites
- Flutter installed on development machine
- Android device or emulator with internet connection
- Access to https://lms.histolab.icu server

### Test 1: Basic Model Loading
1. Build and run the Flutter app
2. Login with test credentials
3. Navigate to Explore screen
4. Tap on any urn card (e.g., "Cao Đỉnh")
5. **Expected Result:** 3D model loads correctly from remote URL
6. **Verify in logs:** Check debug console for `[URN_VIEWER] Loading model from: https://lms.histolab.icu/assets/models/...`

### Test 2: All 9 Urns
Test each urn to ensure all models load:
- CAO-DINH (Cao Đỉnh)
- NHAN-DINH (Nhân Đỉnh)
- CHUONG-DINH (Chương Đỉnh)
- ANH-DINH (Anh Đỉnh)
- NGHI-DINH (Nghị Đỉnh)
- THUAN-DINH (Thuần Đỉnh)
- TUYEN-DINH (Tuyên Đỉnh)
- DU-DINH (Dụ Đỉnh)
- HUYEN-DINH (Huyền Đỉnh)

**Expected Result:** All models load correctly without black screen

### Test 3: Model Viewer Controls
1. Open any urn's 3D viewer
2. Test camera controls:
   - Rotate model (drag/swipe)
   - Zoom in/out (pinch gesture)
   - Pan camera
3. **Expected Result:** All controls work smoothly

### Test 4: Hotspot Interaction
1. Open Cao Đỉnh (has motif coordinates)
2. Look for colored hotspots on the model
3. Tap on a hotspot
4. **Expected Result:** Motif sidebar opens with details

### Test 5: Error Handling
1. Disconnect internet
2. Try to open urn viewer
3. **Expected Result:** Error message shown with retry button
4. Reconnect internet and tap retry
5. **Expected Result:** Model loads successfully

### Test 6: Network Performance
1. Monitor network traffic when loading model
2. Check that model is cached by browser after first load
3. Navigate away and back to same urn
4. **Expected Result:** Model loads faster on second view (from cache)

## Debug Commands

### Check Model URLs in Logs
```bash
adb logcat | grep "URN_VIEWER"
```

### Check Network Requests
```bash
adb logcat | grep "DIO"
```

### Monitor Memory Usage
```bash
adb shell dumpsys meminfo <package_name>
```

## Expected Behavior

### ✅ Success Indicators
- 3D model appears within 3 seconds
- Model is properly lit and textured
- Camera controls respond smoothly
- Hotspots (if available) are visible and clickable
- No black screen or blank canvas

### ❌ Failure Indicators
- Black screen after 3 seconds
- Console errors about asset loading
- Network errors (check server availability)
- WebGL errors (check device compatibility)

## Troubleshooting

### Issue: Black Screen Persists
**Possible Causes:**
1. Server is down or model file is missing
2. Network connectivity issues
3. WebGL not supported on device
4. CORS issues (should be handled by nginx proxy)

**Solutions:**
1. Verify model URL in browser: https://lms.histolab.icu/assets/models/CAO-DINH-v1.glb
2. Check device internet connection
3. Test on different device
4. Check nginx configuration for CORS headers

### Issue: Models Load Slowly
**Possible Causes:**
1. Large file size (60-80MB per model)
2. Slow network connection
3. Server bandwidth limitations

**Solutions:**
1. Use WiFi instead of cellular data
2. Implement progressive loading
3. Consider model compression

### Issue: Some Models Don't Load
**Possible Causes:**
1. Model file doesn't exist on server
2. Wrong slug/filename mapping
3. API returns empty model_url

**Solutions:**
1. Check server for missing files
2. Verify slug matches filename (uppercase)
3. Check API response for model_url field

## Code Verification

### Verify Changes Applied
```bash
cd mobile
grep -n "effectiveModelUrl" lib/features/*/domain/entities/urn.dart
```

**Expected Output:**
Should show both files using `remoteModelUrl`

### Verify ModelViewer Configuration
```bash
cd mobile
grep -A 10 "ModelViewer(" lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart
```

**Expected Output:**
Should show `src: modelPath` where modelPath comes from `effectiveModelUrl`

## Rollback Plan

If issues persist, revert changes:

```bash
cd mobile
git checkout HEAD -- lib/features/urn_viewer/domain/entities/urn.dart
git checkout HEAD -- lib/features/explore/domain/entities/urn.dart
git checkout HEAD -- lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart
```

Then implement local asset fallback if needed.

