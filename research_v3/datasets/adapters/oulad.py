"""OULAD adapter: real Open University Learning Analytics Dataset.

Source: Kuzilek, Hlosta & Zdrahal (2017), Scientific Data 4:170171.
License: CC BY 4.0. Raw files live in ``private_data/raw/oulad`` and are never
committed. The adapter produces leakage-aware learner-level rows with a frozen
observation cut-off so no future click/assessment leaks into the features.

IMPORTANT: ``final_result`` is the label and is withheld from ``features``.
Clicks are observational behaviour proxies, NOT measured self-regulation and NOT
an intervention effect.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RAW = PROJECT_ROOT / "private_data" / "raw" / "oulad" / "2013-2014"

LABEL_FIELD = "final_result"
FORBIDDEN_FEATURE_FIELDS = frozenset(
    {"final_result", "date", "id_student", "case_id"}
)

EARLY_WINDOW_DAYS = 60  # observation cut-off used for the leakage-safe feature set


class OuladSchemaError(ValueError):
    pass


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise OuladSchemaError(
            f"missing OULAD file {path}; run research_v3.datasets.fetchers.fetch first"
        )
    with path.open(encoding="utf-8", newline="") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def _extract_zip(raw_dir: Path) -> Path:
    """Return a directory containing the CSV files, unzipping once if needed."""
    if (raw_dir / "studentInfo.csv").is_file():
        return raw_dir
    archive = raw_dir / "oulad.zip"
    if not archive.is_file():
        raise OuladSchemaError(f"no OULAD CSVs or archive under {raw_dir}")
    import zipfile

    target = raw_dir / "_extracted"
    if not (target / "studentInfo.csv").is_file():
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(target)
    return target


def load_students(raw_dir: Path | None = None) -> list[dict[str, Any]]:
    """Return one row per (student, module, presentation) with early-window features."""
    base = _extract_zip(Path(raw_dir or DEFAULT_RAW))
    info = _read_csv(base / "studentInfo.csv")
    vle_path = base / "studentVle.csv"

    early_clicks: dict[tuple[str, str, str], int] = {}
    early_sites: dict[tuple[str, str, str], int] = {}
    if vle_path.is_file():
        with vle_path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                try:
                    day = int(row["date"])
                except (TypeError, ValueError):
                    continue
                if day < 0 or day > EARLY_WINDOW_DAYS:
                    continue
                key = (row["code_module"], row["code_presentation"], row["id_student"])
                early_clicks[key] = early_clicks.get(key, 0) + int(row["sum_click"] or 0)
                early_sites[key] = early_sites.get(key, 0) + 1

    rows: list[dict[str, Any]] = []
    for student in info:
        key = (
            student["code_module"],
            student["code_presentation"],
            student["id_student"],
        )
        features = {
            "code_module": student["code_module"],
            "code_presentation": student["code_presentation"],
            "gender": student["gender"],
            "region": student["region"],
            "highest_education": student["highest_education"],
            "imd_band": student["imd_band"],
            "age_band": student["age_band"],
            "num_of_prev_attempts": int(student["num_of_prev_attempts"]),
            "studied_credits": int(student["studied_credits"]),
            "disability": student["disability"],
            "early_click_total": early_clicks.get(key, 0),
            "early_active_sites": early_sites.get(key, 0),
            "observation_window_days": EARLY_WINDOW_DAYS,
        }
        leaked = set(features) & FORBIDDEN_FEATURE_FIELDS
        if leaked:
            raise OuladSchemaError(f"label/identifier leaked into features: {sorted(leaked)}")
        rows.append(
            {
                "case_id": f"oulad-{student['code_module']}-{student['code_presentation']}-{student['id_student']}",
                "group_id": student["id_student"],  # learner-level grouping
                "time_key": student["code_presentation"],  # chronological split
                "input": features,
                # gold kept OUTSIDE ``input`` so a model can never read it
                "label": student[LABEL_FIELD],
            }
        )
    return rows


def label_distribution(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    dist: dict[str, int] = {}
    for row in rows:
        dist[row["label"]] = dist.get(row["label"], 0) + 1
    return dict(sorted(dist.items()))


def assert_no_label_in_input(rows: Iterable[dict[str, Any]]) -> None:
    for row in rows:
        inp = row.get("input", {})
        if LABEL_FIELD in inp:
            raise OuladSchemaError(f"{row.get('case_id')}: label leaked into input")
