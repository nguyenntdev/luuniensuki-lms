"""Recompute uncertainty and all decision gates using the independently scored pages."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np


def verify(folder):
    with (folder / "page-results.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    result = json.loads((folder / "result.json").read_text())
    methods = sorted(result["contrasts"])
    n_pages = result["pages"]["test"]
    gains = np.zeros((n_pages, len(methods)), dtype=int)
    sizes = np.zeros(n_pages, dtype=int)
    seen = set()
    for row in rows:
        page, method = int(row["page_index"]), row["comparator"]
        key = (page, method)
        assert key not in seen
        seen.add(key)
        difference = int(row["candidate_correct"]) - int(row["comparator_correct"])
        assert difference == int(row["rescued"]) - int(row["regressed"])
        gains[page, methods.index(method)] = difference
        n = int(row["rows"])
        assert sizes[page] in (0, n)
        sizes[page] = n
    assert len(seen) == n_pages * len(methods)
    assert sizes.sum() == result["rows"]["test"]
    rng = np.random.default_rng(42)
    indices = rng.integers(0, n_pages, (10000, n_pages))
    # Tabulate bootstrap multiplicities so each page contributes all its observations.
    weights = np.array([np.bincount(index, minlength=n_pages) for index in indices])
    intervals = np.quantile((weights @ gains) / (weights @ sizes)[:, None], [.025, .975], axis=0)
    signs = rng.choice([-1, 1], (20000, n_pages))
    exceedances = (abs(signs @ gains) >= abs(gains.sum(axis=0))).sum(axis=0)
    p_values = (exceedances + 1) / (len(signs) + 1)
    ranked = np.argsort(p_values)
    adjusted = np.zeros_like(p_values)
    adjusted[ranked] = np.minimum(1, np.maximum.accumulate(p_values[ranked] * np.arange(len(methods), 0, -1)))
    for i, method in enumerate(methods):
        reported = result["contrasts"][method]
        expected = [gains[:, i].sum()/sizes.sum(), *intervals[:, i], p_values[i], adjusted[i]]
        np.testing.assert_allclose(expected, [reported["gain"], *reported["ci95"], reported["p"], reported["holm_p"]],
                                   atol=1e-12, rtol=0)
        assert bool(expected[0] >= .01 and expected[1] > 0 and adjusted[i] < .05) == reported["pass"]
    print(f"{len(methods)} clustered intervals, paired sign-flip tests, Holm adjustments and decisions reproduced")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    verify(parser.parse_args().results)
