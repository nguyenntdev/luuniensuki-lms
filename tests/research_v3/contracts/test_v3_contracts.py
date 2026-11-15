"""Tests for Research V3 immutable cards, license gate and splitter."""
from __future__ import annotations

import pytest

from research_v3.contracts.cards import (
    ContractError,
    DatasetCard,
    EvidenceCard,
    ExperimentCard,
    FrozenSplit,
)
from research_v3.datasets.registry import LicenseGateError, require_approved, summary
from research_v3.eval.leakage import LeakageError, audit_rows
from research_v3.eval.splitters import SplitError, assert_no_leakage, freeze_hash, group_split
from research_v3.eval.statistics import family_control, proportion_ci

H64 = "a" * 64


def _approved_card(**over):
    base = dict(
        dataset_id="d1",
        provider="p",
        source_url="https://example.org/d",
        doi=None,
        version="1",
        retrieved_at="2026-01-01T00:00:00Z",
        license_text_sha256=H64,
        allowed_uses=("academic_analysis",),
        redistribution_policy="CC BY 4.0",
        original_sha256=H64,
        transformed_sha256=None,
        sample_count=10,
        schema_version="1",
        consent_basis="public",
        units="student",
        group_keys=("id",),
        time_key=None,
        leakage_audit="done",
        source_attribution="cite",
        status="APPROVED",
    )
    base.update(over)
    return DatasetCard(**base)


def test_approved_card_requires_license_and_file_hash():
    _approved_card()
    with pytest.raises(ContractError):
        _approved_card(license_text_sha256="")
    with pytest.raises(ContractError):
        _approved_card(original_sha256="")


def test_blocked_card_requires_reason():
    with pytest.raises(ContractError):
        DatasetCard(
            dataset_id="d", provider="p", source_url="", doi=None, version="1",
            retrieved_at="t", license_text_sha256="", allowed_uses=(),
            redistribution_policy="", original_sha256="", transformed_sha256=None,
            sample_count=0, schema_version="", consent_basis="", units="",
            group_keys=(), time_key=None, leakage_audit="", source_attribution="",
            status="BLOCKED",
        )


def test_license_gate_fails_closed_on_blocked_dataset():
    approved = _approved_card()
    blocked = DatasetCard(
        dataset_id="blocked", provider="p", source_url="", doi=None, version="1",
        retrieved_at="t", license_text_sha256="", allowed_uses=(),
        redistribution_policy="", original_sha256="", transformed_sha256=None,
        sample_count=0, schema_version="", consent_basis="", units="",
        group_keys=(), time_key=None, leakage_audit="", source_attribution="",
        status="BLOCKED", blocked_reason="no license",
    )
    registry = [approved, blocked]
    assert len(require_approved(registry, ["d1"], paper_id="P01")) == 1
    with pytest.raises(LicenseGateError):
        require_approved(registry, ["blocked"], paper_id="P01")
    with pytest.raises(LicenseGateError):
        require_approved(registry, ["missing"], paper_id="P01")
    assert summary(registry)["by_status"] == {"APPROVED": 1, "BLOCKED": 1}


def test_experiment_card_validates_hashes():
    ExperimentCard(
        paper_id="P01", rq_id="RQ1", train_dataset_ids=("d1",), holdout_dataset_ids=("d1",),
        method_commit_sha="abc", method_hash=H64, baseline_version="b1", split_hash=H64,
        feature_cutoff="2026-01-01", prereg_sha256=H64, hyperparameter_budget="small",
        seed=11, hardware="cpu", wall_time_seconds=1.0, dependency_lock_sha256=H64,
        output_path="x", status="PASS",
    )
    with pytest.raises(ContractError):
        ExperimentCard(
            paper_id="P01", rq_id="RQ1", train_dataset_ids=(), holdout_dataset_ids=(),
            method_commit_sha="abc", method_hash="short", baseline_version="b1",
            split_hash=H64, feature_cutoff="x", prereg_sha256=H64,
            hyperparameter_budget="small", seed=11, hardware="cpu",
            wall_time_seconds=1.0, dependency_lock_sha256=H64, output_path="x",
        )


def test_evidence_card_requires_allowed_wording_and_valid_ci():
    EvidenceCard(
        paper_id="P01", claim_id="C1", source_type="experiment", source_sha256=H64,
        code_sha="abc", experiment_ids=("e1",), analysis_script="s.py",
        table_cell_ids=("t1",), denominator=100, ci=(0.1, 0.2),
        comparison_family="primary", allowed_wording="improves accuracy by X points",
    )
    with pytest.raises(ContractError):
        EvidenceCard(
            paper_id="P01", claim_id="C1", source_type="experiment", source_sha256=H64,
            code_sha="abc", experiment_ids=("e1",), analysis_script="s.py",
            table_cell_ids=("t1",), denominator=100, ci=None, comparison_family="primary",
            allowed_wording="",
        )
    with pytest.raises(ContractError):
        EvidenceCard(
            paper_id="P01", claim_id="C1", source_type="experiment", source_sha256=H64,
            code_sha="abc", experiment_ids=("e1",), analysis_script="s.py",
            table_cell_ids=("t1",), denominator=100, ci=(0.5, 0.2),
            comparison_family="primary", allowed_wording="x",
        )


def test_group_split_disjoint_and_deterministic():
    rows = [{"case_id": f"c{i}", "group_id": f"g{i % 50}"} for i in range(400)]
    split = group_split(rows, group_key="group_id", paper_id="P01")
    assert_no_leakage(split)
    assert freeze_hash(split) == freeze_hash(group_split(rows, group_key="group_id", paper_id="P01"))


def test_group_split_rejects_missing_group_key():
    with pytest.raises(SplitError):
        group_split([{"case_id": "c1"}], group_key="group_id", paper_id="P01")


def test_frozen_split_rejects_cross_partition_ids():
    with pytest.raises(ContractError):
        FrozenSplit(
            paper_id="P01", protocol="group",
            split_ids={"train": ("a",), "calibration": ("a",), "dev": ("b",), "test": ("c",)},
        )


def test_leakage_audit_detects_gold_and_duplicates():
    clean = [{"case_id": f"c{i}", "input": {"x": i}} for i in range(5)]
    assert audit_rows(clean)["status"] == "PASS"
    dirty = [
        {"case_id": "c1", "input": {"x": 1}},
        {"case_id": "c1", "input": {"x": 2}},
    ]
    with pytest.raises(LeakageError):
        audit_rows(dirty)
    with pytest.raises(LeakageError):
        audit_rows([{"case_id": "c1", "input": {"nested": {"gold": "Pass"}}}])


def test_statistics_helpers_are_sane():
    assert proportion_ci(0, 96)["wilson_ci_95"][1] > 0  # never [0, 0]
    holm = family_control([0.01, 0.04, 0.03])
    assert all(h >= raw for h, raw in zip(holm, [0.01, 0.04, 0.03]))
