#!/bin/bash

# Diagnostic script for Android APK signing issues
# This script helps identify and fix common "app not installed" errors

echo "🔧 Android APK Signing Diagnostics"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Check if we're in the right directory
if [ ! -f "build.gradle" ]; then
    print_error "Please run this script from mobile/android directory"
    exit 1
fi

ISSUES_FOUND=0
FIXES_AVAILABLE=()

echo "Checking for common issues..."
echo ""

# Check 1: Debug keystore exists
echo "1. Checking debug keystore..."
if [ -f "debug.keystore" ]; then
    print_success "Shared debug.keystore found"
    
    # Verify it's valid
    if keytool -list -keystore debug.keystore -storepass android -alias androiddebugkey > /dev/null 2>&1; then
        print_success "Debug keystore is valid"
    else
        print_error "Debug keystore exists but is invalid"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        FIXES_AVAILABLE+=("regenerate-debug-keystore")
    fi
else
    print_error "Shared debug.keystore not found"
    print_warning "This is the most common cause of 'app not installed' errors"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
    FIXES_AVAILABLE+=("create-debug-keystore")
fi
echo ""

# Check 2: Build configuration
echo "2. Checking build.gradle configuration..."
if grep -q "sharedDebugKeystoreFile\|debug.keystore" app/build.gradle; then
    print_success "Build configuration includes shared debug keystore"
else
    print_warning "Build configuration might not reference debug.keystore"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi
echo ""

# Check 3: .gitignore configuration
echo "3. Checking .gitignore..."
if grep -q "!debug.keystore" .gitignore; then
    print_success ".gitignore allows debug.keystore to be committed"
elif grep -q "keystore\|\\.jks" .gitignore; then
    print_warning ".gitignore might exclude debug.keystore"
    print_info "This means it won't be shared with other developers"
fi
echo ""

# Check 4: Check if there are existing APKs with different signatures
echo "4. Checking for potential signature conflicts..."
APK_DIR="../build/app/outputs/flutter-apk"
if [ -d "$APK_DIR" ]; then
    APK_COUNT=$(find "$APK_DIR" -name "*.apk" 2>/dev/null | wc -l)
    if [ "$APK_COUNT" -gt 0 ]; then
        print_info "Found $APK_COUNT APK(s) in build directory"
        print_info "Run 'flutter clean' to remove old builds"
    fi
fi
echo ""

# Check 5: Release keystore configuration
echo "5. Checking release keystore configuration..."
if [ -f "key.properties" ]; then
    STORE_FILE=$(grep "storeFile=" key.properties | cut -d'=' -f2)
    STORE_FILE="${STORE_FILE/#\~/$HOME}"
    
    if [ -f "$STORE_FILE" ]; then
        print_success "Release keystore configured and found"
    else
        print_warning "key.properties exists but keystore file not found at: $STORE_FILE"
        print_info "This affects release builds only"
    fi
else
    print_info "No release keystore configured (using debug for release builds)"
    print_info "This is OK for development"
fi
echo ""

# Summary
echo "===================================="
echo ""

if [ $ISSUES_FOUND -eq 0 ]; then
    print_success "No critical issues found!"
    echo ""
    echo "If you're still experiencing 'app not installed' errors:"
    echo "1. Uninstall the existing app: adb uninstall com.luuniensuki.lms"
    echo "2. Clean the build: cd ../.. && flutter clean"
    echo "3. Rebuild: flutter build apk --debug"
else
    print_warning "Found $ISSUES_FOUND issue(s)"
    echo ""
    
    # Offer fixes
    if [[ " ${FIXES_AVAILABLE[@]} " =~ " create-debug-keystore " ]]; then
        echo "Would you like to create the shared debug.keystore? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo ""
            echo "Creating shared debug.keystore..."
            keytool -genkey -v -keystore debug.keystore \
                -storepass android \
                -alias androiddebugkey \
                -keypass android \
                -keyalg RSA \
                -keysize 2048 \
                -validity 10000 \
                -dname "CN=Android Debug,O=Android,C=US"
            
            if [ $? -eq 0 ]; then
                print_success "Debug keystore created successfully!"
                echo ""
                print_info "Next steps:"
                echo "1. Commit debug.keystore to version control"
                echo "2. Clean and rebuild: flutter clean && flutter build apk --debug"
            else
                print_error "Failed to create debug keystore"
            fi
        fi
    fi
    
    if [[ " ${FIXES_AVAILABLE[@]} " =~ " regenerate-debug-keystore " ]]; then
        echo ""
        print_warning "Debug keystore is corrupted"
        echo "Would you like to regenerate it? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm debug.keystore
            keytool -genkey -v -keystore debug.keystore \
                -storepass android \
                -alias androiddebugkey \
                -keypass android \
                -keyalg RSA \
                -keysize 2048 \
                -validity 10000 \
                -dname "CN=Android Debug,O=Android,C=US"
            
            if [ $? -eq 0 ]; then
                print_success "Debug keystore regenerated!"
                print_warning "All team members must uninstall existing apps before installing new builds"
            fi
        fi
    fi
fi

echo ""
echo "For more help, see:"
echo "- QUICK_SETUP.md for quick start guide"
echo "- RELEASE_SIGNING.md for detailed documentation"
echo "- Run ./verify-signing-setup.sh for full configuration check"
echo ""

