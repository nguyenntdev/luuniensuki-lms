"""Materialize Research V2 datasets from the frozen legacy held-out test sets.

Legacy ``research/fixtures/holdout/*.jsonl`` are read-only historical evidence.
This script writes NEW versioned V2 datasets under ``research_v2/data/<ln>/``:

  t3_inputs.jsonl : case_id, group_id, input   (inference-time only, oracle-free)
  t3_gold.jsonl   : case_id, expected_decision (evaluator-side, access controlled)
  dataset_manifest.json : per-study SHA-256 + counts

Gold labels are separated so a model can never read them, and the V2 input file
is derived by masking away every forbidden key.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research_v2.contracts.canonical_hash import sha256_bytes, sha256_input, canonical_json
from research_v2.contracts.input_masking import mask_case_input

STUDY_IDS = [f"LN-{i:02d}" for i in range(1, 11)]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def materialize_study(repo_root: Path, study_id: str) -> dict:
    src = repo_root / "research" / "fixtures" / "holdout" / f"{study_id}_holdout.jsonl"
    if not src.is_file():
        raise FileNotFoundError(f"missing legacy holdout {src}")
    out_dir = repo_root / "research_v2" / "data" / study_id.lower().replace("-", "")
    out_dir.mkdir(parents=True, exist_ok=True)

    inputs: list[dict] = []
    golds: list[dict] = []
    for lineno, line in enumerate(src.open(encoding="utf-8"), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        cid = row["case_id"]
        features = mask_case_input(row)
        group_id = (
            row.get("group_id")
            or (row.get("input") or {}).get("group_id")
            or f"{study_id}-grp-{lineno:03d}"
        )
        inputs.append(
            {
                "study_id": study_id,
                "case_id": cid,
                "group_id": str(group_id),
                "input": features,
                "input_sha256": sha256_input(features),
            }
        )
        oracle = row.get("oracle") or {}
        decision = row.get("expected_decision") or oracle.get("expected_decision")
        if not decision:
            raise ValueError(f"{study_id}:{lineno}: no expected decision in legacy row")
        golds.append(
            {
                "study_id": study_id,
                "case_id": cid,
                "expected_decision": decision,
                "oracle_basis": oracle.get("basis"),
            }
        )

    inp_path = out_dir / "t3_inputs.jsonl"
    gold_path = out_dir / "t3_gold.jsonl"
    inp_path.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in inputs),
        encoding="utf-8",
    )
    gold_path.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in golds),
        encoding="utf-8",
    )
    return {
        "study_id": study_id,
        "n_cases": len(inputs),
        "inputs_path": str(inp_path.relative_to(repo_root)),
        "inputs_sha256": sha256_bytes(inp_path.read_bytes()),
        "gold_path": str(gold_path.relative_to(repo_root)),
        "gold_sha256": sha256_bytes(gold_path.read_bytes()),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Materialize Research V2 datasets")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--study", default=None)
    a = ap.parse_args(argv)
    root = _repo_root()
    studies = [a.study] if a.study else STUDY_IDS
    results = []
    for study in studies:
        try:
            results.append(materialize_study(root, study))
        except Exception as exc:  # pragma: no cover - surfaced to CLI
            print(f"FAIL {study}: {exc}", file=sys.stderr)
            return 1
    manifest = {
        "hash_standard": "sha256(sort_keys,compact,utf8)",
        "tier": "T3",
        "datasets": results,
        "total_cases": sum(r["n_cases"] for r in results),
    }
    (root / "research_v2" / "data" / "dataset_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"n_studies": len(results), "total_cases": manifest["total_cases"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
