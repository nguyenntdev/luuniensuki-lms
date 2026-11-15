#!/usr/bin/env python3
"""P14 preregistered experiment runner (audit-only run, no human arm).

Produces the full experiment artifact set under research_artifacts_v3/runs/p14/:
  experiment_card.json    — frozen provenance (P14-T12 format)
  prereg_snapshot.json    — canonical hash of pre_registration.yaml
  method_snapshot.json    — canonical hash of METHOD.md + rubric + engine versions
  audit_report.json/.sha256
  baseline_results.json   — C0/C1 vs proposed + McNemar verdict comparison
  metrics_summary.json    — CIs + descriptive statistics (no confirmatory claims)
  ablation_results.json   — named-mechanism mutations
  claims_ledger.json      — claims gate records (benefit claims must be absent)
  run_manifest.sha256     — checksums of every artifact in the run

Exit code 0 on success; any integrity failure is fatal (fail-closed).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from research_v2.contracts.canonical_hash import sha256_input, sha256_file
from research_v3.contracts.cards import ExperimentCard
from research_v3.eval.leakage import audit_rows
from research_v3.methods.p14.audit import (
    AUDIT_ENGINE_VERSION,
    audit_manifest,
    audit_object,
)
from research_v3.methods.p14.baselines import run_baselines
from research_v3.methods.p14.claims_guard import classify_claim
from research_v3.methods.p14.metrics import (
    conformance_with_ci,
    paired_baseline_comparison,
)
from research_v3.methods.p14.rights import external_media_status
from research_v3.methods.p14.rubric import RUBRIC_VERSION, load_rubric
from research_v3.methods.p14.synthetic import (
    SYNTHETIC_MANIFEST_VERSION,
    manifest_sha256,
    mutate,
    synthetic_manifest,
)

RUNS_DIR = Path("research_artifacts_v3/runs/p14")
PREREG_PATH = Path("research_v3/experiments/p14/pre_registration.yaml")
METHOD_PATH = Path("research_v3/methods/p14/METHOD.md")


def _write_json(path: Path, payload: dict) -> str:
    data = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8")
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    out = RUNS_DIR
    out.mkdir(parents=True, exist_ok=True)
    checksums: dict[str, str] = {}

    # ---- 1. frozen inputs -------------------------------------------------
    objects = synthetic_manifest()
    rubric = load_rubric()
    manifest_sha = manifest_sha256(objects)
    prereg_sha = sha256_file(PREREG_PATH)
    method_sha = sha256_file(METHOD_PATH)

    leakage = audit_rows(
        [{"case_id": o.object_id, "input": o.to_dict()} for o in objects]
    )
    if leakage["status"] != "PASS":
        print("leakage audit failed; aborting run", file=sys.stderr)
        return 1

    # ---- 2. audit + baselines ---------------------------------------------
    report = audit_manifest(objects, rubric)
    report["manifest"] = {
        "builtin": SYNTHETIC_MANIFEST_VERSION,
        "sha256": manifest_sha,
        "media_scope": "synthetic-only (external media BLOCKED; study PARTIAL)",
        "rights": external_media_status(),
    }
    checksums["audit_report.json"] = _write_json(out / "audit_report.json", report)

    proposed_pass: list[bool] = []
    for obj in objects:
        _, verdict = audit_object(obj, rubric)
        proposed_pass.append(verdict.verdict == "PASS")

    baseline_rows = run_baselines(objects)
    comparisons = {}
    for name, rows in baseline_rows.items():
        baseline_pass = [r["verdict"] == "PASS" for r in rows]
        comparisons[name] = paired_baseline_comparison(proposed_pass, baseline_pass)
    baseline_payload = {
        "proposed": [
            {"object_id": o.object_id, "pass": p} for o, p in zip(objects, proposed_pass)
        ],
        "baselines": baseline_rows,
        "paired_comparisons": comparisons,
        "manifest_sha256": manifest_sha,
    }
    checksums["baseline_results.json"] = _write_json(
        out / "baseline_results.json", baseline_payload
    )

    # ---- 3. descriptive statistics ----------------------------------------
    total_real = report["metrics"]["criteria_evaluated"]
    total_pass = report["metrics"]["criteria_passed"]
    metrics_summary = {
        "conformance": conformance_with_ci(total_pass, total_real),
        "udl_principle_coverage": report["metrics"]["udl_principle_coverage"],
        "missing_affordance_count": report["metrics"]["missing_affordance_count"],
        "per_framework": report["metrics"]["per_framework"],
        "abstained_criteria": report["metrics"]["criteria_abstained"],
        "note": "Descriptive audit statistics only; no confirmatory or benefit claim.",
    }
    checksums["metrics_summary.json"] = _write_json(
        out / "metrics_summary.json", metrics_summary
    )

    # ---- 4. ablations / mutations (named mechanisms) -----------------------
    base = synthetic_manifest()
    mutation_families: dict[str, dict[str, int]] = {}
    ablation_rows: list[dict] = []
    for mutation in ("remove_alt_text", "remove_transcript", "remove_keyboard", "remove_lbw"):
        flipped_named = 0
        total = 0
        for obj in base:
            mutant = mutate(obj, mutation, rng_seed=0)
            results_before, v_before = audit_object(obj, rubric)
            results_after, v_after = audit_object(mutant, rubric)
            missing_before = set(v_before.missing_affordances)
            missing_after = set(v_after.missing_affordances)
            total += 1
            if missing_after - missing_before:
                ablation_rows.append(
                    {
                        "object_id": obj.object_id,
                        "mutation": mutation,
                        "newly_missing": sorted(missing_after - missing_before),
                    }
                )
            if mutation == "remove_alt_text" and {
                "udl-rep-alt-text", "wcag-text-alternative"
            } & (missing_after - missing_before):
                flipped_named += 1
            if mutation == "remove_transcript" and "udl-rep-transcript" in (
                missing_after - missing_before
            ):
                flipped_named += 1
            if mutation == "remove_keyboard" and "udl-action-keyboard" in (
                missing_after - missing_before
            ):
                flipped_named += 1
            if mutation == "remove_lbw" and "udl-eng-low-bandwidth" in (
                missing_after - missing_before
            ):
                flipped_named += 1
        mutation_families[mutation] = {
            "objects_mutated": total,
            "named_mechanism_triggered": flipped_named,
        }
    ablation_payload = {
        "mutations": mutation_families,
        "rows": ablation_rows,
        "note": "Ablations remove exactly the named mechanism; counterexamples listed per object.",
    }
    checksums["ablation_results.json"] = _write_json(
        out / "ablation_results.json", ablation_payload
    )

    # ---- 5. claims ledger (fail-closed) ------------------------------------
    candidate_claims = [
        "The audit produced conformance rate R on manifest M",
        "UDL workflow improves learning outcomes for students",
        "The full audit is more effective for comprehension",
        "C1 checklist baseline missed UDL-principle failures that the full audit caught",
        "UDL design causally increases retention",
    ]
    claims_ledger = [classify_claim(c) for c in candidate_claims]
    rejected = [c for c in claims_ledger if not c["allowed"]]
    if not rejected:
        print("claims gate malfunction: expected benefit claims to be rejected", file=sys.stderr)
        return 1
    checksums["claims_ledger.json"] = _write_json(
        out / "claims_ledger.json",
        {
            "candidate_claims": claims_ledger,
            "rejected_count": len(rejected),
            "human_evidence_dataset_ids": [],
            "human_study_status": "BLOCKED (P14-T19)",
        },
    )

    # ---- 6. experiment card -------------------------------------------------
    card = ExperimentCard(
        paper_id="P14",
        rq_id="RQ-audit",
        train_dataset_ids=(),
        holdout_dataset_ids=(),
        method_commit_sha="workspace",
        method_hash=method_sha,
        baseline_version="C0_has_image;C1_wcag_checklist_only",
        split_hash=manifest_sha,
        feature_cutoff="not_applicable_audit",
        prereg_sha256=prereg_sha,
        hyperparameter_budget="none (fixed rules, no tuning)",
        seed=0,
        hardware="cpu",
        wall_time_seconds=0.0,
        dependency_lock_sha256=sha256_input({"engine": AUDIT_ENGINE_VERSION, "rubric": RUBRIC_VERSION}),
        output_path=str(out / "audit_report.json"),
        protocol_deviations=(
            "external media BLOCKED -> synthetic manifest; human arm BLOCKED -> audit-only run"
        ),
        status="PARTIAL",
    )
    checksums["experiment_card.json"] = _write_json(
        out / "experiment_card.json", card.to_dict() | {"card_sha256": card.sha256()}
    )
    checksums["prereg_snapshot.json"] = _write_json(
        out / "prereg_snapshot.json",
        {
            "prereg_path": str(PREREG_PATH),
            "prereg_sha256": prereg_sha,
            "method_sha256": method_sha,
            "engine": AUDIT_ENGINE_VERSION,
            "rubric": RUBRIC_VERSION,
            "manifest": SYNTHETIC_MANIFEST_VERSION,
            "manifest_sha256": manifest_sha,
        },
    )

    # ---- 7. run manifest ----------------------------------------------------
    (out / "run_manifest.sha256").write_text(
        "".join(f"{v}  {k}\n" for k, v in sorted(checksums.items())), encoding="utf-8"
    )
    print(json.dumps({
        "run_dir": str(out),
        "objects": len(objects),
        "conformance_rate": metrics_summary["conformance"]["rate"],
        "conformance_ci": metrics_summary["conformance"]["wilson_ci_95"],
        "missing_affordances": report["metrics"]["missing_affordance_count"],
        "claims_rejected": len(rejected),
        "artifacts": sorted(checksums),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
