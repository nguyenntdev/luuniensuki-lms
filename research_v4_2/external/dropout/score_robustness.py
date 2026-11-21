"""Audit held-out membership and score frozen probabilities directly against source labels."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss

FAMILIES = ["spline", "catboost", "xgboost"]
CLASSES = ["Dropout", "Enrolled", "Graduate"]


def cells(dataset, target, courses, gold, probs):
    rows = []
    for model, prob in probs.items():
        prob = np.asarray(prob)
        binary = prob.ndim == 1
        if binary:
            prob = np.column_stack([1 - prob, prob])
        assert np.isfinite(prob).all() and np.all(prob >= 0) and np.all(prob <= 1)
        assert np.allclose(prob.sum(axis=1), 1, atol=1e-6, rtol=0)
        # Tree backends emit float32 probabilities. Normalize to the simplex.
        prob = prob / prob.sum(axis=1, keepdims=True)
        for course in sorted(set(courses)):
            mask = courses == course
            local_gold = gold[mask]
            local_prob = prob[mask]
            nll = log_loss(local_gold, local_prob, labels=np.arange(prob.shape[1]))
            assigned = local_prob[np.arange(len(local_gold)), local_gold]
            np.testing.assert_allclose(nll, -np.log(assigned).mean(), atol=1e-10)
            row = dict(dataset=dataset, target=target, course=course, model=model,
                       n=len(local_gold), nll=nll)
            if binary:
                row.update(observed=local_gold.mean(), predicted=local_prob[:, 1].mean())
                row["gap"] = row["predicted"] - row["observed"]
            rows.append(row)
    return rows


def audit(portugal, oulad, run):
    source = pd.read_csv(portugal, sep=";")
    p = pd.read_csv(run / "portugal_three_status.csv.gz").set_index("row").sort_index()
    pd.testing.assert_index_equal(source.index, p.index, check_names=False, exact=False)
    assert source.Course.equals(p.course) and source.Target.equals(p.target)
    resolved = source.Target.ne("Enrolled").to_numpy()
    original = pd.read_csv(run / "predictions.csv")
    np.testing.assert_array_equal(original.course, source.Course[resolved])
    np.testing.assert_array_equal(original.gold, source.Target[resolved] == "Dropout")
    rows = cells("Portugal", "original_resolved", original.course.to_numpy(),
                 original.gold.to_numpy(dtype=int), {name: original[name] for name in FAMILIES})
    primary_prior = np.array([(source.loc[resolved & source.Course.ne(c), "Target"] == "Dropout").mean()
                              for c in sorted(original.course.unique())])
    prior_by_course = dict(zip(sorted(original.course.unique()), primary_prior))
    rows.extend(cells("Portugal", "original_resolved", original.course.to_numpy(),
                      original.gold.to_numpy(dtype=int), {"prior": original.course.map(prior_by_course)}))
    probs = {m: p[[f"{m}_{c}" for c in CLASSES]].to_numpy() for m in [*FAMILIES, "prior"]}
    y = pd.Categorical(source.Target, categories=CLASSES).codes
    course = source.Course.to_numpy()
    rows.extend(cells("Portugal", "three_status", course, y, probs))
    rows.extend(cells("Portugal", "dropout", course, (y == 0).astype(int),
                      {m: scores[:, 0] for m, scores in probs.items()}))
    rows.extend(cells("Portugal", "no_recorded_graduation", course, (y != 2).astype(int),
                      {m: 1 - scores[:, 2] for m, scores in probs.items()}))
    rows.extend(cells("Portugal", "conditional_resolved", course[resolved], (y[resolved] == 0).astype(int),
                      {m: (s[:, 0] / (s[:, 0] + s[:, 2]))[resolved] for m, s in probs.items()}))
    with ZipFile(oulad) as z:
        info = pd.read_csv(z.open("studentInfo.csv"))
        reg = pd.read_csv(z.open("studentRegistration.csv"), na_values=["?"])
    keys = ["code_module", "code_presentation", "id_student"]
    dates = reg.set_index(keys).loc[pd.MultiIndex.from_frame(info[keys])].reset_index()
    eligible = dates.date_registration.le(0) & (dates.date_unregistration.isna() | dates.date_unregistration.gt(0))
    mask = info.code_presentation.eq("2014J") & eligible
    uk = pd.read_csv(run / "uk_later_cohort.csv.gz").set_index("row").sort_index()
    np.testing.assert_array_equal(uk.index, info.index[mask])
    assert uk.code_module.equals(info.code_module[mask]) and uk.final_result.equals(info.final_result[mask])
    test_ids = set(info.loc[info.code_presentation.eq("2014J"), "id_student"])
    historical = eligible & info.code_presentation.isin(["2013B", "2013J"]) & ~info.id_student.isin(test_ids)
    validation = historical & info.code_presentation.eq("2013J")
    train = historical & ~validation & ~info.id_student.isin(info.id_student[validation])
    audit_counts = json.loads((run / "uk_development.json").read_text())
    for field, subset in (("refit", historical), ("validation", validation), ("fit", train), ("test", mask)):
        assert audit_counts[field] == subset.sum()
    np.testing.assert_allclose(uk.prior, info.loc[historical, "final_result"].eq("Withdrawn").mean())
    rows.extend(cells("UK", "withdrawn", uk.code_module.to_numpy(), uk.final_result.eq("Withdrawn").to_numpy(int),
                      {m: uk[m] for m in [*FAMILIES, "prior"]}))
    scores = pd.DataFrame(rows)
    scores.to_csv(run / "course_scores.csv", index=False)
    summary = scores.groupby(["dataset", "target", "model"]).agg(
        n=("n", "sum"), courses=("course", "size"), nll=("nll", "mean"),
        mean_absolute_gap=("gap", lambda s: s.abs().mean())).reset_index()
    summary.to_csv(run / "robustness_summary.csv", index=False)
    primary = json.loads((run / "result.json").read_text())
    for m, value in primary["mean_course_nll"].items():
        observed = summary.loc[(summary.target == "original_resolved") & (summary.model == m), "nll"].item()
        np.testing.assert_allclose(value, observed, atol=1e-7)
    zero_units = source["Curricular units 1st sem (enrolled)"].eq(0)
    support = source.assign(zero_units=zero_units).groupby(["Course", "zero_units", "Target"]).size()
    support.rename("n").to_csv(run / "portugal_unit_support.csv")
    files = [portugal, oulad, Path(__file__), Path(__file__).with_name("robustness.py"),
             Path(__file__).with_name("sensitivity.md"), Path(__file__).with_name("evaluate.py"),
             Path(__file__).with_name("protocol.json")]
    files += [run / name for name in ("dev_trials.json", "predictions.csv", "result.json",
              "portugal_three_status.csv.gz", "uk_later_cohort.csv.gz", "uk_development.json",
              "course_scores.csv", "robustness_summary.csv", "portugal_unit_support.csv")]
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (run / "robustness_sha256.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("portugal", "oulad", "run"):
        parser.add_argument(arg, type=Path)
    args = parser.parse_args()
    audit(args.portugal, args.oulad, args.run)
