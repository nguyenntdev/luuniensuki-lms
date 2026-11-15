"""Input masking: build legitimate inference-time features from a legacy case.

The legacy fixtures carry gold material (``oracle``, ``expected_decision``,
``fault_id``, ``cohort``, annotation provenance). Those keys MUST NOT reach a
policy model. This module produces a masked feature mapping containing only
fields that are legitimately available at inference time.
"""
from __future__ import annotations

from typing import Any, Mapping

from .types import FORBIDDEN_INPUT_KEYS, ContractError


def _strip_forbidden(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return {
            k: _strip_forbidden(v)
            for k, v in obj.items()
            if k not in FORBIDDEN_INPUT_KEYS
        }
    if isinstance(obj, list):
        return [_strip_forbidden(v) for v in obj]
    return obj


def mask_case_input(case: Mapping[str, Any]) -> dict[str, Any]:
    """Return an inference-time feature mapping with all gold material removed.

    ``case`` is a raw fixture row. Only the ``input`` subtree is considered; the
    top-level oracle / provenance fields are dropped entirely.
    """
    if "input" not in case:
        raise ContractError("fixture row has no 'input' subtree to mask")
    fresh = _strip_forbidden(case["input"])
    if not isinstance(fresh, dict):
        raise ContractError("masked input must be a mapping")
    leaked = sorted(set(fresh) & FORBIDDEN_INPUT_KEYS)
    if leaked:
        raise ContractError(f"forbidden keys survived masking: {leaked}")
    return fresh


def assert_no_oracle_leakage(case: Mapping[str, Any]) -> None:
    """Fail when oracle/gold material is nested inside the model input."""
    inp = case.get("input")
    if not isinstance(inp, Mapping):
        return
    leaked = sorted(set(inp) & FORBIDDEN_INPUT_KEYS)
    if leaked:
        raise ContractError(f"oracle leakage detected inside input: {leaked}")
