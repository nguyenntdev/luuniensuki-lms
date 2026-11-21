"""Contracts package for Research V4.2."""

from research_v4_2.contracts.types import (
    ClaimStatus,
    WinType,
    PublicationGrade,
    GateResult,
    canonical_hash,
    canonical_json_bytes,
)
from research_v4_2.contracts.cards import (
    BaseContractCard,
    DatasetCard,
    BaselineCard,
    FailureCard,
    NoveltyCard,
    MethodCard,
    WinCard,
)

__all__ = [
    "ClaimStatus",
    "WinType",
    "PublicationGrade",
    "GateResult",
    "canonical_hash",
    "canonical_json_bytes",
    "BaseContractCard",
    "DatasetCard",
    "BaselineCard",
    "FailureCard",
    "NoveltyCard",
    "MethodCard",
    "WinCard",
]
