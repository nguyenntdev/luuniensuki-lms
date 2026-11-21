"""Select client mixture weights on earlier predictions and score the archived later cohort."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from scipy.special import expit, logit
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent / "shadow" / "run"
WEIGHTS = (0, .25, .5, .75, 1)
KEYS = ["row", "learner", "code_module", "code_presentation", "y"]


def placements(prob, y):
    positive, negative = prob[y == 1], prob[y == 0]
    def midrank(reference, values):
        ordered = np.sort(reference)
        return (ordered.searchsorted(values, "left") + ordered.searchsorted(values, "right")) / 2
    wins = midrank(negative, positive)
    return wins.sum() / (len(negative) * len(positive)), (wins / len(negative),
            1 - midrank(positive, negative) / len(positive))


def select(cal, offsets):
    y = cal.y.to_numpy()
    raw = cal[["raw_local", "raw_transfer"]].to_numpy()
    local, transfer = expit(logit(raw.clip(1e-10, 1-1e-10)) + offsets).T
    estimates = {w: placements(local + w * (transfer - local), y) for w in WEIGHTS}
    winner = min(WEIGHTS, key=lambda w: (-estimates[w][0], abs(w-.5), w))
    base_auc, base_places = estimates[.5]
    candidates = []
    for w, (auc, places) in estimates.items():
        variance = sum((a - b).var(ddof=1) / len(a) for a, b in zip(places, base_places))
        width = norm.isf(.025 / 4) * np.sqrt(variance)
        candidates.append(dict(weight=w, auc=auc, gain=auc-base_auc, lower=auc-base_auc-width,
                               upper=auc-base_auc+width))
    lower = candidates[WEIGHTS.index(winner)]["lower"]
    return dict(calibration_rows=len(y), positives=int(y.sum()), ungated=winner,
                gated=winner if lower > 0 else .5, candidates=candidates)


def run(output):
    subprocess.run(["sha256sum", "-c", "protocol.sha256"], cwd=HERE, check=True)
    cal = pd.read_csv(ARCHIVE / "calibration.csv.gz", float_precision="round_trip").query("roster == 'mlp'")
    later = pd.read_csv(ARCHIVE / "predictions.csv.gz", float_precision="round_trip")
    keys = pd.read_csv(HERE.parent / "run" / "predictions.csv.gz", usecols=KEYS)
    pd.testing.assert_frame_equal(later[KEYS], keys)
    assert list(later.columns[:5]) == KEYS and len(later.columns[5:]) == 31
    assert len(later) == 8815 and later.row.is_unique and cal.row.is_unique
    assert set(cal.row).isdisjoint(later.row) and set(cal.code_module) == set(later.code_module)
    meta = json.loads((ARCHIVE / "gate.json").read_text())["gate"]
    np.testing.assert_allclose(later.mlp_local + .5*(later.mlp_transfer - later.mlp_local),
                               later.mlp_half, rtol=0, atol=2e-16)
    decisions = {}
    forecasts = later[KEYS].copy()
    for module, group in cal.groupby("code_module"):
        config = meta["mlp/" + module]
        assert config["cal_rows"] == len(group)
        decision = select(group, config["offsets"])
        decisions[module] = decision
        mask = later.code_module == module
        for policy in ("gated", "ungated"):
            weight = decision[policy]
            if weight in (0, .5, 1):
                column = {0: "mlp_local", .5: "mlp_half", 1: "mlp_transfer"}[weight]
                values = later.loc[mask, column]
            else:
                local = later.loc[mask, "mlp_local"]
                values = local + weight * (later.loc[mask, "mlp_transfer"] - local)
            forecasts.loc[mask, policy] = values
    assert forecasts.notna().all().all()
    output.mkdir(parents=True, exist_ok=True)
    forecasts.to_csv(output / "predictions.csv.gz", index=False, compression={"method":"gzip","mtime":0})
    (output / "weights.json").write_text(json.dumps(decisions, indent=2) + "\n")
    with TemporaryDirectory() as tmp:
        merged = later.join(forecasts[["gated", "ungated"]])
        merged.to_csv(Path(tmp) / "predictions.csv.gz", index=False)
        subprocess.run([sys.executable, str(HERE.parent / "score.py"), tmp, "gated"], check=True)
        for filename in ("summary.json", "scores.csv"):
            (output / filename).write_bytes((Path(tmp) / filename).read_bytes())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    run(parser.parse_args().output)
