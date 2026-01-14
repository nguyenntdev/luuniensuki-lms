# Android APK Signing - Quick Setup Guide

## ✅ What's Already Configured

Good news! The "app not installed" error has been fixed with a **shared debug keystore**.

### Debug Builds (Development)

✅ **Already configured** - No action needed!

- Shared `debug.keystore` is committed to the repository
- All developers automatically use the same debug signature
- No more "app not installed" errors when switching between machines

**Just build and run:**
```bash
cd mobile
flutter run
# or
flutter build apk --debug
```

---

## 🔐 Optional: Release Keystore Setup

Only needed if you're building production APKs for distribution or Google Play Store.

### Step 1: Generate Release Keystore (One-time)

```bash
keytool -genkey -v -keystore ~/release-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 -alias release
```

**Important:** 
- Choose a strong password and remember it!
- Backup the keystore file securely
- You CANNOT recover it if lost

### Step 2: Configure key.properties

```bash
cd mobile/android
cp key.properties.template key.properties
# Edit key.properties with your actual values
```

Example `key.properties`:
```properties
storePassword=your-keystore-password
keyPassword=your-key-password
keyAlias=release
storeFile=/absolute/path/to/release-keystore.jks
```

### Step 3: Build Release APK

```bash
cd mobile
flutter build apk --release
```

---

## 🔍 Verify Your Setup

Run the verification script:

```bash
cd mobile/android
./verify-signing-setup.sh
```

This will check:
- ✅ Shared debug keystore is present and valid
- ✅ Release keystore configuration (if applicable)
- ✅ Build configuration is correct
- ✅ .gitignore excludes sensitive files

---

## 🚑 Troubleshooting

### Still getting "App not installed" error?

**Solution 1:** Uninstall the existing app first
```bash
adb uninstall com.luuniensuki.lms
# Then install the new APK
adb install build/app/outputs/flutter-apk/app-debug.apk
```

**Solution 2:** Clean and rebuild
```bash
cd mobile
flutter clean
flutter build apk --debug
```

**Solution 3:** Verify debug keystore exists
```bash
ls mobile/android/debug.keystore  # Should exist
```

### Build errors?

Check the configuration:
```bash
cd mobile/android
./verify-signing-setup.sh
```

---

## 📚 Documentation

For detailed information, see:

- **[RELEASE_SIGNING.md](./RELEASE_SIGNING.md)** - Complete signing configuration guide
- **[DEBUG_KEYSTORE.md](./DEBUG_KEYSTORE.md)** - Information about the shared debug keystore
- **[APK_FIX_SUMMARY.md](./APK_FIX_SUMMARY.md)** - Technical implementation details

---

## ⚡ TL;DR

**For Development:**
- ✅ Already fixed! Just run `flutter run` or `flutter build apk --debug`

**For Production:**
- 📖 Follow release keystore setup in [RELEASE_SIGNING.md](./RELEASE_SIGNING.md)

**Having Issues:**
- 🔍 Run `./verify-signing-setup.sh` to diagnose
- 📧 Check [RELEASE_SIGNING.md](./RELEASE_SIGNING.md) troubleshooting section

