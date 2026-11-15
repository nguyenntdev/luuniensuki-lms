#!/usr/bin/env python3
"""P14 accessibility-audit CLI.

Usage:
    python -m research_v3.methods.p14.cli_audit \
        [--manifest PATH] [--out DIR] [--baselines]

Evaluates a learning-object manifest (JSON, list of objects in p14-schema-1.0.0
form) against the UDL + WCAG 2.2 AA rubric and writes:
  - audit_report.json   (verdicts, metrics, remediation list)
  - baseline_results.json (C0 / C1 vs proposed, optional)
  - audit_report.sha256 (checksum of audit_report.json)

With no --manifest, audits the documented synthetic manifest (clearly labelled
"synthetic, no third-party rights") and marks the run PARTIAL for external
media. Exit code is 0 even when objects FAIL (a FAIL is a finding, not a
crash); exit code 1 means the audit itself could not run (fail-closed).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from research_v3.methods.p14.audit import audit_manifest
from research_v3.methods.p14.baselines import run_baselines
from research_v3.methods.p14.rights import external_media_status
from research_v3.methods.p14.schema import MediaAsset, LearningObject, SchemaError
from research_v3.methods.p14.synthetic import (
    SYNTHETIC_MANIFEST_VERSION,
    manifest_sha256,
    synthetic_manifest,
)


def load_manifest(path: Path) -> tuple[list, str, str]:
    """Load objects from a JSON manifest file; returns (objects, label, sha)."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries = raw.get("objects", raw) if isinstance(raw, dict) else raw
    objects: list[LearningObject] = []
    for entry in entries:
        assets = tuple(MediaAsset(**a) for a in entry["assets"])
        lbw = entry.get("low_bandwidth_variant")
        objects.append(
            LearningObject(
                object_id=entry["object_id"],
                title=entry["title"],
                origin=entry["origin"],
                source_url=entry.get("source_url"),
                rights=entry["rights"],
                assets=assets,
                low_bandwidth_variant=tuple(MediaAsset(**a) for a in lbw) if lbw else None,
                metadata=entry.get("metadata", {}),
            )
        )
    if not objects:
        raise SchemaError(f"manifest {path} contains no objects")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return objects, str(path), digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P14 UDL/WCAG learning-object audit")
    parser.add_argument("--manifest", type=Path, default=None, help="JSON manifest; default = synthetic")
    parser.add_argument("--out", type=Path, default=Path("research_artifacts_v3/runs/p14"))
    parser.add_argument("--baselines", action="store_true", help="also run C0/C1 baselines")
    args = parser.parse_args(argv)

    if args.manifest is not None:
        try:
            objects, manifest_label, manifest_sha = load_manifest(args.manifest)
        except Exception as exc:  # fail closed
            print(f"audit could not run: {exc}", file=sys.stderr)
            return 1
        media_scope = "external+synthetic per manifest labels"
    else:
        objects = synthetic_manifest()
        manifest_label = f"builtin:{SYNTHETIC_MANIFEST_VERSION}"
        manifest_sha = manifest_sha256(objects)
        media_scope = "synthetic-only (external media BLOCKED; study PARTIAL for external media)"

    report = audit_manifest(objects)
    report["manifest"] = {
        "label": manifest_label,
        "sha256": manifest_sha,
        "object_count": len(objects),
        "media_scope": media_scope,
        "rights": external_media_status(),
    }

    args.out.mkdir(parents=True, exist_ok=True)
    report_path = args.out / "audit_report.json"
    report_bytes = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8")
    report_path.write_bytes(report_bytes)
    (args.out / "audit_report.sha256").write_text(hashlib.sha256(report_bytes).hexdigest() + "\n")

    print(
        json.dumps(
            {
                "objects": len(objects),
                "objects_pass": report["metrics"]["objects_pass"],
                "objects_fail": report["metrics"]["objects_fail"],
                "conformance_rate": report["metrics"]["accessibility_conformance_rate"],
                "missing_affordance_count": report["metrics"]["missing_affordance_count"],
                "report": str(report_path),
            }
        )
    )

    if args.baselines:
        from research_v3.methods.p14.audit import audit_object
        from research_v3.methods.p14.rubric import load_rubric

        rubric = load_rubric()
        proposed = []
        for obj in objects:
            _, verdict = audit_object(obj, rubric)
            proposed.append(verdict.verdict == "PASS")
        baseline_rows = run_baselines(objects)
        baseline_out = {
            "proposed": [{"object_id": o.object_id, "verdict": v} for o, v in zip(objects, proposed)],
            "baselines": baseline_rows,
            "manifest_sha256": manifest_sha,
        }
        (args.out / "baseline_results.json").write_bytes(
            json.dumps(baseline_out, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8")
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
