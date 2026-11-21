"""Refit released P01 on historical OULAD and audit its decisions on 2014J."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from research_v3.methods.p01.features import (
    CATEGORICAL_FIELDS, NUMERIC_FIELDS, build_vocabulary, featurize_rows,
)
from research_v3.methods.p01.models import (
    _conservative_quantile, calibrate_gate, fit_classical, predict_batch,
)
from research_v3.methods.p01.types import ABSTAIN, ModelConfig

KEY = ["code_module", "code_presentation", "id_student"]
RAW = Path("private_data/raw")
HERE = Path(__file__).resolve().parent
SEED = 20261121


def bucket(value):
    return int.from_bytes(hashlib.sha256(str(value).encode()).digest()[:8], "big") % 100


def load_oulad(path):
    with ZipFile(path) as archive:
        info = pd.read_csv(archive.open("studentInfo.csv"), keep_default_na=False)
        reg = pd.read_csv(archive.open("studentRegistration.csv"), na_values=["?"])
        frame = info.merge(reg, on=KEY, how="left", validate="one_to_one", indicator=True)
        assert frame["_merge"].eq("both").all()
        chunks = []
        with archive.open("studentVle.csv") as source:
            for part in pd.read_csv(source, chunksize=250_000):
                early = part.loc[part.date.between(0, 60)]
                chunks.append(early.groupby(KEY).sum_click.agg(["sum", "size"]))
        activity = pd.concat(chunks).groupby(level=KEY).sum()
    frame = frame.join(activity, on=KEY).rename(
        columns={"sum": "early_click_total", "size": "early_active_sites"})
    for col in ["early_click_total", "early_active_sites"]:
        frame[col] = frame[col].fillna(0).astype(int)
    return frame


def records(frame, training=False):
    fields = list(CATEGORICAL_FIELDS + NUMERIC_FIELDS)
    rows = [{"case_id": str(i), "input": f}
            for i, f in zip(frame.index, frame[fields].to_dict("records"), strict=True)]
    if training:
        for row, label in zip(rows, frame.final_result, strict=True):
            row["label"] = label
    return rows


def oulad(path):
    frame = load_oulad(path)
    assert set(frame.code_presentation) == {"2013B", "2013J", "2014B", "2014J"}
    future = frame.code_presentation.eq("2014J")
    seen = frame.id_student.isin(frame.loc[~future, "id_student"])
    active = (frame.date_registration.le(60) &
              (frame.date_unregistration.isna() | frame.date_unregistration.gt(60)))
    history = frame.code_presentation.isin(["2013B", "2013J"]) & active
    held = frame.id_student.map(bucket) >= 80
    train, cal, test = frame[history & ~held], frame[history & held], frame[future & ~seen & active]
    groups = [set(sub.id_student) for sub in (train, cal, test)]
    assert not (groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2])
    assert set(test.code_presentation) == {"2014J"}
    train_rows, cal_rows, cases = records(train, True), records(cal, True), records(test)
    cfg = ModelConfig()
    vocab = build_vocabulary(train_rows)
    model = fit_classical(train_rows, vocab, config=cfg)
    thresholds = calibrate_gate(cal_rows, model.predict_proba(featurize_rows(cal_rows, vocab)), config=cfg)
    params = dict(model_id="secondary_rc_stg", vocabulary=vocab, weights=model.weights,
                  bias=model.bias, thresholds=thresholds.to_dict())
    gate = predict_batch(cases, params)
    base = predict_batch(cases, dict(params, gate_mode="no_gate"))
    reroute = predict_batch(cases, dict(params, gate_mode="no_abstention"))
    result, pred = audit(test, test.final_result, test.id_student, base.decisions, base.scores,
                         gate.decisions, reroute.decisions, thresholds.tau_conf, "Fail")
    result.update(thresholds=thresholds.to_dict(), train=len(train), calibration=len(cal),
                  total_2014J=int(future.sum()), active_2014J=int((future & active).sum()),
                  previously_seen_active_2014J=int((future & active & seen).sum()),
                  counts_by_module=test.code_module.value_counts().to_dict(),
                  withdrawn_without_date=int((test.final_result.eq("Withdrawn") &
                                              test.date_unregistration.isna()).sum()))
    return result, pred


def uci(path):
    with ZipFile(path) as archive:
        frame = pd.read_csv(archive.open("data.csv"), sep=";")
    split = frame.index.map(bucket)
    train, cal, test = frame[split < 60], frame[(split >= 60) & (split < 80)], frame[split >= 80]
    features = ["Admission grade", "Previous qualification (grade)", "Age at enrollment", "Application order"]
    model = make_pipeline(StandardScaler(), LogisticRegression(C=1, max_iter=1000))
    model.fit(train[features], train.Target)
    labels = model.classes_
    assert set(labels) == {"Dropout", "Enrolled", "Graduate"}
    fail = list(labels).index("Dropout")
    pc = model.predict_proba(cal[features])
    correct = labels[pc.argmax(axis=1)] == cal.Target.to_numpy()
    cfg = ModelConfig()
    tau = _conservative_quantile(sorted(pc[correct].max(axis=1)), 1 - cfg.alpha_conf)
    alarm = _conservative_quantile(sorted(pc[cal.Target.ne("Dropout"), fail]), 1 - cfg.alpha_fail)
    probs = model.predict_proba(test[features])
    score = probs.max(axis=1)
    base = labels[probs.argmax(axis=1)]
    reroute = np.where(probs[:, fail] >= alarm, "Dropout", base)
    gate = np.where(score >= tau, reroute, ABSTAIN)
    result, pred = audit(test, test.Target, test.index, base, score, gate, reroute, tau, "Dropout")
    result.update(thresholds=dict(tau_conf=tau, tau_fail=alarm), train=len(train), calibration=len(cal))
    return result, pred


def paired_intervals(groups, accept, base_ok, gate_ok):
    """Resample entire test learners, preserving each policy's paired observations."""
    ids = pd.factorize(groups)[0]
    contributions = np.column_stack([
        np.bincount(ids, weights=values) for values in
        (np.ones(len(ids)), accept, gate_ok & accept, base_ok & accept, base_ok)
    ])
    draws = []
    rng = np.random.default_rng(SEED)
    for _ in range(2000):
        n, k, g, b, all_b = contributions[rng.integers(len(contributions), size=len(contributions))].sum(axis=0)
        if k:
            draws.append([k/n, 1-g/k, 1-b/k, (g-b)/k, b/k-all_b/n, g/k-all_b/n])
    names = ["coverage", "gate_risk", "same_cases_argmax_risk", "label_effect",
             "selection_effect_vs_full", "total_effect_vs_full"]
    return dict(zip(names, np.percentile(draws, [2.5, 97.5], axis=0).T.tolist(), strict=True))


