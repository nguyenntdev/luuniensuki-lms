"""Cache fitted development trials atomically while running the frozen evaluator."""
import argparse
import hashlib
import json
import os
import pickle
import platform
import sys
import tempfile
from pathlib import Path

import study

cli = argparse.ArgumentParser(description=__doc__)
cli.add_argument("out", type=Path)
cli.add_argument("cache", type=Path)
cli.add_argument("--prefit-depth8", choices=["weighted", "unweighted"],
                 help="Prepare one expensive registered fit in the same cache, then exit.")
args = cli.parse_args()
settings = {
    "source": {p.name: study.digest(p) for p in [
        Path(study.__file__), study.ROOT / "protocol.md", study.ARCHIVE, study.REFERENCE]},
    "python": platform.python_version(),
    "versions": [m.__version__ for m in (
        study.np, study.sklearn, study.scipy, study.catboost, study.pd)],
}
run_hash = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
cache = args.cache / run_hash
cache.mkdir(parents=True, exist_ok=True)
original_fit = study.fit


def recoverable_fit(train, name, setting, reference):
    key = hashlib.sha256(json.dumps([name, setting]).encode()).hexdigest()
    target = cache / f"{name}_{key}.pkl"
    if target.exists():
        with target.open("rb") as saved:
            return pickle.load(saved)
    fitted = original_fit(train, name, setting, reference)
    with tempfile.NamedTemporaryFile(dir=cache, prefix="partial_", delete=False) as handle:
        pickle.dump(fitted, handle)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(handle.name, target)
    return fitted


def prefit(train, name, setting, reference):
    if name != "constant":
        raise RuntimeError("Unexpected first trial in frozen development grid")
    recoverable_fit(train, "matched_catboost", (8, 800, args.prefit_depth8 == "weighted"), reference)
    raise SystemExit(0)


study.fit = prefit if args.prefit_depth8 else recoverable_fit
sys.argv = [study.__file__, "train", str(args.out)]
study.main()
