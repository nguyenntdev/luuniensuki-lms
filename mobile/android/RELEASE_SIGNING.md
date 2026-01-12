# Android Release Signing Guide

## Overview

This guide explains how to set up release signing for the Android app to avoid APK installation failures caused by signature mismatches.

## Problem Statement

When building release APKs without proper signing configuration, the app uses the debug keystore, which is machine-specific. This causes "App not installed" errors when:
- Users try to install an APK built on a different machine
- The device already has a version installed with a different debug signature

## Solution

Use a dedicated release keystore that is shared across all build machines and developers.

---

## Setup Instructions

### Step 1: Generate a Release Keystore

Run the following command to create a new release keystore:

```bash
keytool -genkey -v -keystore ~/release-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias release
```

You'll be prompted to enter:
- **Keystore password**: Choose a strong password
- **Key password**: Can be the same as keystore password or different
- **Name, Organization, etc.**: Fill in your details

**Important Notes:**
- Store the keystore file in a secure location (e.g., `~/release-keystore.jks`)
- Remember your passwords - you cannot recover them if lost
- The keystore is valid for 10,000 days (~27 years)

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

3. Verify the file is listed in `.gitignore` to prevent committing sensitive credentials.

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

## Security Best Practices

### ⚠️ Critical: Backup Your Keystore

**IMPORTANT:** If you lose your keystore or forget the passwords:
- You CANNOT update your app on the Play Store
- You will need to publish a new app with a different package name
- Users will need to uninstall and reinstall

**Backup Strategy:**
1. Store the keystore file in a secure location (encrypted cloud storage, password manager)
2. Keep multiple backups in different locations
3. Store passwords securely (password manager)
4. Document the keystore location and credentials in your team's secure documentation

### 🔒 Keep Credentials Secure

- **NEVER** commit `key.properties` or the keystore file to version control
- **NEVER** share the keystore or passwords in plain text (email, chat, etc.)
- Use secure methods to share with team members (encrypted channels, password managers)
- Add to `.gitignore`:
  ```
  key.properties
  *.jks
  *.keystore
  ```

### 👥 Team Sharing

For teams, securely share:
1. The keystore file (via encrypted storage)
2. The `key.properties` values (via secure password manager)

Each developer should:
1. Place the keystore in their local secure location
2. Create their own `key.properties` file with the correct local path

---

## Troubleshooting

### Build fails with "Keystore file not found"

**Error:** `java.io.FileNotFoundException: /path/to/keystore.jks`

**Solution:** 
- Verify the `storeFile` path in `key.properties` is correct and absolute
- Ensure the keystore file exists at that location

### Build fails with "Incorrect password"

**Error:** `Keystore was tampered with, or password was incorrect`

**Solution:**
- Verify `storePassword` and `keyPassword` in `key.properties` are correct
- Try regenerating the keystore if passwords are lost

### "App not installed" on device

**Error:** Installation failed on device

**Possible causes:**
1. **Signature mismatch:** Device has an app installed with different signature
   - Solution: Uninstall the existing app first
   
2. **No key.properties file:** Building with debug signature
   - Solution: Create `key.properties` as described above

### Building without key.properties

If `key.properties` doesn't exist, the build will fall back to the debug keystore. This is useful for:
- Quick local testing with `flutter run --release`
- CI/CD builds that don't need production signing

**Warning:** Debug-signed APKs should NOT be distributed to users.

---

## Verification

To verify your APK is properly signed with the release keystore:

```bash
# View APK signature
jarsigner -verify -verbose -certs mobile/build/app/outputs/flutter-apk/app-release.apk

# Check keystore details
keytool -list -v -keystore ~/release-keystore.jks -alias release
```

Compare the certificate fingerprints - they should match.

---

## Additional Resources

- [Official Android App Signing Documentation](https://developer.android.com/studio/publish/app-signing)
- [Flutter Deployment Documentation](https://docs.flutter.dev/deployment/android)
- [Gradle Signing Configuration](https://developer.android.com/studio/build/gradle-tips#sign-your-app)

---

## Summary

✅ **Done:**
- Generated release keystore
- Created `key.properties` file
- Built release APK successfully
- Backed up keystore securely

🔐 **Remember:**
- Keep keystore and passwords secure
- Never commit credentials to version control
- Maintain multiple backups
- Document everything for your team

