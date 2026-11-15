"""Shift scenario definitions for CurriculumShiftBench (P04).

A scenario is a frozen, named evaluation context derived from REAL dataset
structure (course identity, presentation calendar, demographic subgroups). No
scenario invents labels or synthetic learners: strata select real rows, and
injectors only degrade the MAPPING information available to a predictor, never
the gold labels.

Scenario families (each maps to a preregistered stratum):
- S1 partial mappings  : fraction of verified bridge edges hidden (injector)
- S2 unknown categories: real platform categories outside the verified ontology
- S3 domain shift      : train and evaluate across courses / subjects
- S4 cold-start        : learners with zero early-window activity
- A1..A4               : true-removal ablations of S1/S2/S3/S4
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

STRATUM_IDS = ("S0", "S1", "S2", "S3", "S4")
ABLATION_IDS = ("A1", "A2", "A3", "A4")
ALL_STRATA = STRATUM_IDS + ABLATION_IDS

# S0 is the in-domain reference stratum (no injected shift) that anchors every
# degradation delta; S1-S4 are the preregistered shift strata.
PARTIAL_MAPPING_FRACTIONS: tuple[float, ...] = (0.2, 0.5, 0.8)


class ScenarioError(ValueError):
    """Raised when a scenario definition violates protocol invariants."""


@dataclass(frozen=True)
class Scenario:
    stratum: str
    name: str
    dataset_id: str
    description: str
    params: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.stratum not in ALL_STRATA:
            raise ScenarioError(f"unknown stratum {self.stratum!r}")
        if not self.name or not self.dataset_id:
            raise ScenarioError("scenario needs name and dataset_id")


def oulad_scenarios(courses: Sequence[str], presentations: Sequence[str]) -> list[Scenario]:
    """Scenarios grounded in the OULAD course/presentation catalogue."""
    scenarios = [
        Scenario(
            stratum="S1",
            name=f"partial_mapping_{int(f * 100)}pct",
            dataset_id="oulad-2013-2014",
            description=f"Hide {int(f * 100)}% of verified bridge edges before mapping.",
            params={"hide_fraction": f},
        )
        for f in PARTIAL_MAPPING_FRACTIONS
    ]
    scenarios += [
        Scenario(
            stratum="S3",
            name="course_shift_train_AAA_EEE_test_FFF_GGG",
            dataset_id="oulad-2013-2014",
            description="Train on courses AAA/BBB/CCC/EEE, evaluate on held-out FFF/GGG.",
            params={"train_courses": ["AAA", "BBB", "CCC", "EEE"], "test_courses": ["FFF", "GGG"]},
        ),
        Scenario(
            stratum="S3",
            name="presentation_shift_train_2013_test_2014",
            dataset_id="oulad-2013-2014",
            description="Train on 2013 presentations, evaluate on 2014 presentations (time shift).",
            params={"train_time": "2013", "test_time": "2014"},
        ),
        Scenario(
            stratum="S4",
            name="cold_start_zero_early_clicks",
            dataset_id="oulad-2013-2014",
            description="Evaluate on learners with zero clicks in the 60-day early window.",
            params={"criterion": "early_click_total == 0"},
        ),
    ]
    return scenarios


def uci_scenarios(subjects: Sequence[str]) -> list[Scenario]:
    scenarios = [
        Scenario(
            stratum="S3",
            name="subject_shift_train_mat_test_por",
            dataset_id="uci-student-performance-2014",
            description="Train on mathematics, evaluate on portuguese (subject shift).",
            params={"train_subject": "mathematics", "test_subject": "portuguese"},
        ),
        Scenario(
            stratum="S3",
            name="school_shift_within_subject",
            dataset_id="uci-student-performance-2014",
            description="Leave-one-school-out shift across Gabriel Pereira / Mousinho da Silveira.",
            params={"criterion": "school"},
        ),
        Scenario(
            stratum="S4",
            name="cold_start_no_early_engagement_proxy",
            dataset_id="uci-student-performance-2014",
            description=(
                "Learners with no outside-school academic support signals "
                "(no nursery, no higher-ed parent, no internet)."
            ),
            params={"criterion": "no_support_signals"},
        ),
    ]
    return scenarios


def ablation_for(stratum: str) -> Scenario:
    """The true-removal ablation paired with a stratum (A1<-S1, ..., A4<-S4)."""
    pairs = {
        "S1": ("A1", "remove_uncertain_mapping_stratum"),
        "S2": ("A2", "remove_unknown_edge_category"),
        "S3": ("A3", "remove_domain_shift"),
        "S4": ("A4", "remove_cold_start_learners"),
    }
    if stratum not in pairs:
        raise ScenarioError(f"no ablation for stratum {stratum!r}")
    aid, name = pairs[stratum]
    return Scenario(
        stratum=aid,
        name=name,
        dataset_id="protocol",
        description=f"True removal: recompute protocol without stratum {stratum} members.",
        params={"removes": stratum},
    )


def check_strata_complete(scenarios: Sequence[Scenario]) -> dict[str, bool]:
    """Fail-closed helper: every preregistered stratum must have >=1 scenario."""
    present = {s.stratum for s in scenarios}
    return {sid: sid in present for sid in ALL_STRATA}
