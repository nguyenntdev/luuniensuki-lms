"""Charge archived setup across alternative numbers of distinct cancellations."""
from collections import defaultdict
import csv
from math import ceil
from pathlib import Path
from statistics import geometric_mean, median
import sys

BASE = Path(__file__).resolve().parents[1] / "route_memo"


def calculate(root, run, workload):
    setup = defaultdict(list)
    samples = defaultdict(lambda: defaultdict(list))
    with (root / workload / "setup.csv").open() as f:
        for row in csv.DictReader(f):
            setup[row["method"]].append(int(row["ns"]))
    with (root / workload / "latency.csv").open() as f:
        for row in csv.DictReader(f):
            samples[row["method"]][int(row["scenario"])].append(int(row["ns"]))
    assert len(setup) == len(samples) == 4
    for method, scenarios in samples.items():
        assert len(scenarios) == 48 and len(setup[method]) == 7
        assert all(len(reps) == 15 for reps in scenarios.values())
        cost = median(setup[method])
        for horizon in (1, 8, 48, 128, 512):
            times = sorted(median(reps) + cost / horizon for reps in scenarios.values())
            yield (run, workload, horizon, method, round(times[ceil(.95*len(times))-1]/1000, 3),
                   round(geometric_mean(times)/1000, 3))


if __name__ == "__main__":
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(("run", "workload", "updates", "method", "p95_us", "geomean_us"))
    for name, root in (("initial", BASE), ("repeat", BASE / "repeat")):
        for workload in ("original", "bursts"):
            writer.writerows(calculate(root, name, workload))
