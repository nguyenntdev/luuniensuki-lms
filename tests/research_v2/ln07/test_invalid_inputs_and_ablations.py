"""Invalid-input handling: typed failures, never silent defaults (spec G.5).

Malformed rows reject the batch with their location; unknown decision labels
raise typed errors; ablation divergence is verified on targeted
counterexamples (each ablation must move at least one sensitive case).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pytest  # noqa: E402

from research_v2.contracts.types import StudyInput  # noqa: E402
from research_v2.methods.ln07.baselines import b0_solve, c1_solve  # noqa: E402
from research_v2.methods.ln07.dataset import DatasetError  # noqa: E402
from research_v2.methods.ln07.labels import (  # noqa: E402
    LabelError,
    map_decision,
    to_contract_decision,
)
from research_v2.methods.ln07.proposed import predict_batch  # noqa: E402
from tests.research_v2.ln07.ln07_helpers import (  # noqa: E402
    make_case,
    make_input,
    policy_solve,
)


def _study_input(features: dict, case_id: str = "bad") -> StudyInput:
    return StudyInput(
        study_id="LN-07", case_id=case_id, split_id="test", group_id="g", features=features
    )


class TestTypedFailures:
    def test_missing_options_rejects_batch(self):
        features = {"content": {"id": "x", "type": "urn"}, "device": {}, "task": {}, "options": []}
        with pytest.raises(DatasetError):
            predict_batch([_study_input(features)], {})

    def test_duplicate_option_ids_rejected_with_location(self):
        features = {
            "content": {"id": "x", "type": "urn"},
            "device": {"webgl": True, "network_kbps": 3000},
            "task": {"type": "t", "required_affordances": ["a"], "transcript_required": False},
            "options": [
                {"id": "same", "modality": "3d", "kb": 1, "affordances": ["a"]},
                {"id": "same", "modality": "2d", "kb": 1, "affordances": ["a"]},
            ],
        }
        with pytest.raises(DatasetError) as ei:
            predict_batch([_study_input(features)], {})
        assert "duplicate option ids" in str(ei.value)

    def test_bad_option_kb_rejected(self):
        features = {
            "content": {"id": "x", "type": "urn"},
            "device": {"webgl": True, "network_kbps": 3000},
            "task": {"type": "t", "required_affordances": [], "transcript_required": False},
            "options": [{"id": "o", "modality": "3d", "kb": -5, "affordances": []}],
        }
        with pytest.raises(DatasetError):
            predict_batch([_study_input(features)], {})

    def test_non_study_input_rejected(self):
        with pytest.raises(DatasetError):
            predict_batch([{"case_id": "x", "features": {}}], {})

    def test_unknown_decision_label_raises_typed_error(self):
        with pytest.raises(LabelError):
            map_decision("not_a_real_label")

    def test_unknown_contract_mapping_raises_typed_error(self):
        with pytest.raises(LabelError):
            to_contract_decision("not_a_real_label")

    def test_predict_one_type_error(self):
        from research_v2.methods.ln07.proposed import predict_one

        with pytest.raises(DatasetError):
            predict_one({"not": "a StudyInput"})


class TestLabelOntology:
    def test_native_labels_within_contract_recognisable(self):
        # All five gold strata map deterministically into the contract space.
        for native, contract in (
            ("choose_feasible_modality", "complete_multimodal"),
            ("choose_accessible_fallback", "fallback_acceptable"),
            ("choose_low_data_fallback", "fallback_acceptable"),
            ("choose_accessible_audio_text", "fallback_acceptable"),
            ("choose_curated_archive_fallback", "fallback_acceptable"),
            ("reject_inaccessible_option", "reject_inaccessible"),
            ("reject_audio_equivalence", "reject_missing_affordance"),
            ("reject_missing_affordance", "reject_missing_affordance"),
        ):
            assert to_contract_decision(native) == contract

    def test_rejection_families_stay_distinct(self):
        # Accessibility rejection must never collapse into a cognitive-
        # affordance rejection in the contract mapping.
        assert (
            to_contract_decision("reject_inaccessible_option") != "reject_missing_affordance"
        )


class TestAblationDivergence:
    def _transcript_case(self):
        return make_case(
            required=["visual_detail", "spatial_relation"],
            transcript_required=True,
            screen_reader=True,
            options=[
                {
                    "id": "t_audio",
                    "modality": "audio",
                    "kb": 480,
                    "keyboard": True,
                    "requires_webgl": False,
                    "available": True,
                    "transcript": False,
                    "screen_reader_ready": False,
                    "affordances": ["visual_detail", "spatial_relation", "description"],
                },
            ],
            case_id="abl-a1",
        )

    def _keyboard_case(self):
        return make_case(
            required=["visual_detail", "spatial_relation"],
            keyboard_only=True,
            options=[
                {
                    "id": "k_3d",
                    "modality": "3d",
                    "kb": 1850,
                    "keyboard": False,
                    "requires_webgl": True,
                    "available": True,
                    "affordances": ["visual_detail", "spatial_relation", "relief_depth"],
                },
            ],
            case_id="abl-a2",
        )

    def _inscription_case(self):
        return make_case(
            required=["visual_detail", "inscription"],
            options=[
                {
                    "id": "i_rubbing",
                    "modality": "2d",
                    "sub_type": "rubbing",
                    "kb": 95,
                    "keyboard": True,
                    "requires_webgl": False,
                    "available": True,
                    "alt_text": "image present",
                    "affordances": ["visual_detail", "spatial_relation"],
                },
                {
                    "id": "i_3d",
                    "modality": "3d",
                    "kb": 1850,
                    "keyboard": True,
                    "requires_webgl": True,
                    "available": False,
                    "affordances": ["visual_detail", "inscription"],
                },
            ],
            case_id="abl-a3",
        )

    def test_each_ablation_changes_at_least_one_sensitive_case(self):
        sensitive = {
            "ablations_a1": self._transcript_case(),
            "ablations_a2": self._keyboard_case(),
            "ablations_a3": self._inscription_case(),
        }
        for method, case in sensitive.items():
            proposed = policy_solve("proposed", case)
            ablated = policy_solve(method, case)
            assert proposed["decision"] != ablated["decision"], method
            assert "ablation" in ablated["reason_codes"], method

    def test_ablation_baselines_share_label_space(self):
        case = self._inscription_case()
        for method in ("baselines_b0", "baselines_c1"):
            result = policy_solve(method, case)
            assert result["decision"] in {
                "choose_feasible_modality",
                "choose_accessible_fallback",
                "choose_low_data_fallback",
                "choose_accessible_audio_text",
                "choose_curated_archive_fallback",
                "reject_inaccessible_option",
                "reject_audio_equivalence",
                "reject_missing_affordance",
            }

    def test_c1_and_b0_solvers_run_on_validated_cases(self):
        case = self._inscription_case()
        assert b0_solve(case)["decision"] == "choose_feasible_modality"
        # C1 sees the 3D primary unavailable -> static fallback; the visual
        # requirement set (inscription excluded) is covered -> feasible.
        assert c1_solve(case)["task_feasible"] is True
        assert c1_solve(case)["decision"] == "choose_feasible_modality"


class TestBatchIntegrity:
    def test_invalid_row_rejects_whole_batch(self):
        good = make_input(make_case(required=["visual_detail"], case_id="good"))
        bad_features = {"content": {"id": "x", "type": "urn"}, "device": {}}
        bad = _study_input(bad_features, case_id="bad")
        with pytest.raises(DatasetError):
            predict_batch([good, bad], {})
