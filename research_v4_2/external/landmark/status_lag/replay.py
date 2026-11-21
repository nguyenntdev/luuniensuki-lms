"""Replay published OULAD day-60 rankings at fixed capacity and simulated reporting lags."""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PARENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PARENT))
from evaluate import prepare as prepare_landmark


def select(score, seats):
    if seats == 0:
        return np.zeros(len(score))
    cutoff = np.partition(score, len(score)-seats)[len(score)-seats]
    above = score > cutoff
    tied = score == cutoff
    return above.astype(float) + tied * ((seats-above.sum())/tied.sum())


def evaluate(archive):
    roster = prepare_landmark(archive)
    roster = roster.loc[roster.code_presentation.eq("2014J")].reset_index(drop=True)
    prediction_file = PARENT/"run/predictions.csv.gz"
    predictions = pd.read_csv(prediction_file)
    assert len(roster) == len(predictions) == 11249
    assert np.array_equal(predictions.learner, pd.factorize(roster.id_student, sort=True)[0])
    for field in ("outcome", "eligible"):
        assert np.array_equal(roster[field], predictions[field])
    roster["catboost_all"] = predictions.catboost_all
    roster["logit_all"] = predictions.logit_all
    roster["uniform"] = 0.
    rows = []
    for module, module_rows in roster.groupby("code_module"):
        eligible = module_rows.eligible.to_numpy()
        case = module_rows.outcome.to_numpy() & eligible
        date = module_rows.date_unregistration
        for percent in (5, 10, 20):
            seats = int(eligible.sum()*percent//100)
            for model in ("catboost_all", "logit_all", "uniform"):
                previous = None
                for lag in (0, 1, 7, 14, 30, None):
                    available = np.ones(len(eligible), bool) if lag is None else ~date.le(60-lag).to_numpy()
                    w = np.zeros(len(eligible))
                    w[available] = select(module_rows.loc[available, model].to_numpy(), seats)
                    assert np.isclose(w.sum(), seats)
                    if previous is not None:
                        assert np.all(w[eligible] <= previous[eligible]+1e-12)
                    previous = w
                    rows.append(dict(module=module, percent=percent, model=model,
                                     lag="all" if lag is None else str(lag), seats=seats,
                                     stale_seats=w[~eligible].sum(), captured=w[case].sum(),
                                     eligible_cases=case.sum()))
    result = pd.DataFrame(rows)
    for _, group in result.groupby(["module", "percent", "model"]):
        difference = group.iloc[0].captured - group.captured
        assert (difference >= -1e-8).all() and (difference <= group.stale_seats+1e-8).all()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    records = evaluate(args.archive)
    records.to_csv(args.out/"modules.csv", index=False, float_format="%.8f")
    summary = records.groupby(["percent","model","lag"], sort=False, as_index=False)[
        ["seats","stale_seats","captured","eligible_cases"]].sum()
    summary["actionable_precision"] = summary.captured/summary.seats
    summary.to_csv(args.out/"summary.csv", index=False, float_format="%.8f")
