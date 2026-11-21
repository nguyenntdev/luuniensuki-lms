"""Join the returned GPU forecasts to locally held outcomes, then use the parent scorer."""
import argparse
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd


def score(staging, output):
    parent = Path(__file__).resolve().parent.parent
    keys = ["row", "learner", "code_module", "code_presentation", "y"]
    labels = pd.read_csv(staging/"labels.csv")
    archived = pd.read_csv(parent/"schedule/run/predictions.csv.gz")
    controls = ["previous_weak_ridge", "mlp_half"]
    assert labels[keys].equals(archived[keys])
    forecasts = pd.read_csv(staging/"forecasts.csv").rename(columns={"hier_temporal":"adapted"})
    expected = ["row","hier_totals","boost_totals","adapted","local","shared","boost_temporal"]
    assert set(forecasts.columns) == set(expected)
    combined = archived[keys+controls].merge(forecasts, on="row", validate="one_to_one", how="left")
    probabilities = combined.drop(columns=keys).to_numpy()
    assert len(forecasts) == len(combined) == 8815 and np.all((probabilities > 0) & (probabilities < 1))
    output.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output/"predictions.csv.gz", index=False, compression={"method":"gzip","mtime":0})
    subprocess.run([sys.executable, str(parent/"score.py"), str(output)], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("staging", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    score(args.staging, args.output)
