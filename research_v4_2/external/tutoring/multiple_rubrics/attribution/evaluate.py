"""Reproduce the post hoc MRBench rubric-subset audit from two pinned JSON inputs."""

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
from itertools import combinations
import json
from pathlib import Path
import re

import numpy as np


INPUTS = {
    "mrbench_v3_devset.json": "a395feab801de50d44b73e1e9b88f84824a1f1d92e15ae86842d90c2b6dbf33c",
    "MRBench_V2.json": "a8792225075533d15c23e1c903d0c649f19708ee93f5c3d8267eaa6ab623aac1",
}
TUTORS = ("GPT4", "Gemini", "Llama31405B", "Llama318B", "Mistral", "Sonnet")
GUIDANCE = "Providing_Guidance"
SUPPLEMENTS = ("Mistake_Identification", "Mistake_Location", "Actionability")
RUBRICS = (GUIDANCE, *SUPPLEMENTS)
COMPLETE_LABELS = {"Yes", "No", "To some extent"}
SEED = 42
DRAWS = 10_000


@dataclass(frozen=True)
class Case:
    conversation_id: str
    source: str | None
    opening: str
    yes: np.ndarray


def load(directory, filename):
    raw = (directory / filename).read_bytes()
    if hashlib.sha256(raw).hexdigest() != INPUTS[filename]:
        raise ValueError(f"SHA-256 mismatch for {filename}")
    return json.loads(raw)


def conversation_key(row):
    history = " ".join(row["conversation_history"].lower().split())
    return row["conversation_id"], history


def paired_counts(selected, baseline, group_indices, group_draws, sample_sizes):
    difference = selected.astype(int) - baseline.astype(int)
    group_differences = np.bincount(group_indices, weights=difference)
    bootstrap = group_differences[group_draws].sum(axis=1) / sample_sizes
    return {
        "successes": int(selected.sum()),
        "recovered": int((difference == 1).sum()),
        "lost": int((difference == -1).sum()),
        "delta_successes": int(difference.sum()),
        "delta_rate": float(difference.mean()),
        "paired_95pct_interval": np.quantile(bootstrap, [0.025, 0.975]).tolist(),
    }


def evaluate_transfer(cases, origin, target):
    test = [case for case in cases if case.source == target]
    origin_cases = [case for case in cases if case.source == origin]
    test_openings = {case.opening for case in test}
    train = [case for case in origin_cases if case.opening not in test_openings]
    id_overlap = {case.conversation_id for case in train} & {case.conversation_id for case in test}
    train_openings = {case.opening for case in train}
    if id_overlap or train_openings & test_openings:
        raise ValueError(f"Overlapping train and test conversations for {origin} -> {target}")

    train_labels = np.stack([case.yes for case in train])
    test_labels = np.stack([case.yes for case in test])

    # Fit all selectors using the origin labels alone. Preserve every exact maximum.
    subsets = []
    for size in range(len(SUPPLEMENTS) + 1):
        for supplements in combinations(SUPPLEMENTS, size):
            columns = [RUBRICS.index(rubric) for rubric in (GUIDANCE, *supplements)]
            totals = train_labels[:, :, columns].all(axis=2).sum(axis=0)
            maximizers = [tutor for tutor, total in zip(TUTORS, totals) if total == totals.max()]
            subsets.append({
                "supplements": list(supplements),
                "training_successes": dict(zip(TUTORS, totals.tolist())),
                "training_maximizers": maximizers,
                "frozen_tie_break_choice": maximizers[0],
            })

    baseline = subsets[0]["frozen_tie_break_choice"]
    baseline_index = TUTORS.index(baseline)
    groups, group_indices = np.unique([case.opening for case in test], return_inverse=True)
    group_draws = np.random.default_rng(SEED).integers(len(groups), size=(DRAWS, len(groups)))
    sample_sizes = np.bincount(group_indices)[group_draws].sum(axis=1)
    endpoints = {
        "guidance": test_labels[:, :, 0],
        "all_four": test_labels.all(axis=2),
    }
    # The paired outcomes are identical whenever different subsets select the same tutor.
    selected_tutors = {tutor for subset in subsets for tutor in subset["training_maximizers"]}
    paired = {}
    for index, tutor in enumerate(TUTORS):
        if tutor in selected_tutors:
            paired[tutor] = {
                endpoint: paired_counts(
                    labels[:, index], labels[:, baseline_index],
                    group_indices, group_draws, sample_sizes,
                )
                for endpoint, labels in endpoints.items()
            }
    return {
        "origin": origin,
        "target": target,
        "origin_cases_before_opening_filter": len(origin_cases),
        "origin_cases_excluded_by_opening": len(origin_cases) - len(train),
        "train_cases": len(train),
        "train_openings": len(train_openings),
        "test_cases": len(test),
        "test_openings": len(groups),
        "train_test_conversation_id_overlap": len(id_overlap),
        "train_test_opening_overlap": len(train_openings & test_openings),
        "guidance_only_baseline": baseline,
        "subsets": subsets,
        "target_successes_by_endpoint": {
            name: dict(zip(TUTORS, labels.sum(axis=0).tolist()))
            for name, labels in endpoints.items()
        },
        "paired_target_outcomes_vs_guidance_baseline": paired,
    }


