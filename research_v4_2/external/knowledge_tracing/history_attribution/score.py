"""Audit and rescore archived P05 forecasts by observed history depth."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from source import PARENT, assist_histories, ednet_histories

STUDY = Path(__file__).resolve().parent
ROOT = PARENT.parents[2]
EDNET_KEY = ["uid", "row", "start", "y"]
ASSIST = ["full_blend", "skill_mean", "logistic", "dkt", "full", "short", "short_blend"]
TEMPORAL = ["blend_joint", "sakt", "base", "blend_base", "clock", "blend_clock",
            "interference", "blend_interference", "joint"]
SIMPLE = ["items", "skill_only"]
ABILITY = ["rasch", "difficulty", "matched", "ability"]
OPTIONS = ["distractor", "lag_control"]
SCOPES = {"overall": (1, None), "1–16": (1, 16), "17–31": (17, 31), "32+": (32, None)}
DRAWS = 20_000
MARGIN = .015


def verify_hashes():
    for line in (STUDY / "inputs.sha256").read_text().splitlines():
        expected, path = line.split(maxsplit=1)
        with (ROOT / path).open("rb") as file:
            actual = hashlib.file_digest(file, "sha256").hexdigest()
        if actual != expected:
            raise ValueError(f"SHA-256 mismatch: {path}")


def join(left, right, key):
    expected = set(left.columns) & set(right.columns)
    assert expected == set(key), expected
    result = left.merge(right, on=key, validate="one_to_one")
    assert len(result) == len(left) == len(right), key
    return result


def forecasts(path, key, columns):
    frame = pd.read_csv(PARENT / path)
    selected = key + columns
    assert set(frame.columns) == set(selected), path
    return frame[selected]


def load_assist(raw):
    source = assist_histories(raw)
    key = ["uid", "step", "y"]
    return join(source, forecasts("run/predictions.csv.gz", key, ASSIST), key)


def load_ednet(raw, cache):
    source = ednet_histories(raw, cache)
    past = forecasts("temporal/run/screen.csv.gz", EDNET_KEY + ["gap_s"], TEMPORAL)
    simple = forecasts("published_simplekt/run/screen.csv.gz", EDNET_KEY,
                       ["gap_s", "blend_joint", "clock", "sakt", *SIMPLE])
    overlaps = ["blend_joint", "clock", "sakt", "gap_s"]
    aligned = join(past, simple.rename(columns={k: f"shared_{k}" for k in overlaps}), EDNET_KEY)
    for name in overlaps:
        np.testing.assert_allclose(aligned[name], aligned.pop(f"shared_{name}"), atol=1e-12, rtol=0)
    frame = join(source, aligned.rename(columns={"gap_s": "ledger_gap_s"}), EDNET_KEY)
    np.testing.assert_allclose(frame.gap_s, frame.pop("ledger_gap_s"), atol=1e-9, rtol=0)
    ability = forecasts("item_ability/run/estimates.csv.gz", EDNET_KEY, ["question_support", *ABILITY])
    options = forecasts("distractors/run/estimates.csv.gz", EDNET_KEY, OPTIONS)
    frame = join(join(frame, ability, EDNET_KEY), options, EDNET_KEY)
    train = pd.read_pickle(cache / "rows.pkl")
    support = train.loc[train.bucket.lt(60), "question"].value_counts()
    np.testing.assert_array_equal(frame.question.map(support).fillna(0), frame.question_support)
    return frame


def scope_sums(frame, losses, methods, pairs):
    by_learner = pd.Index(sorted(frame.uid.unique()))
    sums = []
    summaries = {}
    for scope, (lower, upper) in SCOPES.items():
        member = frame.depth.ge(lower) & (True if upper is None else frame.depth.le(upper))
        events = frame.loc[member]
        assert len(events), f"No events in {scope}"
        nll = losses.loc[member].mean()
        grouped = losses.loc[member].assign(events=1).groupby(events.uid).sum()
        grouped = grouped.reindex(by_learner, fill_value=0)
        contrasts = [grouped[c] - grouped[m] for c, m in pairs]
        sums.append(np.column_stack([grouped.events, *contrasts]))
        summaries[scope] = dict(
            events=len(events), learners=events.uid.nunique(), correct=int(events.y.sum()),
            repeated_skill=int(events.same_skill.gt(0).sum()),
            nll=nll.to_dict(), strongest_control=min(methods[1:], key=nll.__getitem__))
    assert sum(s["events"] for k, s in summaries.items() if k != "overall") == len(frame)
    return summaries, np.stack(sums, axis=1)


def bootstrap(sums, seed):
    learners, scopes, metrics = sums.shape
    rng = np.random.default_rng(seed)
    averages = []
    for _ in range(DRAWS // 200):
        weights = rng.multinomial(learners, np.full(learners, 1 / learners), size=200)
        sampled = (weights @ sums.reshape(learners, -1)).reshape(-1, scopes, metrics)
        counts = sampled[:, :, 0]
        if (counts == 0).any():
            raise ValueError(f"Undefined bootstrap denominator by scope: {(counts == 0).sum(axis=0)}")
        averages.append(sampled[:, :, 1:] / counts[:, :, None])
    return np.concatenate(averages)


def analyze(frame, methods, tree_pair, match, seed, alpha):
    candidate = methods[0]
    assert frame.y.isin([0, 1]).all() and frame.depth.ge(1).all()
    p = frame[methods].to_numpy()
    assert np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()
    p = np.clip(p, 1e-7, 1 - 1e-7)
    losses = pd.DataFrame(-np.where(frame.y.to_numpy()[:, None], np.log(p), np.log1p(-p)),
                          columns=methods, index=frame.index)
    pairs = [(control, candidate) for control in methods[1:]] + [tree_pair]
    summaries, sums = scope_sums(frame, losses, methods, pairs)
    draws = bootstrap(sums, seed)
    lower, upper = np.quantile(draws, [alpha, 1 - alpha], axis=0)
    for i, scope in enumerate(summaries.values()):
        scope["contrasts"] = {}
        for j, (control, model) in enumerate(pairs):
            gain = scope["nll"][control] - scope["nll"][model]
            scope["contrasts"][f"{control} minus {model}"] = dict(
                gain=gain, simultaneous_ci=[lower[i, j], upper[i, j]],
                clears_margin=bool(gain >= MARGIN and lower[i, j] > 0))
    # Use the same bootstrap draws for both depth bands.
    name = f"{match} minus {candidate}"
    j = pairs.index((match, candidate))
    gap = summaries["32+"]["contrasts"][name]["gain"] - summaries["1–16"]["contrasts"][name]["gain"]
    interaction = np.quantile(draws[:, 3, j] - draws[:, 1, j], [alpha, 1 - alpha])
    return dict(candidate=candidate, closest_control=match, models=methods, forecasts=int(p.size),
                scopes=summaries, long_minus_short_gain=dict(contrast=name, gain=gap,
                                                             simultaneous_ci=interaction.tolist()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path, help="Fresh temporal cache including simplekt.npz")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    verify_hashes()
    assist = load_assist(ROOT / "private_data/raw/assist2015")
    ednet = load_ednet(ROOT / "private_data/raw/ednet/temporal", args.cache)
    ednet_models = [*TEMPORAL, *SIMPLE, *ABILITY, *OPTIONS]
    comparisons = (len(ASSIST) + len(ednet_models)) * len(SCOPES) + 2
    alpha = .025 / comparisons
    result = dict(metric="event-weighted natural-log loss", margin=MARGIN, bootstrap_draws=DRAWS,
                  simultaneous_family=comparisons, quantiles=[alpha, 1 - alpha],
                  assist2015=analyze(assist, ASSIST, ("short", "full"), "short_blend", 731, alpha),
                  ednet_kt1=analyze(ednet, ednet_models, ("clock", "joint"), "blend_clock", 732, alpha))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
