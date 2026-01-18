#!/bin/bash

# Release Build Script for Luuniensuki LMS Mobile App
# Version: 1.6.0+7
# Description: Automated build script for production release

set -e  # Exit on error

echo "=========================================="
echo "Luuniensuki LMS - Release Build"
echo "Version: 1.6.0+7"
echo "=========================================="
echo ""

# Check if we're in the mobile directory
if [ ! -f "pubspec.yaml" ]; then
    echo "❌ Error: pubspec.yaml not found. Please run from mobile directory."
    exit 1
fi

# Check if key.properties exists
if [ ! -f "android/key.properties" ]; then
    echo "❌ Error: android/key.properties not found."
    echo "   Release signing requires key.properties file."
    exit 1
fi

# Check if keystore exists
KEYSTORE_PATH=$(grep "storeFile=" android/key.properties | cut -d'=' -f2)
if [ ! -f "$KEYSTORE_PATH" ]; then
    echo "❌ Error: Keystore not found at: $KEYSTORE_PATH"
    exit 1
fi

echo "✅ Release signing configuration verified"
echo ""

# Clean previous builds
echo "🧹 Cleaning previous builds..."
flutter clean

# Get dependencies
echo "📦 Getting dependencies..."
flutter pub get

# Run code generation if needed
if [ -d "lib" ] && grep -r "@riverpod\|@freezed" lib --include="*.dart" > /dev/null 2>&1; then
    echo "🔧 Running code generation..."
    dart run build_runner build --delete-conflicting-outputs
fi

echo ""
echo "🏗️  Building release APK..."
echo ""

# Build release APK
flutter build apk --release

# Check build success
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Build Successful!"
    echo "=========================================="
    echo ""
    
    # Get APK info
    APK_PATH="build/app/outputs/flutter-apk/app-release.apk"
    if [ -f "$APK_PATH" ]; then
        APK_SIZE=$(ls -lh "$APK_PATH" | awk '{print $5}')
        echo "📱 APK Location: $APK_PATH"
        echo "📊 APK Size: $APK_SIZE"
        echo ""
        
        # Copy to builds directory
        mkdir -p builds
        cp "$APK_PATH" "builds/app-release-v1.6.0+7.apk"
        echo "💾 Copied to: builds/app-release-v1.6.0+7.apk"
        echo ""
    fi
    
    echo "Next Steps:"
    echo "1. Test the APK on physical devices"
    echo "2. Verify production API connectivity"
    echo "3. Test offline functionality"
    echo "4. Check ProGuard doesn't break features"
    echo ""
    echo "Install command:"
    echo "  adb install $APK_PATH"
    echo ""
    
else
    echo ""
    echo "❌ Build Failed!"
    echo "Please check the error messages above."
    exit 1
fi

