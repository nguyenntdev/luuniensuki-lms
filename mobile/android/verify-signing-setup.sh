#!/bin/bash

# Script to verify Android signing setup
# Run this from the mobile/android directory

echo "🔍 Verifying Android Signing Setup"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "build.gradle" ]; then
    echo "❌ Error: Please run this script from mobile/android directory"
    exit 1
fi

echo "✅ Running from correct directory"
echo ""

# Check for shared debug keystore
echo "📦 Debug Keystore Configuration:"
if [ -f "debug.keystore" ]; then
    echo "✅ Shared debug.keystore exists"

    # Verify it's a valid keystore
    if keytool -list -keystore debug.keystore -storepass android -alias androiddebugkey > /dev/null 2>&1; then
        echo "✅ debug.keystore is valid and contains androiddebugkey"

        # Show fingerprint
        echo ""
        echo "Debug Keystore Certificate Fingerprint:"
        keytool -list -keystore debug.keystore -storepass android -alias androiddebugkey | grep -A 1 "Certificate fingerprint"
    else
        echo "⚠️  Warning: debug.keystore exists but appears invalid"
    fi
else
    echo "❌ debug.keystore not found"
    echo "   This should be committed to the repository"
    echo "   Generate it with:"
    echo "   keytool -genkey -v -keystore debug.keystore -storepass android -alias androiddebugkey -keypass android -keyalg RSA -keysize 2048 -validity 10000 -dname \"CN=Android Debug,O=Android,C=US\""
fi

echo ""
echo "📦 Release Keystore Configuration:"

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
            echo "✅ Release keystore file exists: $STORE_FILE"

            # Try to verify it's a valid keystore
            KEY_ALIAS=$(grep "keyAlias=" key.properties | cut -d'=' -f2)
            echo ""
            echo "Release Keystore Certificate Fingerprint:"
            keytool -list -keystore "$STORE_FILE" -alias "$KEY_ALIAS" 2>&1 | grep -A 1 "Certificate fingerprint" || echo "   (Enter keystore password to view)"
        else
            echo "⚠️  Warning: Release keystore file not found: $STORE_FILE"
            echo "   Please verify the storeFile path in key.properties"
        fi
    else
        echo "⚠️  Warning: key.properties is missing some required fields"
    fi
else
    echo "ℹ️  key.properties not found (release builds will use debug signing)"
    echo "   To set up release signing:"
    echo "   1. cp key.properties.template key.properties"
    echo "   2. Edit key.properties with your keystore details"
    echo "   See RELEASE_SIGNING.md for detailed instructions"
fi

echo ""
echo "📄 Documentation:"

# Check for documentation
if [ -f "RELEASE_SIGNING.md" ]; then
    echo "✅ RELEASE_SIGNING.md documentation exists"
else
    echo "❌ RELEASE_SIGNING.md not found"
fi

echo ""
echo "🔧 Build Configuration:"

# Check build.gradle for signing config
if grep -q "signingConfigs {" app/build.gradle && \
   grep -q "sharedDebugKeystoreFile\|debug.keystore" app/build.gradle; then
    echo "✅ app/build.gradle has shared debug keystore configuration"
else
    echo "⚠️  app/build.gradle might be missing shared debug keystore configuration"
fi

if grep -q "keystorePropertiesFile" app/build.gradle; then
    echo "✅ app/build.gradle has release signing configuration"
else
    echo "❌ app/build.gradle is missing release signing configuration"
fi

echo ""
echo "🔒 Security:"

# Check .gitignore
if [ -f ".gitignore" ]; then
    if grep -q "key.properties" .gitignore; then
        echo "✅ .gitignore excludes key.properties"
    else
        echo "⚠️  Warning: key.properties should be in .gitignore"
    fi

    if grep -q "!debug.keystore" .gitignore; then
        echo "✅ .gitignore allows debug.keystore (as intended)"
    else
        if grep -q "\\.keystore" .gitignore || grep -q "keystore" .gitignore; then
            echo "⚠️  Warning: .gitignore might exclude debug.keystore"
            echo "   Add '!debug.keystore' to allow it"
        fi
    fi
fi

echo ""
echo "=========================================="

# Summary
echo ""
DEBUG_READY=false
RELEASE_READY=false

if [ -f "debug.keystore" ]; then
    DEBUG_READY=true
fi

if [ -f "key.properties" ] && [ -f "$STORE_FILE" ]; then
    RELEASE_READY=true
fi

if [ "$DEBUG_READY" = true ]; then
    echo "✅ Debug builds configured with shared keystore"
    echo "   Ready to build: flutter build apk --debug"
else
    echo "⚠️  Debug keystore setup incomplete"
fi

echo ""

if [ "$RELEASE_READY" = true ]; then
    echo "✅ Release builds configured with production keystore"
    echo "   Ready to build: flutter build apk --release"
else
    echo "ℹ️  Release keystore not configured (will fall back to debug)"
    echo "   See RELEASE_SIGNING.md for setup instructions"
fi

echo ""


