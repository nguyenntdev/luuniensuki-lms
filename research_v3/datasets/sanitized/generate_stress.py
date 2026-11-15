"""V3-G15/G16/G17: NEW stress datasets under research_v3/datasets/sanitized/.

These are SYNTHETIC stress suites authored for V3 — they never touch the
frozen V2 T3 files and never reuse their labels. Every generator is
deterministic per (family, seed); the emitted manifest records SHA-256 file
hashes so the suites are reproducible byte-for-byte.

- LN-06 ``external_solver_parity``: route-planning cases with a *known exact
  answer* (brute-force over <= 8 stops) used to test that the V2 policy never
  reports false infeasibility and never claims exactness it does not have.
- LN-07 ``transcript_failure``: transcript_required tasks whose audio options
  lack transcripts — the stratum ABSENT from the V2 T3 gold (disclosed gap).
- LN-09 ``small_cohort``: cohort_size < k (k=5) with otherwise-nominal
  evidence — the stratum ABSENT from the V2 T3 gold (disclosed gap).

Gold decisions are produced ONLY by independent oracles:
- LN-06: brute-force enumeration over stop subsets (independent rubric);
- LN-07/LN-09: written decision rules from the published policy invariants
  (accessibility / k-anonymity), independent of any proposed-method code path.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from research_v2.contracts.canonical_hash import sha256_input
from research_v3.scripts._paths import SANITIZED_DIR

LN06_LABELS = (
    "find_valid_route",
    "no_feasible_route",
    "cost_exceeded",
    "reject_checkpoint_source",
    "reject_cycle",
)
LN07_LABELS = (
    "choose_feasible_modality",
    "choose_accessible_audio_text",
    "reject_audio_equivalence",
    "choose_accessible_fallback",
)
LN09_LABELS = (
    "propose_explained_action",
    "abstain_missing_evidence",
    "descriptive_only",  # native k-anonymity suppression decision
    "request_refresh",
)

N_CASES_PER_FAMILY = 24
K_THRESHOLD = 5


# --------------------------------------------------------------------------
# LN-06 — external solver parity stratum (independent brute-force oracle)
# --------------------------------------------------------------------------

def _ln06_oracle(stops: list[dict[str, Any]], targets: frozenset[str], budget: int, verified: bool) -> str:
    """Independent exact oracle: enumerate subsets/permutations (<= 8 stops).

    Mirrors the *rules* of the task (coverage + prerequisites + cost) but is
    implemented HERE, separate from research_v2.methods.ln06.rubric, so a
    policy bug cannot hide inside a shared oracle.
    """
    import itertools

    if not verified:
        return "reject_checkpoint_source"
    by_id = {s["id"]: s for s in stops}

    def blocked_outcomes() -> bool:
        # prerequisite chain cycle: outcome o requires chain that never grounds
        provides_all = {o for s in stops for o in s["provides"]}
        for s in stops:
            for req in s["requires"]:
                if req not in provides_all:
                    return True  # unprovidable prerequisite -> structural block
        return False

    if blocked_outcomes():
        return "reject_cycle"

    available = [s["id"] for s in stops]
    best: int | None = None
    for r in range(len(available) + 1):
        for subset in itertools.combinations(available, r):
            covered = {o for sid in subset for o in by_id[sid]["provides"]}
            if not targets <= covered:
                continue
            acquired: set[str] = set()
            ok = True
            for sid in subset:
                if any(req not in acquired for req in by_id[sid]["requires"]):
                    ok = False
                    break
                acquired |= set(by_id[sid]["provides"])
            if not ok:
                continue
            cost = sum(by_id[sid]["cost"] for sid in subset)
            if best is None or cost < best:
                best = cost
    if best is None:
        return "no_feasible_route"
    return "cost_exceeded" if best > budget else "find_valid_route"


def generate_ln06_family(seed: int) -> list[dict[str, Any]]:
    import random

    rng = random.Random(f"ln06-parity-{seed}")
    rows: list[dict[str, Any]] = []
    for i in range(N_CASES_PER_FAMILY):
        n = rng.randint(3, 6)
        outcomes = [f"o{j}" for j in range(n)]
        targets = frozenset(rng.sample(outcomes, rng.randint(2, min(3, n))))
        stops = []
        for j, o in enumerate(outcomes):
            stop = {
                "id": f"s{j}",
                "cost": rng.randint(5, 30),
                "provides": [o],
                "requires": [],
                "type": "sanitized-stress",
            }
            if j > 0 and rng.random() < 0.4:
                stop["requires"] = [outcomes[j - 1]]
            stops.append(stop)
        # mandatory alternative-provider pair: A/B both provide the first target
        t0 = sorted(targets)[0]
        stops.append({"id": "ALT_A", "cost": rng.randint(10, 25), "provides": [t0], "requires": [], "type": "alt"})
        stops.append({"id": "ALT_B", "cost": rng.randint(10, 25), "provides": [t0], "requires": [], "type": "alt"})
        budget = rng.randint(25, 70)
        verified = rng.random() > 0.15
        decision = _ln06_oracle(stops, targets, budget, verified)
        rows.append(
            {
                "case_id": f"LN06-PARITY-{seed:02d}-{i:03d}",
                "group_id": f"parity-grp-{seed:02d}-{i % 8}",
                "input": {
                    "case_id": f"LN06-PARITY-{seed:02d}-{i:03d}",
                    "stops": stops,
                    "available_stops": [s["id"] for s in stops],
                    "target_outcomes": sorted(targets),
                    "time_budget_minutes": budget,
                    "checkpoint_claim_verified": verified,
                    "learner": {"synthetic": True, "evaluation_mode": "sanitized_stress"},
                },
                "label": decision,
            }
        )
    return rows


# --------------------------------------------------------------------------
# LN-07 — transcript-failure scored stratum
# --------------------------------------------------------------------------

def _ln07_oracle(task_transcript_required: bool, audio_has_transcript: bool, text_variant: bool) -> str:
    """Published-rule oracle (WCAG 1.2.1 axis), independent of policy code:
    - transcript_required + no transcript anywhere on audio + no text variant
      -> reject_audio_equivalence;
    - transcript_required + missing transcript but a text-equivalent variant
      exists -> choose_accessible_audio_text;
    - no transcript requirement -> choose_feasible_modality.
    """
    if not task_transcript_required:
        return "choose_feasible_modality"
    if audio_has_transcript:
        return "choose_feasible_modality"
    return "choose_accessible_audio_text" if text_variant else "reject_audio_equivalence"


def generate_ln07_family(seed: int) -> list[dict[str, Any]]:
    import random

    rng = random.Random(f"ln07-transcript-{seed}")
    rows: list[dict[str, Any]] = []
    for i in range(N_CASES_PER_FAMILY):
        scenario = i % 4
        # scenario 0: compliant audio (transcript present)          -> feasible
        # scenario 1: no transcript but a text-equivalent variant   -> audio_text
        # scenario 2: no transcript and NO text-equivalent variant  -> reject (positive)
        # scenario 3: transcript not required at all                -> feasible
        audio_transcript = scenario == 0
        text_variant = scenario in (0, 1)
        transcript_required = scenario != 3
        options = [
            {
                "id": "opt_audio",
                "modality": "audio",
                "kb": 800,
                "affordances": ["inscription", "narrative"],
                "keyboard": True,
                "requires_webgl": False,
                "available": True,
                "transcript": audio_transcript,
                "sub_type": "audio",
            }
        ]
        if text_variant:
            options.append(
                {
                    "id": "opt_text",
                    "modality": "text",
                    "kb": 120,
                    "affordances": ["inscription", "narrative"],
                    "keyboard": True,
                    "requires_webgl": False,
                    "available": True,
                    "transcript": True,
                    "sub_type": "transcript",
                }
            )
        options.append(
            {
                "id": "opt_3d",
                "modality": "3d",
                "kb": 2400,
                "affordances": ["inscription", "spatial_relation"],
                "keyboard": True,
                "requires_webgl": True,
                "available": True,
                "sub_type": "model",
            }
        )
        decision = _ln07_oracle(transcript_required, audio_transcript, text_variant)
        rows.append(
            {
                "case_id": f"LN07-TRANS-{seed:02d}-{i:03d}",
                "group_id": f"trans-grp-{seed:02d}-{i % 6}",
                "input": {
                    "case_id": f"LN07-TRANS-{seed:02d}-{i:03d}",
                    "content": {"id": "sanitized-motif", "type": "bronze-urn", "synthetic": True},
                    "device": {"keyboard_only": False, "network_kbps": 8000, "screen_reader": False, "webgl": True},
                    "learner": {"access": "standard", "synthetic": True, "evaluation_mode": "sanitized_stress"},
                    "options": options,
                    "task": {
                        "type": "inscription_reading",
                        "description": "sanitized stress: read the inscription",
                        "required_affordances": ["inscription"],
                        "transcript_required": transcript_required,
                    },
                },
                "label": decision,
            }
        )
    return rows


# --------------------------------------------------------------------------
# LN-09 — small-cohort (n < k=5) scored stratum
# --------------------------------------------------------------------------

def _ln09_oracle(cohort_size: int | None, k: int = K_THRESHOLD) -> str:
    """Published-rule oracle (k-anonymity invariant), independent of policy
    code: cohort_size < k -> descriptive_only (suppression), else propose."""
    if cohort_size is not None and cohort_size < k:
        return "descriptive_only"
    return "propose_explained_action"


def generate_ln09_family(seed: int) -> list[dict[str, Any]]:
    import random

    rng = random.Random(f"ln09-smallcohort-{seed}")
    rows: list[dict[str, Any]] = []
    for i in range(N_CASES_PER_FAMILY):
        small = i % 2 == 0
        cohort = rng.randint(1, 4) if small else rng.randint(6, 30)
        decision = _ln09_oracle(cohort)
        rows.append(
            {
                "case_id": f"LN09-COHORT-{seed:02d}-{i:03d}",
                "group_id": f"cohort-grp-{seed:02d}-{i % 6}",
                "input": {
                    "case_id": f"LN09-COHORT-{seed:02d}-{i:03d}",
                    "cohort_size": cohort,
                    "observation_age_days": 3,
                    "required_signal_types": ["quiz"],
                    "learning_evidence": [
                        {"type": "quiz", "outcome": "evidence_use", "score": 0.55, "verified": True}
                    ],
                    "signals_conflict": False,
                    "candidate_intervention": "additional_source_comparison_activity",
                    "content": {"id": "sanitized-site", "type": "imperial-site", "synthetic": True},
                    "learner": {"access": "standard", "synthetic": True, "evaluation_mode": "sanitized_stress"},
                },
                "label": decision,
            }
        )
    return rows


FAMILIES = {
    "ln06_external_solver_parity": (generate_ln06_family, LN06_LABELS),
    "ln07_transcript_failure": (generate_ln07_family, LN07_LABELS),
    "ln09_small_cohort": (generate_ln09_family, LN09_LABELS),
}


def write_family(
    family: str,
    seeds: tuple[int, ...] = (11, 23, 37),
    *,
    output_dir: Path | None = None,
) -> dict:
    """Generate + write one family across seeds; returns the manifest dict."""
    if family not in FAMILIES:
        raise ValueError(f"unknown family {family!r}; known: {sorted(FAMILIES)}")
    generator, labels = FAMILIES[family]
    target_dir = (output_dir or SANITIZED_DIR) / family
    target_dir.mkdir(parents=True, exist_ok=True)
    files: list[dict[str, Any]] = []
    total = 0
    label_counts: dict[str, int] = {}
    for seed in seeds:
        rows = generator(seed)
        for row in rows:
            if row["label"] not in labels:
                raise ValueError(
                    f"{family}: generated label {row['label']!r} outside declared oracle space"
                )
            label_counts[row["label"]] = label_counts.get(row["label"], 0) + 1
        path = target_dir / f"seed{seed}.jsonl"
        payload = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
        path.write_text(payload, encoding="utf-8")
        files.append({"path": str(path), "seed": seed, "sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest()})
        total += len(rows)
    manifest = {
        "schema": "research_v3.sanitized_dataset/v1",
        "task_ids": ["V3-G15", "V3-G16", "V3-G17"],
        "family": family,
        "provenance": "V3-authored sanitized synthetic stress suite; frozen V2 T3 untouched",
        "n_cases_total": total,
        "n_cases_per_seed": N_CASES_PER_FAMILY,
        "oracle_labels": sorted(labels),
        "label_counts": dict(sorted(label_counts.items())),
        "files": files,
        "suite_sha256": sha256_input({"family": family, "files": files}),
    }
    (target_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def write_all(output_dir: Path | None = None) -> dict[str, dict]:
    return {
        family: write_family(family, output_dir=output_dir) for family in sorted(FAMILIES)
    }
