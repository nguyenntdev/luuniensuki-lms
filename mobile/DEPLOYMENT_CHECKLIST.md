# Deployment Checklist - Custom Model Viewer Integration

## Pre-Deployment

### 1. Code Review
- [x] CustomModelViewer widget created
- [x] JavaScript handlers properly registered
- [x] Error handling implemented
- [x] Loading states implemented
- [x] Hotspot tap detection working
- [x] Documentation created
- [ ] Code reviewed by team
- [ ] No lint errors or warnings

### 2. Dependencies
- [x] flutter_inappwebview added to pubspec.yaml
- [ ] Dependencies installed: `flutter pub get`
- [ ] No dependency conflicts
- [ ] All dependencies compatible with Flutter version

### 3. Platform Configuration

#### Android
- [ ] `minSdkVersion` set to 24 or higher in `android/app/build.gradle`
- [ ] `android:usesCleartextTraffic="true"` in `AndroidManifest.xml` OR
- [ ] Network security config created for localhost

#### iOS
- [ ] `io.flutter.embedded_views_preview` = YES in `Info.plist`
- [ ] Camera permissions configured (for AR)
- [ ] WebView settings configured

## Testing

### Unit Tests
- [ ] Test HTML generation
- [ ] Test hotspot color mapping
- [ ] Test icon mapping
- [ ] Test callback triggering

### Integration Tests
- [ ] Test model loading with valid URL
- [ ] Test model loading with invalid URL
- [ ] Test progress updates
- [ ] Test error handling
- [ ] Test hotspot tap detection
- [ ] Test retry functionality

### Device Testing

#### Android
- [ ] Test on Android 9 (API 28)
- [ ] Test on Android 10 (API 29)
- [ ] Test on Android 11+ (API 30+)
- [ ] Test with slow network
- [ ] Test with no network
- [ ] Test hotspot interactions
- [ ] Test model rotation/zoom
- [ ] Check console logs

#### iOS
- [ ] Test on iOS 14
- [ ] Test on iOS 15
- [ ] Test on iOS 16+
- [ ] Test with slow network
- [ ] Test with no network
- [ ] Test hotspot interactions
- [ ] Test model rotation/zoom
- [ ] Check console logs

### Performance Testing
- [ ] Check memory usage
- [ ] Check CPU usage
- [ ] Test with large models (>10MB)
- [ ] Test with multiple hotspots (>10)
- [ ] Check loading times
- [ ] Monitor for memory leaks

## Deployment Steps

### 1. Prepare
```bash
# Clean project
flutter clean

# Get dependencies
flutter pub get

# Run code generation if needed
flutter pub run build_runner build --delete-conflicting-outputs

# Check for issues
flutter analyze

# Format code
flutter format lib/
```

### 2. Build

#### Android
```bash
# Debug build
flutter build apk --debug

# Release build
flutter build apk --release
# or
flutter build appbundle --release
```

#### iOS
```bash
# Debug build
flutter build ios --debug

# Release build
flutter build ios --release
```

### 3. Verify Build
- [ ] Debug build successful
- [ ] Release build successful
- [ ] APK/IPA size acceptable
- [ ] No build warnings

### 4. Deploy
- [ ] Upload to internal testing track
- [ ] Test on physical devices
- [ ] Verify all features working
- [ ] Check error logging/analytics

## Post-Deployment

### 1. Monitoring
- [ ] Monitor error rates
- [ ] Check crash reports
- [ ] Review user feedback
- [ ] Monitor performance metrics

### 2. Documentation
- [ ] Update changelog
- [ ] Update version number
- [ ] Update API documentation
- [ ] Update README if needed

### 3. Rollback Plan
If critical issues are found:
1. Revert to previous version
2. Fix issues in development
3. Re-test thoroughly
4. Re-deploy

## Known Issues to Monitor

### High Priority
- [ ] Model loading failures
- [ ] JavaScript handler not firing
- [ ] Hotspot tap not detected
- [ ] WebView crashes

### Medium Priority
- [ ] Slow loading times
- [ ] Memory usage spikes
- [ ] UI responsiveness issues

### Low Priority
- [ ] Minor visual glitches
- [ ] Console log noise

## Success Criteria

### Functional
- [x] Models load successfully
- [x] Progress tracking works
- [x] Error handling works
- [x] Hotspots are clickable
- [x] Callbacks fire correctly

### Performance
- [ ] Models load in < 10 seconds on 3G
- [ ] Memory usage < 200MB
- [ ] No ANR/crashes
- [ ] Smooth interactions (60fps)

### User Experience
- [ ] Loading state is clear
- [ ] Error messages are helpful
- [ ] Retry function works
- [ ] Hotspots are visible
- [ ] Controls are responsive

## Support & Contacts

### Documentation
- Implementation guide: `mobile/CUSTOM_MODEL_VIEWER_INTEGRATION.md`
- Quick reference: `mobile/lib/features/urn_viewer/presentation/widgets/CUSTOM_MODEL_VIEWER_README.md`
- Summary: `mobile/3D_VIEWER_HANDLER_FIX_SUMMARY.md`

### Technical Contacts
- Flutter Team: [contact info]
- Backend Team: [contact info]
- QA Team: [contact info]

### External Resources
- [flutter_inappwebview Issues](https://github.com/pichillilorenzo/flutter_inappwebview/issues)
- [model-viewer Issues](https://github.com/google/model-viewer/issues)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/flutter)

## Notes

### Version
- Flutter SDK: [version]
- Dart SDK: [version]
- flutter_inappwebview: ^6.0.0
- App version: [version]

### Date
- Implementation: [date]
- Testing: [date]
- Deployment: [date]

### Sign-off
- Developer: [ ] Name, Date
- Code Reviewer: [ ] Name, Date
- QA Lead: [ ] Name, Date
- Product Manager: [ ] Name, Date

