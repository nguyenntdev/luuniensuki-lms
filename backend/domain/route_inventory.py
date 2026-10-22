# -*- coding: utf-8 -*-
"""Route inventory and reachability baseline for polyglot Luu Nien monorepo.

Implements V5-T001 (W00 Slot 1):
- Inspects all active routes in FastAPI (backend/app.py & backend/routers/*)
  and Axum Rust gateway (backend-rust/src/main.rs & backend-rust/config/route-modes.toml).
- Determines definitive request ownership: 'rust-native' vs 'python-gateway'.
- Extracts auth requirements and RBAC role constraints for each endpoint.
- Provides route classification & verification, ensuring unmapped/non-existent
  backend routes are flagged UNKNOWN / unreachable rather than marked ready.
- Exports the baseline artifact:
  artifacts/implementation/W00/W00_A01_route_inventory_baseline.json
"""
from __future__ import annotations

import json
import os
import re
import tomllib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi.routing import APIRoute

# Repository constants
REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_SHA = "54da2beb71f3df70e1f00b215ae0fb1a850eb263"
TICKET_ID = "V5-T001"
SLOT = "W00-A01"
BASELINE_ARTIFACT_REL_PATH = "artifacts/implementation/W00/W00_A01_route_inventory_baseline.json"
ROUTE_MODES_REL_PATH = "backend-rust/config/route-modes.toml"
MAIN_RS_REL_PATH = "backend-rust/src/main.rs"

# Domain grouping rules mapped by regex prefix
GROUP_RULES = [
    (r"^/api/v1/auth/", "auth"),
    (r"^/api/v1/users/me/streak", "progress"),
    (r"^/api/v1/users/me/hearts", "progress"),
    (r"^/api/v1/users/me/daily-goal", "progress"),
    (r"^/api/v1/users/me/milestones", "progress"),
    (r"^/api/v1/users/me/collection", "users"),
    (r"^/api/v1/users/me/avatar", "users"),
    (r"^/api/v1/users/me/change-password", "users"),
    (r"^/api/v1/users/me/starting-path", "users"),
    (r"^/api/v1/users/me/notification", "notifications"),
    (r"^/api/v1/users/me/quest", "badges-quests"),
    (r"^/api/v1/users/me/badges", "badges-quests"),
    (r"^/api/v1/users/me", "users"),
    (r"^/api/v1/users/", "users"),
    (r"^/api/v1/u/", "users"),
    (r"^/api/v1/onboarding/", "users"),
    (r"^/api/v1/urns", "lessons"),
    (r"^/api/v1/motifs", "lessons"),
    (r"^/api/v1/lessons", "lessons"),
    (r"^/api/v1/preview/", "lessons"),
    (r"^/api/v1/quizzes", "quizzes"),
    (r"^/api/v1/quiz", "quizzes"),
    (r"^/api/v1/quests", "badges-quests"),
    (r"^/api/v1/missions", "badges-quests"),
    (r"^/api/v1/badges", "badges-quests"),
    (r"^/api/v1/classrooms", "classrooms"),
    (r"^/api/v1/classes", "classrooms"),
    (r"^/api/v1/assignments", "classrooms"),
    (r"^/api/v1/leaderboard", "leaderboards"),
    (r"^/api/v1/leagues", "leaderboards"),
    (r"^/api/v1/notifications", "notifications"),
    (r"^/api/v1/push", "notifications"),
    (r"^/api/v1/sessions", "sessions"),
    (r"^/api/v1/analytics", "sessions"),
    (r"^/api/v1/crash-reports", "crash-reports"),
    (r"^/api/v1/admin/crash-reports", "admin"),
    (r"^/api/v1/admin/push", "admin"),
    (r"^/api/v1/admin/analytics", "admin"),
    (r"^/api/v1/admin/", "admin"),
    (r"^/api/v1/teacher/trails", "trails"),
    (r"^/api/v1/live/", "ai-tutor"),
    (r"^/api/v1/live-sessions", "live"),
    (r"^/api/v1/livekit", "live"),
    (r"^/api/v1/ai-tutor/", "ai-tutor"),
    (r"^/api/v1/ai/", "ai"),
    (r"^/api/v1/social/", "social"),
    (r"^/api/v1/history/", "history"),
    (r"^/api/v1/heritage/", "heritage"),
    (r"^/api/v1/rbpc/", "rbpc"),
    (r"^/api/v1/imperial/", "imperial"),
    (r"^/api/v1/content/ratings", "public-reads"),
    (r"^/api/v1/ranks", "public-reads"),
    (r"^/api/v1/tags", "public-reads"),
    (r"^/api/v1/timeline/", "timeline"),
    (r"^/api/v1/trails", "trails"),
    (r"^/api/v1/reviews", "fsrs"),
    (r"^/api/v1/review", "fsrs"),
    (r"^/api/v1/learning-path", "gamification"),
    (r"^/api/v1/progress", "progress"),
    (r"^/api/v1/streak", "progress"),
    (r"^/api/v1/hearts", "progress"),
    (r"^/api/v1/daily-missions", "badges-quests"),
    (r"^/api/v1/daily-goal", "progress"),
    (r"^/api/v1/weekly-quests", "badges-quests"),
    (r"^/api/v1/milestones", "progress"),
    (r"^/api/v1/skills", "gamification"),
    (r"^/api/v1/recommendations", "gamification"),
    (r"^/api/v1/search", "search"),
    (r"^/api/v1/certificates", "gamification"),
    (r"^/api/v1/dashboard", "users"),
    (r"^/api/v1/internal/", "foundations"),
    (r"^/progress/", "progress"),
    (r"^/motifs/", "lessons"),
    (r"^/health", "foundations"),
    (r"^/metrics", "foundations"),
    (r"^/api/v1/content/flags", "admin"),
    (r"^/api/v1/reports/abuse", "users"),
    (r"^/api/v1/features", "admin"),
    (r"^/api/v1/experiments", "admin"),
    (r"^/api/v1/app/", "admin"),
]


