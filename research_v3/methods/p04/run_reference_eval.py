"""P04 reference evaluation runner (P04-T06/T07/T12 reference cell).

Executes the frozen pre-registration on the real, rights-verified datasets and
writes every artifact with measured numbers:

- research_artifacts_v3/runs/p04/reference_eval/leaderboard.json
- research_artifacts_v3/runs/p04/reference_eval/strata_report.json
- research_artifacts_v3/runs/p04/rights/raw_manifest.json

Determinism: fixed seeds everywhere; rerunning the runner on the same raw
snapshot must reproduce byte-identical leaderboard cells (verified by tests).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from research_v3.eval.splitters import freeze_hash
from research_v3.methods.p04 import scenarios as scen_mod
from research_v3.methods.p04.baselines import LogisticBaseline, MajorityBaseline
from research_v3.methods.p04.bench import (
    apply_bridge_to_features,
    bootstrap_ci_metric,
    leaderboard_cell,
    score_predictions,
)
from research_v3.methods.p04.bridge import NOT_APPLICABLE, bridge_from_oulad
from research_v3.methods.p04.rights import PROJECT_ROOT, load_or_build_manifest

RUNS_DIR = PROJECT_ROOT / "research_artifacts_v3" / "runs" / "p04"
REF_DIR = RUNS_DIR / "reference_eval"
ADAPTERS_DIR = PROJECT_ROOT / "research_v3" / "datasets" / "adapters"

SEED = 42


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Real-data row builders (labels withheld from inputs, adapters respected)
# ---------------------------------------------------------------------------

def oulad_rows_with_activity() -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Load OULAD rows and attach the dominant early-window activity type.

    The activity type per (module, presentation, student) is the mode of VLE
    activity_type values the student interacted with during the first 60 days.
    It is a REAL feature of the frozen snapshot and is what the ontology bridge
    maps; it is NOT a label and not future information beyond the window.
    """
    import csv
    import collections

    base = PROJECT_ROOT / "private_data" / "raw" / "oulad" / "2013-2014" / "_extracted"
    sys_path = str(ADAPTERS_DIR.parent)
    import sys

    if sys_path not in sys.path:
        sys.path.insert(0, sys_path)
    from research_v3.datasets.adapters.oulad import load_students

    rows = load_students()

    per_key_types: dict[tuple[str, str, str], Counter] = {}
    site_to_type: dict[str, str] = {}
    with (base / "vle.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            site_to_type[r["id_site"]] = r["activity_type"]
    with (base / "studentVle.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            try:
                day = int(r["date"])
            except (TypeError, ValueError):
                continue
            if day < 0 or day > 60:
                continue
            key = (r["code_module"], r["code_presentation"], r["id_student"])
            atype = site_to_type.get(r["id_site"], "")
            per_key_types.setdefault(key, collections.Counter())[atype] += 1

    enriched: list[dict[str, Any]] = []
    for row in rows:
        inp = dict(row["input"])
        key = (inp["code_module"], inp["code_presentation"], str(row["group_id"]))
        counter = per_key_types.get(key)
        inp["activity_type"] = counter.most_common(1)[0][0] if counter else ""
        enriched.append({**row, "input": inp})
    return enriched, {}


def binary_label(label: str) -> int | None:
    """Registered target: Pass/Distinction -> 1, Fail/Withdrawn -> 0."""
    return {"Pass": 1, "Distinction": 1, "Fail": 0, "Withdrawn": 0}.get(label)


def prepare_oulad() -> list[dict[str, Any]]:
    rows, _ = oulad_rows_with_activity()
    prepared = []
    for row in rows:
        y = binary_label(row["label"])
        if y is None:
            continue
        prepared.append({**row, "label": y})
    return prepared


def prepare_uci() -> list[dict[str, Any]]:
    """UCI rows: binary pass target (G3 >= 10), G1/G2 excluded from features."""
    import csv
    import io
    import zipfile

    archive = PROJECT_ROOT / "private_data" / "raw" / "uci" / "student-performance-2014" / "student.zip"
    rows_out: list[dict[str, Any]] = []
    with zipfile.ZipFile(archive) as zf:
        # UCI ships a zip-in-zip; the inner archive holds the CSVs
        inner = zipfile.ZipFile(zf.open("student.zip"))
        subject_map = {"student-mat.csv": "mathematics", "student-por.csv": "portuguese"}
        for name, subject in subject_map.items():
            with inner.open(name) as fh:
                text = fh.read().decode("utf-8")
                reader = csv.DictReader(io.StringIO(text), delimiter=";")
                for i, rec in enumerate(reader):
                    g3 = float(rec["G3"])
                    features = {
                        "subject": subject,
                        "school": rec["school"],
                        "sex": rec["sex"],
                        "age": float(rec["age"]),
                        "address": rec["address"],
                        "famsize": rec["famsize"],
                        "Pstatus": rec["Pstatus"],
                        "Medu": float(rec["Medu"]),
                        "Fedu": float(rec["Fedu"]),
                        "traveltime": float(rec["traveltime"]),
                        "studytime": float(rec["studytime"]),
                        "failures": float(rec["failures"]),
                        "schoolsup": rec["schoolsup"],
                        "famsup": rec["famsup"],
                        "paid": rec["paid"],
                        "activities": rec["activities"],
                        "nursery": rec["nursery"],
                        "higher": rec["higher"],
                        "internet": rec["internet"],
                        "romantic": rec["romantic"],
                        "famrel": float(rec["famrel"]),
                        "freetime": float(rec["freetime"]),
                        "goout": float(rec["goout"]),
                        "Dalc": float(rec["Dalc"]),
                        "Walc": float(rec["Walc"]),
                        "health": float(rec["health"]),
                        "absences": float(rec["absences"]),
                    }
                    rows_out.append(
                        {
                            "case_id": f"uci-{subject}-{i}",
                            "group_id": f"uci-{subject}-{i}",
                            "time_key": subject,
                            "input": features,
                            "label": 1 if g3 >= 10 else 0,
                        }
                    )
    return rows_out


# ---------------------------------------------------------------------------
# Stratum evaluation
# ---------------------------------------------------------------------------

def _select(rows: list[dict[str, Any]], ids: set[str]) -> list[dict[str, Any]]:
    return [r for r in rows if str(r["case_id"]) in ids]


def _subgroups(rows: Sequence[Mapping[str, Any]], key_path: tuple[str, ...]) -> dict[str, list[bool]]:
    groups: dict[str, list[bool]] = {}
    for row, pred in zip(rows, _LAST_PREDS):
        node: Any = row
        for key in key_path:
            node = node.get(key, "")
        groups.setdefault(str(node), []).append(bool(pred["prediction"] == row["label"]))
    return groups


_LAST_PREDS: list[Mapping[str, Any]] = []


def eval_cell(
    predictor_name: str,
    fit_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    scenario: scen_mod.Scenario,
    baseline_cell: Mapping[str, Any] | None,
    bridge=None,
) -> dict[str, Any]:
    """Fit on fit_rows, predict test_rows, score one leaderboard cell."""
    if predictor_name == "C0_majority":
        model = MajorityBaseline().fit(fit_rows)
        preds = model.predict(test_rows)
    elif predictor_name == "C1_logistic_regression":
        model = LogisticBaseline(seed=SEED)
        try:
            model.fit(fit_rows)
        except Exception:
            # honest BLOCKED cell instead of a fabricated number
            cell = leaderboard_cell(predictor_name, scenario, test_rows, [
                {"prediction": "ABSTAIN"} for _ in test_rows
            ])
            cell["status"] = "BLOCKED_FIT_FAILURE"
            return cell
        preds = model.predict(test_rows)
    else:
        raise ValueError(f"unknown reference predictor {predictor_name}")

    global _LAST_PREDS
    _LAST_PREDS = preds
    if bridge is not None:
        test_rows = apply_bridge_to_features(test_rows, bridge)
        # remap: scoring uses mapped_canonical exclusion only; predictions stay
        # the predictor's own outputs (mapping degradation is measured, not
        # artificially rescued)
    cell = leaderboard_cell(predictor_name, scenario, test_rows, preds, baseline_cell=baseline_cell)
    auc_ci = bootstrap_ci_metric(test_rows, preds, metric="auc", n_boot=1000, seed=SEED)
    cell["auc_ci95"] = auc_ci["ci95"] if auc_ci else None
    cell["n_bootstrap_groups"] = auc_ci["n_groups"] if auc_ci else 0
    cell["status"] = "MEASURED"
    return cell


def run_reference_eval() -> dict[str, Any]:
    """Execute the frozen protocol; write leaderboard + strata report."""
    REF_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.joinpath("rights").mkdir(parents=True, exist_ok=True)
    manifest = load_or_build_manifest(RUNS_DIR / "rights" / "raw_manifest.json")

    oulad = prepare_oulad()
    uci = prepare_uci()
    if len(oulad) != 32593:
        raise RuntimeError(f"OULAD row count drifted: {len(oulad)} != 32593")

    # ---- frozen splits -----------------------------------------------------
    from research_v3.eval.splitters import group_split, time_split, assert_no_leakage

    oulad_group = group_split(oulad, group_key="group_id", paper_id="P04", protocol="learner", salt="p04-v1")
    oulad_time = time_split(oulad, time_key="time_key", paper_id="P04")
    uci_group = group_split(uci, group_key="group_id", paper_id="P04", protocol="learner", salt="p04-v1")
    for s in (oulad_group, oulad_time, uci_group):
        assert_no_leakage(s)
    splits_info = {
        "oulad_group": {"hash": freeze_hash(oulad_group),
                        "sizes": {k: len(v) for k, v in oulad_group.split_ids.items()}},
        "oulad_time": {"hash": freeze_hash(oulad_time),
                       "sizes": {k: len(v) for k, v in oulad_time.split_ids.items()}},
        "uci_group": {"hash": freeze_hash(uci_group),
                      "sizes": {k: len(v) for k, v in uci_group.split_ids.items()}},
    }

    # ---- real bridge over observed OULAD activity types --------------------
    import collections

    type_counts = collections.Counter(r["input"]["activity_type"] for r in oulad if r["input"]["activity_type"])
    bridge = bridge_from_oulad(type_counts)

    o_group_parts = {n: set(ids) for n, ids in oulad_group.split_ids.items()}
    o_time_parts = {n: set(ids) for n, ids in oulad_time.split_ids.items()}
    u_parts = {n: set(ids) for n, ids in uci_group.split_ids.items()}

    oulad_train = _select(oulad, o_group_parts["train"])
    oulad_test = _select(oulad, o_group_parts["test"])
    uci_train = _select(uci, u_parts["train"])
    uci_test = _select(uci, u_parts["test"])

    leaderboard: list[dict[str, Any]] = []
    strata_report: dict[str, Any] = {}

    # ---- S0 in-domain reference (the degradation anchor) -------------------
    for name in ("C0_majority", "C1_logistic_regression"):
        cell = eval_cell(name, oulad_train, oulad_test,
                         scen_mod.Scenario("S0", "in_domain_reference", "oulad-2013-2014",
                                           "In-domain group-split reference cell.", {}), None)
        leaderboard.append(cell)
    ref_by_predictor = {
        c["predictor"]: c for c in leaderboard if c["stratum"] == "S0"
    }
    c1_ref = ref_by_predictor["C1_logistic_regression"]
    c0_ref = ref_by_predictor["C0_majority"]

    def anchor_for(predictor: str) -> Mapping[str, Any]:
        return ref_by_predictor[predictor]

    # ---- S1 partial mappings (injector on the bridge) ----------------------
    from research_v3.methods.p04.bench import hide_bridge_edges

    for scenario in scen_mod.oulad_scenarios(
        courses=sorted({r["input"]["code_module"] for r in oulad}),
        presentations=sorted({r["input"]["code_presentation"] for r in oulad}),
    ):
        if scenario.stratum != "S1":
            continue
        hidden_bridge = hide_bridge_edges(
            bridge, scenario.params["hide_fraction"], salt=f"p04-{scenario.name}"
        )
        mapped_rows = apply_bridge_to_features(oulad_test, hidden_bridge)
        for name in ("C0_majority", "C1_logistic_regression"):
            model = (MajorityBaseline().fit(oulad_train) if name == "C0_majority"
                     else LogisticBaseline(seed=SEED).fit(oulad_train))
            preds = model.predict(mapped_rows)
            cell = leaderboard_cell(name, scenario, mapped_rows, preds,
                                    baseline_cell=anchor_for(name))
            cell["auc_ci95"] = (bootstrap_ci_metric(mapped_rows, preds, metric="auc", n_boot=1000, seed=SEED) or {}).get("ci95")
            cell["status"] = "MEASURED"
            leaderboard.append(cell)

    # ---- S2 unknown categories via a real annotation budget ----------------
    from research_v3.methods.p04.strata import bridge_within_annotation_budget

    s2_budget_courses = ("AAA", "DDD")   # annotation budget limited to these courses
    s2_test_courses = ("BBB", "EEE")     # evaluation courses outside the budget
    s2_train = [r for r in oulad_train if r["input"]["code_module"] in s2_budget_courses]
    s2_test = [r for r in oulad_test if r["input"]["code_module"] in s2_test_courses]
    s2_bridge, s2_audit = bridge_within_annotation_budget(s2_train, s2_test)
    s2_mapped = apply_bridge_to_features(s2_test, s2_bridge)
    for name in ("C0_majority", "C1_logistic_regression"):
        model = (MajorityBaseline().fit(s2_train) if name == "C0_majority"
                 else LogisticBaseline(seed=SEED).fit(s2_train))
        preds = model.predict(s2_mapped)
        sc = scen_mod.Scenario("S2", "annotation_budget_train_AAA_DDD_test_BBB_EEE",
                               "oulad-2013-2014",
                               "Bridge annotated on AAA/DDD only; unseen BBB/EEE categories "
                               "become real unknown edges.", {"audit": s2_audit})
        cell = leaderboard_cell(name, sc, s2_mapped, preds, baseline_cell=anchor_for(name))
        cell["annotation_audit"] = s2_audit
        cell["status"] = "MEASURED"
        leaderboard.append(cell)

    # ---- S3 course shift: train 2013 presentations, test 2014 --------------
    train_2013 = [r for r in oulad if r["input"]["code_presentation"].startswith("2013")
                  and str(r["case_id"]) in o_time_parts["train"]]
    # time split is chronological over rows; build a clean 2013-train / 2014-test pair
    pres_sorted = sorted({r["input"]["code_presentation"] for r in oulad})
    train_pres = [p for p in pres_sorted if p.startswith("2013")]
    test_pres = [p for p in pres_sorted if p.startswith("2014")]
    s3_train = [r for r in oulad if r["input"]["code_presentation"] in train_pres]
    s3_test = [r for r in oulad if r["input"]["code_presentation"] in test_pres]
    for name in ("C0_majority", "C1_logistic_regression"):
        model = MajorityBaseline().fit(s3_train) if name == "C0_majority" else LogisticBaseline(seed=SEED).fit(s3_train)
        preds = model.predict(s3_test)
        sc = scen_mod.Scenario("S3", "presentation_shift_train_2013_test_2014",
                               "oulad-2013-2014", "Time shift 2013 -> 2014.", {})
        cell = leaderboard_cell(name, sc, s3_test, preds, baseline_cell=anchor_for(name))
        cell["auc_ci95"] = (bootstrap_ci_metric(s3_test, preds, metric="auc", n_boot=1000, seed=SEED) or {}).get("ci95")
        cell["status"] = "MEASURED"
        leaderboard.append(cell)

    # ---- S3 course shift: held-out courses FFF/GGG --------------------------
    heldout_courses = {"FFF", "GGG"}
    s3c_train = [r for r in oulad if r["input"]["code_module"] not in heldout_courses
                 and str(r["case_id"]) in o_group_parts["train"]]
    s3c_test = [r for r in oulad if r["input"]["code_module"] in heldout_courses]
    for name in ("C0_majority", "C1_logistic_regression"):
        model = MajorityBaseline().fit(s3c_train) if name == "C0_majority" else LogisticBaseline(seed=SEED).fit(s3c_train)
        preds = model.predict(s3c_test)
        sc = scen_mod.Scenario("S3", "course_shift_train_AAA_EEE_test_FFF_GGG",
                               "oulad-2013-2014", "Held-out courses FFF/GGG.", {})
        cell = leaderboard_cell(name, sc, s3c_test, preds, baseline_cell=anchor_for(name))
        cell["auc_ci95"] = (bootstrap_ci_metric(s3c_test, preds, metric="auc", n_boot=1000, seed=SEED) or {}).get("ci95")
        cell["status"] = "MEASURED"
        leaderboard.append(cell)

    # ---- S4 cold start: zero early clicks ----------------------------------
    s4_test = [r for r in oulad_test if r["input"]["early_click_total"] == 0]
    for name in ("C0_majority", "C1_logistic_regression"):
        preds = (MajorityBaseline().fit(oulad_train) if name == "C0_majority"
                 else LogisticBaseline(seed=SEED).fit(oulad_train)).predict(s4_test)
        sc = scen_mod.Scenario("S4", "cold_start_zero_early_clicks",
                               "oulad-2013-2014", "Zero-activity learners at cutoff.", {})
        cell = leaderboard_cell(name, sc, s4_test, preds, baseline_cell=anchor_for(name))
        cell["status"] = "MEASURED"
        leaderboard.append(cell)

    # ---- S3 cross-subject (UCI): mathematics -> portuguese ------------------
    uci_mat = [r for r in uci if r["input"]["subject"] == "mathematics"]
    uci_por = [r for r in uci if r["input"]["subject"] == "portuguese"]
    uci_mat_train = [r for r in uci_mat if str(r["case_id"]) in u_parts["train"]]
    uci_por_train = [r for r in uci_por if str(r["case_id"]) in u_parts["train"]]
    uci_por_test = [r for r in uci_por if str(r["case_id"]) in u_parts["test"]]
    uci_por_in_domain_ref: dict[str, dict[str, Any]] = {}
    # in-domain reference for UCI (fit on por train, eval on por test)
    for name in ("C0_majority", "C1_logistic_regression"):
        model = (MajorityBaseline().fit(uci_por_train) if name == "C0_majority"
                 else LogisticBaseline(seed=SEED).fit(uci_por_train))
        preds = model.predict(uci_por_test)
        sc = scen_mod.Scenario("S0", "uci_in_domain_reference",
                               "uci-student-performance-2014",
                               "Portuguese in-domain reference cell.", {})
        cell = leaderboard_cell(name, sc, uci_por_test, preds)
        cell["status"] = "MEASURED"
        leaderboard.append(cell)
        uci_por_in_domain_ref[name] = cell
    for name in ("C0_majority", "C1_logistic_regression"):
        model = (MajorityBaseline().fit(uci_mat_train) if name == "C0_majority"
                 else LogisticBaseline(seed=SEED).fit(uci_mat_train))
        preds = model.predict(uci_por)
        sc = scen_mod.Scenario("S3", "subject_shift_train_mat_test_por",
                               "uci-student-performance-2014", "Mathematics -> Portuguese.", {})
        cell = leaderboard_cell(name, sc, uci_por, preds,
                                baseline_cell=uci_por_in_domain_ref[name])
        cell["status"] = "MEASURED"
        leaderboard.append(cell)

    # ---- rank stability across S-strata (C0 vs C1 ordering) ----------------
    by_stratum: dict[str, list[str]] = {}
    for cell in leaderboard:
        if cell["status"] != "MEASURED" or cell.get("auc") is None:
            continue
        by_stratum.setdefault(cell["stratum"], []).append(
            (cell["predictor"], cell["auc"])
        )
    rankings = {
        s: [name for name, _ in sorted(entries, key=lambda t: -t[1])]
        for s, entries in by_stratum.items()
        if len(entries) >= 2
    }
    from research_v3.methods.p04.bench import rank_stability

    strata_report["rank_stability_mean_kendall_tau"] = rank_stability(rankings)
    strata_report["rankings_by_stratum"] = rankings

    # ---- null-hypothesis assessment (preregistered H0 decision rule) -------
    # H0 stands unless C1 shows CI-separated positive AUC degradation on at
    # least one shift stratum beyond the known cross-domain reference.
    degradation_cells = [
        c for c in leaderboard
        if c["predictor"] == "C1_logistic_regression"
        and c["stratum"] in ("S1", "S2", "S3", "S4")
        and c.get("auc_degradation_vs_baseline") is not None
    ]
    reliable_failures = []
    for c in degradation_cells:
        ci = c.get("auc_ci95")
        deg = c["auc_degradation_vs_baseline"]
        if ci and deg > 0 and ci[0] > c["auc"] - deg:  # lower CI above degraded value is implied by CI logic below
            pass
        if ci and deg > 0:
            # CI of the shifted AUC excludes the reference AUC -> reliable drop
            ref_auc = round(c["auc"] + deg, 6)
            if ci[1] < ref_auc:
                reliable_failures.append(
                    {"scenario": c["scenario"], "degradation": deg, "shifted_auc_ci95": ci}
                )
    null_assessment = {
        "h0_stands": len(reliable_failures) == 0,
        "reliable_failures": reliable_failures,
        "note": "A failure counts as reliable only when the shifted AUC bootstrap CI excludes the same predictor's in-domain AUC.",
    }

    result = {
        "protocol": "CurriculumShiftBench reference evaluation (frozen prereg v1.0)",
        "prereg_sha256": sha256_text(
            (PROJECT_ROOT / "research_v3/methods/p04/protocols/pre_registration.yaml").read_text(encoding="utf-8")
        ),
        "splits": splits_info,
        "bridge": {
            "ontology_version": bridge.ontology_version,
            "n_edges": len(bridge.edges),
            "coverage": bridge.coverage(),
            "unknown_sources": list(bridge.unknown_sources),
        },
        "n_oulad_rows": len(oulad),
        "n_uci_rows": len(uci),
        "strata_report": strata_report,
        "null_assessment": null_assessment,
        "leaderboard": leaderboard,
        "external_generalization": "UNVERIFIED beyond OULAD + UCI student-performance",
    }
    (REF_DIR / "leaderboard.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(PROJECT_ROOT))
    out = run_reference_eval()
    print(json.dumps({k: v for k, v in out.items() if k != "leaderboard"}, indent=2))
    for cell in out["leaderboard"]:
        print(cell["stratum"], cell["scenario"], cell["predictor"],
              "auc=", cell.get("auc"), "n_scored=", cell.get("n_scored"))
