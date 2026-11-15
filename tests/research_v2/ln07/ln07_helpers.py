"""Shared helpers for LN-07 V2 tests: case builders and policy dispatch.

Uniquely named (NOT ``helpers.py``) so pytest never collides module names
across study directories. Importable standalone: adds the repo root to
``sys.path`` before importing ``research_v2``.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research_v2.contracts.input_masking import mask_case_input  # noqa: E402
from research_v2.contracts.types import StudyInput, StudyPrediction  # noqa: E402
from research_v2.methods.ln07.dataset import ModalityCase  # noqa: E402
from research_v2.methods.ln07.labels import NATIVE_DECISIONS  # noqa: E402
from research_v2.methods.ln07.proposed import solve_case  # noqa: E402

STUDY_ID = "LN-07"

DATASET_PATH = REPO_ROOT / "research_v2" / "data" / "ln07" / "t3_inputs.jsonl"
GOLD_PATH = REPO_ROOT / "research_v2" / "data" / "ln07" / "t3_gold.jsonl"


def make_case(
    *,
    required: list[str] | None = None,
    transcript_required: bool = False,
    webgl: bool = True,
    webgl_context_lost: bool = False,
    network_kbps: int = 3200,
    keyboard_only: bool = False,
    screen_reader: bool = False,
    options: list[dict] | None = None,
    case_id: str = "t",
) -> ModalityCase:
    """Build a validated ModalityCase from concise kwargs (defaults = nominal)."""
    if options is None:
        options = default_options(required=required)
    features: dict = {
        "content": {"id": "cao-dinh", "motif": "long", "motif_name": "Rồng", "type": "bronze-urn"},
        "device": {
            "keyboard_only": keyboard_only,
            "network_kbps": network_kbps,
            "screen_reader": screen_reader,
            "webgl": webgl,
            "webgl_context_lost": webgl_context_lost,
        },
        "learner": {"access": "standard", "profile_id": "SYN-TEST"},
        "task": {
            "description": "Xác định mối tương quan không gian và bố cục phù điêu.",
            "required_affordances": list(required or ["visual_detail", "spatial_relation"]),
            "transcript_required": transcript_required,
            "type": "identify_relief_relation",
        },
        "options": options,
        "seed": 11,
    }
    return ModalityCase.from_features(features, case_id=case_id)


def default_options(required: list[str] | None = None) -> list[dict]:
    """The standard 5-variant option set shaped like the T3 fixtures.

    ``required`` is injected into every variant's affordance list so callers
    can create inscription/audio-description requirements without hand-writing
    options; inscription variants are made explicit via ``rubbing_affordances``
    tweaks by the caller when needed.
    """
    req = list(required or [])
    return [
        {
            "id": "opt_3d",
            "modality": "3d",
            "kb": 1850,
            "keyboard": True,
            "requires_webgl": True,
            "available": True,
            "affordances": sorted({"visual_detail", "spatial_relation", "relief_depth", *req}),
        },
        {
            "id": "opt_static",
            "modality": "static_image",
            "kb": 320,
            "keyboard": False,
            "requires_webgl": False,
            "available": True,
            "alt_text": "Ảnh tĩnh phù điêu",
            "affordances": sorted({"visual_detail", *req}),
        },
        {
            "id": "opt_rubbing",
            "modality": "2d",
            "sub_type": "rubbing",
            "kb": 95,
            "keyboard": True,
            "requires_webgl": False,
            "available": True,
            "alt_text": "Bản dập nổi phù điêu",
            "affordances": sorted({"visual_detail", "spatial_relation", "relief_depth", *req}),
        },
        {
            "id": "opt_audio",
            "modality": "audio",
            "kb": 480,
            "keyboard": True,
            "requires_webgl": False,
            "available": True,
            "transcript": True,
            "screen_reader_ready": True,
            "affordances": sorted(
                {"visual_detail", "spatial_relation", "relief_depth", "description", *req}
            ),
        },
        {
            "id": "opt_text",
            "modality": "text",
            "kb": 10,
            "keyboard": True,
            "requires_webgl": False,
            "available": True,
            "screen_reader_ready": True,
            "affordances": sorted(
                {"visual_detail", "spatial_relation", "relief_depth", "description", *req}
            ),
        },
    ]


def make_input(case: ModalityCase) -> StudyInput:
    """Wrap a validated case into the contract StudyInput (oracle-free)."""
    return StudyInput(
        study_id=STUDY_ID,
        case_id=case.case_id,
        split_id="test",
        group_id=f"{STUDY_ID}-grp-{case.case_id}",
        features=json.loads(json.dumps(_case_features(case))),
    )


def _case_features(case: ModalityCase) -> dict:
    from dataclasses import asdict

    d = asdict(case)
    # asdict keeps tuples as lists via json round-trip in make_input
    return {
        "content": {"id": case.content_id, "type": case.content_type},
        "device": {
            "webgl": case.device.webgl,
            "network_kbps": case.device.network_kbps,
            "keyboard_only": case.device.keyboard_only,
            "screen_reader": case.device.screen_reader,
            "webgl_context_lost": case.device.webgl_context_lost,
        },
        "learner": {"access": "standard", "profile_id": "SYN-TEST"},
        "task": {
            "type": case.task.type,
            "description": case.task.description,
            "required_affordances": list(case.task.required_affordances),
            "transcript_required": case.task.transcript_required,
        },
        "options": d["options"],
        "seed": case.seed,
    }


def policy_solve(name: str, case: ModalityCase) -> dict:
    """Run any LN-07 method by its matrix id on a validated case."""
    if name == "proposed":
        return solve_case(case)
    from research_v2.methods.ln07.ablations import a1_solve, a2_solve, a3_solve
    from research_v2.methods.ln07.baselines import b0_solve, c1_solve

    return {
        "baselines_b0": b0_solve,
        "baselines_c1": c1_solve,
        "ablations_a1": a1_solve,
        "ablations_a2": a2_solve,
        "ablations_a3": a3_solve,
    }[name](case)


def policy_predict(name: str, inputs: list[StudyInput], config: dict | None = None) -> list:
    """Run any LN-07 method by its matrix id through the contract ABI."""
    from importlib import import_module

    module = import_module(f"research_v2.methods.ln07.{name}")
    return module.predict_batch(inputs, dict(config or {}))


def load_t3_rows() -> tuple[list[dict], list[dict]]:
    """Load the sealed T3 fixture rows (inputs + gold) as raw dicts."""
    rows = [json.loads(l) for l in DATASET_PATH.open(encoding="utf-8") if l.strip()]
    gold = [json.loads(l) for l in GOLD_PATH.open(encoding="utf-8") if l.strip()]
    return rows, gold


def t3_inputs() -> list[StudyInput]:
    """Contract StudyInputs for the full T3 holdout (gold masked out)."""
    rows, _ = load_t3_rows()
    return [
        StudyInput(
            study_id=STUDY_ID,
            case_id=r["case_id"],
            split_id="test",
            group_id=r["group_id"],
            features=mask_case_input(copy.deepcopy(r)),
        )
        for r in rows
    ]


def gold_by_case() -> dict[str, str]:
    _, gold = load_t3_rows()
    return {g["case_id"]: g["expected_decision"] for g in gold}


assert NATIVE_DECISIONS, "labels module must expose the native decision space"
