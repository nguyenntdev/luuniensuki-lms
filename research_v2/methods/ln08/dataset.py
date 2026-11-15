"""LN-08 dataset loading, schema validation and typed case parsing.

The inference-time feature schema for one case (the ``input`` subtree of the
T3 holdout fixtures):

    answer              : student textual answer (non-empty string)
    prompt              : task prompt shown to the learner
    evidence            : {claim_id, source_id, verified} citation locator
    content             : {id, type} target heritage monument metadata
    expected_conclusion : target concept code (never the gold decision)
    language            : BCP-47-ish tag ("vi" in the T3 fixtures)
    learner             : profile metadata (never used by any policy)
    seed                : scenario generation seed (unused; determinism)

Any invalid row rejects the whole batch with its location - never a guessed
fallback value. Gold material (``expected_decision``, ``fault_id``, oracle
fields) is stripped upstream by ``research_v2.contracts.input_masking`` and is
additionally rejected here if it ever appears in features.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .labels import STUDY_ID


class DatasetError(ValueError):
    """Raised when a dataset row violates the LN-08 input schema."""


REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = REPO_ROOT / "research_v2" / "data" / "ln08" / "t3_inputs.jsonl"
GOLD_PATH = REPO_ROOT / "research_v2" / "data" / "ln08" / "t3_gold.jsonl"


@dataclass(frozen=True)
class EvidenceRef:
    """Citation locator attached to a case."""

    claim_id: str
    source_id: str
    verified: bool

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], *, location: str) -> "EvidenceRef":
        if not isinstance(raw, Mapping):
            raise DatasetError(f"{location}: evidence must be a mapping, got {type(raw).__name__}")
        claim_id = raw.get("claim_id")
        source_id = raw.get("source_id")
        verified = raw.get("verified", False)
        if not isinstance(claim_id, str) or not claim_id.strip():
            raise DatasetError(f"{location}: evidence.claim_id must be a non-empty string")
        if not isinstance(source_id, str) or not source_id.strip():
            raise DatasetError(f"{location}: evidence.source_id must be a non-empty string")
        if not isinstance(verified, bool):
            raise DatasetError(
                f"{location}: evidence.verified must be a boolean, got {type(verified).__name__}"
            )
        return cls(claim_id=claim_id, source_id=source_id, verified=verified)


@dataclass(frozen=True)
class ContentRef:
    """Target heritage monument metadata."""

    id: str
    type: str

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], *, location: str) -> "ContentRef":
        if not isinstance(raw, Mapping):
            raise DatasetError(f"{location}: content must be a mapping, got {type(raw).__name__}")
        cid = raw.get("id")
        ctype = raw.get("type", "heritage-monument")
        if not isinstance(cid, str) or not cid.strip():
            raise DatasetError(f"{location}: content.id must be a non-empty string")
        if not isinstance(ctype, str):
            raise DatasetError(f"{location}: content.type must be a string")
        return cls(id=cid, type=ctype)


@dataclass(frozen=True)
class DiagnosticCase:
    """One validated inference-time diagnostic case (oracle-free)."""

    case_id: str
    answer: str
    prompt: str
    evidence: EvidenceRef
    content: ContentRef
    expected_conclusion: str
    language: str

    @classmethod
    def from_features(cls, features: Mapping[str, Any], *, case_id: str = "t") -> "DiagnosticCase":
        if not isinstance(features, Mapping):
            raise DatasetError(f"case {case_id!r}: features must be a mapping, got {type(features).__name__}")

        forbidden = ("expected_decision", "fault_id", "oracle", "gold", "gold_label")
        leaked = sorted(set(features) & set(forbidden))
        if leaked:
            raise DatasetError(f"case {case_id!r}: forbidden gold fields in features: {leaked}")

        answer = features.get("answer")
        if not isinstance(answer, str):
            raise DatasetError(f"case {case_id!r}: answer must be a string, got {type(answer).__name__}")
        if not answer.strip():
            # Empty answer is VALID input but triggers abstention; whitespace-only
            # rows still need parseable strings, so keep the raw value.
            pass

        prompt = features.get("prompt", "")
        if not isinstance(prompt, str):
            raise DatasetError(f"case {case_id!r}: prompt must be a string, got {type(prompt).__name__}")

        evidence_raw = features.get("evidence")
        if not isinstance(evidence_raw, Mapping):
            raise DatasetError(f"case {case_id!r}: evidence must be a mapping")
        evidence = EvidenceRef.from_dict(evidence_raw, location=f"case {case_id!r}")

        content_raw = features.get("content")
        if not isinstance(content_raw, Mapping):
            raise DatasetError(f"case {case_id!r}: content must be a mapping")
        content = ContentRef.from_dict(content_raw, location=f"case {case_id!r}")

        conclusion = features.get("expected_conclusion", "")
        if not isinstance(conclusion, str):
            raise DatasetError(f"case {case_id!r}: expected_conclusion must be a string")

        language = features.get("language", "vi")
        if not isinstance(language, str) or not language.strip():
            raise DatasetError(f"case {case_id!r}: language must be a non-empty string")

        return cls(
            case_id=case_id,
            answer=answer,
            prompt=prompt,
            evidence=evidence,
            content=content,
            expected_conclusion=conclusion,
            language=language.strip(),
        )

    @property
    def is_empty_answer(self) -> bool:
        return not self.answer.strip()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise DatasetError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return rows


def load_t3_cases() -> list[DiagnosticCase]:
    rows = load_jsonl(DATASET_PATH)
    return [
        DiagnosticCase.from_features(row["input"], case_id=row["case_id"]) for row in rows
    ]


def load_gold() -> dict[str, str]:
    """Evaluator-only helper: map case_id -> expected contract decision."""
    rows = load_jsonl(GOLD_PATH)
    return {row["case_id"]: row["expected_decision"] for row in rows}
