"""Shared fixtures for LN-10 V2 tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research_v2.methods.ln10.dataset import (  # noqa: E402
    DATASET_PATH,
    GOLD_PATH,
    load_jsonl,
)


@pytest.fixture(scope="module")
def t3_dataset_paths():
    return (DATASET_PATH, GOLD_PATH)


@pytest.fixture(scope="module")
def t3_inputs(t3_dataset_paths):
    inputs_path, _ = t3_dataset_paths
    return load_jsonl(inputs_path)


@pytest.fixture(scope="module")
def t3_gold(t3_dataset_paths):
    _, gold_path = t3_dataset_paths
    rows = load_jsonl(gold_path)
    return {row["case_id"]: row["expected_decision"] for row in rows}