def evaluate(directory):
    dev = load(directory, "mrbench_v3_devset.json")
    provenance = load(directory, "MRBench_V2.json")
    sources = {}
    for row in provenance:
        key = conversation_key(row)
        if sources.setdefault(key, row["Data"]) != row["Data"]:
            raise ValueError("Conflicting source labels for a V2 conversation key")
    if len({row["conversation_id"] for row in dev}) != len(dev):
        raise ValueError("Duplicate conversation IDs in the V3 development input")

    cases = []
    labels_by_rubric = {rubric: Counter() for rubric in RUBRICS}
    dev_sources = Counter()
    eligible_sources = Counter()
    for row in dev:
        conversation_id, history = conversation_key(row)
        source = sources.get((conversation_id, history))
        source_label = source if source is not None else "unlinked"
        dev_sources[source_label] += 1
        labels = []
        for tutor in TUTORS:
            annotation = row["tutor_responses"].get(tutor, {}).get("annotation", {})
            values = [annotation.get(rubric, "<missing>") for rubric in RUBRICS]
            for rubric, value in zip(RUBRICS, values):
                labels_by_rubric[rubric][value] += 1
            labels.append(values)
        if all(COMPLETE_LABELS.issuperset(values) for values in labels):
            eligible_sources[source_label] += 1
            opening = re.split(r"\bstudent\s*:", history, maxsplit=1)[0].strip()
            cases.append(Case(conversation_id, source, opening, np.asarray(labels) == "Yes"))

    return {
        "input_sha256": INPUTS,
        "v2_provenance_rows": len(provenance),
        "v2_unique_provenance_keys": len(sources),
        "v3_cases": len(dev),
        "v3_case_counts_by_source": dict(sorted(dev_sources.items())),
        "eligible_cases": len(cases),
        "eligible_case_counts_by_source": dict(sorted(eligible_sources.items())),
        "eligible_openings": len({case.opening for case in cases}),
        "tutors": TUTORS,
        "label_counts_before_filtering": labels_by_rubric,
        "primary_test_endpoint": "guidance",
        "secondary_test_endpoint": "all_four",
        "bootstrap_draws": DRAWS,
        "bootstrap_seed": SEED,
        "transfers": [
            evaluate_transfer(cases, "MathDial", "Bridge"),
            evaluate_transfer(cases, "Bridge", "MathDial"),
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, help="Directory with the two pinned MRBench input files")
    args = parser.parse_args()
    print(json.dumps(evaluate(args.inputs), indent=2))


if __name__ == "__main__":
    main()
