"""Shared helpers for LN-03 Research V2 tests."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "research_v2" / "data" / "ln03"


CARD_KEYS = frozenset(
    {
        "id",
        "due_utc",
        "last_review_utc",
        "source_verified",
        "stability_days",
        "state",
        "difficulty",
        "repetitions",
        "target_retention",
    }
)


def make_features(**overrides: Any) -> dict[str, Any]:
    """Nominal due, mastered, source-verified generative case.

    Card-level override keys (e.g. ``source_verified=False``) are routed into
    ``review_card`` automatically.
    """
    features: dict[str, Any] = {
        "case_id": "LN-03-TEST-0001",
        "task_type": "historical_explanation",
        "fact_prerequisite_mastered": True,
        "scheduler_weight": 1.0,
        "now_utc": "2026-11-08T12:00:00Z",
        "review_card": {
            "id": "card-test-1",
            "due_utc": "2026-11-02T12:00:00Z",
            "last_review_utc": "2026-10-25T12:00:00Z",
            "source_verified": True,
            "stability_days": 4.0,
            "state": "review",
            "difficulty": 4.5,
            "repetitions": 3,
            "target_retention": 0.9,
        },
    }
    for key, value in overrides.items():
        if key == "review_card" and isinstance(value, dict):
            features["review_card"].update(value)
        elif key in CARD_KEYS:
            features["review_card"][key] = value
        else:
            features[key] = value
    return features


def load_t3_inputs() -> list[dict[str, Any]]:
    path = DATA_DIR / "t3_inputs.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_t3_gold() -> dict[str, str]:
    path = DATA_DIR / "t3_gold.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {row["case_id"]: row["expected_decision"] for row in rows}
