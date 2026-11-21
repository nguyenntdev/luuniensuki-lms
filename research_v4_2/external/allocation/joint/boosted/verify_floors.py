"""Independently check both precision definitions and report maximum captures."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify import check_frontier


def check(folder):
    study = json.loads((folder / "results.json").read_text())
    original = json.loads((Path(__file__).resolve().parents[1] / "run/frontier.json").read_text())
    for filename in ("frontier.json", "logistic_floor.json"):
        bounds = json.loads((folder / filename).read_text())
        for name, data in bounds.items():
            cases = study[name]["female_cases"], study[name]["male_cases"]
            floor = data["required_captures"]
            if filename == "logistic_floor.json":
                assert floor == original[name]["required_captures"]
            else:
                assert floor == data["unrestricted_captured"] - data["seats"] // 100
            for key in ("fixed_score_order", "free_within_group_order"):
                bound = data[key]
                check_frontier(bound, floor, cases)
                maximum = sum(max(f + m for _, f, m in options)
                              for options in bound["course_tables"].values())
                assert (maximum >= floor) == bool(bound["feasible_female_counts"])
                print(name, filename, key, "maximum", maximum, "required", floor)


if __name__ == "__main__":
    check(Path(sys.argv[1]))
