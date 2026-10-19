#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standalone CLI script to seed the Huế Heritage Knowledge Catalogue.

Ingests and synchronizes:
1. data/heritage-hue/inventory.unesco-14.yaml
   - 14 official UNESCO World Heritage components (678-001..678-014)
   - 6 priority child monuments (enclosed inside Kinh thành Huế)
   - 3 traditional craft communities
2. data/heritage-hue/sketchfab-curated.yaml
   - 23 curated Sketchfab 3D models with rights governance & guardrail enforcement

Usage:
    # Dry-run validation only (default, zero DB modifications):
    python scripts/heritage/seed_hue_heritage.py --dry-run

    # Commit mode (upserts records safely without overwriting manual reviews):
    python scripts/heritage/seed_hue_heritage.py --commit

Options:
    --dry-run             Run validation and report statistics without writing to database.
    --commit              Write and synchronize catalogue entries to the database.
    --inventory PATH      Custom path to inventory.unesco-14.yaml.
    --sketchfab PATH      Custom path to sketchfab-curated.yaml.
    --database-url URL    Override DATABASE_URL environment variable.
    --verbose, -v         Enable detailed verbose logging.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.services.heritage_import import (
    DEFAULT_CREATORS_PATH,
    DEFAULT_EXPERIENCES_PATH,
    DEFAULT_INVENTORY_PATH,
    DEFAULT_SKETCHFAB_PATH,
    DEFAULT_STORIES_PATH,
    HeritageImportService,
    ImportStats,
    ValidationReport,
    import_heritage_data,
)


