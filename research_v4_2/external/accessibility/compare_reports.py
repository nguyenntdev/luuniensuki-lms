"""Compare two pinned W3C implementation reports on the local study's ACT rules."""

import csv
import hashlib
import json
import sys
from pathlib import Path

report_hashes = {
    "axe-core": "733e1d80e991154c7bd7293bd26c762b4777bfa8b0c9efc7b0e06a4f067d4736",
    "alfa": "eb0c760d8e56dbfb4f2338511b79e1873587ca13cd6392e562ba56fcd802e213",
}
study_dir = Path(__file__).resolve().parent
rule_ids = {row["id"] for row in json.loads((study_dir / "result.json").read_bytes())["cases"]}
reports = {}
for tool, digest in report_hashes.items():
    raw = (Path(sys.argv[1]) / f"{tool}.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f"Unexpected report revision for {tool}")
    rows = {}
    for rule in json.loads(raw)["actRuleMapping"]:
        if rule["ruleId"] not in rule_ids:
            continue
        for case in rule["testCaseResults"]:
            key = (rule["ruleId"], case["testcaseId"])
            if key in rows:
                raise ValueError(f"Duplicated testcase {key}")
            outcomes = {value for proc in case["procedureResults"] for value in proc["outcomes"]}
            priority = ("failed", "cantTell", "passed", "inapplicable")
            if not outcomes or outcomes.difference(priority):
                raise ValueError(f"Unexpected outcome for {key}: {outcomes}")
            outcome = next(value for value in priority if value in outcomes)
            rows[key] = (case["testCaseName"], case["expected"], outcome)
    reports[tool] = rows

axe, alfa = reports["axe-core"], reports["alfa"]
if axe.keys() != alfa.keys():
    raise ValueError("Reports differ in testcase membership")
writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("act_rule", "testcase_id", "example", "expected", "axe_core", "alfa"))
for key in sorted(axe):
    if axe[key][:2] != alfa[key][:2]:
        raise ValueError(f"Disagreement about fixture identity or expectation for {key}")
    writer.writerow((*key, *axe[key], alfa[key][2]))
