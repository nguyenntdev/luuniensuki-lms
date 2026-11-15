#!/usr/bin/env python3
"""P11 status ledger runner — emits the T01-T21 task manifest with honest statuses.

Writes research_artifacts_v3/runs/p11/status_manifest.json. RULES:
- Human-only tasks (T19, T21) and tasks requiring real responses (T02 source-data gate,
  T06 external descriptive, T12 preregistered external matrix, T13 robustness on external
  data, T14 inference) are BLOCKED with explicit reasons.
- No fabricated metrics, annotator IDs, agreement values, or approvals anywhere.
- Engineering-complete tasks carry artifact paths so a reviewer can verify each claim.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ART = REPO / "research_artifacts_v3" / "runs" / "p11"
METHODS = REPO / "research_v3" / "methods" / "p11"
PACK = REPO / "research_v3" / "annotations" / "tasks" / "p11_annotation_pack"
EXPERIMENTS = REPO / "research_v3" / "experiments" / "p11"
MANUSCRIPT = REPO / "research_v3" / "manuscripts" / "p11" / "MANUSCRIPT.md"
TESTS = REPO / "tests" / "research_v3" / "method"

BLOCKED_NO_HUMAN = "BLOCKED: requires human raters, ethics approval and consented responses (P11-T19); none exist as of 2026-11-15. No substitute data permitted."
BLOCKED_HUMAN_SIGNOFF = "BLOCKED: human-only signoff. No signature/approval exists; none may be simulated."
BLOCKED_NO_RESPONSES = "BLOCKED: no real consented student responses available; synthetic data is restricted to regression/canary use and may not feed this task."


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ""


def rel(p: Path) -> str:
    return str(p.relative_to(REPO))


def main() -> int:
    ART.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()

    rubric_py, reliability_py = METHODS / "rubric.py", METHODS / "reliability.py"
    prereg = METHODS / "pre_registration.yaml"
    method_md = METHODS / "METHOD.md"
    codebook = PACK / "CODEBOOK.md"
    card = PACK / "ANNOTATION_CARD.md"
    cases_csv = PACK / "constructed_cases" / "expected_levels.csv"
    exp_status = EXPERIMENTS / "p11_status.py"
    manuscript = MANUSCRIPT

    tasks = [
        # ---- engineering-complete ----
        dict(id="P11-T01", title="RQ, estimand, null, nearest prior, collision checks", status="ENGINEERING_PASS",
             artifacts=[rel(method_md), rel(prereg), rel(manuscript)],
             evidence="RQ+H0 frozen in prereg (2026-11-15) and METHOD.md s1; collision audit vs P10/P14 recorded (no MERGE_REQUIRED)."),
        dict(id="P11-T03", title="Data and target schema definition", status="ENGINEERING_PASS",
             artifacts=[rel(rubric_py), rel(codebook)],
             evidence="Typed HistoricalReasoningResponse/EvidenceItem/Claim/EvidenceLink schema with validation, NA/ABSTAIN distinct from 0; long-format rating record defined."),
        dict(id="P11-T07", title="Strong classical baseline (C0 keyword) with matched inputs", status="ENGINEERING_PASS",
             artifacts=[rel(rubric_py)],
             evidence="C0 keyword-presence baseline implemented over identical declared structures; documented failure family (fabricated/relation-inverted keyword hits). B00/B02 holistic = human-only, BLOCKED."),
        dict(id="P11-T08", title="Closest published implementation or honest BLOCKED card", status="PARTIAL",
             artifacts=[rel(manuscript)],
             evidence="Construct lineage documented (Wineburg/Monte-Sano/Breakstone-Smith); no external implementation adapted, so no pinning required yet; comparator pinning deferred to data-ready state, else BLOCKED card."),
        dict(id="P11-T09", title="Method implementation and invariant proofs", status="ENGINEERING_PASS",
             artifacts=[rel(rubric_py), rel(reliability_py), rel(TESTS / "test_p11_rubric.py"), rel(TESTS / "test_p11_reliability.py")],
             evidence="Deterministic scorer (property: same input -> same output); fail-closed reliability math validated against reference krippendorff package (36 comparisons, 12 matrices x 3 levels); NA/ABSTAIN never imputed."),
        dict(id="P11-T10", title="Independent ablations and mutation counterexamples", status="ENGINEERING_PASS",
             artifacts=[rel(rubric_py), rel(TESTS / "test_p11_rubric.py")],
             evidence="Mutation tests realize spec s5 stress families on constructed cases: fabricated citations (S1 cap), zero evidence (full cap), relation-inverted links, allow_handling_bonus mechanism removal; all fail-closed assertions tested."),
        dict(id="P11-T16", title="Scientific failure review and collision audit", status="ENGINEERING_PASS",
             artifacts=[rel(exp_status), rel(manuscript)],
             evidence="H0 non-rejection path pre-registered (prereg falsification section); collision audit vs all 13 sibling papers on file; statuses never auto-promote."),
        dict(id="P11-T17", title="Manuscript methods/limitations/appendix build", status="ENGINEERING_PASS",
             artifacts=[rel(manuscript)],
             evidence="Skeleton with RQ, related work, method, ALL results cells BLOCKED, Threats to Validity led by no-human-raters; no numeric or causal claim lacks an evidence pointer; zero validity wording."),
        # ---- data-gated ----
        dict(id="P11-T02", title="Dataset rights assessment and source selection", status="BLOCKED",
             artifacts=[rel(card)],
             evidence=BLOCKED_NO_RESPONSES + " Rights/license snapshot to be taken when the response collection source is chosen."),
        dict(id="P11-T04", title="Raw ingestion and immutable provenance", status="BLOCKED",
             artifacts=[],
             evidence=BLOCKED_NO_RESPONSES + " SHA-256 raw+processed pipeline defined in ANNOTATION_CARD but cannot run without data."),
        dict(id="P11-T05", title="Leakage-proof preprocessing and split", status="BLOCKED",
             artifacts=[],
             evidence=BLOCKED_NO_RESPONSES + " Rater-blind split protocol defined; nothing to split yet."),
        dict(id="P11-T06", title="External descriptive baseline and distribution checks", status="BLOCKED",
             artifacts=[],
             evidence=BLOCKED_NO_RESPONSES),
        dict(id="P11-T11", title="Training/calibration with frozen hyperparameter budget", status="BLOCKED",
             artifacts=[],
             evidence="BLOCKED: calibrated (link-aware, weight-fitted) scoring variant requires rater training data; hypothesis only, not implemented. No learning happened; nothing to report."),
        dict(id="P11-T12", title="Full preregistered matrix on external data", status="BLOCKED",
             artifacts=[],
             evidence=BLOCKED_NO_RESPONSES + " Prereg matrix frozen in pre_registration.yaml; cells stay BLOCKED."),
        dict(id="P11-T13", title="Robustness, shift, subgroup, resource and stress", status="BLOCKED",
             artifacts=[],
             evidence=BLOCKED_NO_RESPONSES + " Constructed-case stress mutations exist for the scorer but external robustness needs real data."),
        dict(id="P11-T14", title="Statistical tests and uncertainty", status="BLOCKED",
             artifacts=[],
             evidence="BLOCKED: no real annotation matrix exists; computing kappa/alpha/ICC now would fabricate a result. Harness verified on toy data inside tests ONLY."),
        dict(id="P11-T15", title="Source-to-table generator and independent replication", status="BLOCKED",
             artifacts=[],
             evidence="BLOCKED: no results table exists to generate; ledger runner (this script) is the only table and contains statuses only. Source-to-table generation unblocks with real data."),
        dict(id="P11-T18", title="External reviewer reproduction and frozen release", status="BLOCKED",
             artifacts=[],
             evidence="BLOCKED: reviewers cannot reproduce a study that has not run; engineering artifacts are reproducible from tests, but the release gate stays BLOCKED until the study runs."),
        # ---- human-only ----
        dict(id="P11-T19", title="Ethics/human annotation/license approval (human-only)", status="BLOCKED",
             artifacts=[rel(card), rel(PACK / "adjudication_protocol.md")],
             evidence=BLOCKED_HUMAN_SIGNOFF + " ANNOTATION_CARD fields left unfilled by design; no simulated approvals."),
        dict(id="P11-T20", title="Novelty and nearest-work signoff (research lead)", status="BLOCKED",
             artifacts=[rel(manuscript)],
             evidence=BLOCKED_HUMAN_SIGNOFF + " Collision audit (automated part) done; human lead signoff with full-text overlap matrix pending."),
        dict(id="P11-T21", title="Coauthor/venue/submission signoff (human-only)", status="BLOCKED",
             artifacts=[rel(manuscript)],
             evidence=BLOCKED_HUMAN_SIGNOFF),
    ]

    manifest = {
        "paper_id": "P11",
        "generated_at": generated_at,
        "release_status": "BLOCKED_RATER_AND_SAMPLE_REQUIRED",
        "h0_publication_rule": "If reliability/validity is never shown to beat the single-holistic scale, H0 is published as a null result.",
        "artifact_hashes": {
            rel(p): sha256_file(p)
            for p in [rubric_py, reliability_py, prereg, method_md, codebook, card, cases_csv, exp_status, manuscript]
            if p.exists()
        },
        "annotation_pack": {
            "path": rel(PACK),
            "status": "BLOCKED_AWAITING_HUMAN_RATERS",
            "fabricated_content_check": "templates contain headers only; no annotator IDs, ratings, timestamps or agreement numbers",
            "constructed_cases": "6 cases, labeled CONSTRUCTED_NOT_HUMAN, sha256 in artifact_hashes",
        },
        "reliability_harness_smoke": {
            "note": "SYNTHETIC TOY verification only; never a result",
            "command": "python3 research_v3/methods/p11/reliability.py",
        },
        "tasks": tasks,
        "summary": {
            "total": len(tasks),
            "engineering_pass": sum(1 for t in tasks if t["status"] == "ENGINEERING_PASS"),
            "partial": sum(1 for t in tasks if t["status"] == "PARTIAL"),
            "blocked": sum(1 for t in tasks if t["status"] == "BLOCKED"),
        },
    }

    out = ART / "status_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {rel(out)}: {manifest['summary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
