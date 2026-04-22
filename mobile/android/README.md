# Android Build Configuration

This directory contains the Android-specific configuration for the Flutter mobile app.

## 🔐 Release Signing Setup

To avoid APK installation failures and properly sign your release builds, follow these steps:

### Quick Start

1. **Read the documentation:**
   ```bash
   cat RELEASE_SIGNING.md
   ```

2. **Generate a release keystore** (one-time):
   ```bash
   keytool -genkey -v -keystore ~/release-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias release
   ```

3. **Create your key.properties file:**
   ```bash
   cp key.properties.template key.properties
   # Edit key.properties with your actual values
   ```

4. **Verify your setup:**
   ```bash
   ./verify-signing-setup.sh
   ```

5. **Build release APK:**
   ```bash
   cd ..
   flutter build apk --release
   ```

## 📚 Documentation

- **[RELEASE_SIGNING.md](RELEASE_SIGNING.md)** - Comprehensive guide for release signing setup
- **[APK_FIX_SUMMARY.md](APK_FIX_SUMMARY.md)** - Summary of the signature mismatch fix implementation
- **[key.properties.template](key.properties.template)** - Template for keystore configuration

## 🛠️ Tools

- **[verify-signing-setup.sh](verify-signing-setup.sh)** - Script to verify your signing configuration

## ⚠️ Important Notes

### Security
- ✅ `key.properties` is in `.gitignore` - DO NOT commit it
- ✅ `*.jks` and `*.keystore` files are in `.gitignore` - DO NOT commit them
- ✅ Backup your keystore and passwords securely

### Build Behavior
- **With `key.properties`**: Uses release keystore (production-ready)
- **Without `key.properties`**: Falls back to debug keystore (development only)

### Common Issues

**Problem:** "App not installed" error
- **Cause:** Signature mismatch between installed app and new APK
- **Solution:** 
  - For development: Uninstall existing app first
  - For production: Ensure all builds use the same release keystore

**Problem:** Build fails with keystore errors
- **Solution:** Run `./verify-signing-setup.sh` to diagnose issues

## 📁 File Structure

```
mobile/android/
├── app/
│   ├── build.gradle              # Updated with release signing config
│   └── src/main/
│       └── AndroidManifest.xml   # Updated with allowBackup=false
├── key.properties.template       # Template for keystore config
├── key.properties               # Your actual config (gitignored)
├── RELEASE_SIGNING.md           # Detailed documentation
├── APK_FIX_SUMMARY.md          # Implementation summary
├── verify-signing-setup.sh     # Setup verification script
└── .gitignore                  # Excludes sensitive files
```

## 🚀 Building

### Debug Build
```bash
flutter build apk --debug
# or
flutter run
```

### Release Build
```bash
flutter build apk --release
```

### Build Split APKs (per ABI)
```bash
flutter build apk --split-per-abi
```

## 📱 Installation

### From Development Machine
```bash
flutter install
```

### Manual Installation
```bash
adb install build/app/outputs/flutter-apk/app-release.apk
```

## 🔄 Migration from Debug Signing

If you previously distributed APKs signed with debug keystore:
1. Users must uninstall the old app
2. Install the new properly-signed APK
3. This is a one-time migration

## 💡 Tips

1. **Team Sharing**: Share the keystore and `key.properties` values securely with your team
2. **Backup**: Keep multiple backups of your keystore in secure locations
3. **Documentation**: Document where the keystore is stored and who has access
4. **CI/CD**: Store keystore and credentials as encrypted secrets in your CI/CD system

## 🆘 Need Help?

1. Check [RELEASE_SIGNING.md](RELEASE_SIGNING.md) for detailed instructions
2. Run `./verify-signing-setup.sh` to diagnose issues
3. Review [APK_FIX_SUMMARY.md](APK_FIX_SUMMARY.md) for implementation details

---

**Last Updated:** 2024
**Status:** ✅ Ready for production builds

