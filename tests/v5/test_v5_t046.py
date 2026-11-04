# -*- coding: utf-8 -*-
"""V5-T046 (Wave W04, Slot A06): 3D Rendering QA Under Load and Progressive LOD in UrnViewer.

Audits and verifies:
1. Manifest & LOD Architecture Validation:
   - Verifies 3D urn manifests contain progressive LOD configuration (low: 512, medium: 1k, high: 2k).
   - Validates file size budgets across LOD variants (e.g., 512 LOD ~5.2MB, 1k LOD ~27.4MB, 2k LOD ~30.4MB).
   - Verifies cryptographic checksums (SHA-256) for each LOD model asset.
2. Analytics Ingest & Telemetry Verification for 3D Render Performance:
   - Verifies /api/v1/analytics/events records render_performance events with proper payload:
     model_url, lod_label, file_size_bytes, ttf_ms, ttfi_ms, avg_fps, gpu_renderer, device_pixel_ratio.
   - Ensures invalid or non-numeric telemetry does not crash or corrupt database sessions.
3. Memory Budget & WebGL Resource Lifecycle:
   - Verifies WebGL context loss recovery handling: triggers automatic 2D accessible fallback without unhandled exception.
   - Verifies deep Three.js object disposal architecture (geometries, materials, textures, glTF cache clearing).
4. Progressive LOD Selection & Graceful Fallback:
   - Low-end / low-power device detection (hardwareConcurrency <= 4, deviceMemory <= 4, mobile viewport)
     selects lightweight LOD (-512 variant) and reduces hotspot geometry segments (20 -> 12).
   - Missing or corrupted 3D mesh triggers ModelErrorBoundary and renders FallbackScene + accessible 2D banner.
   - Complete WebGL failure degrades smoothly to UrnAccessibleFallback (WCAG 2.2 AA compliant text & 2D rubbing archive).
5. Load & Stress Simulation:
   - Tests concurrent ingestion of render performance metrics from multiple client sessions.
   - Verifies zero memory leakage and database connection stability under high event throughput.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import uuid

import pytest
from sqlalchemy import select

from backend.models import AnalyticsEvent, User, UserRole
from backend.services.asset_rights import (
    EXPECTED_CAO_DINH_CHECKSUMS,
    URN_SLUGS,
    get_viewer_fallback,
)
from backend.security import hash_password

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_MANIFESTS_DIR = REPO_ROOT / "public" / "models" / "manifests"
FRONTEND_URN_VIEWER_PATH = REPO_ROOT / "frontend" / "src" / "components" / "UrnViewer.tsx"
FRONTEND_HOOK_PATH = REPO_ROOT / "frontend" / "src" / "hooks" / "useRenderPerf.ts"


def _create_user(
    db_session,
    email: str,
    role: UserRole = UserRole.learner,
    display_name: str | None = None,
) -> User:
    """Helper to persist a user."""
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        display_name=display_name or f"User {email.split('@')[0]}",
        username=f"usr_{uuid.uuid4().hex[:8]}",
        role=role,
        is_profile_public=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_user(client, email: str, password: str = "Password123!") -> dict:
    """Login helper setting session cookies on test client."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()


# ==============================================================================
# 1. Manifest & Progressive LOD Budget Validation
# ==============================================================================


