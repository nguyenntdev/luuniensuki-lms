"""Replay fixed-capacity allocations. Run as a module from the project root."""
import hashlib
import io
import json
import sys
import tarfile
import tempfile
from functools import lru_cache
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
from scipy.stats import binom
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from research_v4_2.diagnostics import course_allocation as original

OUT = Path(__file__).resolve().parent
RAW = OUT.parents[2] / "private_data/raw"
PACKAGE = RAW / "allocation/fairsearchcore-1.0.4.tar.gz"


def verified(path, sha):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == sha, path
    return path


def cohorts():
    path = verified(RAW / "uci/dropout-697/source.zip", original.SOURCE_SHA)
    source = pd.read_csv(path, sep=";")
    assert set(source.Target) == {"Dropout", "Graduate", "Enrolled"}
    primary = source[source.Target != "Enrolled"].copy()
    primary["dropout"] = primary.Target == "Dropout"
    transfer_path = verified(RAW / "uci/student-performance-2014/student.zip",
                             "82ae9d66437b9808df42e8c89d2bb179c46e9cfbcf06f38abc1d20b3b747e177")
    with ZipFile(transfer_path) as outer, ZipFile(io.BytesIO(outer.read("student.zip"))) as inner:
        transfer = pd.read_csv(inner.open("student-mat.csv"), sep=";")
    assert set(primary.Gender) == {0, 1} and set(transfer.sex) == {"F", "M"}
    assert len(transfer) == 395 and transfer.G3.between(0, 20).all()
    transfer = transfer.assign(Gender=transfer.sex.map({"F": 0, "M": 1}),
                               dropout=transfer.G3 < 10, Course=transfer.school)
    return {"dropout": primary, "mathematics": transfer}


@lru_cache(None)
def thresholds(k, p):
    from fairsearchcore.mtable_generator import MTableGenerator
    # Same adjusted generator as Fair.create_adjusted_mtable, including for k=1.
    generator = MTableGenerator(k, p, 0.10, True)
    m = generator.mtable_as_list()
    adjusted = generator.adjusted_alpha
    quantiles = np.maximum(0, binom.ppf(adjusted, np.arange(1, k + 1), p))
    assert np.array_equal(m, quantiles)
    # Bernoulli path mass that survives every prefix; includes final position.
    mass = np.ones(1)
    for lower in m:
        mass = np.convolve(mass, [1 - p, p])
        mass[:lower] = 0
    return m, adjusted, max(0., 1 - mass.sum())