def setup_logging(verbose: bool = False) -> None:
    """Configure structured logging for CLI execution."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def print_banner(dry_run: bool) -> None:
    mode_str = "DRY-RUN VALIDATION MODE" if dry_run else "COMMIT & SYNCHRONIZE MODE"
    print("=" * 80)
    print(f" LƯU NIÊN — RBPC 2026: HUẾ HERITAGE CATALOGUE SEEDER")
    print(f" Mode: {mode_str}")
    print("=" * 80)


def print_report(report: ValidationReport, stats: ImportStats | None = None) -> None:
    print("\n--- VALIDATION SUMMARY ---")
    print(f"Status:                    {'PASS' if report.is_valid else 'FAIL'}")
    print(f"UNESCO Components:         {report.unesco_components_count} / 14")
    print(f"Child Monuments:           {report.child_monuments_count} / 6")
    print(f"Craft Communities:         {report.craft_communities_count} / 3")
    print(f"Total Places:              {report.total_places_count} / 23")
    print(f"Total Relationships:       {report.total_relations_count}")
    print(f"Sketchfab 3D Models:       {report.models_count} / 23")
    print(f"Consented Creators:        {report.creators_count} / 3")
    print(f"Workshop Experiences:      {report.experiences_count} / 3")
    print(f"Curated Stories:           {report.stories_count} / 3")
    print(f"Evidence Claims:           {report.claims_count}")
    print(f"Guardrails Enforced:       {'YES' if report.guardrails_passed else 'NO'}")

    print("\n--- GUARDRAILS AUDIT ---")
    gd = report.guardrail_details
    print(f"  SF-020 Rejected Accuracy Guardrail: {'ENFORCED' if gd.get('sf020_rejected_accuracy') else 'FAILED'}")
    print(f"  SF-010 Blocked NC Guardrail:        {'ENFORCED' if gd.get('sf010_blocked_nc') else 'FAILED'}")
    print(f"  SF-017 Blocked NoAI Guardrail:      {'ENFORCED' if gd.get('sf017_blocked_noai') else 'FAILED'}")
    print(f"  Candidate CC BY Embeds:             {', '.join(gd.get('candidate_cc_by_models', []))}")

    if report.warnings:
        print(f"\n--- WARNINGS ({len(report.warnings)}) ---")
        for w in report.warnings:
            print(f"  [WARN] {w}")

    if report.errors:
        print(f"\n--- ERRORS ({len(report.errors)}) ---")
        for e in report.errors:
            print(f"  [ERROR] {e}")

    if stats and not stats.dry_run:
        print("\n--- INGESTION METRICS ---")
        print(f"Places Inserted:           {stats.places_inserted}")
        print(f"Places Updated:            {stats.places_updated}")
        print(f"Places Preserved (Review): {stats.places_preserved_editorial}")
        print(f"Relations Inserted:        {stats.relations_inserted}")
        print(f"Relations Updated:         {stats.relations_updated}")
        print(f"Relations Preserved (Ver): {stats.relations_preserved_verified}")
        print(f"Media Assets Inserted:     {stats.media_inserted}")
        print(f"Media Assets Updated:      {stats.media_updated}")
        print(f"Media Preserved (Review):  {stats.media_preserved_editorial}")
        print(f"Creators Inserted:         {stats.creators_inserted}")
        print(f"Creators Updated:          {stats.creators_updated}")
        print(f"Creators Preserved (Rev):  {stats.creators_preserved_consent}")
        print(f"Experiences Inserted:      {stats.experiences_inserted}")
        print(f"Experiences Updated:       {stats.experiences_updated}")
        print(f"Stories Inserted:          {stats.stories_inserted}")
        print(f"Stories Updated:           {stats.stories_updated}")
        print(f"Stories Preserved (Rev):   {stats.stories_preserved_editorial}")
        print(f"Claims Inserted:           {stats.claims_inserted}")
        print(f"Claims Updated:            {stats.claims_updated}")

    print("=" * 80)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed and synchronize Huế Living Heritage data into the database."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Perform dry-run validation only without writing to database (default).",
    )
    group.add_argument(
        "--commit",
        action="store_true",
        help="Execute database writes and synchronize catalogue.",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=DEFAULT_INVENTORY_PATH,
        help=f"Path to inventory.unesco-14.yaml (default: {DEFAULT_INVENTORY_PATH})",
    )
    parser.add_argument(
        "--sketchfab",
        type=Path,
        default=DEFAULT_SKETCHFAB_PATH,
        help=f"Path to sketchfab-curated.yaml (default: {DEFAULT_SKETCHFAB_PATH})",
    )
    parser.add_argument(
        "--creators",
        type=Path,
        default=DEFAULT_CREATORS_PATH,
        help=f"Path to creators.yaml (default: {DEFAULT_CREATORS_PATH})",
    )
    parser.add_argument(
        "--experiences",
        type=Path,
        default=DEFAULT_EXPERIENCES_PATH,
        help=f"Path to experiences.yaml (default: {DEFAULT_EXPERIENCES_PATH})",
    )
    parser.add_argument(
        "--stories",
        type=Path,
        default=DEFAULT_STORIES_PATH,
        help=f"Path to stories.yaml (default: {DEFAULT_STORIES_PATH})",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="Database connection URL. Defaults to DATABASE_URL environment variable.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose debug logging.",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    dry_run = not args.commit

    print_banner(dry_run)

    if not args.inventory.is_file():
        print(f"Error: Inventory file not found: {args.inventory}", file=sys.stderr)
        return 1
    if not args.sketchfab.is_file():
        print(f"Error: Sketchfab file not found: {args.sketchfab}", file=sys.stderr)
        return 1
    if args.creators and not args.creators.is_file():
        print(f"Error: Creators file not found: {args.creators}", file=sys.stderr)
        return 1
    if args.experiences and not args.experiences.is_file():
        print(f"Error: Experiences file not found: {args.experiences}", file=sys.stderr)
        return 1
    if args.stories and not args.stories.is_file():
        print(f"Error: Stories file not found: {args.stories}", file=sys.stderr)
        return 1

    db_url = (
        args.database_url
        or os.environ.get("DATABASE_URL")
        or "postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki"
    )

    if dry_run:
        # Dry-run validation does not strictly require an active database, but will connect if available
        session = None
        engine = None
        try:
            engine = create_engine(db_url, pool_pre_ping=True)
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()
        except Exception as e:
            logging.debug("Running dry-run without active DB connection: %s", e)

        try:
            service = HeritageImportService(
                db=session,
                inventory_path=args.inventory,
                sketchfab_path=args.sketchfab,
                stories_path=args.stories,
                creators_path=args.creators,
                experiences_path=args.experiences,
            )
            report = service.validate()
            stats = ImportStats(dry_run=True)
            print_report(report, stats)
            return 0 if report.is_valid else 1
        finally:
            if session:
                session.close()
            if engine:
                engine.dispose()
    else:
        # Commit mode requires active DB session
        try:
            engine = create_engine(db_url, pool_pre_ping=True)
            SessionLocal = sessionmaker(bind=engine)
            with SessionLocal() as session:
                report, stats = import_heritage_data(
                    db=session,
                    inventory_path=args.inventory,
                    sketchfab_path=args.sketchfab,
                    stories_path=args.stories,
                    creators_path=args.creators,
                    experiences_path=args.experiences,
                    dry_run=False,
                )
                print_report(report, stats)
                return 0 if report.is_valid else 1
        except Exception as exc:
            print(f"\nFATAL DATABASE ERROR: {exc}", file=sys.stderr)
            logging.exception("Database transaction failed during commit.")
            return 2


if __name__ == "__main__":
    sys.exit(main())
