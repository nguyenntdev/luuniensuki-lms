"""LN-07 baseline policies (C0 sanity + C1 strong classical).

- ``b0`` (``baselines_b0`` alias): naive URL/image-presence check. Any
  available option with an image (or merely listed in metadata) counts as
  complete - INV-LN-07-01 "asset existence in metadata does not guarantee
  pedagogical availability". It never verifies affordances, accessibility or
  bandwidth. SANITY_ONLY comparator - never a strong baseline.

- ``c1`` (``baselines_c1`` alias): static-2D-raster fallback without
  inscription/transcript equivalence. When the primary 3D path fails
  (WebGL, bandwidth, missing asset), C1 falls back to the first static image
  and checks ONLY the non-inscription affordance subset, mirroring the
  classical "serve a picture" behaviour. The inscription-affordance gap is
  exactly the matched-subtask weakness under study.

Both baselines share the legitimate input features, device semantics and the
LN-07 native label space with I1. Neither shares implementation code with the
proposed engine (independent decision procedures by design).
"""
from __future__ import annotations

from typing import Any, Mapping

from .dataset import DatasetError, ModalityCase, from_input
from .labels import (
    BANDWIDTH_3D_MIN_KBPS,
    INSCRIPTION_AFFORDANCES,
    REASON_AFFORDANCE_PRESERVED,
    REASON_BASELINE_NAIVE,
    REASON_BASELINE_STATIC_FALLBACK,
    REASON_BASELINE_URL_ONLY,
    build_prediction,
)

STUDY_ID = "LN-07"


# ---------------------------------------------------------------------------
# B0 - naive URL/image-presence check (C0, SANITY_ONLY)
# ---------------------------------------------------------------------------

def b0_solve(case: ModalityCase) -> dict[str, Any]:
    """Image exists (or option merely listed) -> complete. Nothing else checked."""
    required = case.task.required_affordances
    device = case.device

    # Blindly prefer the primary 3D option, else the first listed available one.
    opt_3d = next((o for o in case.options if o.modality == "3d"), None)
    chosen = None
    if opt_3d is not None and opt_3d.available and device.webgl_usable and not device.low_bandwidth:
        chosen = opt_3d
    else:
        chosen = next((o for o in case.options if o.available), None)

    if chosen is None:
        return {
            "decision": "choose_feasible_modality",
            "reason_codes": (REASON_BASELINE_URL_ONLY, "no_option_listed"),
            "selected_option_id": "",
            "selected_modality": "",
            "missing_affordances": tuple(required),
            "task_feasible": False,
        }

    # B0's sole test: a URL/image is present. Affordances are "assumed".
    image_present = chosen.modality != "audio" or chosen.transcript is True
    return {
        "decision": "choose_feasible_modality",
        "reason_codes": (REASON_BASELINE_URL_ONLY, REASON_BASELINE_NAIVE),
        "selected_option_id": chosen.id,
        "selected_modality": chosen.modality,
        "missing_affordances": (),
        "task_feasible": bool(image_present) or chosen.modality in ("3d", "2d", "static_image"),
    }


# ---------------------------------------------------------------------------
# C1 - static 2D raster fallback without inscription/transcript equivalence
# ---------------------------------------------------------------------------

def _primary_feasible_3d(case: ModalityCase) -> bool:
    device = case.device
    opt_3d = next((o for o in case.options if o.modality == "3d" and o.available), None)
    return (
        opt_3d is not None
        and device.webgl_usable
        and device.network_kbps >= BANDWIDTH_3D_MIN_KBPS
        and not device.screen_reader
        and not device.keyboard_only
    )


def c1_solve(case: ModalityCase) -> dict[str, Any]:
    """Static-image fallback; verifies affordances EXCEPT inscription fidelity.

    The deliberate classical blind spot (spec 12_C1_STRONG_CLASSICAL): C1
    checks the visual/spatial affordance subset and keyboard operability of
    the static image, but treats inscription/text-equivalence requirements as
    satisfied by image presence. It also ignores screen-reader semantics.
    """
    required = case.task.required_affordances

    if _primary_feasible_3d(case):
        opt_3d = next(o for o in case.options if o.modality == "3d" and o.available)
        missing = tuple(a for a in required if a not in opt_3d.affordance_set)
        return {
            "decision": "choose_feasible_modality",
            "reason_codes": ("c1_primary_3d_selected",),
            "selected_option_id": opt_3d.id,
            "selected_modality": opt_3d.modality,
            "missing_affordances": tuple(sorted(set(missing))),
            "task_feasible": not missing,
        }

    # Fallback: first available static image (2d or static_image), any sub_type.
    static = next(
        (
            o
            for o in case.options
            if o.available and o.modality in ("static_image", "2d")
        ),
        None,
    )
    if static is None:
        return {
            "decision": "reject_missing_affordance",
            "reason_codes": (REASON_BASELINE_STATIC_FALLBACK, "no_static_option"),
            "selected_option_id": "",
            "selected_modality": "",
            "missing_affordances": tuple(sorted(set(required))),
            "task_feasible": False,
        }

    # C1's partial check: non-inscription affordances only.
    visual_required = tuple(
        a for a in required if a not in INSCRIPTION_AFFORDANCES
    )
    missing_visual = tuple(a for a in visual_required if a not in static.affordance_set)
    # Inscription requirements are silently treated as covered by the image.
    inscription_missing = tuple(
        a for a in required if a in INSCRIPTION_AFFORDANCES and a not in static.affordance_set
    )
    feasible = not missing_visual  # inscription gap deliberately ignored
    reasons = [REASON_BASELINE_STATIC_FALLBACK, "unverified_cognitive_affordances"]
    if inscription_missing:
        reasons.append("inscription_not_verified:" + ",".join(sorted(inscription_missing)))
    return {
        "decision": "choose_feasible_modality" if feasible else "reject_missing_affordance",
        "reason_codes": tuple(reasons),
        "selected_option_id": static.id,
        "selected_modality": static.modality,
        "missing_affordances": tuple(sorted(set(missing_visual))),
        "task_feasible": feasible,
    }


# ---------------------------------------------------------------------------
# Contract ABI
# ---------------------------------------------------------------------------

def _predict(inputs: list, config: dict | None, solver) -> list:
    del config
    out = []
    for i, inp in enumerate(inputs):
        if not isinstance(inp, object) or type(inp).__name__ != "StudyInput":
            # isinstance check via lazy import avoids a hard module cycle
            from research_v2.contracts.types import StudyInput

            if not isinstance(inp, StudyInput):
                raise DatasetError(f"input[{i}] expects StudyInput, got {type(inp).__name__}")
        case = from_input(inp)
        try:
            result = solver(case)
        except DatasetError:
            raise
        except Exception as exc:
            raise DatasetError(f"input[{i}] case {inp.case_id!r}: {exc}") from exc
        out.append(
            build_prediction(
                case_id=inp.case_id,
                decision=result["decision"],
                reason_codes=result["reason_codes"],
                evidence_ids=(result["selected_option_id"],) if result["selected_option_id"] else (),
                score=1.0 if result["task_feasible"] else 0.0,
            )
        )
    return out


def b0_predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> Any:
    return _predict([inp], config, b0_solve)[0]


def predict_batch_b0(inputs: list, config: dict | None = None) -> list:
    return _predict(inputs, config, b0_solve)


def c1_predict_one(inp: Any, config: Mapping[str, Any] | None = None) -> Any:
    return _predict([inp], config, c1_solve)[0]


def predict_batch_c1(inputs: list, config: dict | None = None) -> list:
    return _predict(inputs, config, c1_solve)
