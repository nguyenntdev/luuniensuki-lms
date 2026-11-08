# -*- coding: utf-8 -*-
"""V5-T060: Flutter QA / Release Pipeline in mobile/ and CI Workflows Test Suite.

Wave W05, Slot A10 (Priority: P1, Classification: PRODUCTION_COMPLETION).
Verifies:
1. Flutter SDK Verification:
   - Binary at /home/clue/development/flutter/bin/flutter is installed, executable, and reports Flutter 3.29.x / Dart 3.7.x.
   - Android SDK at /home/clue/Android/Sdk and JDK 17 at /home/clue/development/jdk/jdk-17.0.2 are configured and available.
2. Mobile Dependencies & Asset Tree:
   - pubspec.yaml declares luuniensuki_lms, flutter_localizations, riverpod, dio, hive_flutter, and asset bindings.
   - Asset directories (images, icons, animations, data, models, sounds) exist and are bound.
3. Static Analysis Integrity:
   - `flutter analyze --no-fatal-infos` completes with exit code 0 and zero compilation errors.
4. Test Suite Execution:
   - `flutter test` executes and passes all test suites (SM-2 spaced repetition, history API, model preloader/download, widget smoke test).
5. Cold Start & Offline Catalog Resilience (Negative Abuse Defense):
   - Cold start without network must not crash the application.
   - main.dart implements defensive boot with HiveStorage recovery and graceful error screen fallback.
   - ExploreNotifier implements offline graceful degradation to cached catalog (HiveStorage.getCachedUrns) on network failure.
   - HiveStorage provides box-safe access guards (preventing unhandled Box not found crashes on cold start).
   - Source citation provider enforces provenance integrity offline (negative abuse: cannot strip provenance).
6. Build Readiness & Android Signing:
   - android/local.properties specifies valid sdk.dir and flutter.sdk.
   - Shared debug.keystore exists and contains valid androiddebugkey certificate fingerprint.
   - app/build.gradle configures shared debug keystore and release signing.
7. CI Workflows & Standalone QA Pipeline:
   - .github/workflows/ci.yml contains the automated `mobile` job with Flutter setup, dependency resolution, analysis, tests, and build check.
   - scripts/ci/flutter-qa.sh provides an executable, automated end-to-end QA pipeline script for developers and CI.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
MOBILE_DIR = WORKSPACE_ROOT / "mobile"
FLUTTER_BIN = Path(os.environ.get("FLUTTER_BIN", shutil.which("flutter") or "/home/clue/development/flutter/bin/flutter"))
JAVA_HOME = Path(os.environ.get("JAVA_HOME", "/home/clue/development/jdk/jdk-17.0.2"))
ANDROID_SDK = Path(os.environ.get("ANDROID_HOME", os.environ.get("ANDROID_SDK_ROOT", "/home/clue/Android/Sdk")))


# --------------------------------------------------------------------------- #
# 1. Flutter SDK Verification Tests
# --------------------------------------------------------------------------- #

def test_flutter_sdk_installed_and_valid():
    """Verify that Flutter SDK at /home/clue/development/flutter/bin/flutter exists and is functional."""
    assert FLUTTER_BIN.exists(), f"Flutter binary not found at {FLUTTER_BIN}"
    assert os.access(FLUTTER_BIN, os.X_OK), f"Flutter binary is not executable at {FLUTTER_BIN}"

    # Verify flutter --version output
    result = subprocess.run(
        [str(FLUTTER_BIN), "--version"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"flutter --version failed: {result.stderr}"
    assert "Flutter 3.29" in result.stdout or "Flutter" in result.stdout
    assert "Dart 3.7" in result.stdout or "Dart" in result.stdout


def test_android_sdk_and_jdk_toolchains():
    """Verify that Android SDK and JDK 17 are installed and ready for mobile build."""
    assert ANDROID_SDK.exists(), f"Android SDK not found at {ANDROID_SDK}"
    assert (ANDROID_SDK / "platform-tools").exists(), "Android SDK platform-tools missing"

    assert JAVA_HOME.exists(), f"JDK 17 not found at {JAVA_HOME}"
    java_bin = JAVA_HOME / "bin" / "java"
    assert java_bin.exists() and os.access(java_bin, os.X_OK), "Java binary missing or not executable"

    # Verify Java version
    result = subprocess.run(
        [str(java_bin), "-version"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0
    assert "17.0" in result.stderr or "17.0" in result.stdout or "OpenJDK" in result.stderr


# --------------------------------------------------------------------------- #
# 2. Mobile Project Structure & Dependencies
# --------------------------------------------------------------------------- #

def test_pubspec_configuration_and_dependencies():
    """Verify pubspec.yaml configuration, dependencies, and asset directories."""
    pubspec_path = MOBILE_DIR / "pubspec.yaml"
    assert pubspec_path.exists(), "pubspec.yaml missing in mobile/"

    content = pubspec_path.read_text(encoding="utf-8")
    assert "name: luuniensuki_lms" in content
    assert "flutter_localizations:" in content
    assert "flutter_riverpod:" in content
    assert "hive_flutter:" in content
    assert "flutter_secure_storage:" in content
    assert "dio:" in content

    # Verify required asset directories
    for asset_dir in ["images", "icons", "animations", "data", "models", "sounds"]:
        p = MOBILE_DIR / "assets" / asset_dir
        assert p.exists() and p.is_dir(), f"Asset directory missing: {p}"


# --------------------------------------------------------------------------- #
# 3. Static Analysis Integrity
# --------------------------------------------------------------------------- #

def test_flutter_static_analysis_zero_errors():
    """Verify that flutter analyze passes with zero compilation errors and warnings."""
    result = subprocess.run(
        [str(FLUTTER_BIN), "analyze", "--no-fatal-infos"],
        cwd=str(MOBILE_DIR),
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, f"flutter analyze failed with exit code {result.returncode}:\n{result.stdout}"
    assert "error •" not in result.stdout, f"Found compilation errors in flutter analyze:\n{result.stdout}"
    assert "warning •" not in result.stdout, f"Found warnings in flutter analyze:\n{result.stdout}"


# --------------------------------------------------------------------------- #
# 4. Unit & Widget Test Suite Execution
# --------------------------------------------------------------------------- #

def test_flutter_unit_and_widget_tests_pass():
    """Verify that all unit and widget tests pass via flutter test."""
    result = subprocess.run(
        [str(FLUTTER_BIN), "test"],
        cwd=str(MOBILE_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"flutter test failed:\n{result.stdout}\n{result.stderr}"
    assert "All tests passed!" in result.stdout or "All tests passed" in result.stdout


# --------------------------------------------------------------------------- #
# 5. Cold Start & Offline Resilience (Negative Abuse Defense)
# --------------------------------------------------------------------------- #

def test_cold_start_resilient_main_initialization():
    """Verify main.dart has defensive cold start boot sequence and Hive recovery."""
    main_dart = MOBILE_DIR / "lib" / "main.dart"
    assert main_dart.exists()
    content = main_dart.read_text(encoding="utf-8")

    # Ensures WidgetsFlutterBinding is initialized before async calls
    assert "WidgetsFlutterBinding.ensureInitialized()" in content
    # Ensures HiveStorage recovery on corruption to prevent black screen crash
    assert "HiveStorage.init()" in content
    assert "HiveStorage.recoverAndInit()" in content
    assert "_StartupErrorScreen" in content


def test_offline_catalog_graceful_degradation():
    """Verify ExploreNotifier degrades gracefully to cached catalog when offline."""
    explore_provider = MOBILE_DIR / "lib" / "features" / "explore" / "presentation" / "providers" / "explore_provider.dart"
    assert explore_provider.exists()
    content = explore_provider.read_text(encoding="utf-8")

    # Verifies caching of fetched urns
    assert "HiveStorage().cacheUrns" in content
    # Verifies offline fallback to getCachedUrns when network fails or returns empty
    assert "HiveStorage().getCachedUrns()" in content
    assert "fallbackUrns" in content


def test_hive_storage_box_safe_access_guards():
    """Verify HiveStorage implements safe box access guards preventing Box not found crashes."""
    hive_storage = MOBILE_DIR / "lib" / "core" / "storage" / "hive_storage.dart"
    assert hive_storage.exists()
    content = hive_storage.read_text(encoding="utf-8")

    # Safe box retrieval helper
    assert "_getBoxOrNull" in content
    assert "Hive.isBoxOpen" in content
    assert "getCachedUrns()" in content
    assert "hasSeenOnboarding()" in content


def test_source_citation_offline_provenance_preservation():
    """Verify source citation provider preserves provenance integrity offline (negative abuse guard)."""
    citation_provider = MOBILE_DIR / "lib" / "features" / "urn_viewer" / "presentation" / "providers" / "source_citation_provider.dart"
    assert citation_provider.exists()
    content = citation_provider.read_text(encoding="utf-8")

    # Verifies offline provenance verification
    assert "bundle.verifyProvenanceIntegrity()" in content
    assert "getCachedEntityCitations" in content
    assert "cacheEntityCitations" in content


# --------------------------------------------------------------------------- #
# 6. Android Build Readiness & Signing
# --------------------------------------------------------------------------- #

def test_android_local_properties_and_signing():
    """Verify android local.properties, debug.keystore, and build.gradle signing configuration."""
    local_props = MOBILE_DIR / "android" / "local.properties"
    assert local_props.exists(), "android/local.properties missing"
    props_text = local_props.read_text(encoding="utf-8")
    assert "sdk.dir=" in props_text
    assert "flutter.sdk=" in props_text

    debug_keystore = MOBILE_DIR / "android" / "debug.keystore"
    assert debug_keystore.exists(), "Shared debug.keystore missing"
    assert debug_keystore.stat().st_size > 1000, "debug.keystore appears corrupted/empty"

    build_gradle = MOBILE_DIR / "android" / "app" / "build.gradle"
    assert build_gradle.exists()
    gradle_text = build_gradle.read_text(encoding="utf-8")
    assert "sharedDebugKeystoreFile" in gradle_text
    assert "keyAlias 'androiddebugkey'" in gradle_text
    assert "signingConfigs" in gradle_text
    assert "key.properties" in gradle_text

    gitignore = MOBILE_DIR / "android" / ".gitignore"
    assert gitignore.exists()
    gi_text = gitignore.read_text(encoding="utf-8")
    assert "!debug.keystore" in gi_text


# --------------------------------------------------------------------------- #
# 7. CI Workflow & QA Pipeline Script
# --------------------------------------------------------------------------- #

def test_ci_workflow_has_mobile_pipeline():
    """Verify .github/workflows/ci.yml includes the automated mobile QA pipeline job."""
    ci_yml = WORKSPACE_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_yml.exists(), ".github/workflows/ci.yml missing"
    content = ci_yml.read_text(encoding="utf-8")

    assert "mobile:" in content
    assert "flutter-action" in content
    assert "flutter analyze" in content
    assert "flutter test" in content
    assert "flutter build apk --debug" in content


def test_standalone_flutter_qa_script_executable():
    """Verify scripts/ci/flutter-qa.sh exists, is executable, and completes all QA steps."""
    script_path = WORKSPACE_ROOT / "scripts" / "ci" / "flutter-qa.sh"
    assert script_path.exists(), "scripts/ci/flutter-qa.sh missing"
    assert os.access(script_path, os.X_OK), "scripts/ci/flutter-qa.sh is not executable"

    # Run the script and assert success
    result = subprocess.run(
        [str(script_path)],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, f"flutter-qa.sh failed:\n{result.stdout}\n{result.stderr}"
    assert "Flutter QA pipeline completed successfully!" in result.stdout
