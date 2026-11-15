"""Shared LN-05 test fixtures: dataset rows, gold, and the 100x duplicate case."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from research_v2.contracts.types import StudyInput
from research_v2.methods.ln05.labels import LEGACY_TO_V2

REPO = Path(__file__).resolve().parents[3]
INPUTS_PATH = REPO / "research_v2" / "data" / "ln05" / "t3_inputs.jsonl"
GOLD_PATH = REPO / "research_v2" / "data" / "ln05" / "t3_gold.jsonl"

# dataset_sha256 recorded in prereg; bounds the replay-ledger epoch per run.
DATASET_SHA256 = "481f9038e89e842dba30a1a1c971b1e401ec59efebe217b27583cff369d038f1"


def load_rows() -> list[dict]:
    return [json.loads(line) for line in INPUTS_PATH.open(encoding="utf-8") if line.strip()]


def load_gold() -> dict[str, str]:
    rows = [json.loads(line) for line in GOLD_PATH.open(encoding="utf-8") if line.strip()]
    return {r["case_id"]: r["expected_decision"] for r in rows}


def gold_v2() -> dict[str, str]:
    return {cid: LEGACY_TO_V2[d] for cid, d in load_gold().items()}


def make_inputs(rows: list[dict], split_id: str = "test") -> list[StudyInput]:
    return [
        StudyInput("LN-05", r["case_id"], split_id, str(r.get("group_id") or r["case_id"]), r["input"])
        for r in rows
    ]


def run_config(seed: int = 11) -> dict:
    return {
        "seed": seed,
        "dataset_sha256": DATASET_SHA256,
        "badge_policy_version": 2,
    }


def duplicate_case_inputs(count: int = 100) -> list[StudyInput]:
    """100 concurrent deliveries of ONE valid submission.

    Hard requirement: case_id must stay unique per delivery (the runner and the
    contract treat case_id as the case key), so the duplicates share the same
    submission content — identical dedup identity — under 100 distinct case_ids.
    """
    base = next(
        r
        for r in load_rows()
        if any(e.get("actor") == "server" for e in r["input"]["reward_events"])
    )
    inputs: list[StudyInput] = []
    for k in range(count):
        features = copy.deepcopy(base["input"])
        features["case_id"] = f"LN-05-DUP-{k:03d}"
        inputs.append(
            StudyInput(
                "LN-05",
                features["case_id"],
                "test",
                f"LN-05-dupgrp-{k:03d}",  # distinct groups; same replay family
                features,
            )
        )
    return inputs


@pytest.fixture(scope="session")
def rows() -> list[dict]:
    return load_rows()


@pytest.fixture(scope="session")
def gold() -> dict[str, str]:
    return load_gold()


@pytest.fixture(scope="session")
def gold_v2_map() -> dict[str, str]:
    return gold_v2()


@pytest.fixture(scope="session")
def inputs(rows) -> list[StudyInput]:
    return make_inputs(rows)
