"""Baseline tests: B0 sanity and C1 strong classical comparators (LN-05-11/12)."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

from research_v2.methods.ln05.baselines import predict_batch_b0, predict_batch_c1
from tests.research_v2.ln05.conftest import (
    REPO,
    duplicate_case_inputs,
    load_gold,
    load_rows,
    make_inputs,
    run_config,
)


def test_b0_grants_on_event_count_including_forged_and_replays():
    """SANITY_ONLY control: B0 awards on any activity, so it fails all threats."""
    inputs = make_inputs(load_rows())
    preds = predict_batch_b0(inputs, run_config())
    decisions = Counter(p.decision for p in preds)
    assert decisions["grant_if_eligible"] == 120
    # B0 cannot separate false accepts from legitimate awards — that is the point.


def test_b0_never_a_chosen_solution():
    prereg_path = REPO / "research_v2" / "experiments" / "ln05" / "prereg.yaml"
    import yaml

    prereg = yaml.safe_load(prereg_path.read_text(encoding="utf-8"))
    b0 = next(m for m in prereg["methods_registered"] if m["id"] == "baselines_b0")
    assert b0["role"] == "C0_sanity"
    assert "SANITY_ONLY" in b0["note"]


def test_c1_streak_grants_within_window_and_rejects_repeat_in_window():
    inputs = duplicate_case_inputs(2)
    preds = predict_batch_c1(inputs, run_config())
    # Classical window idempotency: first window grant, second delivery in the
    # same window rejected — but with profile-id keys, not content keys.
    assert preds[0].decision == "grant_if_eligible"
    assert preds[1].decision == "deduplicate_events"


def test_c1_defeats_nothing_without_provenance_or_proof():
    """C1 has no competency proof: unverified tasks with streaks get grants."""
    rows = load_rows()
    base = next(r for r in rows if gold_missing(r))
    features = dict(base["input"])
    # Strip mastery proof but keep a valid server event streak.
    features["skill_evidence"] = {"verified_task": False}
    preds = predict_batch_c1(
        make_inputs([{**base, "case_id": "LN-05-C1-UNPROOF", "group_id": "grp-c1"}]),
        run_config(),
    )
    # The classical baseline only counts the streak, so the unproven case is
    # awarded (documents the C1 failure mode against I1's denial).
    assert preds[0].decision == "grant_if_eligible"


def gold_missing(row: dict) -> bool:
    return load_gold()[row["case_id"]] == "grant_if_eligible"


def test_c1_and_b0_emit_same_output_family():
    """Like-for-like comparability: same labels as I1 for shared case_ids."""
    inputs = make_inputs(load_rows())
    for preds in (predict_batch_b0(inputs, run_config()), predict_batch_c1(inputs, run_config())):
        assert len(preds) == len(inputs)
        assert all(p.case_id == i.case_id for p, i in zip(preds, inputs))
        assert all(p.decision for p in preds)


def test_seed_repeatability_for_baselines():
    inputs = make_inputs(load_rows())
    a = [p.to_dict() for p in predict_batch_b0(inputs, run_config(seed=11))]
    b = [p.to_dict() for p in predict_batch_b0(inputs, run_config(seed=11))]
    assert a == b
    c = [p.to_dict() for p in predict_batch_c1(inputs, run_config(seed=11))]
    d = [p.to_dict() for p in predict_batch_c1(inputs, run_config(seed=11))]
    assert c == d