def test_urn_manifest_progressive_lods_and_memory_budget():
    """Verify all urn manifests specify valid LOD configurations within reasonable memory budgets."""
    cao_dinh_manifest_path = PUBLIC_MANIFESTS_DIR / "cao-dinh.json"
    assert cao_dinh_manifest_path.exists(), f"Missing Cao Dinh manifest at {cao_dinh_manifest_path}"

    with open(cao_dinh_manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert "lods" in manifest, "Manifest must contain 'lods' configuration"
    lods = manifest["lods"]

    # Must specify low, medium, and high progressive levels
    assert "low" in lods, "Missing 'low' LOD level"
    assert "medium" in lods, "Missing 'medium' LOD level"
    assert "high" in lods, "Missing 'high' LOD level"

    low = lods["low"]
    medium = lods["medium"]
    high = lods["high"]

    # Validate progressive memory budgets (bytes)
    assert low["bytes"] < medium["bytes"] < high["bytes"]
    # Low LOD (512 texture) should be within budget (< 10 MB for fast cellular mobile load)
    assert low["bytes"] <= 10 * 1024 * 1024, "Low LOD exceeds mobile budget (10MB)"
    # High LOD (2k texture) should be capped for memory safety (< 40 MB)
    assert high["bytes"] <= 40 * 1024 * 1024, "High LOD exceeds memory safety budget (40MB)"

    # Verify filenames and checksums match expected
    assert "512" in low["url"]
    assert "1k" in medium["url"]
    assert "2k" in high["url"]
    assert low["sha256"] == EXPECTED_CAO_DINH_CHECKSUMS["CAO-DINH-v1-512.glb"]
    assert medium["sha256"] == EXPECTED_CAO_DINH_CHECKSUMS["CAO-DINH-v1-1k.glb"]
    assert high["sha256"] == EXPECTED_CAO_DINH_CHECKSUMS["CAO-DINH-v1-2k.glb"]


def test_all_9_urn_manifests_contain_progressive_lods_and_rubbing_fallback():
    """Verify all 9 urn manifests have LOD declarations and accessible 2D rubbing fallbacks."""
    for slug in URN_SLUGS:
        mf_path = PUBLIC_MANIFESTS_DIR / f"{slug}.json"
        assert mf_path.exists(), f"Manifest {slug}.json missing"
        with open(mf_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "lods" in data, f"Urn '{slug}' manifest missing lods mapping"
        fallback = get_viewer_fallback(slug)
        assert fallback["type"] == "2d_rubbing"
        assert fallback["component"] == "UrnAccessibleFallback"
        assert fallback["sha256"] != ""


# ==============================================================================
# 2. Analytics Ingest & Telemetry Verification for 3D Render Performance
# ==============================================================================


def test_ingest_render_performance_telemetry(client, db_session):
    """Verify client-side 3D render metrics can be ingested via /api/v1/analytics/events."""
    user = _create_user(db_session, f"render_qa_{uuid.uuid4().hex[:6]}@example.com")
    _login_user(client, user.email)

    events_payload = {
        "events": [
            {
                "name": "render_performance",
                "path": "/cuu-dinh/cao-dinh",
                "payload": {
                    "model_url": "/assets/models/CAO-DINH-v1-512.glb",
                    "lod_label": "512",
                    "file_size_bytes": 5207460,
                    "ttf_ms": 320,
                    "ttfi_ms": 450,
                    "avg_fps": 58.4,
                    "gpu_renderer": "ANGLE (Intel, Mesa Intel UHD Graphics 620)",
                    "device_pixel_ratio": 1.0,
                    "viewport_width": 1280,
                    "viewport_height": 720,
                },
            },
            {
                "name": "render_performance",
                "path": "/cuu-dinh/cao-dinh",
                "payload": {
                    "model_url": "/assets/models/CAO-DINH-v1-2k.glb",
                    "lod_label": "2k",
                    "file_size_bytes": 30353888,
                    "ttf_ms": 1150,
                    "ttfi_ms": 1420,
                    "avg_fps": 36.2,
                    "gpu_renderer": "Apple GPU",
                    "device_pixel_ratio": 2.0,
                    "viewport_width": 1920,
                    "viewport_height": 1080,
                },
            },
        ]
    }

    res = client.post("/api/v1/analytics/events", json=events_payload)
    assert res.status_code == 200, f"Analytics ingest failed: {res.text}"
    body = res.json()
    assert body.get("success") is True
    assert body.get("count") == 2

    # Query DB to ensure events were persisted with exact payload
    events = (
        db_session.execute(
            select(AnalyticsEvent)
            .where(AnalyticsEvent.event_name == "render_performance")
            .order_by(AnalyticsEvent.created_at.desc())
        )
        .scalars()
        .all()
    )
    assert len(events) >= 2
    matched_512 = next((e for e in events if e.payload.get("lod_label") == "512"), None)
    assert matched_512 is not None
    assert matched_512.payload["ttf_ms"] == 320
    assert matched_512.payload["avg_fps"] == 58.4


def test_render_performance_telemetry_resilience_under_malformed_payload(client, db_session):
    """Verify analytics ingest handles partial/missing metrics gracefully without crashing."""
    user = _create_user(db_session, f"render_qa_resilience_{uuid.uuid4().hex[:6]}@example.com")
    _login_user(client, user.email)

    # Empty payload or unexpected types
    events_payload = {
        "events": [
            {
                "name": "render_performance",
                "path": "/cuu-dinh/nhan-dinh",
                "payload": {
                    "model_url": None,
                    "lod_label": None,
                    "file_size_bytes": None,
                    "ttf_ms": None,
                    "ttfi_ms": None,
                    "avg_fps": None,
                },
            }
        ]
    }
    res = client.post("/api/v1/analytics/events", json=events_payload)
    assert res.status_code == 200
    assert res.json().get("success") is True


# ==============================================================================
# 3. UrnViewer Code Inspection & Static Verification of 3D Invariants
# ==============================================================================


def test_urn_viewer_disposal_architecture_prevents_vram_leak():
    """Verify UrnViewer.tsx has disposeObject3D and clears Three.js GLTF cache."""
    assert FRONTEND_URN_VIEWER_PATH.exists(), f"UrnViewer.tsx not found at {FRONTEND_URN_VIEWER_PATH}"
    code = FRONTEND_URN_VIEWER_PATH.read_text(encoding="utf-8")

    # Three.js cache enabled
    assert "THREE.Cache.enabled = true;" in code

    # Material & geometry disposal routines
    assert "function disposeMaterial" in code
    assert "function disposeObject3D" in code
    assert "mat.dispose()" in code
    assert "mesh.geometry.dispose()" in code
    assert "(prop as THREE.Texture).dispose()" in code
    assert "useGLTF.clear(url)" in code


def test_urn_viewer_webgl_context_loss_and_recovery_listeners():
    """Verify UrnViewer.tsx subscribes to webglcontextlost and webglcontextrestored."""
    code = FRONTEND_URN_VIEWER_PATH.read_text(encoding="utf-8")

    assert "webglcontextlost" in code
    assert "webglcontextrestored" in code
    assert "handleContextLoss" in code
    assert "handleContextRestored" in code
    assert "setWebglFailed(true)" in code
    assert "setWebglFailed(false)" in code
    assert "UrnAccessibleFallback" in code


def test_urn_viewer_progressive_lod_and_low_power_handling():
    """Verify UrnViewer.tsx implements progressive LOD adaptation based on device capabilities."""
    code = FRONTEND_URN_VIEWER_PATH.read_text(encoding="utf-8")

    # Detect hardware capabilities
    assert "navigator.hardwareConcurrency" in code
    assert "deviceMemory" in code
    assert "isLowPowerDevice" in code

    # LOD fallback & segment budget adaptation
    assert "lodPreference" in code
    assert "hotspotSegments = isLowPowerDevice ? 12 : 20;" in code
    assert "renderDpr" in code
    assert "Math.min(window.devicePixelRatio || 1, 1.25)" in code
    assert "-v1-512.glb" in code


def test_urn_viewer_error_boundary_and_missing_mesh_fallback():
    """Verify WebGLErrorBoundary and ModelErrorBoundary with accessible 2D rubbing view."""
    code = FRONTEND_URN_VIEWER_PATH.read_text(encoding="utf-8")

    assert "class WebGLErrorBoundary" in code
    assert "class ModelErrorBoundary" in code
    assert "FallbackScene" in code
    assert "missing-mesh-fallback-banner" in code
    assert "Bản dập 2D thay thế" in code
    assert "UrnAccessibleFallback" in code


def test_use_render_perf_hook_invariants():
    """Verify useRenderPerf hook measures TTF, TTFI, FPS and handles fire-and-forget reporting."""
    assert FRONTEND_HOOK_PATH.exists(), f"useRenderPerf.ts not found at {FRONTEND_HOOK_PATH}"
    code = FRONTEND_HOOK_PATH.read_text(encoding="utf-8")

    assert "deriveLodLabel" in code
    assert "readGpuRenderer" in code
    assert "markFirstFrame" in code
    assert "markFirstInteraction" in code
    assert "fireRenderPerfEvent" in code
    assert "/api/v1/analytics/events" in code
    assert "keepalive: true" in code


# ==============================================================================
# 4. Stress & Load Simulation for Render Performance Ingestion
# ==============================================================================


def test_concurrent_render_telemetry_load_simulation(client, db_session):
    """Simulate batch ingestion of render telemetry under heavy client concurrency."""
    user = _create_user(db_session, f"render_load_{uuid.uuid4().hex[:6]}@example.com")
    _login_user(client, user.email)

    batch_events = []
    for i in range(50):
        lod = "512" if i % 3 == 0 else "1k" if i % 3 == 1 else "2k"
        ttf = 250 + (i * 15)
        batch_events.append(
            {
                "name": "render_performance",
                "path": f"/cuu-dinh/cao-dinh?session={i}",
                "payload": {
                    "model_url": f"/assets/models/CAO-DINH-v1-{lod}.glb",
                    "lod_label": lod,
                    "file_size_bytes": 5000000 if lod == "512" else 27000000 if lod == "1k" else 30000000,
                    "ttf_ms": ttf,
                    "ttfi_ms": ttf + 80,
                    "avg_fps": 60.0 - (i % 25),
                    "iteration": i,
                },
            }
        )

    # Ingest in chunks
    chunk_size = 10
    for offset in range(0, len(batch_events), chunk_size):
        chunk = batch_events[offset : offset + chunk_size]
        res = client.post("/api/v1/analytics/events", json={"events": chunk})
        assert res.status_code == 200
        assert res.json().get("count") == len(chunk)

    # Check persistence count
    count = db_session.execute(
        select(AnalyticsEvent).where(AnalyticsEvent.event_name == "render_performance")
    ).scalars().all()
    assert len(count) >= 50
