"""Audit the pinned day-84 prediction exports without fitting any models."""

import argparse
import csv
import hashlib
import io
import json
import math
from itertools import groupby
from pathlib import Path
from zipfile import ZipFile

DAY = 84
TERM = "2014J"
KEY = ("code_module", "code_presentation", "id_student")
SUPPLEMENT_SHA256 = "5904a9d351047cd96cf9715d9b42dbfd6b59093a93b7f3c82bcafb9f22baf85b"
UCI_SHA256 = "f2ed1902616c1fe8d2824d872c0b7d2d72be435bf0124d077044fe4be2c6d3e4"
METHODS = {
    "Assessment": ("Logistic regression", "Random forest", "XGBoost"),
    "Score-free": ("Logistic regression", "Random forest", "XGBoost"),
    "Assessment + VLE": ("Logistic regression",),
    "Score-free + VLE": ("Logistic regression",),
}
SOURCE_TABLES = {
    "assessments.csv", "courses.csv", "studentAssessment.csv", "studentInfo.csv",
    "studentRegistration.csv", "studentVle.csv", "vle.csv",
}


def require(test, message):
    if not test:
        raise ValueError(message)


def sha256(stream):
    return hashlib.file_digest(stream, "sha256").hexdigest()


def pinned_zip(path, expected):
    with path.open("rb") as stream:
        require(sha256(stream) == expected, f"Unexpected archive hash for {path.name}")
    return ZipFile(path)


def rows(archive, member):
    with archive.open(member) as raw, io.TextIOWrapper(raw, encoding="utf-8", newline="") as stream:
        yield from csv.DictReader(stream)


def indexed(archive, member):
    records = {}
    for row in rows(archive, member):
        key = tuple(row[column] for column in KEY)
        require(all(key) and key not in records, f"Missing or duplicate key in {member}")
        records[key] = row
    return records


def date(value):
    return int(value.removesuffix(".0")) if value not in {"", "?"} else None


def dates(row):
    return date(row["date_registration"]), date(row["date_unregistration"])


def current_exit(end):
    return end is None or end > DAY


def check_fields(published, calculated, context):
    for field, value in calculated.items():
        require(math.isclose(float(published[field]), value, rel_tol=0, abs_tol=1e-12),
                f"{context}: mismatch in {field}")


