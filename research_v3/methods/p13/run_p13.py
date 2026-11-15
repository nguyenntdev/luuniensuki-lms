"""P13 runner: end-to-end preregistered pipeline on real OULAD clickstream.

Stages (each fail-closed, artifacts under research_artifacts_v3/runs/p13/):
  E00 dataset+license gate -> E01 schema+split integrity -> E02/E03 baselines
  -> E05 proposed -> E06 ablations -> E07 robustness/subgroups -> E08
  calibration -> E09 statistics -> E10 failure analysis.

Everything observational. Every narrative artifact passes the construct
guard; numeric artifacts carry the proxy_only flag in their metadata.
"""
from __future__ import annotations

import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from research_v3.contracts.cards import ExperimentCard
from research_v3.datasets.registry import load_registry, require_approved
from research_v3.eval.leakage import audit_rows
from research_v3.eval.splitters import assert_no_leakage
from research_v3.methods.p13.analysis import (
    FEATURE_SETS,
    SEED,
    confirmatory_family,
    fit_calibrate_scores,
    guarded_text,
    paired_auc_comparison,
    subgroup_auc,
)
from research_v3.methods.p13.construct_validity import (
    CONSTRUCT_VALIDITY_FLAG,
    PROXY_ONLY,
    enforce_proxy_guard,
)
from research_v3.methods.p13.splits import (
    assert_train_test_disjoint,
    materialize_group_split,
    materialize_time_split,
)
from research_v3.methods.p13.srl_features import (
    FEATURE_CUTOFF_DAYS,
    FEATURE_CUTOFF_START_DAY,
    build_srl_proxy_rows,
    load_clickstream,
    load_student_info,
    mutate_temporal_order,
    srl_proxy_definitions,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "research_artifacts_v3" / "runs" / "p13"

RAW_DIR = PROJECT_ROOT / "private_data" / "raw" / "oulad" / "2013-2014"
RAW_ZIP_SHA256 = "f2ed1902616c1fe8d2824d872c0b7d2d72be435bf0124d077044fe4be2c6d3e4"
LICENSE_SHA256 = "41003d4a74749c0220e33dd415042164b5a1093ed401f36277234f772d22d3d0"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _json_write(name: str, payload: Any, *, guard: bool = True) -> Path:
    """Write a JSON artifact; narrative strings pass the construct guard."""
    out = OUT_DIR / name
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=1, sort_keys=False, default=str)
    if guard:
        enforce_proxy_guard(name, text)
    out.write_text(text, encoding="utf-8")
    return out


def _md_write(name: str, text: str) -> Path:
    out = OUT_DIR / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(enforce_proxy_guard(name, text), encoding="utf-8")
    return out


