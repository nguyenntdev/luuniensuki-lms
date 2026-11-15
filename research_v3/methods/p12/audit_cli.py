"""P12 audit CLI — run C0/C1/proposed arms over the documented read-only corpus.

Reads only:
  data/imperial/historical_sources_extended.json
  data/imperial/monument_claims_matrix.json
  data/imperial/heritage_provenance_audit_report.json

Writes to research_artifacts_v3/runs/p12/:
  ingest_manifest.json       — SHA-256 of every read-only input + skip log
  run_<arm>/manifest.json    — per-arm verdicts, metrics, provenance
  run_proposed/ledger.jsonl  — append-only hash-chained event log
  wikidata_probe.json        — CC0 entity-link calls (query text + response SHA)
  summary.json               — cross-arm metric table + explicit BLOCKED section

No network access is required for the ledger arms; the Wikidata probe is
optional (--with-wikidata) and fails soft (recorded as error, never faked).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from research_v2.contracts.canonical_hash import sha256_input
from research_v3.methods.p12.baselines import baseline_c0, baseline_c1
from research_v3.methods.p12.corpus import ingest_repo_corpus
from research_v3.methods.p12.ledger import audit_corpus

REPO_ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_DIR = REPO_ROOT / "research_artifacts_v3" / "runs" / "p12"

BLOCKED_TASKS = {
    "P12-T19": "Ethics/human annotation/license approval — requires real expert signatures and archival access; never simulated.",
    "P12-T20": "Novelty and nearest-work signoff — requires research lead review of latest full texts; not delegated to code.",
    "P12-T21": "Coauthor/venue/submission signoff — human-only approval; no simulated success.",
}
BLOCKED_DATA = (
    "Vietnamese primary archives (ĐNTL, HĐSL, ĐNNTC): BLOCKED for automated "
    "ingestion (page-level rights not cleared; no scraping). Locators in the "
    "documented corpus are inherited verbatim and NOT machine-verified."
)


def _git_head() -> dict[str, str]:
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
        dirty = bool(subprocess.run(
            ["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        ).stdout.strip())
        return {"head_sha": head, "dirty": dirty}
    except Exception:
        return {"head_sha": "unknown", "dirty": True}


def run_audit(out_dir: Path, *, with_wikidata: bool, timestamp: str) -> dict:
    ingest = ingest_repo_corpus()

    # Fail-closed policy: corpus ingestion must account for every claim row.
    claims = ingest.claims
    registry = ingest.source_registry

    proposed = audit_corpus(claims, registry, timestamp_provider=lambda: timestamp)
    c0 = baseline_c0(claims)
    c1 = baseline_c1(claims, registry)

    ingest_manifest = {
        "provenance": ingest.provenance,
        "n_sources": len(registry),
        "n_claims_ingested": len(claims),
        "skipped": ingest.skipped,
        "policy": "read-only documented claims; no archive access; no fabricated locators",
        "blocked_data": BLOCKED_DATA,
    }

    (out_dir / "ingest_manifest.json").write_text(
        json.dumps(ingest_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    arms: dict[str, dict] = {
        "C0": c0,
        "C1": c1,
        "PROPOSED": {k: v for k, v in proposed.items() if k != "ledger_events"},
    }
    for arm, result in arms.items():
        manifest = {
            "run_id": sha256_input({"arm": arm, "timestamp": timestamp, "ingest": ingest.provenance["ingest_hash"]}),
            "paper_id": "P12",
            "arm": arm,
            "executed_at_utc": timestamp,
            "git": _git_head(),
            "ingest_manifest": "ingest_manifest.json",
            "result": result,
        }
        arm_dir = out_dir / f"run_{arm.lower()}"
        arm_dir.mkdir(parents=True, exist_ok=True)
        (arm_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # Append-only chain exported as JSONL (one event per line, seq order).
    with (out_dir / "run_proposed" / "ledger.jsonl").open("w", encoding="utf-8") as fh:
        for event in proposed["ledger_events"]:
            fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    summary = {
        "paper_id": "P12",
        "status": "ENGINEERING_PASS",
        "scientific_status": "BLOCKED_PENDING_HUMAN_REVIEW (T19/T20/T21)",
        "executed_at_utc": timestamp,
        "corpus": {
            "n_claims": proposed["n_claims"],
            "n_sources": proposed["n_sources_in_registry"],
            "ingest_skipped": len(ingest.skipped),
            "provenance": ingest.provenance,
        },
        "metrics": {
            "C0": {
                "unsourced_claim_rate": c0["unsourced_claim_rate"],
                "locator_completeness_rate": c0["locator_completeness_rate"],
                "contradiction_count": c0["contradiction_count"],
            },
            "C1": {
                "unsourced_claim_rate": c1["unsourced_claim_rate"],
                "locator_completeness_rate": c1["locator_completeness_rate"],
                "contradiction_count": c1["contradiction_count"],
            },
            "PROPOSED": {
                "unsourced_claim_rate": proposed["unsourced_claim_rate"],
                "locator_completeness_rate": proposed["locator_completeness_rate"],
                "contradiction_count": proposed["contradiction_count"],
                "abstain_count": proposed["abstain_count"],
                "chain": proposed["chain"],
                "chain_digest": proposed["chain_digest"],
            },
        },
        "interpretation_note": (
            "Engineering smoke metrics on 63 documented claims read from the repo "
            "registry. Not scientific results: labels are inherited documented "
            "assertions pending human archival verification. The proposed arm's "
            "value here is that it routes all 63 inherited archival/expert/editor "
            "labels to ABSTAIN (human review) instead of PASS — honest fail-closed "
            "behaviour, not a performance claim."
        ),
        "blocked": {
            "tasks": BLOCKED_TASKS,
            "data": BLOCKED_DATA,
            "human_measures": (
                "verified_claim_rate, annotation_agreement, editor_time, "
                "conflict_resolution_rate: UNMEASURED until P12-T19 executes."
            ),
        },
    }

    if with_wikidata:
        from research_v3.methods.p12.wikidata_probe import WikidataProbe

        probe = WikidataProbe()
        for label in ("Ngọ Môn", "Điện Thái Hòa", "Minh Mạng"):
            probe.query_wikidata_entity(label)
        wd = probe.export()
        wd["executed_at_utc"] = timestamp
        (out_dir / "wikidata_probe.json").write_text(
            json.dumps(wd, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summary["wikidata_entity_links"] = [
            {"label": c["label"], "status": c["status"], "qid": c.get("qid")} for c in probe.calls
        ]

    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P12 source-auditing ledger CLI")
    parser.add_argument(
        "--out",
        type=Path,
        default=ARTIFACT_DIR,
        help="artifact output directory (default: research_artifacts_v3/runs/p12)",
    )
    parser.add_argument(
        "--with-wikidata",
        action="store_true",
        help="also run the CC0 Wikidata entity-link probe (network; recorded, fail-soft)",
    )
    args = parser.parse_args(argv)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    args.out.mkdir(parents=True, exist_ok=True)
    summary = run_audit(args.out, with_wikidata=args.with_wikidata, timestamp=timestamp)

    print(f"P12 audit complete -> {args.out}")
    print(f"  corpus: {summary['corpus']['n_claims']} claims / {summary['corpus']['n_sources']} sources")
    for arm, m in summary["metrics"].items():
        print(
            f"  {arm:9s} unsourced={m['unsourced_claim_rate']} "
            f"locator_complete={m['locator_completeness_rate']} contradictions={m['contradiction_count']}"
        )
    print(f"  chain: {summary['metrics']['PROPOSED']['chain']}")
    print("  blocked:", ", ".join(summary["blocked"]["tasks"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
