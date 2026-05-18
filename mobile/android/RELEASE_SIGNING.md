# Android Signing Configuration Guide

## Overview

This guide explains how to set up signing for the Android app to avoid APK installation failures caused by signature mismatches.

## Problem Statement

The "App not installed" error occurs when Android detects a signature mismatch between:
- An installed app and a new APK you're trying to install
- APKs built on different machines using different keystores

### Root Cause

By default, each developer's machine generates its own unique debug keystore. When you build an APK on Machine A and try to install it over an APK built on Machine B, Android blocks the installation because the signatures don't match.

## Solutions Implemented

We've implemented **two complementary solutions**:

### 1. Shared Debug Keystore (For Development) ✅
- A shared `debug.keystore` file is committed to the repository
- All developers use the same debug keystore for debug builds
- **Safe for development** - uses standard Android debug credentials
- ✅ **Prevents "app not installed" errors during development**

### 2. Release Keystore (For Production) 🔐
- A separate, secure release keystore for production builds
- **Must be kept private** and never committed to version control
- Required for Google Play Store submissions
- ✅ **Production-ready signing**

---

## Quick Start

### For Development (Debug Builds)

**Good News!** Debug builds are already configured with a shared keystore. Just build and run:

```bash
cd mobile
flutter run
# or
flutter build apk --debug
```

The shared `debug.keystore` in the repository ensures all developers get consistent signatures.

### For Production (Release Builds)

If you need to create production APKs for distribution or Google Play:

