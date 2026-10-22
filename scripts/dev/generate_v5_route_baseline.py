#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI script to generate W00_A01_route_inventory_baseline.json artifact for V5-T001."""
import json
import sys
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.domain.route_inventory import export_baseline_artifact


def main() -> int:
    target = export_baseline_artifact(REPO_ROOT)
    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)

    summary = data.get("summary", {})
    print(f"Generated unified route inventory baseline: {target}")
    print(f"  - Total unified endpoints: {summary.get('total_unified_endpoints')}")
    print(f"  - FastAPI endpoints: {summary.get('fastapi_endpoints_count')}")
    print(f"  - Rust Axum endpoints: {summary.get('rust_endpoints_count')}")
    print(f"  - Rust-native: {summary.get('owner_counts', {}).get('rust-native')}")
    print(f"  - Python-gateway: {summary.get('owner_counts', {}).get('python-gateway')}")
    print(f"  - Auth required: {summary.get('auth_counts', {}).get('auth_required')}")
    print(f"  - Auth optional: {summary.get('auth_counts', {}).get('auth_optional')}")
    print(f"  - Public endpoints: {summary.get('auth_counts', {}).get('public')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
