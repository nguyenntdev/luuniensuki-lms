# Release Checklist - v1.6.0+7

## Pre-Build Checks ✅

### Configuration
- [x] Version updated in pubspec.yaml (1.6.0+7)
- [x] API base URL set to production (https://lms.histolab.icu)
- [x] Release keystore exists and is valid
- [x] key.properties configured correctly
- [x] ProGuard rules comprehensive and tested

### Code Quality
- [x] All debug print() wrapped in kDebugMode
- [x] No hardcoded test credentials
- [x] No exposed API keys
- [x] Debug logging disabled for release
- [x] TODOs reviewed (none blocking)

### Build Configuration
- [x] Release signing config in build.gradle
- [x] Minification enabled (R8)
- [x] Resource shrinking enabled
- [x] ProGuard rules applied
- [x] Debug flag disabled for release

---

## Build Process

### 1. Clean Build
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms/mobile
./build_release.sh
```

### 2. Alternative Manual Build
```bash
flutter clean
flutter pub get
flutter build apk --release
```

---

## Post-Build Verification

### APK Validation
- [ ] APK generated successfully
- [ ] APK signed with release keystore
- [ ] APK size reasonable (<50MB recommended)
- [ ] ProGuard mapping file generated

### Installation Testing
- [ ] Install on Android 8.0+ device
- [ ] Install on Android 13+ device
- [ ] No installation errors
- [ ] App icon displays correctly
- [ ] App name correct ("Luuniensuki LMS")

### Functional Testing
- [ ] App launches without crashes
- [ ] Splash screen displays correctly
- [ ] Login flow works
- [ ] Register flow works
- [ ] Production API calls successful
- [ ] 3D model viewer loads models
- [ ] Sound effects play correctly
- [ ] Haptic feedback works
- [ ] Offline mode functions properly
- [ ] Local storage persists data
- [ ] Push notifications work (if FCM configured)

### Performance Testing
- [ ] App startup time acceptable (<3s)
- [ ] UI animations smooth (60fps)
- [ ] No memory leaks during normal use
- [ ] Battery usage reasonable
- [ ] Network calls efficient

### Security Testing
- [ ] No debug logs in logcat
- [ ] Secure storage working
- [ ] HTTPS enforced for API calls
- [ ] No sensitive data in logs
- [ ] Keystore signature verified

---

## Distribution

### APK Location
```
build/app/outputs/flutter-apk/app-release.apk
builds/app-release-v1.6.0+7.apk (backup copy)
```

### Verify Signature
```bash
jarsigner -verify -verbose -certs build/app/outputs/flutter-apk/app-release.apk
```

### For Google Play Store
```bash
# Build App Bundle instead
flutter build appbundle --release

# Output: build/app/outputs/bundle/release/app-release.aab
```

---

## Rollback Plan

If critical issues found:

1. **Don't publish** to production
2. Document the issue in detail
3. Create hotfix branch from release tag
4. Fix the issue
5. Re-test completely
6. Increment version (1.6.1+8)
7. Rebuild and retest

---

## Release Notes (Draft)

### Version 1.6.0 - Build 7

**What's New:**
- Enhanced UI/UX with modern animations
- Improved 3D model viewer performance
- Optimized offline functionality
- Better error handling and user feedback
- Performance optimizations

**Improvements:**
- Faster app startup time
- Reduced memory usage
- Smoother animations
- Better network error handling

**Bug Fixes:**
- Fixed various minor UI issues
- Improved stability

**Technical:**
- Updated dependencies
- Enhanced ProGuard configuration
- Improved code quality
- Better debug logging control

---

## Sign-Off

**Built by:** _________________  
**Date:** _________________  
**Tested by:** _________________  
**Date:** _________________  
**Approved by:** _________________  
**Date:** _________________  

**Status:** ⬜ APPROVED FOR RELEASE  ⬜ REJECTED

**Notes:**
_____________________________________________
_____________________________________________
_____________________________________________

