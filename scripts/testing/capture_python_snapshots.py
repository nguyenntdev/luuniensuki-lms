#!/usr/bin/env python3
"""
Capture contract test snapshots from the Python FastAPI service.

Task 1.20: Exercises Python_Service with a deterministic seed corpus and
writes fixture files to `backend-rust/tests/contract/fixtures/<group>/<case>.json`.

Usage:
    python scripts/testing/capture_python_snapshots.py [--base-url http://localhost:8000]

Each fixture is a JSON file with the shape:
    {
        "name": "<case_name>",
        "request": { "method": "...", "path": "...", "headers": {...}, "body": ... },
        "expected": { "status": <int>, "content_type": "...", "body": ... }
    }

Validates: Req 4.1, 4.6, 4.8
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install with: pip install requests")
    sys.exit(1)


# Project root (two levels up from this script)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = PROJECT_ROOT / "backend-rust" / "tests" / "contract" / "fixtures"


# ---------------------------------------------------------------------------
# Seed corpus: deterministic test cases per endpoint group
# ---------------------------------------------------------------------------

SEED_CORPUS = {
    "foundations": [
        {
            "name": "health_happy_path",
            "method": "GET",
            "path": "/health",
            "headers": {},
            "body": None,
        },
    ],
    "public-reads": [
        {
            "name": "content_ratings_happy_path",
            "method": "GET",
            "path": "/api/v1/content/ratings",
            "headers": {},
            "body": None,
        },
        {
            "name": "ranks_happy_path",
            "method": "GET",
            "path": "/api/v1/ranks",
            "headers": {},
            "body": None,
        },
        {
            "name": "tags_happy_path",
            "method": "GET",
            "path": "/api/v1/tags",
            "headers": {},
            "body": None,
        },
        {
            "name": "badges_happy_path",
            "method": "GET",
            "path": "/api/v1/badges",
            "headers": {},
            "body": None,
        },
    ],
    "auth": [
        {
            "name": "login_missing_body",
            "method": "POST",
            "path": "/api/v1/auth/login",
            "headers": {"Content-Type": "application/json"},
            "body": {},
        },
        {
            "name": "login_invalid_credentials",
            "method": "POST",
            "path": "/api/v1/auth/login",
            "headers": {"Content-Type": "application/json"},
            "body": {"username": "nonexistent@test.com", "password": "wrong"},
        },
        {
            "name": "register_missing_fields",
            "method": "POST",
            "path": "/api/v1/auth/register",
            "headers": {"Content-Type": "application/json"},
            "body": {},
        },
        {
            "name": "me_no_auth",
            "method": "GET",
            "path": "/api/v1/auth/me",
            "headers": {},
            "body": None,
        },
    ],
}


def capture_response(
    base_url: str,
    method: str,
    path: str,
    headers: dict,
    body: Optional[Any],
) -> dict:
    """Send a request to Python_Service and capture the response."""
    url = f"{base_url}{path}"

    kwargs: dict = {"headers": headers, "timeout": 30}
    if body is not None:
        kwargs["json"] = body

    resp = requests.request(method, url, **kwargs)

    # Extract content type
    content_type = resp.headers.get("Content-Type", "")
    # Normalize: strip parameters for comparison (e.g., "; charset=utf-8")
    content_type_base = content_type.split(";")[0].strip()

    # Parse body as JSON if possible
    try:
        response_body = resp.json()
    except (json.JSONDecodeError, ValueError):
        response_body = None

    return {
        "status": resp.status_code,
        "content_type": content_type_base,
        "body": response_body,
    }


def write_fixture(group: str, case: dict, response: dict) -> Path:
    """Write a fixture JSON file."""
    group_dir = FIXTURES_DIR / group
    group_dir.mkdir(parents=True, exist_ok=True)

    fixture = {
        "name": case["name"],
        "request": {
            "method": case["method"],
            "path": case["path"],
            "headers": case.get("headers", {}),
            "body": case.get("body"),
        },
        "expected": response,
    }

    fixture_path = group_dir / f"{case['name']}.json"
    with open(fixture_path, "w") as f:
        json.dump(fixture, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return fixture_path


def main():
    parser = argparse.ArgumentParser(
        description="Capture contract test snapshots from Python_Service"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the Python FastAPI service (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--groups",
        nargs="*",
        default=None,
        help="Specific groups to capture (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be captured without making requests",
    )
    args = parser.parse_args()

    groups = args.groups or list(SEED_CORPUS.keys())

    print(f"Capturing snapshots from: {args.base_url}")
    print(f"Groups: {', '.join(groups)}")
    print(f"Output: {FIXTURES_DIR}")
    print()

    total = 0
    errors = 0

    for group in groups:
        if group not in SEED_CORPUS:
            print(f"  SKIP: Unknown group '{group}'")
            continue

        cases = SEED_CORPUS[group]
        print(f"  [{group}] {len(cases)} cases")

        for case in cases:
            if args.dry_run:
                print(f"    DRY-RUN: {case['method']} {case['path']} ({case['name']})")
                total += 1
                continue

            try:
                response = capture_response(
                    args.base_url,
                    case["method"],
                    case["path"],
                    case.get("headers", {}),
                    case.get("body"),
                )
                fixture_path = write_fixture(group, case, response)
                print(f"    OK: {case['name']} -> {fixture_path.relative_to(PROJECT_ROOT)}")
                total += 1
            except requests.ConnectionError:
                print(f"    ERROR: Cannot connect to {args.base_url} for {case['name']}")
                errors += 1
            except Exception as e:
                print(f"    ERROR: {case['name']}: {e}")
                errors += 1

    print()
    print(f"Done: {total} captured, {errors} errors")

    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