def curve_intervals(groups, order, base_ok, reroute_ok, capacities):
    """Rerank bootstrap cohorts by the original scores and refill each capacity."""
    group_index = pd.factorize(groups)[0][order]
    n_groups = group_index.max() + 1
    errors = np.column_stack((~base_ok[order], ~reroute_ok[order]))
    rng = np.random.default_rng(SEED)
    draws = []
    for _ in range(2000):
        multiplicity = np.bincount(rng.integers(n_groups, size=n_groups), minlength=n_groups)
        weights = multiplicity[group_index]
        cumulative = np.cumsum(weights)
        k = np.maximum(1, (cumulative[-1] * capacities).astype(int))
        last = np.searchsorted(cumulative, k)
        totals = np.cumsum(weights[:, None] * errors, axis=0)[last]
        totals -= (cumulative[last] - k)[:, None] * errors[last]
        risk = totals / k[:, None]
        draws.append(np.column_stack((risk, risk[:, 1] - risk[:, 0])))
    return np.percentile(draws, [2.5, 97.5], axis=0).transpose(1, 2, 0)


def audit(test, truth, groups, base, scores, gate, reroute, tau, alarm_label):
    truth, base, scores, gate, reroute = map(np.asarray, (truth, base, scores, gate, reroute))
    accept = gate != ABSTAIN
    assert np.array_equal(accept, scores >= tau)
    assert np.array_equal(gate[accept], reroute[accept])
    order = np.argsort(-scores, kind="stable")
    k = int(accept.sum())
    assert np.array_equal(np.sort(order[:k]), np.flatnonzero(accept))
    b, g = base == truth, gate == truth
    label_effect = float(g[accept].mean() - b[accept].mean())
    selection = float(b[accept].mean() - b.mean())
    delta = float(g[accept].mean() - b.mean())
    assert np.isclose(delta, label_effect + selection)
    risk_curve = []
    capacities = np.array([.10, .25, .50, .75, 1.])
    bands = curve_intervals(groups, order, b, reroute == truth, capacities)
    for capacity, band in zip(capacities, bands, strict=True):
        which = order[:int(len(test)*capacity)]
        risk_curve.append(dict(accepted=len(which), coverage=len(which)/len(test),
                               argmax_risk=float((~b[which]).mean()),
                               reroute_risk=float((reroute[which] != truth[which]).mean()),
                               argmax_interval95=band[0].tolist(), reroute_interval95=band[1].tolist(),
                               risk_difference_interval95=band[2].tolist()))
    pred = pd.DataFrame(dict(source_row=test.index, learner_cluster=pd.factorize(groups)[0],
                             truth=truth, argmax=base, max_probability=scores, gate=gate,
                             rerouted_at_full_coverage=reroute))
    result = dict(test=len(test), test_learners=len(set(groups)), accepted=k, coverage=k/len(test),
                  gold_counts=pd.Series(truth).value_counts().to_dict(),
                  gate_correct=int(g[accept].sum()), argmax_correct_same_cases=int(b[accept].sum()),
                  full_argmax_correct=int(b.sum()), full_argmax_risk=float((~b).mean()),
                  gate_risk=float((~g[accept]).mean()), same_cases_argmax_risk=float((~b[accept]).mean()),
                  label_disagreements=int((gate[accept] != base[accept]).sum()),
                  corrections=int((accept & g & ~b).sum()), spoiled=int((accept & ~g & b).sum()),
                  changed_both_wrong=int((accept & (base != gate) & ~g & ~b).sum()),
                  accepted_true_alarm=int((accept & (truth == alarm_label)).sum()),
                  label_effect=label_effect, selection_effect_vs_full=selection,
                  total_effect_vs_full=delta, top_k_selector_different_ids=0,
                  interval95=paired_intervals(groups, accept, b, g), risk_curve=risk_curve)
    return result, pred


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oulad", type=Path, default=RAW/"oulad/2013-2014/oulad.zip")
    parser.add_argument("--uci", type=Path, default=RAW/"uci/dropout-697/source.zip")
    parser.add_argument("--out", type=Path, default=HERE/"secondary_run")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    results = {}
    with threadpool_limits(1):
        for name, path, run in [("oulad", args.oulad, oulad), ("uci", args.uci, uci)]:
            result, predictions = run(path)
            result["archive_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            out = args.out / f"{name}_predictions.csv"
            predictions.to_csv(out, index=False, float_format="%.17g")
            result["predictions_sha256"] = hashlib.sha256(out.read_bytes()).hexdigest()
            results[name] = result
    (args.out/"results.json").write_text(json.dumps(results, indent=2, sort_keys=True, allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