def source_roster(archive, uci):
    manifest = json.loads(archive.read("results/environment.json"))["source_sha256"]
    require(manifest.keys() == SOURCE_TABLES, "Unexpected source hash inventory")
    for table, expected in sorted(manifest.items()):
        with archive.open(f"source/{table}") as furnished, uci.open(table) as reference:
            require(sha256(furnished) == expected, f"Author manifest mismatch in {table}")
            require(sha256(reference) == expected, f"UCI source mismatch in {table}")

    registrations = indexed(uci, "studentRegistration.csv")
    outcomes = indexed(uci, "studentInfo.csv")
    require(registrations.keys() == outcomes.keys(), "Registration/outcome keys differ")
    records = {}
    for key, row in registrations.items():
        start, end = dates(row)
        result = outcomes[key]["final_result"]
        require(result in {"Withdrawn", "Fail", "Pass", "Distinction"},
                "Unexpected final result")
        records[key] = (start, end, result)

    raw_active = {key: row for key, row in records.items() if current_exit(row[1])}
    active = {key: row for key, row in raw_active.items()
              if row[0] is not None and row[0] <= DAY}
    eligibility = next(r for r in rows(archive, "results/eligibility_audit.csv")
                       if int(r["cutoff"]) == DAY)
    check_fields(eligibility, {
        "withdrawal_eligible": len(raw_active),
        "registration_after_cutoff": sum(row[0] is not None and row[0] > DAY
                                         for row in raw_active.values()),
        "missing_registration": sum(row[0] is None for row in raw_active.values()),
        "eligible_n": len(active),
    }, "Day-84 eligibility audit")

    analysis = indexed(archive, f"results/analysis_day{DAY}.csv")
    require(analysis.keys() == active.keys(), "Day-84 analytical roster keys differ")
    for key, row in analysis.items():
        start, end, result = active[key]
        require((*dates(row), row["final_result"]) == (start, end, result)
                and int(row["withdraw_after_cutoff"]) == (result == "Withdrawn"),
                "Day-84 analytical roster has a date or outcome discrepancy")

    test = {key: row for key, row in active.items() if key[1] == TERM}
    labels = {key: int(row[2] == "Withdrawn") for key, row in test.items()}
    prior_students = {key[2] for key in records if key[1] != TERM}
    disjoint = {key: key[2] not in prior_students for key in test}
    summary = next(r for r in rows(archive, "results/stage_summary.csv")
                   if int(r["cutoff"]) == DAY)
    check_fields(summary, {
        "active_enrolments": len(active),
        "future_withdrawals": sum(row[2] == "Withdrawn" for row in active.values()),
        "test_n": len(test),
        "test_events": sum(labels.values()),
    }, "Day-84 stage summary")
    overlap = next(r for r in rows(archive, "results/student_overlap.csv")
                   if int(r["cutoff"]) == DAY)
    check_fields(overlap, {
        "test_n": len(test),
        "test_students": len({key[2] for key in test}),
        "disjoint_test_n": sum(disjoint.values()),
        "disjoint_test_students": len({key[2] for key in test if disjoint[key]}),
        "disjoint_positives": sum(label for key, label in labels.items() if disjoint[key]),
    }, "Day-84 student overlap audit")
    return records, test, labels, disjoint


def ranked_predictions(archive, scenario, model, labels, disjoint):
    slug = f"{scenario.lower().replace(' + ', '_plus_').replace('-', '_')}_{model.lower()}"
    member = f"results/predictions_day{DAY}_{slug.replace(' ', '_')}.csv"
    predictions = indexed(archive, member)
    require(predictions.keys() == labels.keys(), f"Risk set mismatch in {member}")
    scores = []
    for key, row in predictions.items():
        require(int(row["withdraw_after_cutoff"]) == labels[key], f"Outcome mismatch in {member}")
        require(row["student_disjoint"] == str(disjoint[key]), f"Split mismatch in {member}")
        score = float(row["probability"])
        require(0 <= score <= 1, f"Invalid probability in {member}")
        scores.append((score, labels[key]))
    return sorted(scores, key=lambda pair: pair[0], reverse=True)


def discrimination(ranked, positives):
    negatives = len(ranked) - positives
    cumulative_tp = 0
    cumulative_n = 0
    favorable_pairs = 0.0
    ap = 0.0
    for _, group in groupby(ranked, key=lambda pair: pair[0]):
        labels = [label for _, label in group]
        tp = sum(labels)
        fp = len(labels) - tp
        favorable_pairs += cumulative_tp * fp + tp * fp / 2
        cumulative_tp += tp
        cumulative_n += len(labels)
        ap += (tp / positives) * (cumulative_tp / cumulative_n)
    return favorable_pairs / (positives * negatives), ap


def queue(ranked, positives, seats):
    tp = sum(label for _, label in ranked[:seats])
    fp = seats - tp
    cutoff = ranked[seats - 1][0]
    above = [label for score, label in ranked if score > cutoff]
    tied = [label for score, label in ranked if score == cutoff]
    tied_seats = seats - len(above)
    return {
        "n": len(ranked),
        "positives": positives,
        "alerts": seats,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": positives - tp,
        "true_negative": len(ranked) - positives - fp,
        "precision": tp / seats,
        "recall": tp / positives,
        "cutoff_tie_size": len(tied),
        "cutoff_tie_positives": sum(tied),
        "cutoff_tie_seats": tied_seats,
        "uniform_tie_true_positive": sum(above) + tied_seats * sum(tied) / len(tied),
    }


