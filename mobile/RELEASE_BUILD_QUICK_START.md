# Release Build Quick Start Guide

## Prerequisites Verified ✅

All release configuration requirements (R-B1 to R-B5) have been successfully verified and configured.

## Quick Build Commands

### 1. Build Release APK (for testing)
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms/mobile

# Clean previous builds
/Users/nguyennt/development/flutter/bin/flutter clean

# Get dependencies
/Users/nguyennt/development/flutter/bin/flutter pub get

# Build release APK
/Users/nguyennt/development/flutter/bin/flutter build apk --release

# Output: build/app/outputs/flutter-apk/app-release.apk
```

### 2. Build App Bundle (for Google Play Store)
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms/mobile

# Clean and prepare
/Users/nguyennt/development/flutter/bin/flutter clean
/Users/nguyennt/development/flutter/bin/flutter pub get

# Build app bundle
/Users/nguyennt/development/flutter/bin/flutter build appbundle --release

# Output: build/app/outputs/bundle/release/app-release.aab
```

### 3. Install Release APK on Device
```bash
# After building APK
/Users/nguyennt/development/flutter/bin/flutter install --release
```

## Configuration Verification

Before building, run the verification script:

```bash
cd /Users/nguyennt/Documents/luuniensuki-lms/mobile
./check_release_config.sh
```

This will verify:
- ✅ Keystore configuration
- ✅ Build.gradle settings
- ✅ ProGuard rules
- ✅ Version information
- ✅ API endpoint
- ✅ Manifest security settings
- ⚠️  Debug log warnings

## What Was Configured

### Version: 1.6.0+7
- Version name: 1.6.0
- Version code: 7
- Updated in: pubspec.yaml, local.properties

### Release Optimizations
- **Code Minification**: Enabled (R8/ProGuard)
- **Resource Shrinking**: Enabled
- **Debug Symbols**: Disabled
- **HTTPS Only**: Enforced (no cleartext traffic)

### Security
- **Keystore**: `/Users/nguyennt/Documents/luuniensuki-lms/release-keystore.jks`
- **Key Alias**: release
- **Production API**: https://lms.histolab.icu

### Files Created/Modified
1. `pubspec.yaml` - Version updated to 1.6.0+7
2. `android/app/build.gradle` - Release optimizations added
3. `android/app/proguard-rules.pro` - ProGuard rules created
4. `android/app/src/main/AndroidManifest.xml` - Security hardened
5. `android/app/src/debug/AndroidManifest.xml` - Debug config updated
6. `android/local.properties` - Version metadata updated

## Testing Checklist

After building release APK:

- [ ] Install on physical device
- [ ] Test user registration and login
- [ ] Verify 3D model viewer works
- [ ] Test video and audio playback
- [ ] Check image loading (motifs, urns)
- [ ] Verify API connectivity to https://lms.histolab.icu
- [ ] Test Firebase push notifications
- [ ] Check offline mode functionality
- [ ] Verify all navigation flows
- [ ] Test quiz functionality
- [ ] Check gamification features (badges, leaderboard)

## Known Issues

### ⚠️ Debug Logging (Non-Critical)
- **Issue**: 13 `print()` statements found in code
- **Impact**: These will appear in release builds
- **Files Affected**:
  - `lib/core/errors/error_handler.dart`
  - `lib/core/services/model_preloader.dart`
  - `lib/core/services/sound_service.dart`
  - `lib/features/hearts/presentation/providers/hearts_provider.dart`
  - `lib/shared/services/xp_celebration_service.dart`
- **Recommendation**: Replace with `debugPrint()` in future updates
- **Severity**: LOW (mostly error logging)

## Distribution

### Google Play Store
1. Build app bundle: `flutter build appbundle --release`
2. Upload to Play Console: `build/app/outputs/bundle/release/app-release.aab`
3. Complete release information
4. Submit for review

### Direct APK Distribution
1. Build APK: `flutter build apk --release`
2. Share file: `build/app/outputs/flutter-apk/app-release.apk`
3. Users must enable "Install from unknown sources"

## Troubleshooting

### Build Fails
```bash
# Clean and rebuild
cd /Users/nguyennt/Documents/luuniensuki-lms/mobile
/Users/nguyennt/development/flutter/bin/flutter clean
/Users/nguyennt/development/flutter/bin/flutter pub get
/Users/nguyennt/development/flutter/bin/flutter build apk --release --verbose
```

### ProGuard Issues
If you encounter runtime errors like ClassNotFoundException:
1. Check the error in logcat
2. Update `android/app/proguard-rules.pro` to keep the affected classes
3. Rebuild

### Keystore Issues
- Ensure keystore exists: `/Users/nguyennt/Documents/luuniensuki-lms/release-keystore.jks`
- Verify key.properties has correct path and credentials
- Password: Suongnguyen83

## Important Reminders

1. **Backup Keystore**: Store keystore and credentials securely
2. **API Endpoint**: Verify production API is accessible
3. **Version Increment**: Update version for each release
4. **Testing**: Always test release build before distribution
5. **Documentation**: Keep RELEASE_CONFIGURATION.md updated

## Support Documentation

- **Full Report**: `RELEASE_CONFIGURATION.md`
- **Verification Script**: `check_release_config.sh`
- **ProGuard Rules**: `android/app/proguard-rules.pro`

---

**Build Status**: ✅ Ready for Production Release
**Last Updated**: Version 1.6.0+7
**Configuration**: All requirements R-B1 to R-B5 completed

