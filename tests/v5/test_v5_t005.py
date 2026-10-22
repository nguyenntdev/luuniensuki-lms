# -*- coding: utf-8 -*-
"""API Contract Snapshot & Validation Tests — Ticket V5-T005 (Slot W00-A05).

Contract Requirements:
1. Inspect OpenAPI contract export from active FastAPI app.
2. Verify error envelope standard consistency across all endpoints:
   {"error": {"code": "...", "message": "...", "details": {...}}}.
3. Compare exported schema with frontend TypeScript types (frontend/src/types/api.ts)
   and mobile client contracts (04_MOBILE/MOBILE_API_CONTRACTS.md).
4. Verify OpenAPI schema validity.
5. Negative/abuse test: Any undocumented or broken endpoint path fails contract validation.
6. Verify API contract snapshot artifact integrity:
   artifacts/implementation/W00/W00_A05_api_contract_snapshot.json.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import backend.main as main

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACT_PATH = (
    REPO_ROOT
    / "artifacts"
    / "implementation"
    / "W00"
    / "W00_A05_api_contract_snapshot.json"
)
FRONTEND_TYPES_PATH = REPO_ROOT / "frontend" / "src" / "types" / "api.ts"
MOBILE_SPEC_PATH = (
    REPO_ROOT
    / "LUU_NIEN_V6_MASTER_AND_MODULAR_SPECS_WITH_MOBILE"
    / "LUU_NIEN_V6_MODULAR_IMPLEMENTATION_SPECS"
    / "04_MOBILE"
    / "MOBILE_API_CONTRACTS.md"
)


class ContractValidationError(Exception):
    """Raised when an endpoint call-site or definition fails contract validation."""


def validate_endpoint_contract(
    openapi_schema: dict[str, Any],
    method: str,
    path: str,
) -> dict[str, Any]:
    """Validates that a method and path are documented and well-formed in OpenAPI schema.

    Raises ContractValidationError if:
    - The path is undocumented or absent from the contract.
    - The HTTP method is unsupported on the path.
    - Path parameter templates are malformed.
    """
    paths = openapi_schema.get("paths", {})
    method_lower = method.lower()

    # Exact or parameterized matching
    target_spec_path = None
    if path in paths:
        target_spec_path = path
    else:
        # Check parameterized pattern match e.g. /users/{id}
        norm_input = re.sub(r"\{[^}]+\}", "{}", path)
        for cand_path in paths:
            if re.sub(r"\{[^}]+\}", "{}", cand_path) == norm_input:
                target_spec_path = cand_path
                break

    if target_spec_path is None:
        raise ContractValidationError(
            f"Undocumented endpoint path: '{method.upper()} {path}' is not present in OpenAPI contract."
        )

    path_item = paths[target_spec_path]
    if method_lower not in path_item:
        allowed = [m.upper() for m in path_item.keys() if m in {"get", "post", "put", "patch", "delete"}]
        raise ContractValidationError(
            f"Method not allowed by contract: '{method.upper()}' is not supported on '{target_spec_path}'. "
            f"Allowed methods: {allowed}"
        )

    operation = path_item[method_lower]
    # Verify path parameters defined in path template are declared
    template_params = set(re.findall(r"\{([a-zA-Z0-9_]+)\}", target_spec_path))
    declared_params = set()
    for p in operation.get("parameters", []) + path_item.get("parameters", []):
        if p.get("in") == "path":
            declared_params.add(p.get("name"))

    missing_params = template_params - declared_params
    if missing_params:
        raise ContractValidationError(
            f"Broken path parameter contract on '{method.upper()} {target_spec_path}': "
            f"Parameters {missing_params} in URL template are not declared in OpenAPI parameter schema."
        )

    return operation


@pytest.fixture(scope="module")
def api_client() -> TestClient:
    """FastAPI TestClient for active app."""
    return TestClient(main.app, raise_server_exceptions=False)


@pytest.fixture(scope="module")
def live_schema() -> dict[str, Any]:
    """Live OpenAPI schema from active FastAPI app."""
    return main.app.openapi()


# ============================================================================
# 1. OpenAPI Schema Validity & Structure
# ============================================================================


def test_openapi_schema_validity(live_schema):
    """The live OpenAPI export must be syntactically valid and complete."""
    assert "openapi" in live_schema, "OpenAPI version missing"
    assert live_schema["openapi"].startswith("3."), f"Expected OpenAPI 3.x, got {live_schema['openapi']}"

    info = live_schema.get("info", {})
    assert info.get("title") == "Luuniensuki API"
    assert "version" in info

    paths = live_schema.get("paths", {})
    assert len(paths) >= 300, f"Expected >= 300 endpoints, found {len(paths)}"

    valid_methods = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
    for path, operations in paths.items():
        assert path.startswith("/"), f"Path must start with '/': {path}"
        for method, op in operations.items():
            if method in {"parameters", "summary", "description"}:
                continue
            assert method.lower() in valid_methods, f"Invalid method {method} on {path}"
            assert isinstance(op, dict), f"Operation must be a dict on {method} {path}"
            assert "responses" in op, f"Operation missing responses: {method} {path}"
            assert len(op["responses"]) >= 1, f"Operation must define at least one response: {method} {path}"

    components = live_schema.get("components", {})
    assert "schemas" in components, "Components must contain schemas"
    assert len(components["schemas"]) >= 100


# ============================================================================
# 2. Error Envelope Standard Consistency
# ============================================================================


def test_error_envelope_on_validation_failure(api_client):
    """Validation failure (422) must follow the standard error envelope and redact secrets."""
    sensitive_token = "TOP_SECRET_PASSPHRASE_V5_T005"
    payload = {
        "email": "not-an-email-address",
        "password": sensitive_token * 4,  # Exceeds max length, sensitive field
        "display_name": "Valid User",
    }
    resp = api_client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 422

    body = resp.json()
    assert set(body.keys()) == {"error"}
    err = body["error"]
    assert set(err.keys()) == {"code", "message", "details"}
    assert err["code"] == "VALIDATION_ERROR"
    assert err["message"] == "Invalid request parameters"
    assert isinstance(err["details"], dict)
    assert "errors" in err["details"]

    # Sensitive token must NEVER appear anywhere in response body or raw text
    assert sensitive_token not in resp.text

    # Each error item contains only loc, msg, type
    for item in err["details"]["errors"]:
        assert set(item.keys()) == {"loc", "msg", "type"}
        assert "input" not in item
        assert "ctx" not in item

    # Password error message must be redacted to generic value
    by_loc = {tuple(item["loc"]): item for item in err["details"]["errors"]}
    if ("body", "password") in by_loc:
        assert by_loc[("body", "password")]["msg"] == "invalid value"


def test_error_envelope_on_not_found(api_client):
    """Calling an unmapped path (404) must return standard error envelope."""
    resp = api_client.get("/api/v1/nonexistent_phantom_route_v5_t005")
    assert resp.status_code == 404

    body = resp.json()
    assert set(body.keys()) == {"error"}
    err = body["error"]
    assert err["code"] == "HTTP_ERROR"
    assert err["message"] == "Not Found"
    assert isinstance(err["details"], dict)


def test_error_envelope_on_unauthorized(api_client):
    """Unauthenticated access to protected endpoint (401) must return standard error envelope."""
    resp = api_client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    body = resp.json()
    assert set(body.keys()) == {"error"}
    err = body["error"]
    assert err["code"] in {"HTTP_ERROR", "UNAUTHORIZED"}
    assert isinstance(err["message"], str) and len(err["message"]) > 0
    assert isinstance(err["details"], dict)


def test_error_envelope_on_method_not_allowed(api_client):
    """Invoking an invalid method on a valid route (405) must return standard error envelope."""
    resp = api_client.patch("/api/v1/auth/register", json={})
    assert resp.status_code == 405

    body = resp.json()
    assert set(body.keys()) == {"error"}
    err = body["error"]
    assert err["code"] == "HTTP_ERROR"
    assert err["message"] == "Method Not Allowed"
    assert isinstance(err["details"], dict)


# ============================================================================
# 3. Negative / Abuse Contract Tests
# ============================================================================


def test_negative_undocumented_endpoint_fails_contract(live_schema):
    """Negative/abuse test: Undocumented endpoint must fail contract validation."""
    with pytest.raises(ContractValidationError) as exc_info:
        validate_endpoint_contract(
            live_schema,
            method="GET",
            path="/api/v1/shadow_undocumented_route",
        )
    assert "Undocumented endpoint path" in str(exc_info.value)


def test_negative_unsupported_method_fails_contract(live_schema):
    """Negative/abuse test: Unsupported HTTP method on valid path must fail contract validation."""
    with pytest.raises(ContractValidationError) as exc_info:
        validate_endpoint_contract(
            live_schema,
            method="DELETE",
            path="/api/v1/auth/login",
        )
    assert "Method not allowed by contract" in str(exc_info.value)


def test_negative_broken_path_parameter_contract(live_schema):
    """Negative/abuse test: Synthetic broken path template must fail contract validation."""
    # Create a synthetic schema where a path parameter in template is not declared
    broken_schema = {
        "paths": {
            "/api/v1/items/{broken_param_id}": {
                "get": {
                    "responses": {"200": {"description": "OK"}},
                    "parameters": [],  # missing declared path param!
                }
            }
        }
    }
    with pytest.raises(ContractValidationError) as exc_info:
        validate_endpoint_contract(
            broken_schema,
            method="GET",
            path="/api/v1/items/{broken_param_id}",
        )
    assert "Broken path parameter contract" in str(exc_info.value)


# ============================================================================
# 4. Domain & Role Partitioning Integrity
# ============================================================================


def test_domain_role_partitioning_coverage(live_schema):
    """Every endpoint in the contract must map to a recognized domain/role partition."""
    from scripts.dev.export_api_contract_snapshot import get_partition

    paths = live_schema.get("paths", {})
    partitions = {"public": 0, "admin": 0, "partner": 0, "teacher": 0, "student_core": 0}

    for path in paths:
        part = get_partition(path)
        assert part in partitions, f"Unrecognized partition {part} for path {path}"
        partitions[part] += 1

    # Verify all partitions are populated
    assert partitions["public"] >= 20, f"Public endpoints count low: {partitions['public']}"
    assert partitions["admin"] >= 50, f"Admin endpoints count low: {partitions['admin']}"
    assert partitions["partner"] >= 10, f"Partner endpoints count low: {partitions['partner']}"
    assert partitions["teacher"] >= 15, f"Teacher endpoints count low: {partitions['teacher']}"
    assert partitions["student_core"] >= 100, f"Student core endpoints count low: {partitions['student_core']}"
    assert sum(partitions.values()) == len(paths)


# ============================================================================
# 5. Client Parity (Frontend TypeScript & Mobile Contracts)
# ============================================================================


def test_frontend_typescript_parity(live_schema):
    """Frontend generated TypeScript types (api.ts) must cover all active OpenAPI paths."""
    assert FRONTEND_TYPES_PATH.exists(), f"Frontend types missing at {FRONTEND_TYPES_PATH}"
    content = FRONTEND_TYPES_PATH.read_text(encoding="utf-8")

    ts_paths = set(re.findall(r'\"([/][^\"]+)\":\s*\{', content))
    openapi_paths = set(live_schema.get("paths", {}).keys())

    unmapped = openapi_paths - ts_paths
    assert len(unmapped) == 0, (
        f"Frontend types drifted! {len(unmapped)} OpenAPI paths missing in frontend/src/types/api.ts. "
        f"Sample: {sorted(list(unmapped))[:5]}. Run: cd frontend && npm run gen:api"
    )


def test_mobile_contract_spec_alignment(live_schema):
    """All 24 endpoints in MOBILE_API_CONTRACTS.md must be accounted for in the contract snapshot."""
    from scripts.dev.export_api_contract_snapshot import parse_mobile_contract_spec

    openapi_paths = set(live_schema.get("paths", {}).keys())
    mappings = parse_mobile_contract_spec(MOBILE_SPEC_PATH, openapi_paths)

    assert len(mappings) == 24, f"Expected 24 mobile endpoints in spec, found {len(mappings)}"
    exact_matches = [m for m in mappings if m["match_type"] == "EXACT_PATH_MATCH"]
    equiv_matches = [m for m in mappings if m["match_type"] == "EXISTING_EQUIVALENT_MATCH"]
    target_specs = [m for m in mappings if m["match_type"] == "TARGET_SPEC_PENDING_IMPLEMENTATION"]

    assert len(exact_matches) >= 5, "Expected at least 5 exact path matches"
    assert len(equiv_matches) >= 6, "Expected at least 6 existing equivalent matches"
    assert len(target_specs) >= 5, "Expected target pending endpoints"


# ============================================================================
# 6. Artifact Verification
# ============================================================================


def test_contract_snapshot_artifact_integrity(live_schema):
    """Snapshot artifact must exist, match live schema, and carry required metadata."""
    assert ARTIFACT_PATH.exists(), f"Artifact missing at {ARTIFACT_PATH}"
    data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    meta = data.get("meta", {})
    assert meta.get("ticket_id") == "V5-T005"
    assert meta.get("slot") == "W00-A05"
    assert meta.get("baseline_source_sha") == "54da2beb71f3df70e1f00b215ae0fb1a850eb263"
    assert meta.get("api_title") == "Luuniensuki API"

    summary = data.get("summary", {})
    live_paths = live_schema.get("paths", {})
    assert summary.get("total_paths") == len(live_paths)
    assert summary.get("total_operations") >= 400

    error_std = data.get("error_envelope_standard", {})
    assert error_std.get("compliance_status") == "VERIFIED"

    client_parity = data.get("client_parity", {})
    assert client_parity.get("typescript_frontend", {}).get("status") == "PASS"
    assert len(client_parity.get("mobile_client_contracts", {}).get("mappings", [])) == 24
