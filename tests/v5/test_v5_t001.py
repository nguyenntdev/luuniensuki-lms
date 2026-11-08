# -*- coding: utf-8 -*-
"""Test suite for V5-T001 (W00 Slot 1): Freeze snapshot & lock route inventory.

Verifies:
1. Baseline artifact integrity (W00_A01_route_inventory_baseline.json).
2. Monorepo route inventory consistency across FastAPI and Axum Rust gateway.
3. Accurate ownership assignment ('rust-native' vs 'python-gateway') respecting
   pinned routes in route-modes.toml.
4. Auth and RBAC role requirement mappings.
5. Mandatory Negative/Abuse Test:
   - An unmapped or non-existent backend route MUST be flagged UNKNOWN and
     unreachable, and MUST NEVER be marked ready.
   - Real HTTP request to unmapped route returns 404 error envelope.
6. Positive reachability flows and parameterized path resolution.
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.domain.route_inventory import (
    BASELINE_ARTIFACT_REL_PATH,
    REPO_ROOT,
    ROUTE_MODES_REL_PATH,
    SNAPSHOT_SHA,
    TICKET_ID,
    build_unified_route_inventory,
    evaluate_route,
    export_baseline_artifact,
    inspect_fastapi_routes,
    inspect_route_modes,
    inspect_rust_routes,
    normalize_path,
)


@pytest.fixture(scope="module")
def app_instance():
    """Create a FastAPI application instance without connecting to external DB."""
    return create_app()


@pytest.fixture(scope="module")
def test_client(app_instance):
    """FastAPI TestClient for HTTP level contract verification."""
    return TestClient(app_instance, raise_server_exceptions=False)


@pytest.fixture(scope="module")
def baseline_data():
    """Load or generate the W00_A01 route inventory baseline artifact."""
    artifact_path = REPO_ROOT / BASELINE_ARTIFACT_REL_PATH
    if not artifact_path.exists():
        export_baseline_artifact(REPO_ROOT)
    with open(artifact_path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestV5T001RouteInventoryBaseline:
    """Test suite verifying the route inventory baseline and reachability contracts."""

    def test_artifact_metadata_and_structure(self, baseline_data):
        """Verify baseline artifact metadata, SHA lock, and top-level schema."""
        assert baseline_data["ticket_id"] == TICKET_ID
        assert baseline_data["slot"] == "W00-A01"
        assert baseline_data["baseline_sha"] == SNAPSHOT_SHA
        assert "recorded_at" in baseline_data
        assert "source_lock_reference" in baseline_data

        summary = baseline_data["summary"]
        assert summary["total_unified_endpoints"] >= 480
        assert summary["fastapi_endpoints_count"] >= 412
        assert summary["rust_endpoints_count"] >= 160
        assert summary["owner_counts"]["rust-native"] > 100
        assert summary["owner_counts"]["python-gateway"] > 300

        # Verify group coverage
        groups = summary["group_counts"]
        expected_groups = {
            "auth",
            "users",
            "lessons",
            "quizzes",
            "progress",
            "badges-quests",
            "classrooms",
            "leaderboards",
            "notifications",
            "admin",
            "ai",
            "live",
            "history",
            "heritage",
            "rbpc",
            "imperial",
            "foundations",
        }
        for g in expected_groups:
            assert g in groups, f"Expected domain group '{g}' missing from baseline"
            assert groups[g] > 0, f"Domain group '{g}' has 0 routes"

    def test_route_entry_fields_completeness(self, baseline_data):
        """Ensure every route entry has all required typed fields."""
        routes = baseline_data["routes"]
        assert len(routes) == baseline_data["summary"]["total_unified_endpoints"]

        required_keys = {
            "method",
            "path",
            "group",
            "owner",
            "auth_required",
            "auth_optional",
            "roles_required",
            "status",
            "reachable",
            "fastapi_endpoint",
            "rust_handler",
            "gateway_pinned",
        }

        for r in routes:
            assert required_keys.issubset(r.keys()), (
                f"Route {r.get('method')} {r.get('path')} is missing keys: "
                f"{required_keys - set(r.keys())}"
            )
            assert r["method"] in {"GET", "POST", "PUT", "PATCH", "DELETE"}
            assert r["owner"] in {"rust-native", "python-gateway"}
            assert r["status"] == "ready"
            assert r["reachable"] is True
            assert isinstance(r["auth_required"], bool)
            assert isinstance(r["auth_optional"], bool)
            assert isinstance(r["roles_required"], list)

    def test_route_modes_gateway_pinning_parity(self, baseline_data):
        """Verify that routes pinned to 'gateway' in route-modes.toml are strictly owned by python-gateway."""
        pinned_routes, _ = inspect_route_modes(REPO_ROOT)
        assert len(pinned_routes) == 14

        routes_by_key = {f"{r['method']} {r['path']}": r for r in baseline_data["routes"]}

        for pinned_key in pinned_routes:
            assert pinned_key in routes_by_key, (
                f"Pinned route '{pinned_key}' from route-modes.toml not found in inventory"
            )
            entry = routes_by_key[pinned_key]
            assert entry["owner"] == "python-gateway", (
                f"Pinned route '{pinned_key}' MUST be owned by 'python-gateway', but was '{entry['owner']}'"
            )
            assert entry["gateway_pinned"] is True

    def test_fastapi_active_routes_full_coverage(self, app_instance, baseline_data):
        """Verify 100% of active FastAPI APIRoutes are present in the inventory."""
        live_fastapi_routes = inspect_fastapi_routes(app_instance)
        assert len(live_fastapi_routes) >= 412

        baseline_routes_set = {
            (r["method"], r["path"]) for r in baseline_data["routes"]
        }

        for live in live_fastapi_routes:
            key = (live["method"], live["path"])
            assert key in baseline_routes_set, (
                f"Active FastAPI route {key} missing from baseline inventory"
            )

    def test_openapi_schema_consistency(self, app_instance, baseline_data):
        """Verify consistency between FastAPI OpenAPI documentation and baseline inventory."""
        openapi = app_instance.openapi()
        paths = openapi.get("paths", {})

        baseline_routes_set = {
            (r["method"], r["path"]) for r in baseline_data["routes"]
        }

        for path_str, methods_dict in paths.items():
            for method_str in methods_dict:
                method_upper = method_str.upper()
                if method_upper in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                    key = (method_upper, path_str)
                    assert key in baseline_routes_set, (
                        f"OpenAPI endpoint {key} not found in route inventory baseline"
                    )

    def test_rbac_role_classification_rules(self, baseline_data):
        """Verify that admin, staff, learner, and public routes are accurately classified."""
        routes = baseline_data["routes"]

        # Admin routes should include admin in roles_required
        admin_routes = [r for r in routes if r["path"].startswith("/api/v1/admin/") and r["auth_required"]]
        assert len(admin_routes) > 50
        for ar in admin_routes:
            # admin endpoints should permit admin role
            roles = ar["roles_required"]
            assert "admin" in roles or "super_admin" in roles, (
                f"Admin route {ar['method']} {ar['path']} missing admin/super_admin role: {roles}"
            )

        # Public endpoints like /health and /metrics must have auth_required=False and empty roles
        health_route = next(r for r in routes if r["path"] == "/health" and r["method"] == "GET")
        assert health_route["auth_required"] is False
        assert health_route["roles_required"] == []

        login_route = next(r for r in routes if r["path"] == "/api/v1/auth/login" and r["method"] == "POST")
        assert login_route["auth_required"] is False
        assert login_route["roles_required"] == []

    # ======================================================================= #
    # Negative / Abuse Contract Tests (MUST fail before fix)
    # ======================================================================= #

    def test_negative_unmapped_route_flagged_unknown(self, baseline_data):
        """NEGATIVE TEST: Unmapped or non-existent backend route MUST be flagged UNKNOWN, NOT ready.

        Spec contract:
        'Một route không có backend vẫn hiện trên UI phải bị đánh UNKNOWN, không gán ready.'
        """
        unmapped_test_cases = [
            ("GET", "/api/v1/nonexistent/fake-endpoint"),
            ("POST", "/api/v1/mock/ui-placeholder"),
            ("GET", "/api/v1/phantom/service"),
            ("DELETE", "/api/v1/auth/login"),  # Wrong method for existing path
            ("GET", "/api/v1/imperial/unimplemented/cultural-exchange"),
            ("POST", "/api/v1/rbpc/fake-inquiry-action"),
            ("GET", "/art-details/unprefixed-old-style"),
        ]

        routes = baseline_data["routes"]

        for method, path in unmapped_test_cases:
            evaluation = evaluate_route(method, path, inventory_routes=routes)

            # Strict assertions required by specification
            assert evaluation["status"] == "UNKNOWN", (
                f"Unmapped route '{method} {path}' MUST have status='UNKNOWN', got '{evaluation['status']}'"
            )
            assert evaluation["is_ready"] is False, (
                f"Unmapped route '{method} {path}' MUST NOT be marked ready"
            )
            assert evaluation["is_unknown"] is True, (
                f"Unmapped route '{method} {path}' MUST have is_unknown=True"
            )
            assert evaluation["reachable"] is False, (
                f"Unmapped route '{method} {path}' MUST have reachable=False"
            )
            assert evaluation["owner"] is None, (
                f"Unmapped route '{method} {path}' MUST NOT have an owner, got '{evaluation['owner']}'"
            )
            assert evaluation["matched_path"] is None
            assert "error" in evaluation and evaluation["error"]

    def test_negative_unmapped_route_http_returns_404(self, test_client):
        """NEGATIVE TEST: Unmapped route request to FastAPI returns 404 with error envelope."""
        response = test_client.get("/api/v1/nonexistent/fake-endpoint")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data, "Error response must adhere to error envelope standard"
        assert data["error"]["code"] in {"HTTP_ERROR", "NOT_FOUND", "HTTP_404"} or "detail" in data
        assert data["error"]["message"] == "Not Found"

    # ======================================================================= #
    # Positive Flow & Parameterized Path Resolution Tests
    # ======================================================================= #

    def test_positive_route_evaluation(self, baseline_data):
        """Verify mapped positive routes evaluate to ready and reachable."""
        positive_cases = [
            ("POST", "/api/v1/auth/login", "rust-native", False),
            ("GET", "/api/v1/auth/me", "rust-native", True),
            ("POST", "/api/v1/live/sessions", "python-gateway", True),
            ("GET", "/health", "rust-native", False),
            ("GET", "/api/v1/urns", "rust-native", True),
            ("GET", "/api/v1/imperial/zones", "python-gateway", False),
        ]

        routes = baseline_data["routes"]

        for method, path, expected_owner, expected_auth in positive_cases:
            evaluation = evaluate_route(method, path, inventory_routes=routes)
            assert evaluation["status"] == "ready"
            assert evaluation["is_ready"] is True
            assert evaluation["is_unknown"] is False
            assert evaluation["reachable"] is True
            assert evaluation["owner"] == expected_owner
            assert evaluation["auth_required"] == expected_auth

    def test_parameterized_path_resolution(self, baseline_data):
        """Verify that dynamic URI paths correctly match template route definitions."""
        dynamic_cases = [
            ("GET", "/api/v1/urns/cao-dinh", "/api/v1/urns/{urn_slug}"),
            ("GET", "/api/v1/motifs/motif-12345", "/api/v1/motifs/{motif_id}"),
            (
                "GET",
                "/api/v1/users/550e8400-e29b-41d4-a716-446655440000/public",
                "/api/v1/users/{user_id}/public",
            ),
            (
                "GET",
                "/api/v1/imperial/sites/thai-hoa/timeline",
                "/api/v1/imperial/sites/{slug}/timeline",
            ),
        ]

        routes = baseline_data["routes"]

        for method, concrete_path, expected_template in dynamic_cases:
            evaluation = evaluate_route(method, concrete_path, inventory_routes=routes)
            assert evaluation["status"] == "ready"
            assert evaluation["is_ready"] is True
            assert evaluation["matched_path"] == expected_template, (
                f"Expected '{concrete_path}' to resolve to '{expected_template}', "
                f"got '{evaluation['matched_path']}'"
            )

    def test_health_endpoint_http_returns_200(self, test_client):
        """Verify that /health responds HTTP 200 without DB dependency."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
