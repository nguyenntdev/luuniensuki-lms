"""Independent checks of the saved labels, acceptance masks and time boundary."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
import pytest

from research_v4_2.external.coverage.evaluate import evaluate
from research_v4_2.external.coverage.secondary import KEY, load_oulad

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RESULTS = json.loads((HERE / "secondary_run/results.json").read_text())


@pytest.mark.parametrize("name", ["oulad", "uci"])
def test_policy_counts_and_curve(name):
    path = HERE / "secondary_run" / f"{name}_predictions.csv"
    result = RESULTS[name]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == result["predictions_sha256"]
    pred = pd.read_csv(path, float_precision="round_trip")
    assert pred.source_row.is_unique
    accepted = pred.gate.ne("ABSTAIN")
    assert accepted.equals(pred.max_probability.ge(result["thresholds"]["tau_conf"]))
    assert accepted.sum() == result["accepted"]
    right = pred.argmax.eq(pred.truth)
    gate_right = pred.gate.eq(pred.truth)
    assert (accepted & gate_right).sum() == result["gate_correct"]
    assert (accepted & right).sum() == result["argmax_correct_same_cases"]
    assert right.sum() == result["full_argmax_correct"]
    assert np.isclose(gate_right[accepted].mean() - right.mean(),
                      result["label_effect"] + result["selection_effect_vs_full"])
    ranked = pred.sort_values(["max_probability", "source_row"], ascending=[False, True])
    assert set(ranked.source_row.iloc[:accepted.sum()]) == set(pred.loc[accepted, "source_row"])
    for point in result["risk_curve"]:
        selected = ranked.iloc[:point["accepted"]]
        assert np.isclose(point["argmax_risk"], selected.argmax.ne(selected.truth).mean())
        assert np.isclose(point["reroute_risk"], selected.rerouted_at_full_coverage.ne(selected.truth).mean())


def test_click_window(tmp_path):
    path = tmp_path / "window.zip"
    with ZipFile(path, "w") as archive:
        key = ",".join(KEY)
        archive.writestr("studentInfo.csv", key + ",final_result\nBBB,2014J,1,Pass\n")
        archive.writestr("studentRegistration.csv", key + ",date_registration,date_unregistration\nBBB,2014J,1,0,?\n")
        archive.writestr("studentVle.csv", key + ",date,sum_click\n" + "".join(
            f"BBB,2014J,1,{day},{clicks}\n" for day, clicks in [(-1, 111), (0, 2), (60, 4), (61, 222)]))
    row = load_oulad(path).iloc[0]
    assert (row.early_click_total, row.early_active_sites) == (6, 2)


def test_future_holdout_matches_public_registrations():
    path = ROOT / "private_data/raw/oulad/2013-2014/oulad.zip"
    if not path.exists():
        pytest.skip("Source-level validation requires the OULAD archive")
    with ZipFile(path) as archive:
        info = pd.read_csv(archive.open("studentInfo.csv"))
        reg = pd.read_csv(archive.open("studentRegistration.csv"), na_values=["?"])
    new = info.code_presentation.eq("2014J") & ~info.id_student.isin(
        info.loc[info.code_presentation.ne("2014J"), "id_student"])
    eligible = reg.date_registration.le(60) & (reg.date_unregistration.isna() | reg.date_unregistration.gt(60))
    expected = info.loc[new].join(reg.loc[eligible].set_index(KEY)[[]], on=KEY, how="inner").sort_index()
    pred = pd.read_csv(HERE / "secondary_run/oulad_predictions.csv").set_index("source_row").sort_index()
    assert expected.index.tolist() == pred.index.tolist()
    assert expected.final_result.tolist() == pred.truth.tolist()


def test_frozen_counts():
    assert evaluate(ROOT / "research_artifacts_v3/runs/p01") == json.loads((HERE / "result.json").read_text())
