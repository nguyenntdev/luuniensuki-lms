"""P01-T11 transparency artifact: dev-split hyperparameter sweep.

The preregistration froze C1/gate hyperparameters BEFORE the confirmatory run
(l2_lambda=1.0, max_iters=250, learning_rate=0.5, alpha_conf=0.20,
alpha_fail=0.30). This sweep runs on the DEV split only for transparency: it
documents what the frozen values were measured against. The frozen values are
used in the confirmatory run regardless of this sweep's outcome; no test-row
information is used here, and the sweep result must not change the run config.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from research_v3.eval.splitters import time_split
from research_v3.methods.p01.features import build_vocabulary, featurize_rows
from research_v3.methods.p01.metrics import compute_classification_metrics
from research_v3.methods.p01.models import calibrate_gate, fit_classical, predict_batch
from research_v3.methods.p01.pipeline import enforce_learner_disjointness, load_validated_rows
from research_v3.methods.p01.types import LABELS, ModelConfig

OUT = Path("research_artifacts_v3/runs/p01/hyperparameter_search.json")


def _split_parts(rows):
    split = time_split(rows, time_key="time_key", paper_id="P01", train_fraction=0.70)
    id2part = {}
    for part, ids in split.split_ids.items():
        for cid in ids:
            id2part[cid] = part
    parts = {p: [] for p in split.split_ids}
    for r in rows:
        parts[id2part[r["case_id"]]].append(r)
    parts, _ = enforce_learner_disjointness(parts)
    return parts


def main() -> int:
    rows, _ = load_validated_rows()
    parts = _split_parts(rows)
    config = ModelConfig(seed=0)
    vocab = build_vocabulary(parts["train"])
    gold_rows = [{"case_id": str(r["case_id"]), "label": str(r["label"])} for r in parts["dev"]]

    results = {"note": "DEV-split transparency sweep; frozen prereg values used for the run regardless", "c1_l2": [], "gate_alpha_conf": []}
    for l2 in (0.1, 1.0, 10.0):
        cfg = ModelConfig(l2_lambda=l2, seed=0)
        model = fit_classical(parts["train"], vocab, config=cfg)
        Xdev = featurize_rows(parts["dev"], vocab)
        probs = model.predict_proba(Xdev)
        preds = [
            {"case_id": str(r["case_id"]), "decision": LABELS[int(np.argmax(probs[i]))],
             "score": float(probs[i].max()), "reason_codes": ["dev_sweep"]}
            for i, r in enumerate(parts["dev"])
        ]
        m = compute_classification_metrics(preds, gold_rows, model_id=f"dev_C1_l2_{l2}")
        results["c1_l2"].append({"l2_lambda": l2, "dev_accuracy": m["accuracy"], "dev_macro_f1": m["macro_f1"]})

    model = fit_classical(parts["train"], vocab, config=config)
    Pcal = model.predict_proba(featurize_rows(parts["calibration"], vocab))
    for a in (0.05, 0.10, 0.20, 0.40):
        thresholds = calibrate_gate(
            parts["calibration"], Pcal, config=ModelConfig(alpha_conf=a, seed=0)
        )
        preds = predict_batch(
            parts["dev"],
            {
                "model_id": f"dev_gate_alpha_conf_{a}",
                "vocabulary": vocab,
                "weights": model.weights.tolist(),
                "bias": model.bias.tolist(),
                "thresholds": thresholds.to_dict(),
                "gate_mode": "full",
            },
        )
        m = compute_classification_metrics(
            preds.to_jsonl_rows(), gold_rows, model_id=f"dev_gate_alpha_conf_{a}"
        )
        results["gate_alpha_conf"].append(
            {"alpha_conf": a, "tau_conf": thresholds.tau_conf,
             "dev_accuracy": m["accuracy"], "dev_coverage": m["coverage"]}
        )
    OUT.write_text(json.dumps(results, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
