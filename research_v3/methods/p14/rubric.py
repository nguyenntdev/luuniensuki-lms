"""UDL task-affordance rubric (P14-T02/T09 method artefact, YAML-backed).

The rubric is a fixed, versioned constraint set (NOT a learned model): three
UDL principles plus WCAG 2.2 AA affordances. It is loaded from
``udl/task_affordance_rubric.yaml`` next to this package so reviewers can diff
criterion changes.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from research_v3.methods.p14.schema import AuditCriterion, CriterionVerdict, SchemaError

RUBRIC_PATH = Path(__file__).resolve().parent / "udl" / "task_affordance_rubric.yaml"

RUBRIC_VERSION = "p14-udl-rubric-1.0.0"

# Fixed rubric: no learned weights anywhere in P14 (spec §3.2: separate fixed
# constraints from learned weights; P14 has only fixed constraints).
LEARNED_PARAMETERS: dict[str, float] = {}


def load_rubric(path: Path | None = None) -> list[AuditCriterion]:
    """Load and validate the versioned rubric from YAML."""
    target = Path(path or RUBRIC_PATH)
    raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    if raw.get("rubric_version") != RUBRIC_VERSION:
        raise SchemaError(
            f"rubric_version mismatch: expected {RUBRIC_VERSION!r}, "
            f"got {raw.get('rubric_version')!r}"
        )
    criteria: list[AuditCriterion] = []
    for entry in raw.get("criteria", []):
        criteria.append(
            AuditCriterion(
                criterion_id=str(entry["criterion_id"]),
                framework=str(entry["framework"]),
                description=str(entry["description"]),
                applies_to=tuple(str(a) for a in entry["applies_to"]),
                critical=bool(entry.get("critical", True)),
            )
        )
    if not criteria:
        raise SchemaError("rubric defines no criteria")
    ids = [c.criterion_id for c in criteria]
    if len(ids) != len(set(ids)):
        raise SchemaError("duplicate criterion_id in rubric")
    return criteria


def criteria_for_media_type(
    criteria: list[AuditCriterion], media_types: set[str]
) -> list[AuditCriterion]:
    """Applicable criteria = union over the object's media types.

    A criterion applies when the object contains at least one asset of a media
    type listed in the criterion's ``applies_to`` (or the criterion is marked
    universal). This yields a per-object denominator with NOT_APPLICABLE for
    the rest.
    """
    applicable: list[AuditCriterion] = []
    for criterion in criteria:
        if "all" in criterion.applies_to or (set(criterion.applies_to) & media_types):
            applicable.append(criterion)
    return applicable


def verdict_is_negative(verdict: CriterionVerdict) -> bool:
    """FAIL is the only negative verdict; ABSTAIN/NOT_APPLICABLE are not FAIL."""
    return verdict is CriterionVerdict.FAIL
