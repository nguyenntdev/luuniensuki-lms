"""P10 CLI: run the preregistered matrix, freeze artifacts, print the report.

Usage (from repo root):
    python -m research_v3.methods.p10.cli run      # run + freeze artifact
    python -m research_v3.methods.p10.cli report   # run + print summary (no file)
    python -m research_v3.methods.p10.cli verify   # re-run and compare payload hash
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .experiment import RUNS_DIR, freeze_run, run_matrix


def _print_summary(payload: dict) -> None:
    print("=" * 72)
    print("P10 — Spiral heritage curriculum sequence (grades 10-12) — run report")
    print("=" * 72)
    reg = payload["anchor_registry"]
    print(
        f"Anchors: {reg['total_anchors']} total | documented={reg['documented']} "
        f"| needs_expert_review={reg['needs_expert_review']}"
    )
    corpus = payload["corpus"]
    print(
        f"Corpus : {corpus['n_objects']} objects / {corpus['n_urns']} urns / "
        f"{corpus['n_edges']} DAG edges (AI-generated descriptions: 100% — flagged)"
    )
    print("-" * 72)
    for d in payload["designs"]:
        flag = "VALID" if d["valid"] else "INVALID"
        print(f"[{flag:7s}] {d['design_id']}")
        for rc in d["certificate"]["reason_codes"]:
            print(f"           - {rc}")
        notes = d["notes"]
        print(
            f"           anchors: documented={notes['documented_anchor_objects']} "
            f"needs_expert_review={notes['needs_expert_review_anchor_objects']}"
        )
    print("-" * 72)
    for name, m in payload["metrics"].items():
        print(f"{name}: {m['successes']}/{m['n']} = {m['successes']/m['n'] if m['n'] else float('nan'):.4f}")
        print(f"    wilson95={m['wilson_ci_95']} cp95={m['clopper_pearson_ci_95']}")
    print("-" * 72)
    for note in payload["honesty_notes"]:
        print(f"NOTE: {note}")
    print("-" * 72)
    print(f"BLOCKED (human-only): P10-T19 ethics/expert approval; P10-T20 novelty signoff; "
          f"P10-T21 coauthor/venue signoff — no simulated signoffs produced.")
    print(f"payload_sha256 = {payload['payload_sha256']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="p10")
    parser.add_argument("command", choices=["run", "report", "verify"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.command == "report":
        _print_summary(run_matrix(seed=args.seed))
        return 0

    if args.command == "run":
        path = freeze_run(output_dir=args.out, seed=args.seed)
        print(f"frozen: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        _print_summary(payload)
        return 0

    # verify: two independent runs must produce byte-identical payloads.
    p1 = run_matrix(seed=args.seed)
    p2 = run_matrix(seed=args.seed)
    if p1["payload_sha256"] != p2["payload_sha256"]:
        print("VERIFY FAILED: payload hashes differ across runs", file=sys.stderr)
        return 1
    frozen = sorted(RUNS_DIR.glob("p10_run_*.json"))
    if frozen:
        disk = json.loads(frozen[-1].read_text(encoding="utf-8"))
        if disk["payload_sha256"] != p1["payload_sha256"]:
            print(
                f"VERIFY FAILED: frozen artifact {frozen[-1].name} hash differs from live run",
                file=sys.stderr,
            )
            return 1
        print(f"VERIFY OK: live run matches frozen artifact {frozen[-1].name}")
    else:
        print("VERIFY OK: deterministic across two live runs (no frozen artifact yet)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
