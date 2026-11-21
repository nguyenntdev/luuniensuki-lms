"""Core domain types, enums, and cryptographic canonical hashing utilities for V4.2 contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional


class ClaimStatus(str, Enum):
    """Release status enum for scientific claims as defined in WIN_CONTRACT.md."""
    BLOCKED = "BLOCKED"
    BASELINE_INCOMPLETE = "BASELINE_INCOMPLETE"
    NO_RESIDUAL_GAP = "NO_RESIDUAL_GAP"
    NOVELTY_FAILED = "NOVELTY_FAILED"
    DEVELOPMENT_CANDIDATE = "DEVELOPMENT_CANDIDATE"
    FROZEN = "FROZEN"
    TESTED_NULL = "TESTED_NULL"
    TESTED_WIN_SINGLE = "TESTED_WIN_SINGLE"
    REPLICATED_WIN = "REPLICATED_WIN"
    FORMAL_PROPERTY_PROVED = "FORMAL_PROPERTY_PROVED"
    SUBMISSION_READY = "SUBMISSION_READY"


class WinType(str, Enum):
    """Win types classification - never conflate."""
    FORMALLY_PROVEN = "FORMALLY_PROVEN"
    PREDICTIVE_SUPERIORITY = "PREDICTIVE_SUPERIORITY"
    BETTER_SAFETY_EFFICIENCY_FRONTIER = "BETTER_SAFETY_EFFICIENCY_FRONTIER"
    BETTER_INSTRUMENT_OR_BENCHMARK = "BETTER_INSTRUMENT_OR_BENCHMARK"
    NULL_OR_INFERIOR = "NULL_OR_INFERIOR"


class PublicationGrade(str, Enum):
    """Publication grades for claims and manuscripts."""
    ENGINEERING_ONLY = "ENGINEERING_ONLY"
    FORMAL_CHECKED = "FORMAL_CHECKED"
    SINGLE_DATASET_WIN = "SINGLE_DATASET_WIN"
    REPLICATED_WIN = "REPLICATED_WIN"
    SCIENTIFIC_PARTIAL = "SCIENTIFIC_PARTIAL"
    HUMAN_BLOCKED = "HUMAN_BLOCKED"
    SUBMISSION_READY = "SUBMISSION_READY"


@dataclass
class GateResult:
    """Standard execution result returned by all V4.2 release gates."""
    gate_name: str
    passed: bool
    messages: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "passed": self.passed,
            "messages": self.messages,
            "details": self.details,
            "timestamp": self.timestamp,
        }


def _json_serializable_fallback(obj: Any) -> Any:
    """Serialize custom objects such as Enum, datetime, or dataclass."""
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def canonical_json_bytes(data: Any, exclude_keys: Optional[set[str]] = None) -> bytes:
    """Serialize any Python structure or Pydantic model to deterministic canonical UTF-8 bytes.
    
    Keys are sorted recursively, compact separators (',', ':') are enforced,
    and excluded keys (like card_sha256 or content_sha256) are filtered out.
    """
    if exclude_keys is None:
        exclude_keys = {"card_sha256", "content_sha256"}

    def _filter_obj(item: Any) -> Any:
        if isinstance(item, dict):
            return {
                k: _filter_obj(v)
                for k, v in item.items()
                if k not in exclude_keys
            }
        if isinstance(item, list):
            return [_filter_obj(elem) for elem in item]
        if isinstance(item, tuple):
            return [_filter_obj(elem) for elem in item]
        if hasattr(item, "model_dump"):
            dumped = item.model_dump()
            return _filter_obj(dumped)
        if hasattr(item, "__dict__"):
            return _filter_obj(item.__dict__)
        return item

    filtered = _filter_obj(data)
    json_str = json.dumps(
        filtered,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=_json_serializable_fallback,
    )
    return json_str.encode("utf-8")


def canonical_hash(data: Any, exclude_keys: Optional[set[str]] = None) -> str:
    """Compute deterministic SHA-256 hex digest of any data structure using canonical JSON."""
    raw_bytes = canonical_json_bytes(data, exclude_keys=exclude_keys)
    return hashlib.sha256(raw_bytes).hexdigest()