def check_table_7(archive, replay):
    published = next(r for r in rows(archive, "results/alert_workload.csv")
                     if int(r["cutoff"]) == DAY and r["policy"] == "Top 10% capacity")
    fields = ("n", "positives", "alerts", "true_positive", "false_positive",
              "false_negative", "true_negative", "precision", "recall")
    scaled = {f"{field}_per_1000": 1000 * replay[field] / replay["n"] for field in fields[2:6]}
    check_fields(published, {**{field: replay[field] for field in fields}, **scaled},
                 "Published day-84 workload")
    table = {field: round(value, 1) for field, value in scaled.items()}
    table.update(precision_pct=round(100 * replay["precision"], 1),
                 recall_pct=round(100 * replay["recall"], 1))
    require(tuple(table.values()) == (100.0, 34.0, 66.1, 98.4, 34.0, 25.7),
            "Paper Table 7 rounding mismatch")
    return table


def status_coverage(records, test):
    started = {key: (start, end, result) for key, (start, end, result) in records.items()
               if key[1] == TERM and start is not None and start <= DAY}
    coverage = []
    for lag in (0, 1, 7, 14, 30, None):
        admitted = {key for key, (_, end, _) in started.items()
                    if lag is None or end is None or end > DAY - lag}
        missing = admitted - test.keys()
        require(test.keys() <= admitted, "Status lag removed an eligible enrollment")
        coverage.append({
            "lag_days": lag,
            "admitted": len(admitted),
            "with_all_eight_scores": len(test),
            "prior_exits_without_scores": len(missing),
            "withdrawn_prior_exits_without_scores": sum(started[key][2] == "Withdrawn"
                                                       for key in missing),
        })
    return coverage


def replay(archive, uci):
    records, test, labels, disjoint = source_roster(archive, uci)
    n = len(test)
    positives = sum(labels.values())
    seats = (n + 9) // 10
    published = {(row["scenario"], row["model"]): row
                 for row in rows(archive, "results/model_performance.csv")
                 if int(row["cutoff"]) == DAY}
    comparisons = []
    for scenario, models in METHODS.items():
        for model in models:
            ranked = ranked_predictions(archive, scenario, model, labels, disjoint)
            auc, ap = discrimination(ranked, positives)
            check_fields(published[scenario, model],
                         {"n": n, "positives": positives, "roc_auc": auc, "pr_auc": ap},
                         f"{scenario} / {model}")
            comparisons.append({"scenario": scenario, "model": model,
                                "roc_auc": auc, "average_precision": ap,
                                **queue(ranked, positives, seats)})

    return {
        "cutoff": DAY,
        "presentation": TERM,
        "source_tables_matched_by_sha256": len(SOURCE_TABLES),
        "roster": {
            "source_enrollments": sum(key[1] == TERM for key in records),
            "eligible_enrollments": n,
            "eligible_students": len({key[2] for key in test}),
            "eligible_withdrawn": positives,
            "eligible_withdrawn_missing_exit_date": sum(end is None and result == "Withdrawn"
                                                       for _, end, result in test.values()),
            "disjoint_enrollments": sum(disjoint.values()),
            "disjoint_withdrawn": sum(label for key, label in labels.items() if disjoint[key]),
        },
        "published_table_7": check_table_7(archive, comparisons[0]),
        "matched_comparisons": comparisons,
        "uniform_queue": {"alerts": seats, "expected_true_positive": seats * positives / n,
                          "expected_precision": positives / n, "expected_recall": seats / n},
        "status_coverage": status_coverage(records, test),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("supplement", type=Path)
    parser.add_argument("uci", type=Path)
    args = parser.parse_args()
    with pinned_zip(args.supplement, SUPPLEMENT_SHA256) as supplement, \
            pinned_zip(args.uci, UCI_SHA256) as uci:
        result = replay(supplement, uci)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
