#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LƯU NIÊN — RBPC 2026: CLI Script to Load & Verify Demonstration Fixtures."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.db import SessionLocal
from backend.services.demo_fixtures import verify_demo_fixtures_integrity
from backend.services.heritage_import import import_heritage_data


def main():
    parser = argparse.ArgumentParser(description="Load clean demonstration fixtures for LƯU NIÊN RBPC 2026.")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing fixtures without seeding.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if not args.verify_only:
            print("Seeding verified heritage and commercial data...")
            import_heritage_data(db=db, dry_run=False)

        report = verify_demo_fixtures_integrity(db)
        print("Demo Fixtures Integrity Report:")
        for k, v in report.items():
            print(f"  {k}: {v}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
