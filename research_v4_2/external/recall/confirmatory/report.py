"""Render the expanded comparison after checking every contrast from paired losses."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t, ttest_1samp


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("run", type=Path)
args = parser.parse_args()
run = args.run
result = json.loads((run / "reference_result.json").read_text())
primary = json.loads((run / "result.json").read_text())
losses = pd.read_csv(run / "learner_losses.csv.gz")
extra = pd.read_csv(run / "reference_learner_losses.csv.gz")
keys = ["bucket", "learner_ordinal"]
pd.testing.assert_frame_equal(losses[keys], extra[keys])
losses = losses.merge(extra, validate="one_to_one", on=keys)
names = list(result["contrasts"])
assert len(losses) == result["learners"] and len(names) == 16
gains = losses[names].sub(losses.ensemble, axis=0)
test = ttest_1samp(gains, .005, alternative="greater")
raw = list(test.pvalue)
for name, p in zip(names, raw):
    c = result["contrasts"][name]
    adjusted = min(1., max(x * sum(other >= x for other in raw) for x in raw if x <= p))
    interval = t.interval(1 - .05 / len(names), len(losses) - 1,
                          loc=gains[name].mean(), scale=gains[name].sem())
    np.testing.assert_allclose([adjusted, gains[name].mean(), *interval],
                               [c["holm_p_margin"], c["gain"], *c["simultaneous_ci95"]],
                               atol=1e-12)
    assert c["pass_margin"] == (adjusted < .05 and gains[name].mean() >= .005)
passed = sum(c["pass_margin"] for c in result["contrasts"].values())
assert result["counts_as_superior"] == (passed == len(names))
print("# Results on the reserved Duolingo learners\n")
print(f"The four-component ensemble had mean learner log loss {losses.ensemble.mean():.6f} "
      f"across {result['learners']:,} learners and {result['rows']:,} item encounters. "
      f"It cleared the 0.005-nat margin for {passed} of {len(names)} controls "
      "under one-sided Holm tests. Positive gains favor the ensemble.\n")
print("| Control | Mean learner log loss | Paired gain in nats | Simultaneous 95% interval | Holm p at 0.005 | Clears margin |")
print("|---|---:|---:|---:|---:|---|")
for name in gains.mean().sort_values().index:
    c = result["contrasts"][name]
    lo, hi = c["simultaneous_ci95"]
    print(f"| {name.replace('_', ' ')} | {c['mean_nll']:.6f} | {c['gain']:.6f} | "
          f"[{lo:.6f}, {hi:.6f}] | {c['holm_p_margin']:.3g} | {'Yes' if c['pass_margin'] else 'No'} |")
original = sum(c["pass_margin"] for c in primary["contrasts"].values())
print(f"\nThe original ten-comparator family cleared {original} of 10 margins. Both analyses "
      "condition on fixed fits and assume independent learners. "
      "[Original results](run/result.json) · [Expanded results](run/reference_result.json) · "
      "[Original protocol](protocol.md) · [Additional reference controls](reference_protocol.md)")
