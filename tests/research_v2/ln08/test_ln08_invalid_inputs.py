"""Malformed inputs raise typed failures with batch location - no silent defaults."""
from __future__ import annotations

import pytest

from ln08_helpers import make_features


def test_missing_answer_rejects():
    from research_v2.methods.ln08.dataset import DatasetError, DiagnosticCase

    features = make_features()
    del features["answer"]
    with pytest.raises(DatasetError, match="answer"):
        DiagnosticCase.from_features(features, case_id="bad")


def test_non_string_answer_rejects():
    from research_v2.methods.ln08.dataset import DatasetError, DiagnosticCase

    with pytest.raises(DatasetError, match="answer"):
        DiagnosticCase.from_features(make_features(answer=42), case_id="bad")


def test_missing_evidence_rejects():
    from research_v2.methods.ln08.dataset import DatasetError, DiagnosticCase

    features = make_features()
    del features["evidence"]
    with pytest.raises(DatasetError, match="evidence"):
        DiagnosticCase.from_features(features, case_id="bad")


def test_non_boolean_verified_rejects():
    from research_v2.methods.ln08.dataset import DatasetError, DiagnosticCase

    features = make_features()
    features["evidence"]["verified"] = "yes"
    with pytest.raises(DatasetError, match="verified"):
        DiagnosticCase.from_features(features, case_id="bad")


def test_missing_source_id_rejects():
    from research_v2.methods.ln08.dataset import DatasetError, DiagnosticCase

    features = make_features()
    del features["evidence"]["source_id"]
    with pytest.raises(DatasetError, match="source_id"):
        DiagnosticCase.from_features(features, case_id="bad")


def test_batch_error_carries_index_and_case_location():
    from research_v2.contracts.types import StudyInput
    from research_v2.methods.ln08.dataset import DatasetError
    from research_v2.methods.ln08.proposed import predict_batch

    good = StudyInput("LN-08", "ok", "test", "g", make_features())
    bad = StudyInput("LN-08", "bad", "test", "g", {"answer": 123})
    with pytest.raises(DatasetError, match=r"input\[1\].*'bad'"):
        predict_batch([good, bad], {})


def test_unknown_native_label_raises_typed_error():
    from research_v2.methods.ln08.labels import LabelError, validate_native_decision

    with pytest.raises(LabelError, match="not in native label space"):
        validate_native_decision("mystery_label")


def test_wrong_study_id_rejects():
    from research_v2.contracts.types import StudyInput
    from research_v2.methods.ln08.dataset import DatasetError
    from research_v2.methods.ln08.proposed import predict_one

    inp = StudyInput("LN-06", "t", "test", "g", make_features())
    with pytest.raises(DatasetError, match="study_id"):
        predict_one(inp, {})
