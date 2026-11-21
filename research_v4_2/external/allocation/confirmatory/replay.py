"""Run decide, then evaluate, in separate processes. See README for invocation."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from benchmark import ARCHIVES, cohort, outcomes, predict, verified_archive
from policies import allocate

HERE = Path(__file__).resolve().parent
NAMES = ["unrestricted", "fair", "quota", "threshold", "discount_dp", "robust"]
PROTOCOL = "3ad71e1ec7a550aa9823323aeb6834ebd41c6b342e45e76f9699739ef0729a2a"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decide(raw, work):
    records = []
    training = {}
    for dataset in ARCHIVES:
        with verified_archive(dataset, raw) as archive:
            train, test, categorical, numeric = cohort(dataset, archive)
            historical = outcomes(archive, dataset, set(train.key))
        training[dataset] = len(train)
        scores = predict(train, test, categorical, numeric, historical)
        for pool, rows in test.groupby("pool"):
            # Rows already in lexical ID order; stable sort resolves every tie.
            indices = rows.index[np.argsort(-scores[0, rows.index], kind="stable")]
            rows = test.loc[indices].reset_index(drop=True)
            k = max(1, len(rows)//10)
            rankings, table = allocate(scores[:, indices], rows.female.to_numpy(), k)
            payload = rows[["key", "pool", "female"]].assign(dataset=dataset, score=scores[0, indices])
            payload["minimum"] = np.pad(table, (0, len(rows)-k), constant_values=-1)
            for name, ids in rankings.items():
                rank = np.zeros(len(rows), dtype=int)
                rank[ids] = np.arange(1, k+1)
                payload[name] = rank
            records.append(payload)
    path = work / "decisions.csv"
    pd.concat(records, ignore_index=True).to_csv(path, index=False)
    receipt = {"protocol_sha256": PROTOCOL, "decisions_sha256": digest(path),
               "training_learners": training, "source_sha256": {k: v[1] for k,v in ARCHIVES.items()}}
    (work / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


def counts(table):
    cases = table.outcome.to_numpy()
    female = table.female.to_numpy()
    selected = table[NAMES].to_numpy() > 0
    def column(values):
        return values.astype(int)[:, None]
    return np.column_stack((female & cases, ~female & cases, selected,
                            selected * column(female & cases), selected * column(~female & cases)))


def metrics(totals):
    seats, f_capture, m_capture = np.split(totals[..., 2:], 3, axis=-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        recall = np.minimum(f_capture / totals[..., :1], m_capture / totals[..., 1:2])
        precision = (f_capture + m_capture) / seats
    return recall, precision


def intervals(frame):
    # Compress identical contribution vectors. Multinomial draws exactly reproduce
    # sampling whole learners with replacement within each fixed test pool.
    draws = np.zeros((5000, 2+3*len(NAMES)), dtype=int)
    rng = np.random.default_rng(1701)
    for _, pool in frame.groupby("pool"):
        unique, frequency = np.unique(counts(pool), axis=0, return_counts=True)
        draws += rng.multinomial(len(pool), frequency / len(pool), size=len(draws)) @ unique
    point = metrics(counts(frame).sum(axis=0))
    bootstrap = metrics(draws)
    records = []
    for label, observed, samples in zip(("worst_recall", "precision"), point, bootstrap):
        for i, policy in enumerate(NAMES[:-1]):
            difference = samples[:, -1] - samples[:, i]
            valid = difference[np.isfinite(difference)]
            lo, hi = np.quantile(valid, [.025, .975]) if len(valid) else [np.nan, np.nan]
            records.append(dict(metric=label, comparator=policy,
                                robust_minus_comparator=observed[-1]-observed[i],
                                lower=lo, upper=hi, valid_draws=len(valid)))
    return records


def evaluate(raw, work, out):
    receipt = json.loads((work / "receipt.json").read_text())
    path = work / "decisions.csv"
    assert digest(path) == receipt["decisions_sha256"] and PROTOCOL == receipt["protocol_sha256"]
    decisions = pd.read_csv(path)
    records, differences = [], []
    for dataset, rows in decisions.groupby("dataset"):
        with verified_archive(dataset, raw) as archive:
            labels = outcomes(archive, dataset, set(rows.key))
        frame = rows.assign(outcome=rows.key.map(labels))
        for pool, group in frame.groupby("pool"):
            table = group.minimum[group.minimum >= 0].to_numpy()
            k = len(table)
            for name in NAMES:
                picked = group[group[name] > 0].sort_values(name)
                assert len(picked) == k
                records.append(dict(dataset=dataset, pool=pool, policy=name, n=len(group), k=k,
                                    female=int(group.female.sum()), female_seats=int(picked.female.sum()),
                                    female_cases=int((group.female & group.outcome).sum()),
                                    other_cases=int((~group.female & group.outcome).sum()),
                                    female_capture=int((picked.female & picked.outcome).sum()),
                                    other_capture=int((~picked.female & picked.outcome).sum()),
                                    expected_capture=picked.score.sum(),
                                    oracle_capture=min(k, group.outcome.sum()),
                                    replaced=int((picked.unrestricted == 0).sum()),
                                    violations=int(np.sum(picked.female.cumsum().to_numpy() < table))))
        differences.extend(dict(dataset=dataset, **entry) for entry in intervals(frame))
    pools = pd.DataFrame(records)
    totals = pools.drop(columns="pool").groupby(["dataset", "policy"], as_index=False).sum()
    totals["precision"] = (totals.female_capture + totals.other_capture) / totals.k
    totals["worst_recall"] = np.minimum(totals.female_capture / totals.female_cases,
                                        totals.other_capture / totals.other_cases)
    for name, df in [("pools", pools), ("results", totals), ("contrasts", pd.DataFrame(differences))]:
        df.to_csv(out / f"{name}.csv", index=False, float_format="%.10g")
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["decide", "evaluate"])
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=HERE)
    args = parser.parse_args()
    assert digest(HERE / "protocol.md") == PROTOCOL
    with threadpool_limits(limits=1):
        if args.stage == "decide":
            decide(args.raw, args.work)
        else:
            evaluate(args.raw, args.work, args.out)
