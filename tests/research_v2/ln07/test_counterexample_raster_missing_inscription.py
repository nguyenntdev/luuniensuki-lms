"""Mandatory counterexample (spec LN-07-03 Case 1): raster fallback HAS an image
but OMITS the inscription the task requires.

Expected scientific outcome:
- The proposed engine must NOT treat the raster as pedagogically complete.
- It must flag the missing inscription affordance and either route to a
  sufficient modality (text/audio carrying the inscription) or reject with
  ``reject_missing_affordance`` when no sufficient modality exists.
- B0 (image-presence check) and C1 (static raster without inscription
  equivalence) must both FAIL this case - that is the matched-subtask
  weakness under study.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tests.research_v2.ln07.ln07_helpers import (  # noqa: E402
    make_case,
    policy_solve,
)

REQUIRED = ["visual_detail", "spatial_relation", "inscription"]


def raster_missing_inscription_case(case_id: str = "raster-missing-inscription"):
    """Rubbing available with visual/spatial affordances but NO inscription."""
    options = [
        {
            "id": "urn_3d",
            "modality": "3d",
            "kb": 1850,
            "keyboard": True,
            "requires_webgl": True,
            "available": False,  # asset unavailable -> fallback territory
            "affordances": ["visual_detail", "spatial_relation", "relief_depth", "inscription"],
        },
        {
            "id": "urn_rubbing_2d",
            "modality": "2d",
            "sub_type": "rubbing",
            "kb": 95,
            "keyboard": True,
            "requires_webgl": False,
            "available": True,
            "alt_text": "Bản dập nổi hoa văn (ảnh hiện diện)",  # image EXISTS
            "affordances": ["visual_detail", "spatial_relation", "relief_depth"],
        },
        {
            "id": "urn_text",
            "modality": "text",
            "kb": 10,
            "keyboard": True,
            "requires_webgl": False,
            "available": True,
            "screen_reader_ready": True,
            "affordances": [
                "visual_detail",
                "spatial_relation",
                "relief_depth",
                "inscription",
            ],
        },
    ]
    return make_case(required=REQUIRED, webgl=True, options=options, case_id=case_id)


def raster_missing_inscription_no_alternative(case_id: str = "raster-missing-inscription-none"):
    """Same raster gap but NO sufficient modality anywhere in the option set."""
    case = raster_missing_inscription_case(case_id)
    options = [o for o in case.options if o.modality != "text"]
    from dataclasses import replace

    return replace(case, options=options)


class TestProposedNeverAcceptsIncompleteRaster:
    def test_proposed_does_not_accept_raster_as_complete(self):
        result = policy_solve("proposed", raster_missing_inscription_case())
        assert result["decision"] != "choose_curated_archive_fallback", (
            "raster without the required inscription must not be scored complete"
        )
        assert "missing_required_affordance" in result["reason_codes"] or any(
            rc.startswith("missing:") for rc in result["reason_codes"]
        )
        assert "missing_inscription_affordance" in result["reason_codes"]

    def test_proposed_routes_to_sufficient_modality_when_one_exists(self):
        result = policy_solve("proposed", raster_missing_inscription_case())
        assert result["decision"] == "choose_accessible_audio_text"
        assert result["selected_modality"] == "text"
        assert "routed_to_sufficient_modality" in result["reason_codes"]
        assert result["task_feasible"] is True

    def test_proposed_rejects_when_no_sufficient_modality(self):
        result = policy_solve("proposed", raster_missing_inscription_no_alternative())
        assert result["decision"] == "reject_missing_affordance"
        assert result["task_feasible"] is False
        assert "missing_inscription_affordance" in result["reason_codes"]

    def test_missing_affordance_listed_explicitly(self):
        result = policy_solve("proposed", raster_missing_inscription_case())
        assert "inscription" in result["missing_affordances"]


class TestBaselinesExhibitTheWeakness:
    def test_b0_image_presence_false_accept(self):
        result = policy_solve("baselines_b0", raster_missing_inscription_case())
        # Naive URL/image-presence check accepts the raster blindly.
        assert result["decision"] == "choose_feasible_modality"
        assert result["task_feasible"] is True
        assert not result["missing_affordances"]

    def test_c1_static_fallback_ignores_inscription_gap(self):
        result = policy_solve("baselines_c1", raster_missing_inscription_case())
        # C1 treats inscription requirements as covered by image presence.
        assert "inscription_not_verified:inscription" in result["reason_codes"]
        assert result["task_feasible"] is True

    def test_a3_ablation_reproduces_the_false_accept(self):
        result = policy_solve("ablations_a3", raster_missing_inscription_case())
        # With the inscription check removed the proposed path degenerates to
        # the archive fallback - exactly the regression the engine prevents.
        assert result["decision"] == "choose_curated_archive_fallback"
        assert result["task_feasible"] is True
        assert "ablation" in result["reason_codes"]


class TestDivergence:
    def test_proposed_differs_from_baselines_on_the_counterexample(self):
        case = raster_missing_inscription_case()
        proposed = policy_solve("proposed", case)
        b0 = policy_solve("baselines_b0", case)
        c1 = policy_solve("baselines_c1", case)
        assert proposed["decision"] != b0["decision"]
        assert proposed["decision"] != c1["decision"]
