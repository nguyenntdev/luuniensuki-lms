"""Measure which logit components remain identifiable under balanced decoding."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import lsqr

from paired import comparison, decode_balanced, string_groups


def analyze(rows, logits):
    nc = len({r["claim"] for r in rows})
    _, c = np.unique([r["claim"] for r in rows], return_inverse=True)
    _, e = np.unique([r["evidence"] for r in rows], return_inverse=True)
    e += nc
    n = len(rows)
    design = coo_matrix((np.ones(2*n), (np.tile(np.arange(n), 2), np.r_[c,e]))).tocsr()
    graph = coo_matrix((np.ones(n), (c,e)), shape=(design.shape[1], design.shape[1]))
    n_components, component = connected_components(graph, directed=False)
    groups = string_groups(rows, "claim") + string_groups(rows, "evidence")
    margin = logits[:, 2] - logits[:, 0]
    additive = design @ lsqr(design, margin, atol=1e-13, btol=1e-13, iter_lim=2000)[0]
    residual = margin - additive
    gold = np.array([r["label"] == "SUPPORTS" for r in rows])
    original, _ = decode_balanced(margin, groups)
    centered, _ = decode_balanced(residual, groups)
    shift = np.random.default_rng(42).normal(0., 10., design.shape[1])
    perturbed, _ = decode_balanced(margin + design @ shift, groups)
    if any(solution is None for solution in (original, centered, perturbed)):
        raise ValueError("Unexpected infeasible release")
    if not all(np.isclose(margin @ original, margin @ s) for s in (centered, perturbed)):
        raise ValueError("Group intercepts changed the optimum")
    correct = original == gold
    base = (margin > 0) == gold
    group = component[c]
    counts = np.bincount(group)
    wins = np.bincount(group, weights=correct.astype(int)-base.astype(int))
    picks = np.random.default_rng(42).integers(0, n_components, (10000, n_components))
    draws = wins[picks].sum(axis=1) / counts[picks].sum(axis=1)
    four = [i for i in range(n_components) if counts[i] == 4 and
            len(set(c[group == i])) == 2 and len(set(e[group == i])) == 2 and
            len(set(zip(c[group == i], e[group == i]))) == 4]
    return dict(components=n_components, quartet_components=len(four),
                quartets_completely_correct=sum(bool(correct[group == i].all()) for i in four),
                all_components_correct=sum(bool(correct[group == i].all()) for i in range(n_components)),
                residual_only_independent_correct=int(sum((residual > 0) == gold)),
                optimum_disagreements_after_centering=int(sum(centered != original)),
                optimum_disagreements_after_offset=int(sum(perturbed != original)),
                component_ci95=np.quantile(draws,[.025,.975]).tolist())


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("fever", type=Path)
    p.add_argument("scores", type=Path)
    p.add_argument("--models", nargs="+", default=["bart-large-mnli", "roberta-large-mnli", "original"])
    args = p.parse_args()
    out = {}
    for name in args.models:
        out[name] = {}
        for split in ("dev", "test"):
            rows = [json.loads(l) for l in (args.fever/f"symmetric_{split}.jsonl").read_text().splitlines()]
            with (args.scores/f"{name}-{split}.csv").open() as f:
                scores = list(csv.DictReader(f))
            if [row["id"] for row in rows] != [row["id"] for row in scores]:
                raise ValueError("Gold and score IDs differ")
            logits = np.array([[float(r[k]) for k in ("contradiction","neutral","entailment")] for r in scores])
            report, _ = comparison(rows, logits)
            out[name][split] = {"decisions": report, "geometry": analyze(rows, logits)}
    print(json.dumps(out, indent=2, allow_nan=False))
