"""P14 typed schema for multimodal learning objects and audit records.

Contract requirements (spec §3.1): exact input/output dataclasses with type and
constraint invariants, and configurable ``NOT_APPLICABLE`` and ``ABSTAIN``
verdicts distinct from negative (FAIL) predictions.
"""
from __future__ import annotations

import enum
import re
from dataclasses import dataclass, field, asdict
from typing import Any

PAPER_ID = "P14"

SCHEMA_VERSION = "p14-schema-1.0.0"


class CriterionVerdict(str, enum.Enum):
    """Verdict for one audit criterion.

    PASS / FAIL are real judgements. NOT_APPLICABLE means the criterion does
    not apply to this object (e.g. captions for a silent still image) and is
    excluded from the denominator. ABSTAIN means the auditor could not decide
    (missing evidence) and is reported separately, never silently counted as
    either a pass or a fail.
    """

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ABSTAIN = "ABSTAIN"


REAL_VERDICTS = frozenset({CriterionVerdict.PASS, CriterionVerdict.FAIL})
EVALUABLE_VERDICTS = REAL_VERDICTS | {CriterionVerdict.NOT_APPLICABLE}

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")


def _check_id(value: str, what: str) -> None:
    if not _ID_RE.match(value):
        raise ValueError(f"{what} must match {_ID_RE.pattern}, got {value!r}")


class SchemaError(ValueError):
    """Raised when a learning-object manifest or audit record violates schema."""


@dataclass(frozen=True)
class MediaAsset:
    """One asset inside a learning object (image, audio, video, 3D, text...)."""

    asset_id: str
    media_type: str  # image | audio | video | model3d | text
    rights: str  # e.g. CC0, license URL, or synthetic-no-third-party-rights
    caption: str | None = None
    has_captions: bool | None = None
    has_transcript: bool | None = None
    has_text_alternative: bool | None = None
    keyboard_operable: bool | None = None
    interactive: bool = False

    def __post_init__(self) -> None:
        _check_id(self.asset_id, "asset_id")
        if self.media_type not in {"image", "audio", "video", "model3d", "text"}:
            raise SchemaError(f"{self.asset_id}: unknown media_type {self.media_type!r}")
        if not self.rights:
            raise SchemaError(f"{self.asset_id}: rights statement is required (never blank)")


@dataclass(frozen=True)
class LearningObject:
    """A multimodal learning object: the unit P14 audits."""

    object_id: str
    title: str
    origin: str  # external:<provider> | synthetic:label
    source_url: str | None
    rights: str
    assets: tuple[MediaAsset, ...]
    low_bandwidth_variant: tuple[MediaAsset, ...] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _check_id(self.object_id, "object_id")
        if not self.title:
            raise SchemaError(f"{self.object_id}: title required")
        if not self.origin.startswith(("external:", "synthetic:")):
            raise SchemaError(
                f"{self.object_id}: origin must start with 'external:' or 'synthetic:'"
            )
        if not self.rights:
            raise SchemaError(f"{self.object_id}: rights statement is required")
        if not self.assets:
            raise SchemaError(f"{self.object_id}: at least one asset required")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AuditCriterion:
    """One audit criterion derived from the UDL rubric or WCAG 2.2 AA."""

    criterion_id: str
    framework: str  # udl-representation | udl-engagement | udl-action | wcag22
    description: str
    applies_to: tuple[str, ...]  # media types this criterion applies to
    critical: bool = True

    def __post_init__(self) -> None:
        _check_id(self.criterion_id, "criterion_id")
        if self.framework not in {
            "udl-representation",
            "udl-engagement",
            "udl-action",
            "wcag22",
        }:
            raise SchemaError(f"{self.criterion_id}: unknown framework {self.framework!r}")


@dataclass(frozen=True)
class CriterionResult:
    """Auditor decision on one criterion for one object."""

    criterion_id: str
    object_id: str
    verdict: CriterionVerdict
    evidence: str = ""
    remediation: str | None = None

    def __post_init__(self) -> None:
        if self.verdict is CriterionVerdict.FAIL and not self.remediation:
            raise SchemaError(
                f"{self.object_id}/{self.criterion_id}: FAIL requires a remediation action"
            )


@dataclass(frozen=True)
class RemediationItem:
    """One concrete fix for a failing criterion, ordered by severity."""

    object_id: str
    criterion_id: str
    framework: str
    severity: str  # critical | major | minor
    action: str

    def __post_init__(self) -> None:
        if self.severity not in {"critical", "major", "minor"}:
            raise SchemaError(f"invalid severity {self.severity!r}")
        if not self.action:
            raise SchemaError(f"{self.object_id}/{self.criterion_id}: remediation action required")


@dataclass(frozen=True)
class ObjectAuditVerdict:
    """Aggregated verdict for one learning object."""

    object_id: str
    total_applicable: int
    passed: int
    failed: int
    not_applicable: int
    abstained: int
    missing_affordances: tuple[str, ...]
    verdict: str  # PASS | FAIL | ABSTAIN (whole-object verdict)

    def __post_init__(self) -> None:
        if self.verdict not in {"PASS", "FAIL", "ABSTAIN"}:
            raise SchemaError(f"invalid object verdict {self.verdict!r}")
        if self.passed + self.failed + self.not_applicable + self.abstained != self.total_applicable:
            raise SchemaError(
                f"{self.object_id}: verdict counts do not reconcile "
                f"({self.passed}+{self.failed}+{self.not_applicable}+{self.abstained}"
                f" != {self.total_applicable})"
            )
