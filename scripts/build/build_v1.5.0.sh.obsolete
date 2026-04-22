#!/bin/bash

# Build script cho Lưu Niên Sử Kí LMS v1.5.0
# Gamification & UX Improvements Release

set -e

echo "🚀 Building Lưu Niên Sử Kí LMS v1.5.0..."
echo "================================================"

# Navigate to mobile directory
cd "$(dirname "$0")/mobile"

# Check Flutter
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter not found. Please install Flutter first."
    exit 1
fi

echo "📦 Step 1: Getting dependencies..."
flutter pub get

echo "🔧 Step 2: Running code generator..."
flutter pub run build_runner build --delete-conflicting-outputs

echo "🧹 Step 3: Cleaning previous builds..."
flutter clean
flutter pub get

echo "📱 Step 4: Building release APK..."
flutter build apk --release

echo "📂 Step 5: Copying APK to builds folder..."
mkdir -p ../builds
cp build/app/outputs/flutter-apk/app-release.apk ../builds/luuniensuki-lms-v1.5.0-build6.apk

echo ""
echo "✅ Build complete!"
echo "================================================"
echo "APK location: builds/luuniensuki-lms-v1.5.0-build6.apk"
echo ""
echo "📋 What's new in v1.5.0:"
echo "  - ✨ Onboarding Screen"
echo "  - 🔊 Sound Effects System"
echo "  - ⏳ Shimmer Loading Skeletons"
echo "  - 🏆 Enhanced Achievements/Badges"
echo "  - 💡 Quiz Hint System"
echo "  - 💾 Quiz Progress Auto-Save"
echo "  - 🐛 Bug fixes & improvements"
echo ""

