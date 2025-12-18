#!/usr/bin/env python3
"""
Import motif coordinates from Annotation Tool JSON export into the database.

Usage:
    python -m backend.import_coordinates --json-path data/motif-coordinates.json
    
    # Or with DATABASE_URL set:
    DATABASE_URL=postgresql+psycopg://... python -m backend.import_coordinates data/coords.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import Session, sessionmaker

if __package__ in (None, ""):
    REPO_ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(REPO_ROOT))
    from backend.models import Base, Motif, Urn
else:
    from .models import Base, Motif, Urn


def load_coordinates_json(json_path: Path) -> list[dict]:
    """Load coordinates from exported JSON file."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Expected JSON array at top level")
    return data


def normalize_name(name: str) -> str:
    """Normalize name for matching (lowercase, strip, collapse whitespace)."""
    return " ".join(name.lower().strip().split())


def import_coordinates(session: Session, coordinates: list[dict], dry_run: bool = False) -> dict:
    """Import coordinates into database, matching by urn_slug + motif_name."""
    stats = {"matched": 0, "unmatched": 0, "errors": [], "updated": []}
    
    # Cache urns by slug
    urns_by_slug: dict[str, Urn] = {}
    for urn in session.execute(select(Urn)).scalars().all():
        urns_by_slug[urn.slug] = urn
    
    # Cache motifs by (urn_id, normalized_name) and (urn_id, mesh_name)
    all_motifs = session.execute(select(Motif)).scalars().all()
    motifs_by_name: dict[tuple, Motif] = {}
    motifs_by_mesh: dict[tuple, Motif] = {}
    
    for motif in all_motifs:
        key_name = (motif.urn_id, normalize_name(motif.name))
        key_mesh = (motif.urn_id, motif.mesh_name.lower())
        motifs_by_name[key_name] = motif
        motifs_by_mesh[key_mesh] = motif
    
    for idx, coord in enumerate(coordinates):
        urn_slug = coord.get("urn_slug", "").strip()
        motif_name = coord.get("motif_name", "").strip()
        mesh_name = coord.get("mesh_name", "").strip()
        pos_x = float(coord.get("pos_x", 0))
        pos_y = float(coord.get("pos_y", 0))
        pos_z = float(coord.get("pos_z", 0))
        bounding_radius = float(coord.get("bounding_radius", 0.08))
        
        if not urn_slug or not motif_name:
            stats["errors"].append(f"Entry {idx}: missing urn_slug or motif_name")
            continue
        
        urn = urns_by_slug.get(urn_slug)
        if not urn:
            stats["errors"].append(f"Entry {idx}: urn_slug '{urn_slug}' not found")
            stats["unmatched"] += 1
            continue
        
        # Try to match by name first, then by mesh_name
        motif = motifs_by_name.get((urn.id, normalize_name(motif_name)))
        if not motif and mesh_name:
            motif = motifs_by_mesh.get((urn.id, mesh_name.lower()))
        
        if not motif:
            stats["errors"].append(f"Entry {idx}: motif '{motif_name}' not found in urn '{urn_slug}'")
            stats["unmatched"] += 1
            continue
        
        # Update positions
        old_pos = (motif.pos_x, motif.pos_y, motif.pos_z, motif.bounding_radius)
        if not dry_run:
            motif.pos_x = pos_x
            motif.pos_y = pos_y
            motif.pos_z = pos_z
            motif.bounding_radius = bounding_radius
        
        stats["matched"] += 1
        stats["updated"].append({
            "urn": urn_slug,
            "motif": motif.name,
            "old": old_pos,
            "new": (pos_x, pos_y, pos_z, bounding_radius),
        })
    
    if not dry_run:
        session.commit()
    
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Import motif coordinates from JSON")
    parser.add_argument("json_path", help="Path to coordinates JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without making changes")
    args = parser.parse_args()
    
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki",
    )
    
    json_path = Path(args.json_path)
    if not json_path.exists():
        print(f"Error: File not found: {json_path}")
        sys.exit(1)
    
    print(f"Loading coordinates from {json_path}...")
    coordinates = load_coordinates_json(json_path)
    print(f"Found {len(coordinates)} coordinate entries")
    
    print(f"\nConnecting to database...")
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    
    with SessionLocal() as session:
        print(f"{'DRY RUN - ' if args.dry_run else ''}Importing coordinates...")
        stats = import_coordinates(session, coordinates, dry_run=args.dry_run)
    
    print(f"\n{'=' * 50}")
    print(f"Results:")
    print(f"  Matched & updated: {stats['matched']}")
    print(f"  Unmatched: {stats['unmatched']}")
    print(f"  Errors: {len(stats['errors'])}")
    
    if stats["errors"]:
        print(f"\nErrors:")
        for err in stats["errors"][:20]:
            print(f"  - {err}")
        if len(stats["errors"]) > 20:
            print(f"  ... and {len(stats['errors']) - 20} more")
    
    if args.dry_run and stats["updated"]:
        print(f"\nWould update (first 10):")
        for upd in stats["updated"][:10]:
            print(f"  - {upd['urn']}/{upd['motif']}: {upd['old']} -> {upd['new']}")


if __name__ == "__main__":
    main()

