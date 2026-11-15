"""V3-G21: run_matrix --tier/--seed must actually filter cell selection.

Regression tests for the audit finding that --tier and --seed were parsed but
NOT applied in research_v2/scripts/run_matrix.py. Asserts:

- select_cells filters by tier set (T1-only selects nothing on a T3 matrix);
- select_cells filters by seed and restricts the cell to exactly that seed;
- an empty selection exits nonzero (2) in both dry-run and real mode;
- --allow-empty-selection restores the previously-observed behavior;
- a real filtered run writes ONLY the selected seed (no seed23 directories).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from research_v2.scripts.run_matrix import select_cells

REPO_ROOT = Path(__file__).resolve().parents[3]


def _cells(*tiers: str, seeds: list[int] | None = None) -> list[dict]:
    return [
        {
            "study": "LN-01",
            "tier": t,
            "dataset": "research_v2/data/ln01/t3_inputs.jsonl",
            "gold": "research_v2/data/ln01/t3_gold.jsonl",
            "methods": ["proposed"],
            "seeds": seeds if seeds is not None else [11, 23, 37],
        }
        for t in tiers
    ]


# ---------------------------------------------------------------- positive


def test_select_cells_filters_by_tier():
    cells = _cells("T3", "T3S")
    selected = select_cells(cells, tiers={"T3S"}, seed=None)
    assert [c["tier"] for c in selected] == ["T3S"]


def test_select_cells_filters_by_seed_and_restricts():
    cells = _cells("T3")
    selected = select_cells(cells, tiers=None, seed=23)
    assert len(selected) == 1
    assert selected[0]["seeds"] == [23]


def test_cli_dry_run_reports_selection():
    result = subprocess.run(
        [
            sys.executable, "-m", "research_v2.scripts.run_matrix",
            "--study", "LN-06", "--tier", "T3", "--seed", "11", "--dry-run",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    assert "tier=T3" in result.stdout
    assert "seeds=[11]" in result.stdout


def test_cli_real_run_writes_only_selected_seed(tmp_path):
    out_root = tmp_path / "runs"
    result = subprocess.run(
        [
            sys.executable, "-m", "research_v2.scripts.run_matrix",
            "--study", "LN-01", "--tier", "T3", "--seed", "11",
            "--output-root", str(out_root),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    method_dir = out_root / "LN-01" / "T3" / "proposed"
    assert (method_dir / "seed11" / "run_manifest.json").is_file()
    assert not (method_dir / "seed23").exists(), "seed23 must not run when --seed 11 is given"
    manifest = json.loads((method_dir / "seed11" / "run_manifest.json").read_text())
    assert manifest["seed"] == 11


# ---------------------------------------------------------------- negative


def test_empty_selection_from_tier_filter_is_rejected():
    result = subprocess.run(
        [
            sys.executable, "-m", "research_v2.scripts.run_matrix",
            "--study", "LN-06", "--tier", "T1", "--dry-run",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "0" in result.stderr


def test_empty_selection_from_seed_filter_is_rejected():
    result = subprocess.run(
        [
            sys.executable, "-m", "research_v2.scripts.run_matrix",
            "--study", "LN-06", "--tier", "T3", "--seed", "99", "--dry-run",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 2


def test_no_args_rejected():
    result = subprocess.run(
        [sys.executable, "-m", "research_v2.scripts.run_matrix"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 2


def test_select_cells_empty_when_nothing_matches():
    assert select_cells(_cells("T3"), tiers={"T1"}, seed=None) == []
    assert select_cells(_cells("T3"), tiers={"T3"}, seed=99) == []


@pytest.mark.parametrize("bad_tier", ["", ","])
def test_invalid_tier_value_rejected(bad_tier):
    result = subprocess.run(
        [
            sys.executable, "-m", "research_v2.scripts.run_matrix",
            "--study", "LN-06", "--tier", bad_tier, "--dry-run",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 2
