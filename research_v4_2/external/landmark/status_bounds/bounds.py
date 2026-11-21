"""Sharp capture bounds for an eligible-only score export and known stale admissions."""
import argparse
import csv
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "published_capacity"))
import replay


def capture(ranked, seats):
    if seats == 0:
        return 0.
    return replay.queue(ranked, sum(label for _, label in ranked), seats)["uniform_tie_true_positive"]


def report(supplement, uci):
    records, test, labels, disjoint = replay.source_roster(supplement, uci)
    scenarios = replay.status_coverage(records, test)
    seats = (len(test) + 9) // 10
    positives = sum(labels.values())
    for features, models in replay.METHODS.items():
        for model in models:
            scored = replay.ranked_predictions(supplement, features, model, labels, disjoint)
            assert all(0 < p < 1 for p, _ in scored)
            for case in scenarios:
                m = case["prior_exits_without_scores"]
                assert m == case["withdrawn_prior_exits_without_scores"]
                lo = capture(scored, max(0, seats-m))
                hi = capture(scored, seats)
                for p, expected in ((0.,hi),(1.,lo)):
                    completed = sorted(scored + [(p,0)]*m, reverse=True)
                    assert abs(capture(completed, seats) - expected) < 1e-10
                uniform = seats * positives / case["admitted"]
                yield (features,model,case["lag_days"] if case["lag_days"] is not None else "all",
                       seats,m,lo,hi,uniform,lo > uniform)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive_dir", type=Path)
    root = parser.parse_args().archive_dir
    subprocess.run(["sha256sum","--status","-c","design.sha256"], cwd=HERE, check=True)
    with replay.pinned_zip(root/"published_capacity/data-11-00281-s001.zip", replay.SUPPLEMENT_SHA256) as supplement, \
            replay.pinned_zip(root/"oulad.zip", replay.UCI_SHA256) as uci:
        w = csv.writer(sys.stdout, lineterminator="\n")
        w.writerow(("features","model","lag_days","seats","unscored_prior_exits","capture_lower","capture_upper","uniform_expected","always_above_uniform"))
        w.writerows(report(supplement,uci))