1. **One-time setup**: Follow [Release Keystore Setup](#release-keystore-setup) below
2. **Build**: `flutter build apk --release`

---

## Shared Debug Keystore (Development)

### What is it?

The `mobile/android/debug.keystore` file in this repository is a **shared debug keystore** used by all developers for debug builds.

**Key characteristics:**
- ✅ **Safe to commit** - Uses standard Android debug credentials
- ✅ **Shared across all machines** - No more signature mismatches
- ✅ **Automatic** - No setup required
- ⚠️ **Debug only** - Not for production use

**Credentials (public information):**
```
Keystore: mobile/android/debug.keystore
Alias: androiddebugkey
Store Password: android
Key Password: android
```

### Why is this safe?

These are the **standard Android debug credentials** used by Android SDK. It's safe to commit because:
- It's only used for development/testing
- It uses well-known public credentials
- It should never be used for production releases
- Android prevents debug-signed APKs from being uploaded to Google Play

### How it works

The `app/build.gradle` is configured to:
1. Check if `debug.keystore` exists in `mobile/android/`
2. If yes, use it for all debug builds
3. If no, fall back to the default system debug keystore

This means **zero configuration** for debug builds! Just clone and build.

---

## Release Keystore Setup

For production releases, you need a **private release keystore**. Follow these steps:

### Step 1: Generate a Release Keystore

**⚠️ Important: Only do this once per project!**

Run the following command to create a new release keystore:

```bash
keytool -genkey -v -keystore ~/release-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias release
```

You'll be prompted to enter:
- **Keystore password**: Choose a strong password (remember it!)
- **Key password**: Can be the same as keystore password or different
- **Name, Organization, etc.**: Fill in your details

**Critical Notes:**
- 🔐 Store the keystore file in a secure location (e.g., `~/release-keystore.jks`)
- 🔐 Remember your passwords - they CANNOT be recovered if lost
- 🔐 The keystore is valid for 10,000 days (~27 years)
- 🔐 If you lose this keystore, you cannot update your app on Google Play

### Step 2: Create key.properties File

1. Copy the template file:
   ```bash
   cd mobile/android
   cp key.properties.template key.properties
   ```

2. Edit `key.properties` with your actual values:
   ```properties
   storePassword=your-actual-keystore-password
   keyPassword=your-actual-key-password
   keyAlias=release
   storeFile=/absolute/path/to/release-keystore.jks
   ```

   **Path Examples:**
   - Linux/Mac: `/home/username/release-keystore.jks` or `~/release-keystore.jks`
   - Windows: `C:\\Users\\username\\release-keystore.jks`

3. The file should already be in `.gitignore` to prevent committing credentials.



### Step 3: Build Release APK

Once configured, build your release APK:

```bash
cd mobile
flutter build apk --release
```

The signed APK will be located at:
```
mobile/build/app/outputs/flutter-apk/app-release.apk
```

---

## Build Configuration Details

### Debug Builds

**Configuration in `app/build.gradle`:**
```groovy
debug {
    signingConfig signingConfigs.debug
}
```

**Behavior:**
- Uses `mobile/android/debug.keystore` if it exists
- Falls back to default system debug keystore if not found
- Same signature for all developers using the shared keystore

### Release Builds

**Configuration in `app/build.gradle`:**
```groovy
release {
    signingConfig = keystorePropertiesFile.exists() ? signingConfigs.release : signingConfigs.debug
}
```

**Behavior:**
- If `key.properties` exists → Uses release keystore (production-ready)
- If `key.properties` missing → Falls back to debug keystore (for testing only)

**⚠️ Warning:** Don't distribute release APKs signed with debug keystore to users!

---

## Security Best Practices

### ⚠️ Critical: Backup Your Release Keystore

**IMPORTANT:** If you lose your release keystore or forget the passwords:
- You CANNOT update your app on the Play Store
- You will need to publish a new app with a different package name
- Users will need to uninstall and reinstall

**Backup Strategy:**
1. Store the keystore file in multiple secure locations:
   - Encrypted cloud storage (Google Drive, Dropbox, etc.)
   - Password manager with file attachments
   - Team's secure credential vault
2. Document the keystore location in your team's secure documentation
3. Store passwords in a password manager

### 🔒 Keep Release Credentials Secure

- **NEVER** commit `key.properties` or the release keystore to version control
- **NEVER** share the keystore or passwords in plain text (email, chat, etc.)
- Use secure methods to share with team members (encrypted channels, password managers)
- The `.gitignore` already excludes these files

### ✅ Debug Keystore is Safe to Commit

- The shared `debug.keystore` **IS safe to commit** to version control
- It uses standard Android debug credentials (publicly known)
- It's only for development/testing, never for production

### 👥 Team Sharing

**For the Debug Keystore:**
- Already in the repository - no action needed
- All team members automatically use the same debug signature

**For the Release Keystore:**
Each team member needs:
1. A copy of the release keystore file (share via encrypted storage)
2. The passwords (share via secure password manager)
3. Their own `key.properties` file with the correct local path

---

## Troubleshooting

### "App not installed" Error

**Symptom:** Installation fails with "App not installed" message

**Possible Causes and Solutions:**

1. **Signature mismatch - most common**
   - **Cause:** Device has an app with a different signature
   - **Solution:** Uninstall the existing app first, then install the new APK
   ```bash
   adb uninstall com.luuniensuki.lms
   adb install path/to/app.apk
   ```

2. **Missing shared debug keystore**
   - **Cause:** `debug.keystore` not in `mobile/android/`
   - **Solution:** Ensure you've pulled the latest code with the shared keystore
   ```bash
   git pull origin main
   ls mobile/android/debug.keystore  # Should exist
   ```

3. **Building release without key.properties**
   - **Cause:** Release APK signed with debug keystore (machine-specific)
   - **Solution:** Set up release keystore or use shared debug keystore for testing

### Build Fails: "Keystore file not found"

**Error:** `java.io.FileNotFoundException: /path/to/keystore.jks`

**Solution:**
- Verify the `storeFile` path in `key.properties` is correct and absolute
- Ensure the keystore file exists at that location
- Try using `~/` for home directory instead of full path

### Build Fails: "Incorrect password"

**Error:** `Keystore was tampered with, or password was incorrect`

**Solution:**
- Verify `storePassword` and `keyPassword` in `key.properties` are correct
- Check for extra spaces or special characters
- If passwords are truly lost, you'll need to generate a new keystore

### Shared Debug Keystore Not Working

**Symptom:** Still getting "app not installed" errors with debug builds

**Checklist:**
1. Verify `debug.keystore` exists in `mobile/android/`
2. Clean and rebuild:
   ```bash
   cd mobile
   flutter clean
   flutter build apk --debug
   ```
3. Uninstall existing app on device:
   ```bash
   adb uninstall com.luuniensuki.lms
   ```
4. Check `app/build.gradle` has the correct signing configuration

---

## Verification

### Verify Debug Keystore Setup

Run the verification script:
```bash
cd mobile/android
chmod +x verify-signing-setup.sh
./verify-signing-setup.sh
```

### Verify APK Signature

To check which keystore signed an APK:

```bash
# View APK signature
jarsigner -verify -verbose -certs mobile/build/app/outputs/flutter-apk/app-release.apk

# Extract certificate fingerprint
keytool -printcert -jarfile mobile/build/app/outputs/flutter-apk/app-release.apk
```

### Compare with Keystore

```bash
# View debug keystore details
keytool -list -v -keystore mobile/android/debug.keystore -storepass android -alias androiddebugkey

# View release keystore details (if you have one)
keytool -list -v -keystore ~/release-keystore.jks -alias release
```

The certificate fingerprints should match between the APK and the keystore used to sign it.

---

## Summary Checklist

### ✅ Development Setup (Debug Builds)
- [x] Shared `debug.keystore` exists in `mobile/android/`
- [x] `app/build.gradle` configured to use shared debug keystore
- [x] `.gitignore` allows `debug.keystore` to be committed
- [x] All developers use the same debug signature

### 🔐 Production Setup (Release Builds)
- [ ] Generated release keystore (`~/release-keystore.jks`)
- [ ] Created `key.properties` with correct paths and passwords
- [ ] Backed up release keystore to secure location
- [ ] Stored passwords in password manager
- [ ] Verified `.gitignore` excludes `key.properties` and release keystores

---

## Additional Resources

- [Official Android App Signing Documentation](https://developer.android.com/studio/publish/app-signing)
- [Flutter Deployment Documentation](https://docs.flutter.dev/deployment/android)
- [Gradle Signing Configuration](https://developer.android.com/studio/build/gradle-tips#sign-your-app)
- [Android Debug Keystore Info](https://developer.android.com/studio/publish/app-signing#debug-mode)

---

**Last Updated:** 2024
**Configuration Status:** ✅ Debug keystore configured | 🔐 Release keystore optional

