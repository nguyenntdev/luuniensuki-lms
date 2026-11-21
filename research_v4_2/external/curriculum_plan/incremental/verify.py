"""Validate decisions using independently certified catalog witnesses."""
import csv
import json
import subprocess
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
parent = here.parent
subprocess.run([sys.executable, parent / "verify.py", "private_data/raw/otago-prereqs/release.zip",
                parent / "run"], check=True)
with (parent / "run/repairs.csv").open() as f:
    expected = {(r["table"], r["targets"]): r["witness"] for r in csv.DictReader(f)}
totals = {}
with (here / "episodes.csv").open() as f:
    for r in csv.DictReader(f):
        assert r["witness"] == expected.pop((r["table"], r["targets"]))
        counts = {k: int(r[k]) for k in ("setup", "incremental", "cold_pruned", "cold_plain")}
        assert counts["setup"] + counts["incremental"] == counts["cold_pruned"] <= counts["cold_plain"]
        table = totals.setdefault(r["table"], {})
        for key, value in dict(episodes=1, **counts).items():
            table[key] = table.get(key, 0) + value
assert not expected and totals == json.loads((here / "results.json").read_text())
print("All incremental witnesses and aggregate counts verified.")
