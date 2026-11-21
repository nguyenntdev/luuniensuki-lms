"""Audit selected columns directly against the source rows and print the study tables."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean, median

HERE = Path(__file__).resolve().parent
METHODS = ("greedy", "pruned", "exchange", "zhu_11", "zhu_29", "zhu_47")
FAMILIES = {"4": 10, "5": 10, "6": 5, "a": 5, "b": 5, "c": 5, "d": 5}


def require(ok, detail):
    if not ok:
        raise ValueError(detail)


def verify_instance(raw, name, instance, dual):
    """Independent integer stream parser. Check original row memberships, bypassing bitsets."""
    require(hashlib.sha256(raw).hexdigest() == instance["sha256"], name + " digest")
    tokens = list(map(int, raw.split()))
    m, n = tokens[:2]
    require((m, n) == (instance["rows"], instance["columns"]), name + " shape")
    costs = tokens[2:n + 2]
    cursor = n + 2
    rows = []
    for i in range(m):
        count = tokens[cursor]
        ids = set(tokens[cursor + 1:cursor + 1 + count])
        require(len(ids) == count and ids and min(ids) >= 1 and max(ids) <= n, name + " row")
        rows.append(ids)
        cursor += 1 + count
    require(cursor == len(tokens) and sum(map(len, rows)) == instance["incidences"], name + " size")
    numerators = dual["row_numerators"]
    denom = dual["denominator"]
    require(type(denom) is int and denom > 0 and len(numerators) == m and
            all(type(y) is int and y >= 0 for y in numerators), name + " dual variables")
    spent = [0] * n
    for y, row in zip(numerators, rows):
        for j in row:
            spent[j-1] += y
    require(all(total <= denom*cost for total, cost in zip(spent, costs)), name + " dual infeasible")
    require((sum(numerators) + denom - 1)//denom == dual["integer_lower_bound"] <= instance["reference"],
            name + " dual bound")
    require(set(METHODS) == set(instance["runs"]), name + " methods")
    for method, result in instance["runs"].items():
        cols = result["columns_one_based"]
        chosen = set(cols)
        require(all(type(j) is int and 1 <= j <= n for j in cols) and len(chosen) == len(cols),
                f"{name} {method} columns")
        require(all(row & chosen for row in rows), f"{name} {method} uncovered")
        require(sum(costs[j-1] for j in cols) == result["cost"] >= instance["reference"],
                f"{name} {method} cost")
        require(0 < result["cpu_seconds"] < 90, f"{name} {method} CPU")
    trace = instance["runs"]["exchange"]["accepted_costs"]
    require(trace[0] == instance["runs"]["pruned"]["cost"] and
            trace[-1] == instance["runs"]["exchange"]["cost"] and
            all(a > b for a, b in zip(trace, trace[1:])), name + " exchange trace")


def audit_study():
    cli = argparse.ArgumentParser()
    cli.add_argument("matrices", type=Path)
    cli.add_argument("--csv", type=Path)
    cli.add_argument("--evidence", type=Path, default=HERE)
    args = cli.parse_args()
    datasets = [json.loads((args.evidence / f).read_text())["instances"] for f in ("runs.json", "extended.json")]
    duals = json.loads((args.evidence / "dual.json").read_text())
    original = json.loads((HERE.parent / "result.json").read_text())["instances"]
    names = [f"scp{family}{i}" for family, count in FAMILIES.items() for i in range(1, count+1)]
    require(all(set(data) == set(names) for data in datasets), "incomplete family")
    records = []
    for name in names:
        short, long = (data[name] for data in datasets)
        raw = (args.matrices / (name + ".txt")).read_bytes()
        for inst in (short, long):
            verify_instance(raw, name, inst, duals[name])
        require(short["reference"] == long["reference"], name + " reference")
        for key in METHODS[:3]:
            require(short["runs"][key]["columns_one_based"] == long["runs"][key]["columns_one_based"],
                    name + " deterministic repeat")
        if name in original:
            old = original[name]
            require(old["sha256"] == short["sha256"] and old["solver_bound"] == short["reference"],
                    name + " initial certificate")
            for prev, cur in [("greedy", "greedy"), ("greedy_pruned", "pruned")]:
                require(old["solutions"][prev]["columns_one_based"] == short["runs"][cur]["columns_one_based"],
                        name + " initial witness")
        entry = {"family": name[3].upper(), "instance": name, "reference": short["reference"]}
        entry["dual_lower_bound"] = duals[name]["integer_lower_bound"]
        entry.update({k: short["runs"][k]["cost"] for k in METHODS[:3]})
        for label, data in [("short", short), ("extended", long)]:
            seeds = [data["runs"][key]["cost"] for key in METHODS[3:]]
            entry.update({label+"_"+stat: fn(seeds) for stat, fn in
                          [("min", min), ("median", median), ("max", max)]})
        records.append(entry)
    if args.csv:
        with args.csv.open("w", newline="") as fp:
            writer = csv.DictWriter(fp, records[0].keys(), lineterminator="\n")
            writer.writeheader()
            writer.writerows(records)
    for family in FAMILIES:
        group = [r for r in records if r["family"] == family.upper()]
        methods = ("greedy", "pruned", "exchange", "short_median", "extended_median")
        gaps = [mean(100*(r[k]-r["reference"])/r["reference"] for r in group) for k in methods]
        delta = [r["exchange"]-r["extended_median"] for r in group]
        print(f"| {family.upper()} | {len(group)} |", " | ".join(f"{v:.2f}" for v in gaps),
              f"| {sum(d<0 for d in delta)}/{delta.count(0)}/{sum(d>0 for d in delta)} |")
    print("Verified", len(records), "matrices and", len(records) * len(METHODS) * 2, "witnesses.")


if __name__ == "__main__":
    audit_study()
