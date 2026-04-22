# Release Signing Setup Checklist

Use this checklist to set up release signing on your machine.

## ✅ Initial Setup (One-Time)

- [ ] **1. Read Documentation**
  - [ ] Review `RELEASE_SIGNING.md` for complete instructions
  - [ ] Understand security implications

- [ ] **2. Obtain or Generate Keystore**
  
  **Option A: Team already has a keystore**
  - [ ] Obtain keystore file from team securely (encrypted storage/password manager)
  - [ ] Obtain keystore passwords from team securely
  - [ ] Place keystore in secure location (e.g., `~/release-keystore.jks`)
  
  **Option B: Creating new keystore (first team member)**
  - [ ] Run: `keytool -genkey -v -keystore ~/release-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias release`
  - [ ] Save passwords in password manager
  - [ ] Share keystore with team securely
  - [ ] Backup keystore to multiple secure locations

- [ ] **3. Create key.properties File**
  - [ ] Navigate to: `cd mobile/android`
  - [ ] Copy template: `cp key.properties.template key.properties`
  - [ ] Edit file: `nano key.properties` (or your preferred editor)
  - [ ] Fill in all fields:
    - [ ] `storePassword=your-actual-password`
    - [ ] `keyPassword=your-actual-password`
    - [ ] `keyAlias=release`
    - [ ] `storeFile=/absolute/path/to/release-keystore.jks`
  - [ ] Save file
  - [ ] Verify file is NOT tracked by git: `git status` (should not appear)

- [ ] **4. Verify Setup**
  - [ ] Run verification script: `./verify-signing-setup.sh`
  - [ ] All checks should pass ✅
  - [ ] Fix any warnings

- [ ] **5. Test Build**
  - [ ] Build release APK: `cd .. && flutter build apk --release`
  - [ ] Build should succeed without errors
  - [ ] APK should be at: `build/app/outputs/flutter-apk/app-release.apk`

- [ ] **6. Test Installation**
  - [ ] Install APK on test device
  - [ ] App should install successfully
  - [ ] App should run correctly

## ✅ Security Checklist

- [ ] **Keystore Security**
  - [ ] Keystore file backed up to secure cloud storage
  - [ ] Keystore file backed up to encrypted external drive
  - [ ] Keystore file backed up to password manager (if possible)
  - [ ] Team knows where backups are stored

- [ ] **Password Security**
  - [ ] Passwords stored in password manager
  - [ ] Passwords documented in team's secure documentation
  - [ ] Passwords NOT in plain text anywhere

- [ ] **Git Security**
  - [ ] Verified `key.properties` is in `.gitignore`
  - [ ] Verified `*.jks` is in `.gitignore`
  - [ ] Verified `*.keystore` is in `.gitignore`
  - [ ] Run `git status` to ensure no sensitive files are staged

## ✅ Team Onboarding Checklist

When new team members join:

- [ ] Share this checklist
- [ ] Share keystore file securely (encrypted channel)
- [ ] Share passwords securely (password manager)
- [ ] Verify they can build release APK
- [ ] Verify APK signature matches team's keystore

## ✅ Regular Maintenance

Every 3-6 months:

- [ ] Verify keystore backups are still accessible
- [ ] Test restore from backup
- [ ] Update team documentation if needed
- [ ] Verify all team members have access

## ✅ Pre-Release Checklist

Before each release:

- [ ] Verify using correct keystore (not debug)
- [ ] Run verification script: `./verify-signing-setup.sh`
- [ ] Build release APK
- [ ] Test installation on clean device
- [ ] Test update installation over previous version
- [ ] Verify APK signature: `jarsigner -verify -verbose -certs build/app/outputs/flutter-apk/app-release.apk`

## 🆘 Troubleshooting

If something doesn't work:

1. Run verification script: `./verify-signing-setup.sh`
2. Check common issues in `RELEASE_SIGNING.md`
3. Verify keystore file exists and path is correct
4. Verify passwords are correct
5. Clean and rebuild: `flutter clean && flutter build apk --release`

## 📝 Notes

- Date completed: _______________
- Completed by: _______________
- Keystore location: _______________
- Keystore backup locations: _______________
- Team members with access: _______________

---

**Status**: [ ] Not Started  [ ] In Progress  [ ] Complete

**Last Updated**: _______________

