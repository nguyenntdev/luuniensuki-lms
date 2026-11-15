"""P14 rubric and schema tests: verdict semantics, applicability, versioning."""
from __future__ import annotations

from pathlib import Path

import pytest

from research_v3.methods.p14.rubric import (
    LEARNED_PARAMETERS,
    RUBRIC_VERSION,
    criteria_for_media_type,
    load_rubric,
    verdict_is_negative,
)
from research_v3.methods.p14.schema import (
    AuditCriterion,
    CriterionResult,
    CriterionVerdict,
    LearningObject,
    MediaAsset,
    ObjectAuditVerdict,
    RemediationItem,
    SchemaError,
)


def _rubric() -> list[AuditCriterion]:
    return load_rubric()


def test_rubric_loads_with_expected_frameworks():
    criteria = _rubric()
    frameworks = {c.framework for c in criteria}
    assert frameworks == {"udl-representation", "udl-engagement", "udl-action", "wcag22"}
    assert len(criteria) >= 12


def test_rubric_version_is_pinned_and_no_learned_parameters():
    assert RUBRIC_VERSION == "p14-udl-rubric-1.0.0"
    assert LEARNED_PARAMETERS == {}


def test_rubric_rejects_version_mismatch(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("rubric_version: wrong\ncriteria: []\n", encoding="utf-8")
    with pytest.raises(SchemaError):
        load_rubric(bad)


def test_criteria_applicability_by_media_type():
    criteria = _rubric()
    image_only = criteria_for_media_type(criteria, {"image"})
    ids = {c.criterion_id for c in image_only}
    assert "udl-rep-alt-text" in ids  # images need alt text
    assert "udl-rep-transcript" not in ids  # no audio/video -> N/A
    assert "udl-eng-low-bandwidth" in ids  # universal criterion
    text_only = criteria_for_media_type(criteria, {"text"})
    assert "udl-rep-alt-text" not in {c.criterion_id for c in text_only}


def test_verdict_semantics_only_fail_is_negative():
    assert verdict_is_negative(CriterionVerdict.FAIL)
    assert not verdict_is_negative(CriterionVerdict.NOT_APPLICABLE)
    assert not verdict_is_negative(CriterionVerdict.ABSTAIN)


def test_fail_requires_remediation():
    with pytest.raises(SchemaError):
        CriterionResult(
            criterion_id="udl-rep-alt-text",
            object_id="obj",
            verdict=CriterionVerdict.FAIL,
        )
    ok = CriterionResult(
        criterion_id="udl-rep-alt-text",
        object_id="obj",
        verdict=CriterionVerdict.FAIL,
        remediation="Add alt text",
    )
    assert ok.remediation == "Add alt text"


def test_media_asset_requires_rights_and_known_type():
    with pytest.raises(SchemaError):
        MediaAsset(asset_id="asset-a", media_type="image", rights="")
    with pytest.raises(SchemaError):
        MediaAsset(asset_id="asset-a", media_type="hologram", rights="CC0")


def test_learning_object_requires_labelled_origin_and_rights():
    asset = MediaAsset(asset_id="a1", media_type="text", rights="Synthetic")
    with pytest.raises(SchemaError):
        LearningObject(
            object_id="obj-1", title="t", origin="mystery-source", source_url=None,
            rights="Synthetic", assets=(asset,),
        )
    with pytest.raises(SchemaError):
        LearningObject(
            object_id="obj-1", title="t", origin="synthetic:test", source_url=None,
            rights="", assets=(asset,),
        )
    with pytest.raises(SchemaError):
        LearningObject(
            object_id="obj-1", title="t", origin="synthetic:test", source_url=None,
            rights="Synthetic", assets=(),
        )


def test_object_verdict_counts_must_reconcile():
    with pytest.raises(SchemaError):
        ObjectAuditVerdict(
            object_id="obj", total_applicable=5, passed=2, failed=1,
            not_applicable=1, abstained=0, missing_affordances=("x",), verdict="FAIL",
        )
    ok = ObjectAuditVerdict(
        object_id="obj", total_applicable=4, passed=2, failed=1,
        not_applicable=1, abstained=0, missing_affordances=("x",), verdict="FAIL",
    )
    assert ok.passed + ok.failed + ok.not_applicable + ok.abstained == ok.total_applicable


def test_remediation_item_severity_is_constrained():
    with pytest.raises(SchemaError):
        RemediationItem(object_id="o", criterion_id="c", framework="wcag22", severity="grave", action="x")
