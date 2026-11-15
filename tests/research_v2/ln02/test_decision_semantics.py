"""Core decision semantics: valid labels, nominal flow, batch invariants."""
from __future__ import annotations

import pytest

from research_v2.contracts.label_space import LN02_DECISIONS
from research_v2.contracts.types import StudyPrediction
from research_v2.methods.ln02 import proposed
from research_v2.methods.ln02.baselines_b0 import predict_batch as b0
from research_v2.methods.ln02.baselines_c1 import predict_batch as c1
from research_v2.methods.ln02.ablations_a1 import predict_batch as a1
from research_v2.methods.ln02.ablations_a2 import predict_batch as a2
from research_v2.methods.ln02.ablations_a3 import predict_batch as a3
from ln02_helpers import (
    make_input,
    nominal_features,
)


@pytest.mark.parametrize("predict_batch", [proposed.predict_batch, b0, c1, a1, a2, a3])
def test_nominal_case_produces_valid_structured_prediction(predict_batch):
    inp = make_input()
    preds = predict_batch([inp], {"seed": 11})
    assert len(preds) == 1
    pred = preds[0]
    assert isinstance(pred, StudyPrediction)
    assert pred.study_id == "LN-02"
    assert pred.case_id == inp.case_id
    assert pred.decision in LN02_DECISIONS
    assert isinstance(pred.reason_codes, tuple)
    assert pred.reason_codes  # every decision carries evidence
    assert pred.score is None or -10.0 <= pred.score <= 10.0


def test_nominal_case_recommends_eligible():
    pred = proposed.predict_batch([make_input()], {})[0]
    assert pred.decision == "recommend_eligible"
    assert pred.reason_codes[0] == "ELIGIBLE_RECOMMENDATION"
    assert pred.evidence_ids[0] == "task-nominal"


def test_batch_preserves_order_and_count():
    inputs = [make_input(case_id=f"c{i}") for i in range(7)]
    preds = proposed.predict_batch(inputs, {})
    assert [p.case_id for p in preds] == [i.case_id for i in inputs]
    assert all(p.decision in LN02_DECISIONS for p in preds)


def test_unknown_decision_label_rejected():
    from research_v2.methods.ln02.core import build_prediction, MethodContractError
    from research_v2.contracts.label_space import LabelSpaceError

    inp = make_input()
    with pytest.raises(LabelSpaceError):
        build_prediction(inp, decision="not_a_real_label", reason_codes=("X",))
    # explicit typed contract error path for malformed method input
    with pytest.raises(MethodContractError):
        proposed.predict_batch("not-a-list", {})  # type: ignore[arg-type]


def test_metrics_module_diagnostics():
    from research_v2.methods.ln02 import metrics as m

    summary = m.summarize(
        ["recommend_eligible", "remediate_first", "abstain_insufficient_data"],
        ["recommend_eligible", "remediate_first", "abstain_insufficient_data"],
    )
    assert summary["n_correct"] == 3
    safety = summary["prerequisite_safety"]
    assert safety["safe"] is True
    cov = summary["abstention_coverage"]
    assert cov["coverage"] == 1.0

    bad = m.prerequisite_safety(
        ["recommend_eligible", "recommend_eligible"],
        ["remediate_first", "recommend_eligible"],
    )
    assert bad["n_false_eligible"] == 1
    assert bad["safe"] is False
