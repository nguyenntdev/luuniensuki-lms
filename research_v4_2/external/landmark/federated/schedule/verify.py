"""Assemble paired forecasts, score them and verify against the official archive."""
import sys
import subprocess
from pathlib import Path
import pandas as pd
import numpy as np

here = Path(__file__).resolve().parent
parent = here.parent
run = here / "run"
dev = pd.read_csv(sys.argv[1])
keys = list(dev.columns[:5])
controls = pd.read_csv(parent / "shadow/run/predictions.csv.gz")
pairs = dev.merge(controls[keys + ["previous_weak_ridge", "mlp_half", "previous_adapted"]],
                  on=keys, validate="one_to_one")
assert len(pairs) == len(dev) == len(controls)
np.testing.assert_allclose(pairs.matched, pairs.pop("previous_adapted"), atol=1e-12, rtol=0)
pairs.to_csv(run / "predictions.csv.gz", index=False, compression={"method":"gzip", "mtime":0})
(run / "counts.csv").write_bytes((parent / "run/counts.csv").read_bytes())
subprocess.run([sys.executable, parent / "score.py", run], check=True)
subprocess.run(["node", parent / "verify.mjs", sys.argv[2], run], check=True)
