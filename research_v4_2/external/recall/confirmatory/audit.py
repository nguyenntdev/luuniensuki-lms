"""Check timestamp boundaries and recompute the reported paired test results."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ttest_1samp

import study


def time_check():
    common = dict(user_id="a", learning_language="es", ui_language="en", history_correct=1,
                  history_seen=2, delta=42, session_seen=1, bucket=10)
    f = pd.DataFrame([dict(common, timestamp=ts, lexeme_string=word, session_correct=success)
                      for ts, word, success in [(200,"a",0),(100,"b",1),(100,"a",1),
                                                (300,"b",1),(300,"a",1)]])
    before = study.features(f)
    # Change both outcomes at the same lesson/practice and every later outcome.
    f.loc[f.timestamp >= 200, "session_correct"] = 1 - f.loc[f.timestamp >= 200, "session_correct"]
    after = study.features(f)
    cols = [c for c in study.RICH if c != "item_difficulty"] + study.CATS
    pd.testing.assert_frame_equal(before.loc[f.timestamp <= 200, cols], after.loc[f.timestamp <= 200, cols])
    np.testing.assert_allclose(before.loc[f.timestamp == 100, "prior_user"], .9)
    np.testing.assert_allclose(before.loc[f.timestamp == 200, "prior_user"], 6.5 / 7)
    np.testing.assert_allclose(before.loc[f.timestamp == 300, "prior_user"], 6.5 / 8)
    assert before.loc[3, "prior_user"] < after.loc[3, "prior_user"]
    assert before.loc[4, "prior_item"] < after.loc[4, "prior_item"]
    # Randomize file order, preserving row IDs for the comparison.
    shuffled = study.features(f.assign(row=np.arange(len(f))).sample(frac=1, random_state=7)).sort_values("row")
    pd.testing.assert_frame_equal(after[cols], shuffled[cols].reset_index(drop=True))


def score_check(out):
    freeze = json.loads((out/"freeze.json").read_text())
    result = json.loads((out/"result.json").read_text())
    assert result["freeze_sha256"] == study.digest(out/"freeze.json")
    assert result["losses_sha256"] == study.digest(out/"learner_losses.csv.gz")
    f = pd.read_csv(out/"learner_losses.csv.gz")
    assert len(f) == result["partition"]["learners"]
    assert not f.duplicated(["bucket","learner_ordinal"]).any()
    assert set(f.bucket) == {14,15,16,17}
    assert sum(freeze["weights"].values()) > .999999
    names = list(result["contrasts"])
    gain = f[names].sub(f.ensemble, axis=0)
    for n in [*names,"ensemble"]:
        np.testing.assert_allclose(f[n].mean(),result["mean_learner_nll"][n])
    pm = ttest_1samp(gain, popmean=.005, alternative="greater").pvalue
    # Holm expressed as max over less extreme ordered hypotheses.
    adjusted = [min(1, max(p * (pm >= p).sum() for p in pm if p <= target)) for target in pm]
    for n, p in zip(names,adjusted):
        c = result["contrasts"][n]
        np.testing.assert_allclose([gain[n].mean(),p], [c["gain"],c["holm_p_margin"]],atol=1e-12)
    assert result["counts_as_superior"] == all(p < .05 for p in adjusted)


if __name__ == "__main__":
    time_check()
    if len(sys.argv) > 1:
        score_check(Path(sys.argv[1]))
    print("Checks passed")
