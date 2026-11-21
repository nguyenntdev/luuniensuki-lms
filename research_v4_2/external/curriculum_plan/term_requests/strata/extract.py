"""Summarize frozen timed outcomes. Run with Python 3 from any directory."""
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, median

root = Path(__file__).resolve().parents[1]
instances = json.loads((root / "confirmation/results.json").read_text())["instances"]
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(["instance", "source", "requests", "feasible", "infeasible", "unknown",
                 "interval_calls", "bounded_calls", "interval_over_bounded_time"])
for instance in instances:
    rows = instance["rows"]
    for source in ["pooled", *sorted({r["source"] for r in rows})]:
        group = [r["methods"] for r in rows if source == "pooled" or r["source"] == source]
        status = Counter(r["interval"]["status"] for r in group)
        calls = [sum(r[p]["stage"] == "solver" for r in group) for p in ("interval", "bounded")]
        times = [mean(median(r[p]["ns"]) for r in group) for p in ("interval", "bounded")]
        writer.writerow([instance["instance"], source, len(group), status["FEASIBLE"],
                         status["INFEASIBLE"], status["UNKNOWN"], *calls, f"{times[0]/times[1]:.8f}"])
