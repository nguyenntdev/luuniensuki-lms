"""Determinism & inference seal: identical inputs -> identical outputs;
config/seed noise that should not matter does not matter."""
from __future__ import annotations

import copy

import pytest

from research_v2.methods.ln02 import proposed
from research_v2.methods.ln02.baselines_b0 import predict_batch as b0
from research_v2.methods.ln02.baselines_c1 import predict_batch as c1
from research_v2.methods.ln02.ablations_a1 import predict_batch as a1
from research_v2.methods.ln02.ablations_a2 import predict_batch as a2
from research_v2.methods.ln02.ablations_a3 import predict_batch as a3
from ln02_helpers import (
    load_t3_inputs,
    make_input,
)

ALL_METHODS = [proposed.predict_batch, b0, c1, a1, a2, a3]


@pytest.mark.parametrize("predict_batch", ALL_METHODS)
def test_repeated_runs_are_identical(predict_batch):
    inputs = load_t3_inputs(limit=24)
    first = predict_batch(copy.deepcopy(inputs), {"seed": 11})
    second = predict_batch(copy.deepcopy(inputs), {"seed": 11})
    assert first == second


@pytest.mark.parametrize("predict_batch", ALL_METHODS)
def test_seed_is_inert_for_pure_policy(predict_batch):
    """Policies are pure functions of features; seed must not flip decisions."""
    inputs = load_t3_inputs(limit=24)
    by_seed = {
        seed: tuple(p.decision for p in predict_batch(copy.deepcopy(inputs), {"seed": seed}))
        for seed in (11, 23, 37)
    }
    assert by_seed[11] == by_seed[23] == by_seed[37]


def test_t3_dataset_full_batch_deterministic_proposed():
    inputs = load_t3_inputs()
    assert len(inputs) == 120
    run_a = proposed.predict_batch(inputs, {"seed": 11})
    run_b = proposed.predict_batch(inputs, {"seed": 37})
    assert [(p.case_id, p.decision, p.score, p.reason_codes) for p in run_a] == [
        (p.case_id, p.decision, p.score, p.reason_codes) for p in run_b
    ]


def test_input_feature_mutation_changes_only_intended_case():
    """Metamorphic: breaking one case's required dimension must flip only
    that case (to remediate); neighbours stay untouched."""
    inputs = load_t3_inputs(limit=6)
    baseline = proposed.predict_batch(inputs, {})
    assert baseline[2].decision == "recommend_eligible"

    mutated = copy.deepcopy(inputs)
    features = dict(mutated[2].features)
    mastery = dict(features["mastery"])
    prerequisites = features["target_task"]["prerequisites"]
    # Drive the first *required* dimension far below its threshold.
    required_dim = sorted(prerequisites)[0]
    mastery[required_dim] = 0.0
    features["mastery"] = mastery
    learner = dict(features["learner"])
    learner["competencies"] = dict(learner.get("competencies") or mastery)
    learner["competencies"][required_dim] = 0.0
    features["learner"] = learner
    mutated[2] = type(mutated[2])(
        study_id=mutated[2].study_id,
        case_id=mutated[2].case_id,
        split_id=mutated[2].split_id,
        group_id=mutated[2].group_id,
        features=features,
    )
    after = proposed.predict_batch(mutated, {})
    changed = [i for i, (b, a) in enumerate(zip(baseline, after)) if b.decision != a.decision]
    assert changed == [2], "only the mutated case may change decision"
    assert after[2].decision == "remediate_first"


def test_single_case_hash_paired_runs_stable():
    from research_v2.contracts.canonical_hash import canonical_json, sha256_bytes

    inputs = load_t3_inputs(limit=12)
    hashes_a = [sha256_bytes(canonical_json(i.features)) for i in inputs]
    hashes_b = [sha256_bytes(canonical_json(i.features)) for i in inputs]
    assert hashes_a == hashes_b
