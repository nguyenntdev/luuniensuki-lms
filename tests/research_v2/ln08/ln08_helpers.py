"""Shared helpers for LN-08 V2 tests: case builders and policy dispatch."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "research_v2" / "data" / "ln08"

STUDY_ID = "LN-08"

VERIFIED_EVIDENCE = {"claim_id": "CLAIM-HD-001", "source_id": "SOURCE-DNTL-001", "verified": True}


def make_features(**overrides: Any) -> dict[str, Any]:
    """Nominal supported case: affirmative canonical answer + verified source.

    Override keys are routed into nested structures where applicable
    (``answer``, ``source_id``, ``verified``, ``claim_id``).
    """
    features: dict[str, Any] = {
        "answer": "Ngọ Môn thuộc trục nghi lễ được mô tả chuẩn xác trong nguồn tư liệu.",
        "prompt": "Dựa vào nguồn sử liệu, hãy xác định và giải thích mối quan hệ không gian - nghi lễ của công trình.",
        "evidence": dict(VERIFIED_EVIDENCE),
        "content": {"id": "ngo-mon", "type": "imperial-gate"},
        "expected_conclusion": "spatial_ritual_relationship",
        "language": "vi",
    }
    answer = overrides.pop("answer", None)
    if answer is not None:
        features["answer"] = answer
    source_id = overrides.pop("source_id", None)
    if source_id is not None:
        features["evidence"]["source_id"] = source_id
    verified = overrides.pop("verified", None)
    if verified is not None:
        features["evidence"]["verified"] = verified
    claim_id = overrides.pop("claim_id", None)
    if claim_id is not None:
        features["evidence"]["claim_id"] = claim_id
    features.update(overrides)
    return features


def make_input(case_id: str = "t", features: dict[str, Any] | None = None) -> "object":
    from research_v2.contracts.types import StudyInput

    return StudyInput(
        STUDY_ID,
        case_id,
        "test",
        f"{STUDY_ID}-grp-{case_id}",
        features if features is not None else make_features(),
    )


def load_t3_inputs() -> list[dict[str, Any]]:
    path = DATA_DIR / "t3_inputs.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_t3_gold() -> dict[str, str]:
    path = DATA_DIR / "t3_gold.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {row["case_id"]: row["expected_decision"] for row in rows}


def policy_solve(name: str, features: dict[str, Any]) -> str:
    """Run any LN-08 method by its matrix id on a feature dict; return decision."""
    from research_v2.methods.ln08.ablations import a1_solve, a2_solve, a3_solve
    from research_v2.methods.ln08.baselines import b0_solve, c1_solve
    from research_v2.methods.ln08.dataset import DiagnosticCase
    from research_v2.methods.ln08.proposed import solve_case

    case = DiagnosticCase.from_features(features, case_id="t")
    return {
        "proposed": lambda: solve_case(case)["decision"],
        "baselines_b0": lambda: b0_solve(case)["decision"],
        "baselines_c1": lambda: c1_solve(case)["decision"],
        "ablations_a1": lambda: a1_solve(case)["decision"],
        "ablations_a2": lambda: a2_solve(case)["decision"],
        "ablations_a3": lambda: a3_solve(case)["decision"],
    }[name]()


# ---------------------------------------------------------------------------
# Mandatory counterexample fixtures (spec 14.F / prereg)
# ---------------------------------------------------------------------------

# Case 1: contains ALL canonical keywords yet REVERSES the historical relation.
KEYWORD_COMPLETE_REVERSED_VI = "Ngọ Môn không thuộc trục nghi lễ theo điển chế triều Nguyễn."
KEYWORD_COMPLETE_REVERSED_EN = "The Ngo Mon gate is NOT on the ritual axis according to the source."

# Case 2: correct synonym paraphrase with NO exact canonical keyword.
SYNONYM_PARAPHRASE = "Theo tư liệu, vị trí Ngọ Môn nằm trên tuyến không gian phục vụ nghi thức."

# Case 3: plausible statement with a fabricated source locator.
FABRICATED_SOURCE_ANSWER = "Ngọ Môn thuộc trục nghi lễ được mô tả trong nguồn sử liệu."

# Case 4: generic partial reasoning (no spatial-ritual relation).
PARTIAL_REASONING_ANSWER = "Ngọ Môn là một công trình kiến trúc thời Nguyễn."
