# Shared Debug Keystore

## What is this?

The `debug.keystore` file in this directory is a **shared debug keystore** used by all developers for debug builds.

## Why does this exist?

### The Problem
By default, Android creates a unique debug keystore on each developer's machine. This causes "App not installed" errors when:
- Developer A builds an APK and installs it on a device
- Developer B builds an APK and tries to install it on the same device
- Android sees different signatures and blocks the installation

### The Solution
We use a **shared debug keystore** committed to the repository. Now all developers sign debug builds with the same keystore, eliminating signature mismatches.

## Is this safe?

**Yes!** This is completely safe for development because:

1. **Standard credentials**: Uses the well-known Android debug credentials
   - Keystore password: `android`
   - Key alias: `androiddebugkey`
   - Key password: `android`

2. **Debug only**: Only used for debug builds, never for production

3. **Cannot be used maliciously**: 
   - Android prevents debug-signed APKs from being uploaded to Google Play
   - These credentials are publicly documented by Google

4. **Common practice**: Many teams commit shared debug keystores to avoid this exact problem

## Keystore Details

```
File: debug.keystore
Alias: androiddebugkey
Store Password: android
Key Password: android
Algorithm: RSA
Key Size: 2048 bits
Validity: 10,000 days
Distinguished Name: CN=Android Debug, O=Android, C=US
```

## How to view the certificate

```bash
keytool -list -v -keystore debug.keystore -storepass android -alias androiddebugkey
```

## For Production Releases

**Important:** This debug keystore should **NEVER** be used for production releases!

For production builds:
1. Use a separate, secure release keystore
2. Follow the instructions in [RELEASE_SIGNING.md](./RELEASE_SIGNING.md)

## Technical Details

The `app/build.gradle` is configured to:
1. Check if `debug.keystore` exists in this directory
2. If yes, use it for all debug builds
3. If no, fall back to the default system debug keystore

This means zero configuration for developers - just clone and build!

## Regenerating

If you need to regenerate this keystore (e.g., if it becomes corrupted):

```bash
cd mobile/android
rm debug.keystore
keytool -genkey -v -keystore debug.keystore \
  -storepass android \
  -alias androiddebugkey \
  -keypass android \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -dname "CN=Android Debug,O=Android,C=US"
```

**Important:** After regenerating, all developers must uninstall existing apps on their test devices before installing new builds.

## References

- [Android Official Documentation - Sign your debug build](https://developer.android.com/studio/publish/app-signing#debug-mode)
- [Stack Overflow - Sharing debug keystore](https://stackoverflow.com/questions/4746510/can-i-share-my-debug-keystore-with-other-developers)

