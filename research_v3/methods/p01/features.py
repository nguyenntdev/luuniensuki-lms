"""P01 deterministic featurization with an artifact-pinned vocabulary.

One-hot encoding over a lexicographically sorted vocabulary built from TRAIN
rows only, plus train-standardized numeric fields. The vocabulary and scaler
statistics are saved into the run's artifacts so features are reproducible and
unseen target-domain values degrade to all-zeros (documented, never invented).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .types import P01ContractError, validate_features

# Field order IS the feature order; do not reorder without a new prereg version.
CATEGORICAL_FIELDS: tuple[str, ...] = (
    "code_module",
    "code_presentation",
    "gender",
    "region",
    "highest_education",
    "imd_band",
    "age_band",
    "disability",
)
NUMERIC_FIELDS: tuple[str, ...] = (
    "num_of_prev_attempts",
    "studied_credits",
    "early_click_total",
    "early_active_sites",
)
DROPPED_CONSTANT_FIELDS: tuple[str, ...] = ("observation_window_days",)


def build_vocabulary(train_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Build the fixed encoding from train rows only (never calibration/test)."""
    vocab: dict[str, list[str]] = {}
    for f in CATEGORICAL_FIELDS:
        values: set[str] = set()
        for row in train_rows:
            feats = row["input"]
            if f not in feats:
                raise P01ContractError(f"train row {row.get('case_id')!r} missing feature {f!r}")
            values.add(str(feats[f]))
        vocab[f] = sorted(values)
    numeric_stats: dict[str, dict[str, float]] = {}
    for f in NUMERIC_FIELDS:
        vals = np.asarray([float(row["input"][f]) for row in train_rows], dtype=np.float64)
        numeric_stats[f] = {"mean": float(vals.mean()), "std": float(vals.std() + 1e-9)}
    return {
        "categorical": vocab,
        "numeric": numeric_stats,
        "categorical_fields": list(CATEGORICAL_FIELDS),
        "numeric_fields": list(NUMERIC_FIELDS),
        "dropped_constant_fields": list(DROPPED_CONSTANT_FIELDS),
        "unknown_category_policy": "all_zeros_for_field",
    }


def feature_dim(vocabulary: Mapping[str, Any]) -> int:
    return sum(len(vocabulary["categorical"][f]) for f in CATEGORICAL_FIELDS) + len(NUMERIC_FIELDS)


def featurize_rows(
    rows: Sequence[Mapping[str, Any]],
    vocabulary: Mapping[str, Any],
) -> np.ndarray:
    """Deterministic design matrix; validate_features runs on every row."""
    cat_vocab = vocabulary["categorical"]
    num_stats = vocabulary["numeric"]
    index_of = {f: {v: i for i, v in enumerate(cat_vocab[f])} for f in CATEGORICAL_FIELDS}
    dim = feature_dim(vocabulary)
    X = np.zeros((len(rows), dim), dtype=np.float64)
    for i, row in enumerate(rows):
        feats = row["input"]
        validate_features(feats)
        off = 0
        for f in CATEGORICAL_FIELDS:
            value = str(feats[f])
            pos = index_of[f].get(value)
            if pos is not None:
                X[i, off + pos] = 1.0
            off += len(cat_vocab[f])
        for f in NUMERIC_FIELDS:
            stats = num_stats[f]
            X[i, off] = (float(feats[f]) - stats["mean"]) / stats["std"]
            off += 1
    return X


def save_vocabulary(vocabulary: Mapping[str, Any], path: Path) -> str:
    """Persist the vocabulary; returns its sha256 (canonical JSON standard)."""
    from research_v2.contracts.canonical_hash import sha256_input

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(vocabulary, sort_keys=True, indent=2, allow_nan=False), encoding="utf-8"
    )
    return sha256_input(vocabulary)
