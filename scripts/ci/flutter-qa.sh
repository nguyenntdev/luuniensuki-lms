#!/usr/bin/env bash
# ==============================================================================
# Flutter QA & Release Pipeline Script (Ticket V5-T060)
# Luuniensuki LMS - Mobile CI / CD Verification
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MOBILE_DIR="$WORKSPACE_ROOT/mobile"

# Locate Flutter binary
FLUTTER_BIN="${FLUTTER_BIN:-/home/clue/development/flutter/bin/flutter}"
if ! command -v "$FLUTTER_BIN" >/dev/null 2>&1; then
  if command -v flutter >/dev/null 2>&1; then
    FLUTTER_BIN="flutter"
  else
    echo "❌ Error: Flutter binary not found at $FLUTTER_BIN or on PATH"
    exit 1
  fi
fi

# Locate Java & Android SDK
JAVA_HOME="${JAVA_HOME:-/home/clue/development/jdk/jdk-17.0.2}"
ANDROID_HOME="${ANDROID_HOME:-/home/clue/Android/Sdk}"
if [ -d "$JAVA_HOME/bin" ]; then
  export PATH="$JAVA_HOME/bin:$PATH"
  export JAVA_HOME
fi
if [ -d "$ANDROID_HOME" ]; then
  export ANDROID_HOME
  export ANDROID_SDK_ROOT="$ANDROID_HOME"
fi

echo "======================================================================"
echo "📱 Luuniensuki LMS: Flutter Mobile QA Pipeline"
echo "======================================================================"
echo "Flutter Binary: $FLUTTER_BIN"
"$FLUTTER_BIN" --version
echo "Working Directory: $MOBILE_DIR"
echo "----------------------------------------------------------------------"

cd "$MOBILE_DIR"

echo "Step 1: Checking dependencies..."
"$FLUTTER_BIN" pub get

echo "Step 2: Running static analysis..."
"$FLUTTER_BIN" analyze --no-fatal-infos
echo "✅ Flutter static analysis passed."

echo "Step 3: Running unit & widget test suite..."
"$FLUTTER_BIN" test
echo "✅ All Flutter unit and widget tests passed."

echo "Step 4: Checking build readiness & keystore..."
if [ -f "android/debug.keystore" ]; then
  echo "✅ Shared debug keystore found."
else
  echo "❌ Error: Shared debug.keystore missing."
  exit 1
fi

if [ -f "android/local.properties" ]; then
  echo "✅ Android local.properties found."
fi

echo "======================================================================"
echo "🎉 Flutter QA pipeline completed successfully! Mobile is release-ready."
echo "======================================================================"