def classify_group(path: str) -> str:
    """Classify an API route path into its functional domain group."""
    for pattern, group in GROUP_RULES:
        if re.match(pattern, path):
            return group
    return "misc"


def normalize_path(path: str) -> str:
    """Normalize path by stripping query strings, trailing slashes, and spaces."""
    p = path.split("?")[0].strip()
    if p != "/" and p.endswith("/"):
        p = p[:-1]
    return p


def route_pattern_to_regex(pattern_path: str) -> re.Pattern:
    """Convert route path pattern with {param} or :param into regex Pattern."""
    norm = normalize_path(pattern_path)
    # Convert Axum :param syntax to {param}
    norm = re.sub(r":([a-zA-Z0-9_]+)", r"{\1}", norm)
    # Escape special regex chars except {param}
    regex_str = "^" + re.sub(r"\{[a-zA-Z0-9_]+\}", r"([^/]+)", norm) + "$"
    return re.compile(regex_str)


def inspect_route_modes(repo_root: Optional[Path] = None) -> tuple[set[str], str]:
    """Parse backend-rust/config/route-modes.toml for pinned gateway routes and defaults."""
    root = repo_root or REPO_ROOT
    config_file = root / ROUTE_MODES_REL_PATH
    if not config_file.exists():
        return set(), "native"

    with open(config_file, "rb") as f:
        data = tomllib.load(f)

    routes = data.get("routes", {})
    pinned = {key for key, mode in routes.items() if mode == "gateway"}
    default_mode = data.get("defaults", {}).get("unknown_routes", "native")
    return pinned, default_mode


