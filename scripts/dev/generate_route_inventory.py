#!/usr/bin/env python3
"""Generate backend-rust/docs/route-inventory.json by parsing FastAPI route
decorators from backend/main.py and backend/routes/.

This script does NOT import the FastAPI app (avoids needing all Python deps
installed). Instead it uses regex to extract @app.{method}("path") and
@router.{method}("path") decorators.

Output is sorted by (group, path, method) for deterministic diffs (Property 4).
"""

import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
OUTPUT_PATH = os.path.join(REPO_ROOT, "backend-rust", "docs", "route-inventory.json")

# Regex to match FastAPI route decorators
# Matches: @app.get("/path"...) or @router.post("/path"...)
ROUTE_PATTERN = re.compile(
    r'@(?:app|router)\.(get|post|put|patch|delete)\(\s*\n?\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)

# Map paths to endpoint groups based on prefix patterns
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
    (r"^/api/v1/quests", "badges-quests"),
    (r"^/api/v1/missions", "badges-quests"),
    (r"^/api/v1/badges", "badges-quests"),
    (r"^/api/v1/classrooms", "classrooms"),
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
    (r"^/api/v1/live/", "ai-tutor"),
    (r"^/api/v1/ai-tutor/", "ai-tutor"),
    (r"^/api/v1/content/ratings", "public-reads"),
    (r"^/api/v1/ranks", "public-reads"),
    (r"^/api/v1/tags", "public-reads"),
    (r"^/api/v1/internal/", "foundations"),
    (r"^/progress/", "progress"),
    (r"^/motifs/", "lessons"),
    (r"^/health", "foundations"),
]


def classify_group(path: str) -> str:
    for pattern, group in GROUP_RULES:
        if re.match(pattern, path):
            return group
    return "misc"


def extract_routes_from_file(filepath: str) -> list:
    """Extract (method, path) tuples from a Python file."""
    routes = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return routes

    for match in ROUTE_PATTERN.finditer(content):
        method = match.group(1).upper()
        path = match.group(2)
        routes.append((method, path))

    return routes


def main():
    all_routes = []

    # Parse backend/main.py
    main_py = os.path.join(BACKEND_DIR, "main.py")
    if os.path.exists(main_py):
        all_routes.extend(extract_routes_from_file(main_py))

    # Parse backend/routes/*.py and backend/routers/*.py
    for dir_name in ("routes", "routers"):
        routes_dir = os.path.join(BACKEND_DIR, dir_name)
        if os.path.isdir(routes_dir):
            for fname in sorted(os.listdir(routes_dir)):
                if fname.endswith(".py") and fname != "__init__.py":
                    all_routes.extend(
                        extract_routes_from_file(os.path.join(routes_dir, fname))
                    )

    # Deduplicate (same method+path from different files)
    seen = set()
    unique_routes = []
    for method, path in all_routes:
        key = (method, path)
        if key not in seen:
            seen.add(key)
            unique_routes.append(key)

    # Build inventory entries
    inventory = []
    for method, path in unique_routes:
        group = classify_group(path)
        inventory.append(
            {
                "method": method,
                "path": path,
                "group": group,
                "status": "gateway",  # default; updated as routes go native
            }
        )

    # Sort deterministically (Property 4)
    inventory.sort(key=lambda e: (e["group"], e["path"], e["method"]))

    # Write output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Generated {len(inventory)} routes → {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
