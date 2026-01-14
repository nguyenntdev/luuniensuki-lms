#!/bin/bash
# Script to install the LuuNienSuki LMS app via ADB

set -e

echo "🔍 Checking for connected devices..."
adb devices

echo ""
echo "📱 Uninstalling existing app (if any)..."
adb uninstall com.luuniensuki.lms 2>/dev/null || echo "   (App was not installed)"

echo ""
echo "🚀 Installing latest APK..."

# Check which APK to install
if [ -f "mobile/build/app/outputs/flutter-apk/app-debug.apk" ]; then
    APK_PATH="mobile/build/app/outputs/flutter-apk/app-debug.apk"
    echo "   Using debug APK from build folder..."
elif [ -f "mobile/build/app/outputs/flutter-apk/app-release.apk" ]; then
    APK_PATH="mobile/build/app/outputs/flutter-apk/app-release.apk"
    echo "   Using release APK from build folder..."
elif [ -f "builds/luuniensuki-lms-v1.4.0-build5.apk" ]; then
    APK_PATH="builds/luuniensuki-lms-v1.4.0-build5.apk"
    echo "   Using APK v1.4.0 from builds folder..."
else
    echo "❌ No APK found! Please build first:"
    echo "   cd mobile && flutter build apk --debug"
    exit 1
fi

echo "   APK: $APK_PATH"
adb install -r "$APK_PATH"

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎮 Launching app..."
adb shell am start -n com.luuniensuki.lms/.MainActivity

echo ""
echo "Done! The app should now be open on your device."

