#!/bin/bash

# Script to verify release signing setup
# Run this from the mobile/android directory

echo "🔍 Verifying Android Release Signing Setup"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "build.gradle" ]; then
    echo "❌ Error: Please run this script from mobile/android directory"
    exit 1
fi

echo "✅ Running from correct directory"
echo ""

# Check for key.properties.template
if [ -f "key.properties.template" ]; then
    echo "✅ key.properties.template exists"
else
    echo "❌ key.properties.template not found"
fi

# Check for key.properties
if [ -f "key.properties" ]; then
    echo "✅ key.properties exists"
    
    # Verify it has the required fields
    if grep -q "storePassword=" key.properties && \
       grep -q "keyPassword=" key.properties && \
       grep -q "keyAlias=" key.properties && \
       grep -q "storeFile=" key.properties; then
        echo "✅ key.properties has all required fields"
        
        # Check if storeFile exists
        STORE_FILE=$(grep "storeFile=" key.properties | cut -d'=' -f2)
        # Expand ~ to home directory
        STORE_FILE="${STORE_FILE/#\~/$HOME}"
        
        if [ -f "$STORE_FILE" ]; then
            echo "✅ Keystore file exists: $STORE_FILE"
        else
            echo "⚠️  Warning: Keystore file not found: $STORE_FILE"
            echo "   Please verify the storeFile path in key.properties"
        fi
    else
        echo "⚠️  Warning: key.properties is missing some required fields"
    fi
else
    echo "⚠️  key.properties not found (will use debug signing)"
    echo "   To set up release signing:"
    echo "   1. cp key.properties.template key.properties"
    echo "   2. Edit key.properties with your keystore details"
    echo "   See RELEASE_SIGNING.md for detailed instructions"
fi

echo ""

# Check for documentation
if [ -f "RELEASE_SIGNING.md" ]; then
    echo "✅ RELEASE_SIGNING.md documentation exists"
else
    echo "❌ RELEASE_SIGNING.md not found"
fi

echo ""

# Check build.gradle for signing config
if grep -q "signingConfigs {" app/build.gradle && \
   grep -q "keystorePropertiesFile" app/build.gradle; then
    echo "✅ app/build.gradle has signing configuration"
else
    echo "❌ app/build.gradle is missing signing configuration"
fi

# Check AndroidManifest.xml for allowBackup
if grep -q 'android:allowBackup="false"' app/src/main/AndroidManifest.xml; then
    echo "✅ AndroidManifest.xml has allowBackup=false"
else
    echo "⚠️  AndroidManifest.xml is missing allowBackup=false"
fi

echo ""

# Check .gitignore
if grep -q "key.properties" .gitignore && \
   grep -q "\.jks" .gitignore; then
    echo "✅ .gitignore includes keystore files"
else
    echo "⚠️  Warning: .gitignore might not exclude keystore files"
fi

echo ""
echo "=========================================="

# Check if ready for release build
if [ -f "key.properties" ] && [ -f "$STORE_FILE" ]; then
    echo "🎉 Setup complete! Ready to build release APK"
    echo ""
    echo "To build release APK, run:"
    echo "  cd .."
    echo "  flutter build apk --release"
else
    echo "⚙️  Setup incomplete - see warnings above"
    echo ""
    echo "For setup instructions, see: RELEASE_SIGNING.md"
fi

echo ""

