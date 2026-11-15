"""P13: every shipped P13 document/code file must pass the construct guard.

Guards the corpus itself: if any markdown/yaml/json/py file under the P13
scope contains a construct-overclaim ("measured SRL", causal phrasing, ...),
this test fails. construct_validity.py itself is exempt because it must list
the forbidden phrases verbatim to reject them.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from research_v3.methods.p13.construct_validity import (
    ConstructValidityViolation,
    enforce_proxy_guard,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
P13_DIRS = [
    PROJECT_ROOT / "research_v3" / "methods" / "p13",
    PROJECT_ROOT / "research_v3" / "experiments" / "p13",
    PROJECT_ROOT / "research_v3" / "manuscripts" / "p13",
]


def _p13_files() -> list[Path]:
    files: list[Path] = []
    for d in P13_DIRS:
        for pattern in ("*.py", "*.md", "*.yaml", "*.json"):
            files.extend(f for f in d.glob(pattern) if f.name != "construct_validity.py")
    return sorted(files)


def test_p13_corpus_size_is_sane():
    files = _p13_files()
    assert len(files) >= 8, f"P13 corpus unexpectedly small: {files}"


@pytest.mark.parametrize("path", _p13_files(), ids=lambda p: p.name)
def test_p13_file_passes_construct_guard(path: Path):
    text = path.read_text(encoding="utf-8")
    try:
        enforce_proxy_guard(str(path), text)
    except ConstructValidityViolation as exc:
        pytest.fail(f"{path.name} overclaims: {exc}")


def test_run_artifacts_pass_guard_when_present():
    runs = PROJECT_ROOT / "research_artifacts_v3" / "runs" / "p13"
    if not runs.is_dir():
        pytest.skip("run artifacts not generated yet")
    for f in sorted(runs.glob("*.json")):
        enforce_proxy_guard(f.name, f.read_text(encoding="utf-8"))
    findings = runs / "FINDINGS.md"
    if findings.is_file():
        enforce_proxy_guard("FINDINGS.md", findings.read_text(encoding="utf-8"))
