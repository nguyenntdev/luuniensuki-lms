#!/bin/bash
# Script to install the Cửu Đỉnh Ký app via ADB

set -e

echo "🔍 Checking for connected devices..."
adb devices

echo ""
echo "📱 Uninstalling existing app (if any)..."
adb uninstall com.cuudinhky.app 2>/dev/null || echo "   (App was not installed)"

echo ""
echo "🚀 Installing latest APK..."

# Check which APK to install
if [ -f "mobile/build/app/outputs/flutter-apk/app-debug.apk" ]; then
    APK_PATH="mobile/build/app/outputs/flutter-apk/app-debug.apk"
    echo "   Using debug APK from build folder..."
elif [ -f "mobile/build/app/outputs/flutter-apk/app-release.apk" ]; then
    APK_PATH="mobile/build/app/outputs/flutter-apk/app-release.apk"
    echo "   Using release APK from build folder..."
elif [ -f "builds/cuudinhky-latest.apk" ]; then
    APK_PATH="builds/cuudinhky-latest.apk"
    echo "   Using latest APK from builds folder..."
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
adb shell am start -n com.cuudinhky.app/.MainActivity

echo ""
echo "Done! The app should now be open on your device."