def replay(rows, percent):
    from fairsearchcore.models import FairScoreDoc
    from fairsearchcore.re_ranker import fair_top_k
    rows = rows.sort_values(["score", "tie"], ascending=[False, True])
    female = rows.Gender.to_numpy() == 0
    positives = rows.dropout.to_numpy()
    n = len(rows)
    k = max(1, n * percent // 100)
    m, adjusted, crossing = thresholds(k, female.mean())
    members = [np.flatnonzero(female), np.flatnonzero(~female)]
    # Ordinal utilities encode the identical total ordering for all three policies.
    queues = [[FairScoreDoc(i, n - i, g == 0) for i in indices]
              for g, indices in enumerate(members)]
    ranked = np.array([doc.id for doc in fair_top_k(k, *queues, m)])
    assert (np.cumsum(female[ranked]) >= m).all()
    remaining = list(range(n))
    count = 0
    for i, candidate in enumerate(ranked):
        best = next(j for j in remaining if count >= m[i] or female[j])
        assert best == candidate
        remaining.remove(best)
        count += int(female[best])
    # Two-group largest remainder with ties to group 0.
    q = (2 * k * len(members[0]) + n) // (2 * n)
    selections = {"risk": np.arange(k), "quota": np.sort(np.r_[members[0][:q], members[1][:k-q]]),
                  "fair": ranked}
    stats = []
    for policy, ids in selections.items():
        assert len(np.unique(ids)) == k
        stats.append(dict(policy=policy, n=n, k=k, female=int(female.sum()),
                          female_cases=int((positives & female).sum()),
                          male_cases=int((positives & ~female).sum()),
                          female_seats=int(female[ids].sum()),
                          female_captured=int((positives[ids] & female[ids]).sum()),
                          male_captured=int((positives[ids] & ~female[ids]).sum()),
                          seats_replaced=len(set(ids) - set(range(k))),
                          violating_prefixes=int((np.cumsum(female[ids]) < m).sum())))
    return stats, dict(k=k, p=female.mean(), alpha_adjusted=adjusted, m=m, crossing=crossing)


def run():
    from fairsearchcore import Fair
    # Author fixture from test_create_adjusted_mtable (20, .25, .1).
    expected = [0] * 8 + [1] * 7 + [2] * 5
    assert thresholds(20, 0.25)[0] == Fair(20, 0.25, 0.1).create_adjusted_mtable() == expected
    legacy = json.loads((OUT.parents[1] / "diagnostics/course_allocation.json").read_text())
    records, tables = [], {}
    for dataset, frame in cohorts().items():
        frame["tie"] = np.random.default_rng(42).permutation(len(frame))
        for name, model in [
            ("logistic", make_pipeline(StandardScaler(), LogisticRegression(max_iter=500))),
            ("boosting", HistGradientBoostingClassifier(max_iter=100, random_state=42)),
        ]:
            if dataset == "dropout":
                frame["score"] = original.score_courses(frame, model)
            else:
                features = ["G1", "G2", "failures"]
                for school in frame.Course.unique():
                    held = frame.Course == school
                    model.fit(frame.loc[~held, features], frame.loc[~held, "dropout"])
                    frame.loc[held, "score"] = model.predict_proba(frame.loc[held, features])[:, 1]
            assert np.isfinite(frame.score).all()
            for pool, rows in frame.groupby("Course"):
                if dataset == "dropout":
                    assert original.compare_allocations(rows) == legacy["models"][name]["courses"][str(pool)]
                for percent in (5, 10, 15):
                    stats, table = replay(rows, percent)
                    tables[f"{dataset}/{pool}/{percent}"] = table
                    for record in stats:
                        if dataset == "dropout" and percent == 10 and record["policy"] != "fair":
                            baseline = legacy["models"][name]["courses"][str(pool)][record["policy"]]
                            assert [record["female_captured"], record["male_captured"]] == [
                                baseline["by_group"][g]["captured"] for g in ("0", "1")]
                        records.append(dict(dataset=dataset, model=name, pool=pool,
                                            percent=percent, **record))
    details = pd.DataFrame(records)
    totals = details.drop(columns="pool").groupby(["dataset", "model", "percent", "policy"]).sum()
    totals["worst_recall"] = np.minimum(totals.female_captured / totals.female_cases,
                                        totals.male_captured / totals.male_cases)
    details.to_csv(OUT / "pool_counts.csv", index=False)
    totals.to_csv(OUT / "results.csv")
    (OUT / "thresholds.json").write_text(json.dumps(tables, indent=2, allow_nan=False) + "\n")


def enable_python_hash_compatibility():
    # The 2019 cache key can return a numpy.int64. CPython requires a native int.
    from fairsearchcore.fail_prob import LegalAssignmentKey
    original_hash = LegalAssignmentKey.__hash__
    LegalAssignmentKey.__hash__ = lambda key: int(original_hash(key))


if __name__ == "__main__":
    verified(PACKAGE, "ca15304579a0c9b3135246a1ad41a23367d963e144269553f6200ad608ac44d6")
    with tempfile.TemporaryDirectory(dir=PACKAGE.parent) as unpack, tarfile.open(PACKAGE) as archive:
        archive.extractall(unpack, filter="data")
        sys.path.insert(0, str(Path(unpack) / "fairsearchcore-1.0.4"))
        enable_python_hash_compatibility()
        with threadpool_limits(limits=1):
            run()
