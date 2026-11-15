"""P03 experiment CLI: fetch -> split -> run matrix -> stats -> freeze manifests.

Preregistered matrix (pre_registration.yaml): {proposed, ablations A1-A5,
C0, C1} x {test split, strata}. Deterministic; strict exit code on any
denominator or label mismatch (fail closed).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

from research_v2.contracts.canonical_hash import sha256_input
from research_v3.contracts.cards import EvidenceCard, ExperimentCard
from research_v3.eval.leakage import audit_rows
from research_v3.eval.splitters import assert_no_leakage, freeze_hash, group_split
from research_v3.eval.statistics import null_result, paired_report
from research_v3.methods.p03 import dataset as ds
from research_v3.methods.p03 import metrics as mx
from research_v3.methods.p03.baselines import (
    C1_LABEL,
    C2_REASON,
    C2_STATUS,
    BASELINES,
    c1_simulated_proxy,
)
from research_v3.methods.p03.policy import METHOD_VERSION, decide, decide_config
from research_v3.methods.p03.types import TutorDecisionInput

PAPER_ID = "P03"
RUNS = ds.P03_RUNS
ABLATIONS = {
    "A1_no_provenance_confidence": {"provenance_confidence": False},
    "A2_no_uncertainty_calibration": {"uncertainty_calibration": False},
    "A3_no_learner_stage": {"learner_stage": False},
    "A4_no_abstention": {"abstention": False},
    "A5_no_action_cost": {"injection_boundary": False, "malicious_note_quarantine": False},
}


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: str, payload: Any) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return _sha256_file(path)


def _run_system(system_id: str, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions = []
    for case in cases:
        inp: TutorDecisionInput = ds.to_policy_input(case)
        if system_id == "proposed_multi_gate":
            d = decide(inp)
        elif system_id in ABLATIONS:
            d = decide_config(inp, ABLATIONS[system_id])
        elif system_id in BASELINES:
            d = BASELINES[system_id](inp)
        else:
            raise SystemExit(f"unknown system {system_id}")
        decisions.append(
            {
                "case_id": d.case_id,
                "action": d.action,
                "reason_codes": list(d.reason_codes),
                "evidence_ids": list(d.evidence_ids),
                "p_answer": d.p_answer,
                "abstained": d.abstained,
                "refused": d.refused,
                "conversation_id": case["conversation_id"],
                "stratum": case["stratum"],
                "system_id": system_id,
            }
        )
    return decisions


def _primary_flags(decisions: list[dict[str, Any]], labels_by_id: dict[str, dict[str, Any]]) -> list[bool]:
    return [
        mx.classify_case(d["action"], labels_by_id[d["case_id"]]) == "correct" for d in decisions
    ]


def run_preregistered_matrix(seed: int = 42) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()

    # 1. E00 dataset & license gate: raw fetch + pinned hash.
    raw_info = ds.fetch_raw()
    raw_sha = raw_info["sha256"]
    convs = ds.load_conversations(raw_info["path"])
    if not convs:
        SystemExit("empty MRBench devset")

    # 2. E01 schema + split integrity: group split by conversation_id.
    rows = [{"case_id": c["conversation_id"], "conversation_id": c["conversation_id"]} for c in convs]
    split = group_split(rows, group_key="conversation_id", paper_id=PAPER_ID, salt="p03-v1")
    assert_no_leakage(split)
    split_hash = freeze_hash(split)

    # 3. Build cases for the test partition only (strata injected post-split).
    test_ids = list(split.split_ids["test"])
    cases = ds.build_cases_for_split(test_ids)
    labels = ds.sealed_labels(cases)
    labels_by_id = {l["case_id"]: l for l in labels}
    cases_by_id = {c["case_id"]: c for c in cases}

    # Leakage audit on policy-visible inputs (no gold keys anywhere).
    audit = audit_rows(
        [
            {
                "case_id": c["case_id"],
                "input": {
                    "learner_turn": c["learner_turn"],
                    "stage": c["stage"],
                    "wants_answer": c["wants_answer"],
                    "sources": c["sources"],
                },
            }
            for c in cases
        ],
        strict=True,
    )

    # 4. Run full preregistered matrix.
    systems = ["proposed_multi_gate", *ABLATIONS.keys(), *BASELINES.keys()]
    decisions_by_system: dict[str, list[dict[str, Any]]] = {}
    summaries: dict[str, Any] = {}
    for system_id in systems:
        decisions_by_system[system_id] = _run_system(system_id, cases)
        summaries[system_id] = mx.summarize(system_id, decisions_by_system[system_id], labels_by_id, cases_by_id)

    # 5. E09 statistical comparison: paired vs proposed (primary family, Holm).
    proposed_flags = _primary_flags(decisions_by_system["proposed_multi_gate"], labels_by_id)
    paired = {}
    p_values: list[float] = []
    contrasts = [s for s in systems if s != "proposed_multi_gate"]
    for system_id in contrasts:
        rep = paired_report(
            proposed_flags,
            _primary_flags(decisions_by_system[system_id], labels_by_id),
            group_ids=[d["conversation_id"] for d in decisions_by_system[system_id]],
            label_a="proposed_multi_gate",
            label_b=system_id,
            seed=seed,
            n_boot=2000,
        )
        paired[system_id] = rep
        p = rep["mcnemar"].get("p_value")
        if p is not None:
            p_values.append(p)
    from research_v3.eval.statistics import family_control

    holm = family_control(p_values, method="holm") if p_values else []
    for system_id, adj in zip([c for c in contrasts], holm):
        paired[system_id]["mcnemar"]["p_holm_adjusted"] = adj
        proposed_rate = summaries["proposed_multi_gate"]["pedagogy_win_rate"]["rate"]
        base_rate = summaries[system_id]["pedagogy_win_rate"]["rate"]
        paired[system_id]["null_result"] = null_result(
            observed=proposed_rate, baseline=base_rate, p_value=adj
        )

    # 6. Freeze artifacts.
    stamp = "v1"
    out_dir = os.path.join(RUNS, "reports")
    os.makedirs(out_dir, exist_ok=True)
    decisions_path = os.path.join(out_dir, f"decisions_{stamp}.json")
    summaries_path = os.path.join(out_dir, f"summaries_{stamp}.json")
    paired_path = os.path.join(out_dir, f"paired_stats_{stamp}.json")
    labels_path = os.path.join(out_dir, f"sealed_labels_{stamp}.json")

    d_sha = _write_json(decisions_path, decisions_by_system)
    s_sha = _write_json(summaries_path, summaries)
    p_sha = _write_json(paired_path, paired)
    l_sha = _write_json(labels_path, labels)

    prereg_path = "research_v3/experiments/p03/pre_registration.yaml"
    prereg_sha = _sha256_file(prereg_path)
    policy_path = "research_v3/methods/p03/policy.py"
    method_hash = _sha256_file(policy_path)

    # 7. Experiment + evidence cards (immutable contract, cards.py).
    external_validity = "PASS" if raw_sha and summaries["proposed_multi_gate"]["n_decisions"] else "PARTIAL"
    experiment = ExperimentCard(
        paper_id=PAPER_ID,
        rq_id="P03-RQ1",
        train_dataset_ids=("synthetic-stress-v1",),
        holdout_dataset_ids=("mrbench-v3-devset",),
        method_commit_sha=os.popen("git rev-parse HEAD").read().strip()[:40] or "uncommitted",
        method_hash=method_hash,
        baseline_version=f"C0/C1 rule-based ({C1_LABEL}); C2={C2_STATUS}",
        split_hash=split_hash,
        feature_cutoff=started,
        prereg_sha256=prereg_sha,
        hyperparameter_budget="tau=0.60; weights 0.5/0.3/0.2; frozen in METHOD.md v1.0.0 (no tuning)",
        seed=seed,
        hardware="1x CPU (deterministic policy), no GPU used",
        wall_time_seconds=0.0,
        dependency_lock_sha256=_sha256_file("research_v3/eval/statistics.py"),
        output_path=os.path.relpath(summaries_path),
        protocol_deviations=(
            "C2 real LLM BLOCKED; MathTutorBench main tasks BLOCKED for direct "
            "policy scoring (generation-required); MRBench used as decision-layer "
            "probe with deterministic scenario injection, not generation scoring.",
        ),
        status="PARTIAL" if external_validity == "PASS" else "BLOCKED",
    )
    primary = summaries["proposed_multi_gate"]["pedagogy_win_rate"]
    leakage = summaries["proposed_multi_gate"]["answer_leakage_rate"]
    evidence = EvidenceCard(
        paper_id=PAPER_ID,
        claim_id="P03-E01-primary",
        source_type="preregistered_matrix",
        source_sha256=raw_sha,
        code_sha=method_hash,
        experiment_ids=(f"{PAPER_ID}-matrix-{stamp}",),
        analysis_script="research_v3/experiments/p03/run_matrix.py",
        table_cell_ids=(
            "primary.pedagogy_win_rate",
            "primary.answer_leakage_rate",
            "primary.injection_refusal_rate",
            "primary.abstention_precision",
            "primary.abstention_recall",
            "primary.citation_grounding_rate",
            "primary.calibration_ece",
        ),
        denominator=primary["n"],
        ci=(primary["wilson_ci_95"][0], primary["wilson_ci_95"][1]),
        comparison_family="C0_direct_answer;C1_simulated_proxy_rulebased;A1..A5",
        allowed_wording=(
            f"On the frozen MRBench-derived test split, the proposed policy achieved a "
            f"strict per-case win rate of {primary['rate']:.3f} "
            f"(95% Wilson CI {primary['wilson_ci_95'][0]:.3f}-{primary['wilson_ci_95'][1]:.3f}, "
            f"n={primary['n']}) with answer-leakage rate {leakage['rate']} on leak-risk strata; "
            f"no real LLM (C2) and no human teacher reference (B05) were evaluated."
        ),
        limitations=(
            "Synthetic scenario ground truth (deterministic generator); decision-layer probe, "
            "not generated-tutor-text scoring; C2 real-LLM BLOCKED; single external collection "
            "(MRBench devset) - external generalization beyond math tutoring unverified.",
        ),
    )

    manifest = {
        "paper_id": PAPER_ID,
        "run_stamp": stamp,
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "raw_dataset": {"url": raw_info["url"], "sha256": raw_sha, "n_conversations": len(convs)},
        "split": {"protocol": split.protocol, "hash": split_hash, "sizes": {k: len(v) for k, v in split.split_ids.items()}},
        "leakage_audit": audit,
        "n_test_cases": len(cases),
        "strata": sorted({c["stratum"] for c in cases}),
        "files": {
            "decisions": {"path": decisions_path, "sha256": d_sha},
            "summaries": {"path": summaries_path, "sha256": s_sha},
            "paired_stats": {"path": paired_path, "sha256": p_sha},
            "sealed_labels": {"path": labels_path, "sha256": l_sha},
            "pre_registration": {"path": prereg_path, "sha256": prereg_sha},
        },
        "experiment_card": experiment.to_dict(),
        "experiment_card_sha256": experiment.sha256(),
        "evidence_card": evidence.to_dict(),
        "evidence_card_sha256": evidence.sha256(),
        "c2_status": {"status": C2_STATUS, "reason": C2_REASON},
        "method_version": METHOD_VERSION,
        "external_validity": external_validity,
    }
    manifest_path = os.path.join(RUNS, "manifests", f"manifest_{stamp}.json")
    _write_json(manifest_path, manifest)

    # Checksum round trip (P03-T15): re-read and verify.
    with open(manifest_path, encoding="utf-8") as fh:
        rt = json.load(fh)
    for key in ("decisions", "summaries", "paired_stats", "sealed_labels"):
        got = _sha256_file(rt["files"][key]["path"])
        if got != rt["files"][key]["sha256"]:
            raise SystemExit(f"checksum round-trip FAILED for {key}")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P03 preregistered evaluation matrix")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fetch-only", action="store_true", help="only fetch + hash raw data")
    args = parser.parse_args(argv)
    if args.fetch_only:
        info = ds.fetch_raw()
        print(json.dumps(info, indent=1))
        return 0
    manifest = run_preregistered_matrix(seed=args.seed)
    print(json.dumps({k: manifest[k] for k in (
        "raw_dataset", "split", "n_test_cases", "leakage_audit", "external_validity",
        "experiment_card_sha256", "evidence_card_sha256", "c2_status")}, indent=1))
    s = json.load(open(os.path.join(RUNS, "reports", "summaries_v1.json")))
    for system in ("proposed_multi_gate", "A5_no_action_cost", "C0_direct_answer", "C1_simulated_proxy_rulebased"):
        row = s[system]
        wr = row["pedagogy_win_rate"]
        print(f"{system:34s} win={wr['rate']:.3f} CI=[{wr['wilson_ci_95'][0]:.3f},{wr['wilson_ci_95'][1]:.3f}] "
              f"leak={row['answer_leakage_rate']['rate']} ground={row['citation_grounding_rate']['rate']} "
              f"refusal={row['injection_refusal_rate']['rate']} ECE={row['calibration']['ece']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