def inspect_rust_routes(repo_root: Optional[Path] = None) -> list[dict[str, Any]]:
    """Parse backend-rust/src/main.rs to extract native Axum route registrations."""
    root = repo_root or REPO_ROOT
    main_rs = root / MAIN_RS_REL_PATH
    if not main_rs.exists():
        return []

    with open(main_rs, "r", encoding="utf-8") as f:
        content = f.read()

    # Truncate at test fixtures so test dummy routes are excluded
    if "#[cfg(test)]" in content:
        content = content.split("#[cfg(test)]")[0]

    pos = 0
    rust_routes: list[dict[str, Any]] = []
    while True:
        idx = content.find(".route(", pos)
        if idx == -1:
            break
        start_arg = idx + len(".route(")
        depth = 1
        i = start_arg
        in_string = False
        escape = False
        while i < len(content) and depth > 0:
            ch = content[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
            i += 1
        arg_str = content[start_arg : i - 1]
        pos = i

        m = re.match(r'^\s*"([^"]+)"\s*,\s*(.*)$', arg_str, re.DOTALL)
        if m:
            path = m.group(1)
            handler_expr = m.group(2)
            methods = re.findall(
                r"(?:axum::routing::)?(get|post|put|patch|delete)\(", handler_expr
            )
            norm_path = re.sub(r":([a-zA-Z0-9_]+)", r"{\1}", path)

            # Analyze auth requirements from handler expression
            if "require_admin" in handler_expr:
                auth_req = True
                roles = ["admin", "super_admin"]
            elif "require_teacher" in handler_expr:
                auth_req = True
                roles = ["teacher", "admin", "super_admin"]
            elif "authenticate" in handler_expr:
                auth_req = True
                roles = ["guest", "learner", "teacher", "admin", "super_admin"]
            else:
                auth_req = False
                roles = []

            for meth in methods:
                rust_routes.append(
                    {
                        "method": meth.upper(),
                        "path": norm_path,
                        "axum_path": path,
                        "handler": handler_expr.strip(),
                        "auth_required": auth_req,
                        "auth_optional": False,
                        "roles_required": roles,
                        "status": "ready",
                        "reachable": True,
                    }
                )

    return rust_routes


def _collect_dependencies(dependant: Any) -> set[str]:
    """Recursively collect callable names from a FastAPI Dependant object."""
    calls: set[str] = set()
    for child in getattr(dependant, "dependencies", []):
        if child.call:
            calls.add(getattr(child.call, "__name__", str(child.call)))
        calls.update(_collect_dependencies(child))
    return calls


def inspect_fastapi_routes(app: Optional[Any] = None) -> list[dict[str, Any]]:
    """Extract and analyze all active FastAPI APIRoutes."""
    if app is None:
        from backend.main import app as active_app

        app = active_app

    fastapi_routes: list[dict[str, Any]] = []

    for route_item in app.routes:
        if hasattr(route_item, "original_router"):
            router = route_item.original_router
            for sub in router.routes:
                if isinstance(sub, APIRoute):
                    dep_names = _collect_dependencies(sub.dependant)

                    # Determine auth & role constraints
                    if "get_super_admin_user" in dep_names:
                        auth_req = True
                        auth_opt = False
                        roles = ["super_admin"]
                    elif "get_admin_user" in dep_names:
                        auth_req = True
                        auth_opt = False
                        roles = ["admin", "super_admin"]
                    elif "get_staff_user" in dep_names:
                        auth_req = True
                        auth_opt = False
                        roles = ["teacher", "admin", "super_admin"]
                    elif "get_learner_user" in dep_names:
                        auth_req = True
                        auth_opt = False
                        roles = ["learner", "teacher", "admin", "super_admin"]
                    elif (
                        "get_current_user_optional" in dep_names
                        and "get_current_user" not in dep_names
                    ):
                        auth_req = False
                        auth_opt = True
                        roles = []
                    elif (
                        "get_current_user" in dep_names
                        or any("oauth2" in d.lower() for d in dep_names)
                    ):
                        auth_req = True
                        auth_opt = False
                        roles = ["guest", "learner", "teacher", "admin", "super_admin"]
                    else:
                        auth_req = False
                        auth_opt = False
                        roles = []

                    endpoint_name = (
                        f"{sub.endpoint.__module__}.{sub.endpoint.__name__}"
                        if hasattr(sub, "endpoint") and sub.endpoint
                        else None
                    )
                    summary = sub.summary or (
                        sub.endpoint.__doc__.strip().split("\n")[0]
                        if sub.endpoint and sub.endpoint.__doc__
                        else ""
                    )

                    for m in sub.methods:
                        m_upper = m.upper()
                        if m_upper in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                            fastapi_routes.append(
                                {
                                    "method": m_upper,
                                    "path": sub.path,
                                    "endpoint": endpoint_name,
                                    "auth_required": auth_req,
                                    "auth_optional": auth_opt,
                                    "roles_required": roles,
                                    "summary": summary,
                                    "tags": sub.tags or [],
                                    "status": "ready",
                                    "reachable": True,
                                }
                            )

    return fastapi_routes


def build_unified_route_inventory(
    repo_root: Optional[Path] = None,
    app: Optional[Any] = None,
) -> dict[str, Any]:
    """Build canonical baseline inventory unifying FastAPI and Rust Gateway routes."""
    root = repo_root or REPO_ROOT
    pinned_gateway, default_mode = inspect_route_modes(root)
    rust_routes = inspect_rust_routes(root)
    fastapi_routes = inspect_fastapi_routes(app)

    # Index rust routes by (method, regex_pattern)
    rust_indexed: list[tuple[str, re.Pattern, dict[str, Any]]] = []
    for r in rust_routes:
        rust_indexed.append(
            (r["method"], route_pattern_to_regex(r["path"]), r)
        )

    unified: dict[tuple[str, str], dict[str, Any]] = {}

    # 1. Process all FastAPI routes
    for f in fastapi_routes:
        method = f["method"]
        path = f["path"]
        key = f"{method} {path}"

        # Match against Rust native handlers
        matched_rust = None
        for rm, r_pat, r_entry in rust_indexed:
            if rm == method and r_pat.match(path):
                matched_rust = r_entry
                break

        # Check pinned status in route-modes.toml
        is_pinned = key in pinned_gateway
        if matched_rust:
            axum_key = f"{matched_rust['method']} {matched_rust['axum_path']}"
            if axum_key in pinned_gateway:
                is_pinned = True

        # Determine owner
        if matched_rust and not is_pinned:
            owner = "rust-native"
        else:
            owner = "python-gateway"

        unified[(method, path)] = {
            "method": method,
            "path": path,
            "group": classify_group(path),
            "owner": owner,
            "auth_required": f["auth_required"],
            "auth_optional": f["auth_optional"],
            "roles_required": f["roles_required"],
            "status": "ready",
            "reachable": True,
            "fastapi_endpoint": f["endpoint"],
            "rust_handler": matched_rust["handler"] if matched_rust else None,
            "gateway_pinned": is_pinned,
            "summary": f.get("summary", ""),
            "tags": f.get("tags", []),
        }

    # 2. Add Rust native routes that do not have direct FastAPI counterparts
    for r in rust_routes:
        method = r["method"]
        path = r["path"]
        r_pat = route_pattern_to_regex(path)

        # Check if already covered by a FastAPI route
        already_covered = any(
            fm == method and r_pat.match(fp) for (fm, fp) in unified.keys()
        )
        if not already_covered:
            key = f"{method} {r['axum_path']}"
            is_pinned = key in pinned_gateway
            owner = "python-gateway" if is_pinned else "rust-native"

            unified[(method, path)] = {
                "method": method,
                "path": path,
                "group": classify_group(path),
                "owner": owner,
                "auth_required": r["auth_required"],
                "auth_optional": False,
                "roles_required": r["roles_required"],
                "status": "ready",
                "reachable": True,
                "fastapi_endpoint": None,
                "rust_handler": r["handler"],
                "gateway_pinned": is_pinned,
                "summary": "Native Axum route",
                "tags": [classify_group(path)],
            }

    # 3. Include any pinned routes from route-modes.toml served by Python AI worker
    for pinned_key in pinned_gateway:
        parts = pinned_key.split(" ", 1)
        if len(parts) == 2:
            p_method, p_path = parts[0].upper(), parts[1]
            if (p_method, p_path) not in unified:
                unified[(p_method, p_path)] = {
                    "method": p_method,
                    "path": p_path,
                    "group": classify_group(p_path),
                    "owner": "python-gateway",
                    "auth_required": True,
                    "auth_optional": False,
                    "roles_required": [
                        "guest",
                        "learner",
                        "teacher",
                        "admin",
                        "super_admin",
                    ],
                    "status": "ready",
                    "reachable": True,
                    "fastapi_endpoint": "services.ai_teacher_agent.realtime_worker",
                    "rust_handler": None,
                    "gateway_pinned": True,
                    "summary": "Pinned Python AI teacher worker route",
                    "tags": [classify_group(p_path)],
                }

    # Deterministic sort by (group, path, method)
    routes_list = sorted(
        unified.values(),
        key=lambda e: (e["group"], e["path"], e["method"]),
    )

    # Calculate statistics
    total = len(routes_list)
    rust_native_cnt = sum(1 for e in routes_list if e["owner"] == "rust-native")
    python_gw_cnt = sum(1 for e in routes_list if e["owner"] == "python-gateway")
    auth_req_cnt = sum(1 for e in routes_list if e["auth_required"])
    auth_opt_cnt = sum(1 for e in routes_list if e["auth_optional"])
    public_cnt = sum(1 for e in routes_list if not e["auth_required"] and not e["auth_optional"])

    group_counts: dict[str, int] = {}
    for e in routes_list:
        group_counts[e["group"]] = group_counts.get(e["group"], 0) + 1

    role_counts: dict[str, int] = {}
    for e in routes_list:
        roles_key = ",".join(e["roles_required"]) if e["roles_required"] else "public"
        role_counts[roles_key] = role_counts.get(roles_key, 0) + 1

    return {
        "ticket_id": TICKET_ID,
        "slot": SLOT,
        "baseline_sha": SNAPSHOT_SHA,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "source_lock_reference": "artifacts/implementation/SOURCE_LOCK.json",
        "summary": {
            "total_unified_endpoints": total,
            "fastapi_endpoints_count": len(fastapi_routes),
            "rust_endpoints_count": len(rust_routes),
            "owner_counts": {
                "rust-native": rust_native_cnt,
                "python-gateway": python_gw_cnt,
            },
            "auth_counts": {
                "auth_required": auth_req_cnt,
                "auth_optional": auth_opt_cnt,
                "public": public_cnt,
            },
            "group_counts": group_counts,
            "role_counts": role_counts,
        },
        "route_modes_config": {
            "config_file": ROUTE_MODES_REL_PATH,
            "pinned_gateway_routes": sorted(pinned_gateway),
            "default_mode": default_mode,
        },
        "routes": routes_list,
    }


def evaluate_route(
    method: str,
    path: str,
    inventory_routes: Optional[list[dict[str, Any]]] = None,
    repo_root: Optional[Path] = None,
) -> dict[str, Any]:
    """Evaluate whether an endpoint (e.g. from UI or client) exists on the backend.

    Contract:
    - If the route exists on the backend (FastAPI or Rust):
      returns status="ready", is_ready=True, is_unknown=False, reachable=True.
    - If the route is unmapped or non-existent:
      returns status="UNKNOWN", is_ready=False, is_unknown=True, reachable=False.
      An unmapped route MUST NEVER be marked ready.
    """
    clean_method = method.upper().strip()
    clean_path = normalize_path(path)

    if inventory_routes is None:
        inv = build_unified_route_inventory(repo_root)
        inventory_routes = inv["routes"]

    for entry in inventory_routes:
        if entry["method"] == clean_method:
            # 1. Exact match
            if entry["path"] == clean_path:
                return {
                    "method": clean_method,
                    "path": clean_path,
                    "matched_path": entry["path"],
                    "status": "ready",
                    "is_ready": True,
                    "is_unknown": False,
                    "reachable": True,
                    "owner": entry["owner"],
                    "group": entry["group"],
                    "auth_required": entry["auth_required"],
                    "auth_optional": entry.get("auth_optional", False),
                    "roles_required": entry.get("roles_required", []),
                    "fastapi_endpoint": entry.get("fastapi_endpoint"),
                    "rust_handler": entry.get("rust_handler"),
                }

            # 2. Parameterized regex match
            r_pat = route_pattern_to_regex(entry["path"])
            if r_pat.match(clean_path):
                return {
                    "method": clean_method,
                    "path": clean_path,
                    "matched_path": entry["path"],
                    "status": "ready",
                    "is_ready": True,
                    "is_unknown": False,
                    "reachable": True,
                    "owner": entry["owner"],
                    "group": entry["group"],
                    "auth_required": entry["auth_required"],
                    "auth_optional": entry.get("auth_optional", False),
                    "roles_required": entry.get("roles_required", []),
                    "fastapi_endpoint": entry.get("fastapi_endpoint"),
                    "rust_handler": entry.get("rust_handler"),
                }

    # Negative / unmapped route: MUST be flagged UNKNOWN and NOT ready
    return {
        "method": clean_method,
        "path": clean_path,
        "matched_path": None,
        "status": "UNKNOWN",
        "is_ready": False,
        "is_unknown": True,
        "reachable": False,
        "owner": None,
        "group": None,
        "auth_required": None,
        "auth_optional": None,
        "roles_required": [],
        "fastapi_endpoint": None,
        "rust_handler": None,
        "error": f"Endpoint '{clean_method} {clean_path}' is not mapped to any active backend route.",
    }


def export_baseline_artifact(
    repo_root: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """Build and write the baseline inventory artifact to JSON file."""
    root = repo_root or REPO_ROOT
    target_path = output_path or (root / BASELINE_ARTIFACT_REL_PATH)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    data = build_unified_route_inventory(root)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return target_path
