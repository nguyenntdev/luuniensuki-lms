"""Invalid inputs: malformed rows raise typed failures, never silent defaults.

Also covers the abstain/postpone family: unknown states/actions defer
(``postpone``) instead of guessing, and the postpone family stays distinct
from reject families (LN-10-04.C step 3).
"""
from __future__ import annotations

import pytest

from research_v2.methods.ln10.dataset import DatasetError, parse_case
from research_v2.methods.ln10.labels import LabelError, build_prediction
from research_v2.methods.ln10.proposed import decide_case, predict_one
from tests.research_v2.ln10.ln10_helpers import make_features


def _features(**project_transition_overrides):
    features = make_features()
    features.update(project_transition_overrides)
    return features


def test_missing_project_raises_typed_failure():
    features = make_features()
    del features["project"]
    with pytest.raises(DatasetError, match="project"):
        parse_case("no-project", features)


def test_missing_transition_raises_typed_failure():
    features = make_features()
    del features["transition"]
    with pytest.raises(DatasetError, match="transition"):
        parse_case("no-transition", features)


def test_missing_actor_raises_typed_failure():
    features = make_features()
    del features["actor"]
    with pytest.raises(DatasetError, match="actor"):
        parse_case("no-actor", features)


@pytest.mark.parametrize(
    "field", ["version", "state", "reflection_completed"]
)
def test_bad_project_field_types_raise(field):
    project = make_features()["project"]
    project[field] = None
    with pytest.raises(DatasetError, match=field):
        parse_case(f"bad-{field}", make_features(project=project))


def test_bad_expected_version_type_raises():
    transition = make_features()["transition"]
    transition["expected_version"] = "three"
    with pytest.raises(DatasetError, match="expected_version"):
        parse_case("bad-expected", make_features(transition=transition))


def test_unknown_state_postpones_instead_of_guessing():
    project = make_features()["project"]
    project["state"] = "hyperdrive"
    case = parse_case("unknown-state", make_features(project=project))
    result = decide_case(case)
    assert result["decision"] == "postpone"
    assert result["decision"] not in ("deny_transition", "request_reflection")


def test_unknown_action_postpones_instead_of_guessing():
    transition = make_features()["transition"]
    transition["action"] = "teleport"
    case = parse_case("unknown-action", make_features(transition=transition))
    result = decide_case(case)
    assert result["decision"] == "postpone"


def test_missing_version_info_postpones():
    transition = make_features()["transition"]
    del transition["expected_version"]
    case = parse_case("no-version", make_features(transition=transition))
    result = decide_case(case)
    assert result["decision"] == "postpone"
    assert "missing_version_info" in result["reason_codes"]


def test_illegal_fsm_edge_denied():
    project = make_features()["project"]
    project["state"] = "completed"  # no legal outgoing actionable edge
    case = parse_case("illegal-edge", make_features(project=project))
    result = decide_case(case)
    assert result["decision"] == "deny_transition"
    assert "illegal_state_transition" in result["reason_codes"]


def test_duplicate_event_log_ids_postpone():
    features = make_features(
        event_log=[
            {"event_id": "e1", "type": "edit"},
            {"event_id": "e1", "type": "edit"},
        ]
    )
    case = parse_case("dup-events", features)
    result = decide_case(case)
    assert result["decision"] == "postpone"
    assert "reordered_event_log" in result["reason_codes"]


def test_unknown_native_label_raises_label_error():
    with pytest.raises(LabelError):
        build_prediction(case_id="bad-label", decision="ship_it")


def test_predict_one_rejects_non_study_input():
    with pytest.raises(DatasetError):
        predict_one({"case_id": "not-a-studyinput"}, None)
