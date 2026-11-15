"""CurriculumShiftBench harness (P04): evaluation under incomplete skill mappings.

This module is a BENCHMARK, not a model. It:

1. loads real rows through the OULAD/UCI adapters (labels never in inputs);
2. freezes group/time splits via ``research_v3.eval.splitters`` and hashes them;
3. exposes mapping injectors (hide verified edges -> partial/unknown mappings);
4. scores submitted predictors against a strict contract where NOT_APPLICABLE
   and ABSTAIN are first-class classes distinct from negative predictions;
5. emits a leaderboard schema with per-stratum degradation, calibration,
   worst-group and rank-stability cells plus bootstrap CIs.

Scoring contract (frozen):
- predictor returns either {"prediction": "ABSTAIN"} or
  {"prediction": 0|1, "probability": p in [0,1]} per case;
- ABSTAIN counts as incorrect for AUC-relevant denominators but is reported
  separately as coverage; it never counts as a negative prediction;
- NOT_APPLICABLE cases (no verified mapping) are excluded from scoring and
  reported as mapping coverage, never silently imputed.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from research_v3.contracts.cards import FrozenSplit
from research_v3.eval.splitters import assert_no_leakage, freeze_hash, group_split, time_split
from research_v3.methods.p04.bridge import ABSTAIN, NOT_APPLICABLE, OntologyBridge
from research_v3.methods.p04.scenarios import Scenario

PREDICTOR_RETURN = Mapping[str, Any]
Predictor = Callable[[Sequence[Mapping[str, Any]]], Sequence[PREDICTOR_RETURN]]

LEADERBOARD_SCHEMA_VERSION = "p04-leaderboard-1.0"


class PredictorContractError(ValueError):
    """Raised when a predictor violates the output contract."""


def validate_predictions(rows: Sequence[Mapping[str, Any]], preds: Sequence[PREDICTOR_RETURN]) -> None:
    if len(rows) != len(preds):
        raise PredictorContractError(
            f"predictor returned {len(preds)} outputs for {len(rows)} rows"
        )
    for i, pred in enumerate(preds):
        if not isinstance(pred, Mapping) or "prediction" not in pred:
            raise PredictorContractError(f"prediction {i}: missing 'prediction' key")
        value = pred["prediction"]
        if value == ABSTAIN:
            continue
        if value not in (0, 1):
            raise PredictorContractError(
                f"prediction {i}: must be 0, 1 or '{ABSTAIN}', got {value!r}"
            )
        if value in (0, 1):
            prob = pred.get("probability")
            if not isinstance(prob, (int, float)) or not 0.0 <= float(prob) <= 1.0:
                raise PredictorContractError(
                    f"prediction {i}: probability in [0,1] required for non-abstain"
                )


def hide_bridge_edges(bridge: OntologyBridge, fraction: float, salt: str) -> OntologyBridge:
    """S1 injector: deterministically hide a fraction of VERIFIED edges.

    Hidden edges become 'unknown': mapping them returns NOT_APPLICABLE. Gold
    labels are untouched; only the mapping information degrades.
    """
    if not 0.0 <= fraction <= 1.0:
        raise ValueError("fraction must be in [0,1]")
    verified = sorted(k for k, e in bridge.edges.items() if e.status == "verified")
    n_hide = int(round(fraction * len(verified)))
    ranked = sorted(verified, key=lambda k: hashlib.sha256(f"{salt}:{k}".encode()).hexdigest())
    hidden = set(ranked[:n_hide])
    from dataclasses import replace

    new_edges = {}
    for key, edge in bridge.edges.items():
        if key in hidden:
            new_edges[key] = replace(edge, status="unknown", canonical=NOT_APPLICABLE, confidence=0.0)
        else:
            new_edges[key] = edge
    return OntologyBridge(
        ontology_version=bridge.ontology_version,
        edges=new_edges,
        unknown_sources=tuple(sorted(bridge.unknown_sources) + sorted(hidden)),
    )


def apply_bridge_to_features(rows: Sequence[Mapping[str, Any]], bridge: OntologyBridge,
                             feature_key: str = "activity_type") -> list[dict[str, Any]]:
    """Attach canonical mapping outcomes to rows without altering labels.

    Rows with an empty source category are marked ``no_activity``: they lack a
    mappable resource entirely (learner inactivity), which is reported
    separately from genuine annotation gaps (unknown categories).
    """
    out = []
    for row in rows:
        enriched = dict(row)
        source_val = enriched.get("input", {}).get(feature_key)
        enriched["mapped_canonical"] = bridge.map_source(source_val)
        enriched["no_activity"] = source_val is None or str(source_val) == ""
        out.append(enriched)
    return out


def freeze_splits(
    rows: Sequence[Mapping[str, Any]],
    *,
    paper_id: str,
    protocol: str,
    group_key: str = "group_id",
    time_key: str | None = None,
    salt: str = "p04-v1",
) -> FrozenSplit:
    """Materialize and hash a split through the shared vetted splitters."""
    if protocol == "time" and time_key:
        split = time_split(rows, time_key=time_key, paper_id=paper_id)
    else:
        split = group_split(rows, group_key=group_key, paper_id=paper_id, protocol=protocol, salt=salt)
    assert_no_leakage(split)
    return split


def partition_ids(split: FrozenSplit) -> dict[str, set[str]]:
    return {name: set(ids) for name, ids in split.split_ids.items()}


def _labels(rows: Sequence[Mapping[str, Any]]) -> list[int]:
    ys = []
    for row in rows:
        y = row["label"]
        if y not in (0, 1):
            raise PredictorContractError(f"case {row.get('case_id')!r}: binary label required, got {y!r}")
        ys.append(int(y))
    return ys


def _auc(scores: Sequence[float], ys: Sequence[int]) -> float | None:
    """Rank-based AUC (Mann-Whitney), O(n log n). None when a class is absent."""
    pairs = sorted(zip(scores, ys), key=lambda t: t[0])
    pos = sum(1 for _, y in pairs if y == 1)
    neg = len(pairs) - pos
    if pos == 0 or neg == 0:
        return None
    # average ranks with tie handling (1-based)
    i = 0
    rank_sum_pos = 0.0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0  # 1-based average rank of the tie block
        pos_in_block = sum(1 for k in range(i, j + 1) if pairs[k][1] == 1)
        rank_sum_pos += avg_rank * pos_in_block
        i = j + 1
    return (rank_sum_pos - pos * (pos + 1) / 2.0) / (pos * neg)


def score_predictions(rows: Sequence[Mapping[str, Any]], preds: Sequence[PREDICTOR_RETURN]) -> dict[str, Any]:
    """Score one (rows, predictions) cell under the frozen contract."""
    validate_predictions(rows, preds)
    labels = _labels(rows)
    scored: list[tuple[int, float, bool, str]] = []
    n_abstain = 0
    n_not_applicable = 0
    n_no_activity = 0
    for row, y, pred in zip(rows, labels, preds):
        if row.get("mapped_canonical") == NOT_APPLICABLE:
            n_not_applicable += 1
            if row.get("no_activity"):
                n_no_activity += 1
            continue
        value = pred["prediction"]
        if value == ABSTAIN:
            n_abstain += 1
            continue
        scored.append((y, float(pred["probability"]), int(value) == y, row.get("group_id", "")))

    n_scored = len(scored)
    coverage = n_scored / len(rows) if rows else 0.0
    accuracy = sum(c for _, _, c, _ in scored) / n_scored if n_scored else None
    auc = _auc([p for _, p, _, _ in scored], [y for y, _, _, _ in scored]) if n_scored else None
    return {
        "n_total": len(rows),
        "n_scored": n_scored,
        "n_abstain": n_abstain,
        "n_not_applicable": n_not_applicable,
        "n_no_activity": n_no_activity,
        "coverage": round(coverage, 6),
        "mapping_coverage": round((len(rows) - n_not_applicable) / len(rows), 6) if rows else 0.0,
        "annotation_gap_rows": n_not_applicable - n_no_activity,
        "accuracy": None if accuracy is None else round(accuracy, 6),
        "auc": None if auc is None else round(auc, 6),
    }


def expected_calibration_error_scored(
    rows: Sequence[Mapping[str, Any]],
    preds: Sequence[PREDICTOR_RETURN],
    *,
    n_bins: int = 10,
) -> float | None:
    """ECE over scored (non-abstain, mappable) cases."""
    labels = _labels(rows)
    pairs: list[tuple[float, int]] = []
    for row, y, pred in zip(rows, labels, preds):
        if row.get("mapped_canonical") == NOT_APPLICABLE:
            continue
        value = pred["prediction"]
        if value == ABSTAIN:
            continue
        pairs.append((float(pred["probability"]), int(y)))
    if not pairs:
        return None
    bins = [[] for _ in range(n_bins)]
    for p, y in pairs:
        idx = min(n_bins - 1, max(0, int(p * n_bins)))
        bins[idx].append((p, y))
    total = len(pairs)
    ece = 0.0
    for bucket in bins:
        if not bucket:
            continue
        mean_p = sum(p for p, _ in bucket) / len(bucket)
        observed = sum(y for _, y in bucket) / len(bucket)
        ece += (len(bucket) / total) * abs(mean_p - observed)
    return round(ece, 6)


def worst_group_accuracy(
    rows: Sequence[Mapping[str, Any]],
    preds: Sequence[PREDICTOR_RETURN],
    *,
    min_n: int = 20,
) -> dict[str, Any] | None:
    """Lowest-accuracy demographic group (gender x age_band when available)."""
    groups: dict[str, list[bool]] = {}
    labels = _labels(rows)
    for row, y, pred in zip(rows, labels, preds):
        if row.get("mapped_canonical") == NOT_APPLICABLE or pred["prediction"] == ABSTAIN:
            continue
        inp = row.get("input", {})
        g = f"gender={inp.get('gender', 'NA')}/age={inp.get('age_band', inp.get('sex', 'NA'))}"
        groups.setdefault(g, []).append(int(pred["prediction"]) == y)
    evaluated = [
        {"group": g, "n": len(flags), "accuracy": round(sum(flags) / len(flags), 6)}
        for g, flags in sorted(groups.items())
        if len(flags) >= min_n
    ]
    if not evaluated:
        return None
    return min(evaluated, key=lambda e: e["accuracy"])


def bootstrap_ci_metric(
    rows: Sequence[Mapping[str, Any]],
    preds: Sequence[PREDICTOR_RETURN],
    *,
    metric: str = "accuracy",
    n_boot: int = 1000,
    seed: int = 42,
) -> dict[str, Any] | None:
    """Learner-cluster bootstrap CI for one metric cell (resampling unit = group_id)."""
    import random

    validate_predictions(rows, preds)
    labels = _labels(rows)
    per_group: dict[str, list[tuple[int, float]]] = {}
    for row, y, pred in zip(rows, labels, preds):
        if pred["prediction"] == ABSTAIN or row.get("mapped_canonical") == NOT_APPLICABLE:
            continue
        per_group.setdefault(str(row.get("group_id", row.get("case_id", ""))), []).append(
            (y, float(pred["probability"]))
        )
    groups = sorted(per_group)
    if not groups:
        return None

    def compute(sample_groups: list[str]) -> float:
        flat = [item for g in sample_groups for item in per_group[g]]
        if metric == "accuracy":
            return sum(1.0 for y, p in flat if (1 if p >= 0.5 else 0) == y) / len(flat)
        if metric == "auc":
            val = _auc([p for _, p in flat], [y for y, _ in flat])
            return 0.0 if val is None else val
        raise ValueError(f"unsupported metric {metric!r}")

    rng = random.Random(seed)
    point = compute(groups)
    stats = []
    for _ in range(n_boot):
        sample = [groups[rng.randrange(len(groups))] for _ in range(len(groups))]
        stats.append(compute(sample))
    stats.sort()
    lo = stats[int(0.025 * len(stats))]
    hi = stats[min(len(stats) - 1, int(0.975 * len(stats)))]
    return {"point": round(point, 6), "ci95": [round(lo, 6), round(hi, 6)], "n_groups": len(groups)}


def rank_stability(rankings_by_stratum: Mapping[str, Sequence[str]]) -> float | None:
    """Kendall-tau-based stability of model rankings across strata (mean pairwise)."""
    names = sorted(rankings_by_stratum)
    if len(names) < 2:
        return None

    def tau(a: Sequence[str], b: Sequence[str]) -> float:
        common = sorted(set(a) & set(b))
        if len(common) < 2:
            return 0.0
        rank_a = {m: i for i, m in enumerate(a)}
        rank_b = {m: i for i, m in enumerate(b)}
        concordant = discordant = 0
        for i in range(len(common)):
            for j in range(i + 1, len(common)):
                x, y = common[i], common[j]
                da, db = rank_a[x] - rank_a[y], rank_b[x] - rank_b[y]
                if da * db > 0:
                    concordant += 1
                elif da * db < 0:
                    discordant += 1
        denom = concordant + discordant
        if denom == 0:
            return 1.0
        return (concordant - discordant) / denom

    vals = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            vals.append(tau(list(rankings_by_stratum[names[i]]), list(rankings_by_stratum[names[j]])))
    return round(sum(vals) / len(vals), 6)


def leaderboard_cell(
    predictor_name: str,
    scenario: Scenario,
    rows: Sequence[Mapping[str, Any]],
    preds: Sequence[PREDICTOR_RETURN],
    *,
    baseline_cell: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """One leaderboard row: scenario x predictor with honest denominators."""
    scored = score_predictions(rows, preds)
    cell = {
        "schema_version": LEADERBOARD_SCHEMA_VERSION,
        "predictor": predictor_name,
        "stratum": scenario.stratum,
        "scenario": scenario.name,
        "dataset_id": scenario.dataset_id,
        **scored,
        "ece": expected_calibration_error_scored(rows, preds),
        "worst_group": worst_group_accuracy(rows, preds),
        "small_n_warning": scored["n_scored"] < 100,
    }
    if baseline_cell is not None:
        if scored["auc"] is not None and baseline_cell.get("auc") is not None:
            cell["auc_degradation_vs_baseline"] = round(baseline_cell["auc"] - scored["auc"], 6)
        if scored["accuracy"] is not None and baseline_cell.get("accuracy") is not None:
            cell["accuracy_degradation_vs_baseline"] = round(
                baseline_cell["accuracy"] - scored["accuracy"], 6
            )
    return cell
