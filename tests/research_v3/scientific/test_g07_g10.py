"""V3-G07/G08/G09/G10: evaluation, annotations, ethics, render tests."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from research_v3.scripts.annotations import (
    AnnotatorDecision,
    AnnotationError,
    AnnotationItem,
    blind_adjudication_report,
    cohen_kappa,
    krippendorff_alpha,
)
from research_v3.scripts.evaluate import EvaluationError, run_evaluation
from research_v3.scripts.render import RenderError, load_artifacts
from research_v3.scripts.ethics import run_ethics_audit

REPO_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------- G07


def _aligned(n=60, a_rate=0.9, b_rate=0.6, seed=5):
    import random

    rng = random.Random(seed)
    gold, a, b = {}, {}, {}
    for i in range(n):
        cid = f"c{i:03d}"
        truth = "accept" if rng.random() < 0.5 else "reject"
        gold[cid] = truth
        a[cid] = truth if rng.random() < a_rate else "reject"
        b[cid] = truth if rng.random() < b_rate else "reject"
    return gold, a, b


def test_evaluation_positive_and_null_preserved():
    gold, a, b = _aligned()
    report = run_evaluation(gold=gold, pred_a=a, pred_b=b, label_a="A", label_b="B", seed=7)
    assert report["n"] == 60
    assert report["mcnemar"] is not None
    assert report["family_control"]["method"] == "holm"
    assert report["null_result"]["is_null_or_negative"] in (True, False)

    # identical predictions => explicit null/negative preserved, not dropped
    report_tie = run_evaluation(gold=gold, pred_a=a, pred_b=dict(a), label_a="A", label_b="B", seed=7)
    assert report_tie["null_result"]["is_null_or_negative"] is True


def test_evaluation_rejects_misaligned_predictions():
    gold, a, b = _aligned()
    b_missing = dict(b)
    b_missing.pop(next(iter(b_missing)))
    with pytest.raises(EvaluationError):
        run_evaluation(gold=gold, pred_a=a, pred_b=b_missing, label_a="A", label_b="B", seed=7)
    extra = dict(b)
    extra["zzz"] = "accept"
    with pytest.raises(EvaluationError):
        run_evaluation(gold=gold, pred_a=a, pred_b=extra, label_a="A", label_b="B", seed=7)


def test_evaluate_cli_exit_codes(tmp_path):
    gold, a, b = _aligned()
    d = tmp_path
    for name, data in (("gold", gold), ("a", a), ("b", b)):
        field = "expected_decision" if name == "gold" else "decision"
        (d / f"{name}.jsonl").write_text(
            "".join(json.dumps({"case_id": k, field: v}) + "\n" for k, v in data.items())
        )
    ok = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.evaluate",
         "--gold", str(d / "gold.jsonl"), "--proposed", str(d / "a.jsonl"),
         "--baseline", str(d / "b.jsonl"), "--output", str(d / "rep.json")],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert ok.returncode == 0, ok.stderr
    assert json.loads((d / "rep.json").read_text())["case_count"] == 60

    (d / "gold2.jsonl").write_text((d / "gold.jsonl").read_text() + json.dumps({"case_id": "zz", "expected_decision": "accept"}))
    bad = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.evaluate",
         "--gold", str(d / "gold2.jsonl"), "--proposed", str(d / "a.jsonl"),
         "--baseline", str(d / "b.jsonl")],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert bad.returncode == 13


# ---------------------------------------------------------------- G08


def test_cohen_kappa_known_values():
    assert cohen_kappa(["a"] * 10, ["a"] * 10) is None  # degenerate marginals
    same = ["a", "b", "a", "b", "a", "b", "a", "b"]
    assert cohen_kappa(same, same) == 1.0
    kappa = cohen_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"])
    assert kappa == 0.0  # exactly chance agreement


def test_krippendorff_alpha_extremes():
    perfect = [{"A": "x", "B": "x"}, {"A": "y", "B": "y"}, {"A": "x", "B": "x"}]
    assert krippendorff_alpha(perfect) == 1.0
    awful = [{"A": "x", "B": "y"}, {"A": "y", "B": "x"}, {"A": "x", "B": "y"}]
    assert krippendorff_alpha(awful) < 0.0  # chance-worse, reported verbatim
    too_few = [{"A": "x", "B": "x"}]
    assert krippendorff_alpha(too_few) is None
    with pytest.raises(AnnotationError):
        krippendorff_alpha(perfect, level="bogus")


def test_blind_adjudication_rejects_nonblind_and_empty_tokens():
    items = {"i1": AnnotationItem("i1", "t")}
    with pytest.raises(AnnotationError):
        blind_adjudication_report([AnnotatorDecision("i1", "", "x")], items)
    with pytest.raises(AnnotationError):
        blind_adjudication_report([AnnotatorDecision("i1", "A", "x", blind=False)], items)


def test_blind_adjudication_reports_all_disagreements():
    items = {f"i{k}": AnnotationItem(f"i{k}", "t") for k in range(4)}
    decisions = []
    for k in range(4):
        decisions.append(AnnotatorDecision(f"i{k}", "A", "accept"))
        decisions.append(AnnotatorDecision(f"i{k}", "B", "reject" if k in (0, 2) else "accept"))
    report = blind_adjudication_report(decisions, items)
    assert report.n_items == 4
    assert len(report.disagreements) == 2
    assert {d["item_id"] for d in report.disagreements} == {"i0", "i2"}
    assert report.agreement_rate == 0.5


# ---------------------------------------------------------------- G09


def test_ethics_audit_blocked_without_records(tmp_path):
    report = run_ethics_audit(tmp_path)
    assert report["status"] == "BLOCKED"
    assert report["records_found"] == 0


def test_ethics_audit_detects_tampered_document(tmp_path):
    import hashlib

    doc = tmp_path / "signed_approval.pdf"
    doc.write_bytes(b"doc")
    record = {
        "protocol_id": "P1", "approver_role": "ethics lead", "signed_at": "2026-11-01",
        "scope": ["P11"], "document_sha256": "0" * 64, "document_file": "signed_approval.pdf",
    }
    (tmp_path / "approval_x.json").write_text(json.dumps(record))
    report = run_ethics_audit(tmp_path)
    assert report["status"] == "TAMPERED"

    record["document_sha256"] = hashlib.sha256(doc.read_bytes()).hexdigest()
    (tmp_path / "approval_x.json").write_text(json.dumps(record))
    assert run_ethics_audit(tmp_path, papers=["P11"])["status"] == "APPROVED_FOR_SCOPED_PAPERS"
    uncovered = run_ethics_audit(tmp_path, papers=["P12"])
    assert uncovered["status"] == "BLOCKED"


def test_ethics_cli_exit_codes(tmp_path):
    blocked = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.ethics", "--ethics-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert blocked.returncode == 20
    # the real (empty) governance dir must also be BLOCKED
    real = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.ethics"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert real.returncode == 20


# ---------------------------------------------------------------- G10


def test_render_rejects_non_numeric_artifacts(tmp_path):
    good = tmp_path / "m.json"
    good.write_text(json.dumps({"accuracy": 0.9, "per_class": {"a": 0.5}}))
    values, sources = load_artifacts([good])
    assert values["m.accuracy"] == 0.9 and len(sources) == 1

    for payload in (
        {"accuracy": "best"},
        {"accuracy": None},
        {"flag": True},
        {"deep": {"nested": {"x": "nope"}}},
    ):
        bad = tmp_path / f"bad_{abs(hash(json.dumps(payload)))}.json"
        bad.write_text(json.dumps(payload))
        with pytest.raises(RenderError):
            load_artifacts([bad])


def test_render_cli_writes_derived_files(tmp_path):
    art = tmp_path / "metrics.json"
    art.write_text(json.dumps({"accuracy": 0.83, "n": 100}))
    out = tmp_path / "figs"
    ok = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.render",
         "--artifacts", str(art), "--title", "unit demo", "--output-dir", str(out)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert ok.returncode == 0, ok.stderr
    md = (out / "unit-demo.md").read_text()
    assert "0.830000" in md
    svg = (out / "unit-demo.svg").read_text()
    assert "<svg" in svg and "0.8300" in svg

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"accuracy": "claimed verbally"}))
    failed = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.render", "--artifacts", str(bad), "--output-dir", str(out)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert failed.returncode == 14
