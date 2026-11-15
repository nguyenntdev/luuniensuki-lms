"""Oracle-leakage detection for LN-05: gold material must never reach methods.

Also guards the study data itself: inputs carry no oracle keys; gold is
evaluator-only; label spaces are respected.
"""
from __future__ import annotations

import pytest

from research_v2.contracts.types import ContractError, StudyInput
from tests.research_v2.ln05.conftest import load_gold, load_rows


def test_dataset_inputs_contain_no_oracle_keys():
    from research_v2.contracts.types import FORBIDDEN_INPUT_KEYS

    for r in load_rows():
        assert not (set(r) & FORBIDDEN_INPUT_KEYS), r["case_id"]
        inner = r["input"]
        assert not (set(inner) & FORBIDDEN_INPUT_KEYS), r["case_id"]
        # nested feature objects are clean too
        for section in ("badge", "learner", "skill_evidence", "content"):
            obj = inner.get(section)
            if isinstance(obj, dict):
                assert not (set(obj) & FORBIDDEN_INPUT_KEYS), (r["case_id"], section)
        for ev in inner.get("reward_events", []):
            assert not (set(ev) & FORBIDDEN_INPUT_KEYS), (r["case_id"], "reward_events")


def test_study_input_contract_rejects_oracle_features():
    with pytest.raises(ContractError):
        StudyInput("LN-05", "c", "test", "g", {"expected_decision": "grant_if_eligible"})
    with pytest.raises(ContractError):
        StudyInput("LN-05", "c", "test", "g", {"input": {"oracle": {}}})


def test_gold_is_evaluator_only_and_disjoint_from_inputs():
    rows = load_rows()
    golds = load_gold()
    assert len(golds) == len(rows) == 120
    for r in rows:
        assert "expected_decision" not in r
        assert "oracle" not in r
    # Every gold case has exactly one input; no extra gold cases exist.
    assert set(golds) == {r["case_id"] for r in rows}


def test_gold_decisions_stay_inside_declared_families():
    from research_v2.methods.ln05.labels import LEGACY_TO_V2

    for decision in set(load_gold().values()):
        assert decision in LEGACY_TO_V2, decision


def test_v2_label_projection_covers_every_gold_decision():
    from research_v2.contracts.label_space import LN05_DECISIONS, validate_decision
    from research_v2.methods.ln05.labels import to_v2_decision

    for decision in set(load_gold().values()):
        v2 = to_v2_decision(decision)
        assert v2 in LN05_DECISIONS
        validate_decision("LN-05", v2)


def test_unknown_label_raises_typed_error():
    from research_v2.methods.ln05.labels import DecisionError, to_v2_decision

    with pytest.raises(DecisionError):
        to_v2_decision("mystery_label")
