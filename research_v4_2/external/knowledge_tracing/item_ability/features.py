"""Cross-fitted empirical item probabilities and item-adjusted ability estimates."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit, logit, softmax

COLS = ["item_probability", "skill_probability", "question_support", "prior_mean_expected",
        "prior_success", "prior_answer_count", "ability_mean", "ability_variance", "rasch"]
GRID = np.arange(-3, 3.1, .25)


def construct(raw, output):
    rows = pd.read_pickle(raw / "rows.pkl").reset_index(drop=True)
    with np.load(raw / "simplekt.npz") as cache:
        items = cache["items"]
        skills = cache["skills"]
        current_skills = cache["skill"]
        responses = cache["responses"]
        assert np.array_equal(rows.bucket, cache["bucket"]) and np.array_equal(rows.y, cache["y"])
    assert np.array_equal(rows.question.str[1:].astype(int), items[:, -1])
    assert set(rows.bucket).issubset(range(80))
    assert rows.groupby("uid").bucket.nunique().max() == 1
    assert (rows.uid[rows.bucket < 60].isin(rows.uid[rows.bucket >= 60])).sum() == 0
    fold = rows.bucket.where(rows.bucket < 60, -1).to_numpy(copy=True)
    fold[fold >= 0] %= 5
    features = np.full((len(rows), len(COLS)), np.nan)
    for held in range(-1, 5):
        use = np.flatnonzero((fold >= 0) & (fold != held))
        target = np.flatnonzero(fold == held)
        fit = rows.iloc[use]
        assert set(fit.uid).isdisjoint(rows.uid.iloc[target])
        mean = fit.y.mean()
        skill = fit.groupby("skill").y.agg(["size", "sum"])
        skill.index = skill.index.astype(int)
        skill_rate = (skill["sum"] + 30 * mean) / (skill["size"] + 30)
        item = fit.groupby("question").y.agg(["size", "sum"])
        item.index = item.index.str[1:].astype(int)
        # Unknown exercise IDs are indexed without using their labels.
        qcount = np.zeros(items.max() + 1)
        qsum = np.zeros_like(qcount)
        qcount[item.index] = item["size"]
        qsum[item.index] = item["sum"]
        for ids in np.array_split(target, max(1, len(target) // 1200)):
            qid = items[ids]
            history = skills[ids]
            valid = history != -2
            keys = np.column_stack([history, current_skills[ids]])
            priors = skill_rate.reindex(keys.ravel()).fillna(mean).to_numpy().reshape(keys.shape)
            p = (qsum[qid] + 6 * priors) / (qcount[qid] + 6)
            probs = expit(logit(p)[:, :, None] + GRID)
            y = responses[ids, :, None]
            logl = y * np.log(probs[:, :-1]) + (1 - y) * np.log1p(-probs[:, :-1])
            post = softmax((valid[:, :, None] * logl).sum(axis=1) - GRID**2 / 2, axis=1)
            count = valid.sum(axis=1)
            assert (count > 0).all()
            theta = post @ GRID
            features[ids] = np.column_stack([
                p[:, -1], priors[:, -1], qcount[qid[:, -1]], (p[:, :-1] * valid).sum(axis=1) / count,
                (responses[ids] * valid).sum(axis=1) / count, count, theta,
                (post * (GRID - theta[:, None])**2).sum(axis=1), (post * probs[:, -1]).sum(axis=1)])
    assert np.isfinite(features).all()
    pd.concat([rows, pd.DataFrame(features, columns=COLS)], axis=1).to_csv(output, index=False, compression="gzip")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cache", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    construct(args.cache, args.output)