def run(*, bootstrap_resamples: int = 2000, quick: bool = False) -> dict[str, Any]:
    started = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {"paper_id": "P13", "status": "RUNNING"}

    # ---- E00: dataset & license gate --------------------------------------
    registry = load_registry()
    (approved,) = require_approved(registry, ["oulad-2013-2014"], paper_id="P13")
    zip_sha = _sha256_file(RAW_DIR / "oulad.zip")
    lic_sha = _sha256_file(RAW_DIR / "LICENSE.txt")
    if zip_sha != RAW_ZIP_SHA256:
        raise RuntimeError(f"OULAD zip hash drift: {zip_sha}")
    if lic_sha != LICENSE_SHA256:
        raise RuntimeError(f"OULAD license hash drift: {lic_sha}")
    report["E00"] = {
        "dataset_id": approved.dataset_id,
        "license": approved.redistribution_policy,
        "zip_sha256": zip_sha,
        "license_text_sha256": lic_sha,
        "status": "APPROVED",
    }

    # ---- ingest real data ---------------------------------------------------
    clickstream, _vle = load_clickstream()
    info = load_student_info()
    n_clicks_total = int(len(clickstream))
    n_rows = len(info)

    rows = build_srl_proxy_rows(
        clickstream,
        info,
        start_day=FEATURE_CUTOFF_START_DAY,
        end_day=FEATURE_CUTOFF_DAYS,
    )
    if len(rows) != n_rows:
        raise RuntimeError(f"row accounting failed: {len(rows)} != {n_rows}")

    n_clicks_in_window = int(
        ((clickstream["date"] >= FEATURE_CUTOFF_START_DAY) & (clickstream["date"] <= FEATURE_CUTOFF_DAYS)).sum()
    )
    zero_click_rows = sum(1 for r in rows if r["features"]["no_clicks_in_window"] == 1.0)
    report["data"] = {
        "studentVle_rows_total": n_clicks_total,
        "studentVle_rows_in_window_0_60": n_clicks_in_window,
        "studentInfo_rows": n_rows,
        "rows_with_zero_clicks_in_window": zero_click_rows,
        "outcome_counts": {
            lab: sum(1 for r in rows if r["label"] == lab)
            for lab in ("Pass", "Fail", "Withdrawn", "Distinction")
        },
        "feature_window": [FEATURE_CUTOFF_START_DAY, FEATURE_CUTOFF_DAYS],
    }

    # ---- E01: leakage audit + splits ---------------------------------------
    leak = audit_rows(
        (
            {"case_id": r["case_id"], "input": r["features"]}
            for r in rows[:5000]  # spot-audit subset for runtime; full keys checked by schema
        ),
        strict=True,
    )
    group_manifest = materialize_group_split(rows)
    time_manifest = materialize_time_split(rows)
    assert_train_test_disjoint(rows, group_manifest)
    assert_train_test_disjoint(rows, time_manifest)
    assert_no_leakage(_frozen_from_manifest("P13", "group", group_manifest))
    assert_no_leakage(_frozen_from_manifest("P13", "time", time_manifest))
    report["E01"] = {
        "leakage_audit_rows": leak["rows"],
        "leakage_status": leak["status"],
        "group_split": {k: v for k, v in group_manifest.items() if k != "split_ids"},
        "time_split": {k: v for k, v in time_manifest.items() if k != "split_ids"},
        "splits_disjoint": True,
    }
    _json_write("splits_manifest.json", {"group": group_manifest, "time": time_manifest})

    by_case = {r["case_id"]: r for r in rows}

    def _part(manifest: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        return {
            p: [by_case[c] for c in ids]
            for p, ids in manifest["split_ids"].items()
        }

    group_part = _part(group_manifest)
    time_part = _part(time_manifest)

    # ---- E02/E03/E05: C0/C1/C2 on both split protocols ----------------------
    condition_metrics: dict[str, Any] = {}
    _PARTS = {"group": group_part, "time": time_part}
    for split_name, part in _PARTS.items():
        for cond in ("C0", "C1", "C2"):
            m = fit_calibrate_scores(
                part["train"], part["calibration"], part["test"], FEATURE_SETS[cond]
            )
            condition_metrics[f"{split_name}:{cond}"] = _strip_private(m)
    report["E02_E03_E05"] = condition_metrics

    # paired AUC comparisons (primary contrast: C2 vs C0; then C2 vs C1)
    paired: dict[str, Any] = {}
    for split_name, part in _PARTS.items():
        m_c2 = fit_calibrate_scores(part["train"], part["calibration"], part["test"], FEATURE_SETS["C2"])
        m_c0 = fit_calibrate_scores(part["train"], part["calibration"], part["test"], FEATURE_SETS["C0"])
        m_c1 = fit_calibrate_scores(part["train"], part["calibration"], part["test"], FEATURE_SETS["C1"])
        paired[f"{split_name}:C2_vs_C0"] = paired_auc_comparison(
            m_c2["_proba"], m_c0["_proba"], m_c2["_y"], m_c2["_group_ids"],
            n_boot=bootstrap_resamples,
        )
        paired[f"{split_name}:C2_vs_C1"] = paired_auc_comparison(
            m_c2["_proba"], m_c1["_proba"], m_c2["_y"], m_c2["_group_ids"],
            n_boot=bootstrap_resamples,
        )
    report["E09_paired_auc"] = paired

    # ---- E06: ablations ------------------------------------------------------
    ablations: dict[str, Any] = {}
    for cond in ("A1_no_forethought", "A3_no_help_seeking", "A4_no_effort"):
        for split_name, part in _PARTS.items():
            m = fit_calibrate_scores(
                part["train"], part["calibration"], part["test"], FEATURE_SETS[cond]
            )
            ablations[f"{split_name}:{cond}"] = _strip_private(m)
    # A2: shuffle dates within learner, rebuild features, same frozen cases
    from research_v3.methods.p13.srl_features import window_clicks

    win_mut = window_clicks(
        clickstream, start_day=FEATURE_CUTOFF_START_DAY, end_day=FEATURE_CUTOFF_DAYS
    )
    win_mut = mutate_temporal_order(win_mut, seed=SEED)
    rows_mut = _build_from_window(win_mut, info)
    by_case_mut = {r["case_id"]: r for r in rows_mut}
    for split_name, manifest in (("group", group_manifest), ("time", time_manifest)):
        part = _part(manifest)
        src = {
            "train": [by_case_mut[c] for c in manifest["split_ids"]["train"]],
            "calibration": [by_case_mut[c] for c in manifest["split_ids"]["calibration"]],
            "test": [by_case_mut[c] for c in manifest["split_ids"]["test"]],
        }
        # case alignment sanity: same cases, mutated features
        if [r["case_id"] for r in src["test"]] != [r["case_id"] for r in part["test"]]:
            raise RuntimeError("A2 ablation lost case alignment")
        m = fit_calibrate_scores(
            part["train"], part["calibration"], part["test"], FEATURE_SETS["A2_no_temporal_order"],
            feature_source=src,
        )
        ablations[f"{split_name}:A2_no_temporal_order"] = _strip_private(m)
    report["E06_ablations"] = ablations

    # ---- E07: descriptives + subgroup robustness ----------------------------
    family = confirmatory_family(rows, list(FEATURE_SETS["C2"])) if not quick else _quick_family(rows)
    report["E07_group_contrasts"] = family

    m_c2_group = fit_calibrate_scores(
        group_part["train"], group_part["calibration"], group_part["test"], FEATURE_SETS["C2"]
    )
    subgroups: dict[str, Any] = {}
    # subgroup cuts aligned with the group-split test partition
    test_rows = group_part["test"]
    for key in ("code_presentation", "gender", "age_band", "imd_band", "highest_education", "disability"):
        vals = [r["subgroups"][key] for r in test_rows]
        subgroups[key] = subgroup_auc(m_c2_group["_proba"], m_c2_group["_y"], vals, min_n=20)
    report["E07_subgroups"] = subgroups

    # presentation-level descriptive medians (temporal shift visibility)
    pres_profile: dict[str, Any] = {}
    for pres in sorted({r["time_key"] for r in rows}):
        sub = [r for r in rows if r["time_key"] == pres]
        pres_profile[pres] = {
            "n": len(sub),
            "median_early_click_total": float(np.median([r["features"]["early_click_total"] for r in sub])),
            "median_plan_regularity": float(np.median([r["features"]["plan_regularity"] for r in sub])),
            "median_effort_mean_daily_clicks": float(np.median([r["features"]["effort_mean_daily_clicks"] for r in sub])),
            "median_help_seeking_forum_share": float(np.median([r["features"]["help_seeking_forum_share"] for r in sub])),
            "pass_rate": sum(1 for r in sub if r["label"] == "Pass") / len(sub),
        }
    report["E07_presentation_profile"] = pres_profile

    # ---- experiment card ------------------------------------------------------
    prereg_path = PROJECT_ROOT / "research_v3" / "experiments" / "p13" / "pre_registration.yaml"
    card = ExperimentCard(
        paper_id="P13",
        rq_id="RQ1",
        train_dataset_ids=("oulad-2013-2014",),
        holdout_dataset_ids=("oulad-2013-2014:2014J",),
        method_commit_sha=_git_sha(),
        method_hash=_method_hash(),
        baseline_version="C0/C1/logreg-sklearn-" + __import__("sklearn").__version__,
        split_hash=group_manifest["split_hash"],
        feature_cutoff=f"day{FEATURE_CUTOFF_START_DAY}-{FEATURE_CUTOFF_DAYS}",
        prereg_sha256=_sha256_file(prereg_path),
        hyperparameter_budget="fixed C=1.0, no search (preregistered)",
        seed=SEED,
        hardware=f"{platform.machine()} cpus={__import__('os').cpu_count()}",
        wall_time_seconds=round(time.time() - started, 1),
        dependency_lock_sha256=_deps_hash(),
        output_path=str(OUT_DIR),
        protocol_deviations=(),
        status="PASS",
    )
    _json_write("experiment_card.json", card.to_dict())

    # ---- numeric table + summary ----------------------------------------------
    summary = {
        "headline": {
            "group_split": {
                "C0_auc": condition_metrics["group:C0"]["roc_auc"],
                "C1_auc": condition_metrics["group:C1"]["roc_auc"],
                "C2_auc": condition_metrics["group:C2"]["roc_auc"],
                "C2_vs_C0_delta_auc": paired["group:C2_vs_C0"]["delta_auc"],
                "C2_vs_C0_ci95": paired["group:C2_vs_C0"]["ci_95"],
            },
            "time_split": {
                "C0_auc": condition_metrics["time:C0"]["roc_auc"],
                "C1_auc": condition_metrics["time:C1"]["roc_auc"],
                "C2_auc": condition_metrics["time:C2"]["roc_auc"],
                "C2_vs_C0_delta_auc": paired["time:C2_vs_C0"]["delta_auc"],
                "C2_vs_C0_ci95": paired["time:C2_vs_C0"]["ci_95"],
            },
        },
        "h0_primary_verdict": _h0_verdict(paired),
        "construct_validity": {
            "flag": PROXY_ONLY,
            "measured_construct": None,
            "statement": (
                "All SRL features are behavioural proxies (construct_validity: "
                "proxy_only) derived from OULAD clickstream; SRL itself was not "
                "measured and no causal claim is made."
            ),
        },
    }
    _json_write("summary.json", summary)
    _json_write("metrics_full.json", report)

    # honest narrative
    _md_write(
        "FINDINGS.md",
        _findings_md(report, summary),
    )
    report["status"] = "PASS"
    return report


# ---------------------------------------------------------------------------


def _build_from_window(win: Any, info: Any) -> list[dict[str, Any]]:
    """Feature rows directly from an (already windowed/mutated) frame."""
    from research_v3.methods.p13.srl_features import _features_for_group
    from research_v3.methods.p13.srl_features import (
        C0_FEATURES,
        C1_FEATURES,
        FORBIDDEN_FEATURE_FIELDS,
        SRL_PROXIES,
    )

    grouped = win.groupby(
        ["code_module", "code_presentation", "id_student"], observed=True, sort=True
    )
    feat_rows = {key: _features_for_group(g) for key, g in grouped}
    out: list[dict[str, Any]] = []
    for _, stu in info.iterrows():
        key = (stu["code_module"], stu["code_presentation"], int(stu["id_student"]))
        feats = feat_rows.get(key)
        if feats is None:
            feats = {n: 0.0 for n in set(SRL_PROXIES) | set(C0_FEATURES) | set(C1_FEATURES)}
            feats["no_clicks_in_window"] = 1.0
        else:
            feats = dict(feats)
            feats["no_clicks_in_window"] = 0.0
        features = {
            **{p: feats[p] for p in SRL_PROXIES},
            **{c: feats[c] for c in C0_FEATURES + C1_FEATURES},
            "no_clicks_in_window": feats["no_clicks_in_window"],
        }
        if set(features) & FORBIDDEN_FEATURE_FIELDS:
            raise RuntimeError("forbidden field in A2 features")
        out.append(
            {
                "case_id": f"oulad-{stu['code_module']}-{stu['code_presentation']}-{int(stu['id_student'])}",
                "group_id": str(int(stu["id_student"])),
                "time_key": str(stu["code_presentation"]),
                "module": str(stu["code_module"]),
                "features": features,
                "subgroups": {
                    "code_presentation": str(stu["code_presentation"]),
                    "gender": str(stu["gender"]),
                    "age_band": str(stu["age_band"]),
                    "imd_band": str(stu["imd_band"]),
                    "highest_education": str(stu["highest_education"]),
                    "disability": str(stu["disability"]),
                },
                "label": str(stu["final_result"]),
            }
        )
    return out


def _strip_private(m: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in m.items() if not k.startswith("_")}


def _frozen_from_manifest(paper: str, protocol: str, manifest: dict[str, Any]):
    from research_v3.contracts.cards import FrozenSplit

    return FrozenSplit(
        paper_id=paper,
        protocol=protocol,
        split_ids={k: tuple(v) for k, v in manifest["split_ids"].items()},
    )


def _quick_family(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Reduced-bootstrap family for smoke runs (never used for the paper)."""
    out: dict[str, Any] = {}
    from research_v3.methods.p13.analysis import CONTRAST_FAMILY, group_contrast
    from research_v3.methods.p13.srl_features import SRL_PROXIES

    for ga, gb in CONTRAST_FAMILY:
        out[f"{ga}_vs_{gb}"] = [
            group_contrast(rows, f, ga, gb, n_boot=50) for f in list(SRL_PROXIES)[:4]
        ]
    return out


def _h0_verdict(paired: dict[str, Any]) -> dict[str, Any]:
    v: dict[str, Any] = {}
    for key, p in paired.items():
        lo, hi = p["ci_95"]
        beat = lo > 0 and p["delta_auc"] >= 0.02
        v[key] = {
            "delta_auc": p["delta_auc"],
            "ci_95": p["ci_95"],
            "prereg_threshold": 0.02,
            "rejected": bool(beat),
        }
    primary = v["group:C2_vs_C0"]
    v["verdict_text"] = (
        "H0_primary NOT rejected: C2 phase-structured SRL proxies do not beat "
        "C0 raw click count by the preregistered 0.02 AUC margin "
        f"(delta={primary['delta_auc']:.4f}, CI95 [{primary['ci_95'][0]:.4f}, "
        f"{primary['ci_95'][1]:.4f}]). Per the preregistration this null result "
        "is published: SRL proxy structure adds no classification value beyond "
        "generic activity volume in this setup."
        if not primary["rejected"]
        else "H0_primary rejected: C2 beats C0 by >= 0.02 AUC (CI lower bound > 0)."
    )
    return v


def _git_sha() -> str:
    import subprocess

    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=str(PROJECT_ROOT), stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def _method_hash() -> str:
    h = hashlib.sha256()
    for f in sorted((PROJECT_ROOT / "research_v3" / "methods" / "p13").glob("*.py")):
        h.update(f.name.encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def _deps_hash() -> str:
    import sklearn
    import numpy
    import pandas
    import scipy

    payload = f"numpy={numpy.__version__};pandas={pandas.__version__};scipy={scipy.__version__};sklearn={sklearn.__version__}"
    return hashlib.sha256(payload.encode()).hexdigest()


def _findings_md(report: dict[str, Any], summary: dict[str, Any]) -> str:
    d = report["data"]
    g = summary["headline"]["group_split"]
    t = summary["headline"]["time_split"]
    lines = [
        "# P13 run findings (auto-generated; construct guard passed)",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Data (real OULAD, CC BY 4.0, sha256-verified)",
        f"- studentVle rows: {d['studentVle_rows_total']:,} total; "
        f"{d['studentVle_rows_in_window_0_60']:,} inside the day 0-60 feature window",
        f"- learner-module-presentation rows: {d['studentInfo_rows']:,} "
        f"(zero clicks in window: {d['rows_with_zero_clicks_in_window']:,})",
        f"- outcomes: {d['outcome_counts']}",
        "",
        "## Classification (Pass vs rest; fixed logistic regression)",
        f"- group split  : C0 AUC {g['C0_auc']:.4f} | C1 AUC {g['C1_auc']:.4f} | C2 AUC {g['C2_auc']:.4f}",
        f"- temporal holdout (test=2014J): C0 AUC {t['C0_auc']:.4f} | C1 AUC {t['C1_auc']:.4f} | C2 AUC {t['C2_auc']:.4f}",
        f"- C2 vs C0 (group): delta {g['C2_vs_C0_delta_auc']:.4f} CI95 {g['C2_vs_C0_ci95']}",
        f"- C2 vs C0 (time) : delta {t['C2_vs_C0_delta_auc']:.4f} CI95 {t['C2_vs_C0_ci95']}",
        "",
        f"H0 verdict: {summary['h0_primary_verdict']['verdict_text']}",
        "",
        "## Construct validity (central limitation)",
        "All SRL features are clickstream proxies flagged construct_validity:",
        "proxy_only. OULAD contains no SRL instrument; SRL was NOT measured,",
        "and no causal claim is made anywhere in this study.",
        "",
        "Full metrics: metrics_full.json | splits: splits_manifest.json",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--boot", type=int, default=2000)
    args = ap.parse_args()
    out = run(bootstrap_resamples=args.boot, quick=args.quick)
    print(json.dumps({"status": out["status"], "output": str(OUT_DIR)}, indent=1))
