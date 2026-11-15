"""Research V3 immutable contracts: dataset, experiment and evidence cards.

These are the append-only records the whole V3 stack is built on. Every card is
canonical-JSON serializable, hashable, and validated on construction. A card can
never be silently overwritten after freeze: callers must create a new version.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Mapping

from research_v2.contracts.canonical_hash import sha256_input  # reuse one hash standard


class ContractError(ValueError):
    """Raised when a V3 card violates its schema or a scientific invariant."""


DATASET_STATUSES = frozenset({"APPROVED", "BLOCKED", "RESTRICTED"})
EXPERIMENT_STATUSES = frozenset({"PASS", "FAIL", "BLOCKED", "PARTIAL"})
ALLOWED_USES = frozenset(
    {
        "academic_analysis",
        "derived_artifacts",
        "redistribution",
        "commercial_use",
        "text_media_copying",
        "fine_tuning",
        "third_party_api",
    }
)


@dataclass(frozen=True)
class DatasetCard:
    """Provenance + rights record for one external dataset version."""

    dataset_id: str
    provider: str
    source_url: str
    doi: str | None
    version: str
    retrieved_at: str
    license_text_sha256: str
    allowed_uses: tuple[str, ...]
    redistribution_policy: str
    original_sha256: str
    transformed_sha256: str | None
    sample_count: int
    schema_version: str
    consent_basis: str
    units: str
    group_keys: tuple[str, ...]
    time_key: str | None
    leakage_audit: str
    source_attribution: str
    status: str
    blocked_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.dataset_id:
            raise ContractError("dataset_id is required")
        if self.status not in DATASET_STATUSES:
            raise ContractError(f"invalid dataset status {self.status!r}")
        if self.status == "BLOCKED" and not self.blocked_reason:
            raise ContractError(f"{self.dataset_id}: BLOCKED requires blocked_reason")
        if self.status == "APPROVED":
            if not self.license_text_sha256 or len(self.license_text_sha256) != 64:
                raise ContractError(f"{self.dataset_id}: APPROVED requires license_text_sha256")
            if not self.original_sha256 or len(self.original_sha256) != 64:
                raise ContractError(f"{self.dataset_id}: APPROVED requires original_sha256")
            if not self.source_url:
                raise ContractError(f"{self.dataset_id}: APPROVED requires source_url")
            if self.sample_count <= 0:
                raise ContractError(f"{self.dataset_id}: APPROVED requires sample_count > 0")
        unknown = set(self.allowed_uses) - ALLOWED_USES
        if unknown:
            raise ContractError(f"{self.dataset_id}: unknown allowed_uses {sorted(unknown)}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def sha256(self) -> str:
        return sha256_input(self.to_dict())


@dataclass(frozen=True)
class ExperimentCard:
    """One preregistered experiment run and its provenance."""

    paper_id: str
    rq_id: str
    train_dataset_ids: tuple[str, ...]
    holdout_dataset_ids: tuple[str, ...]
    method_commit_sha: str
    method_hash: str
    baseline_version: str
    split_hash: str
    feature_cutoff: str
    prereg_sha256: str
    hyperparameter_budget: str
    seed: int
    hardware: str
    wall_time_seconds: float
    dependency_lock_sha256: str
    output_path: str
    protocol_deviations: tuple[str, ...] = ()
    status: str = "BLOCKED"

    def __post_init__(self) -> None:
        if not self.paper_id.startswith("P"):
            raise ContractError(f"invalid paper_id {self.paper_id!r}")
        if self.status not in EXPERIMENT_STATUSES:
            raise ContractError(f"invalid experiment status {self.status!r}")
        if not self.rq_id:
            raise ContractError(f"{self.paper_id}: rq_id required")
        for name in ("method_hash", "split_hash", "prereg_sha256", "dependency_lock_sha256"):
            value = getattr(self, name)
            if value and len(value) != 64:
                raise ContractError(f"{self.paper_id}: {name} must be a sha256 hex digest")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def sha256(self) -> str:
        return sha256_input(self.to_dict())


@dataclass(frozen=True)
class EvidenceCard:
    """Binds one manuscript claim to reproducible numeric evidence."""

    paper_id: str
    claim_id: str
    source_type: str
    source_sha256: str
    code_sha: str
    experiment_ids: tuple[str, ...]
    analysis_script: str
    table_cell_ids: tuple[str, ...]
    denominator: int | None
    ci: tuple[float, float] | None
    comparison_family: str
    reviewer_signoffs: tuple[str, ...] = ()
    allowed_wording: str = ""
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.claim_id:
            raise ContractError(f"{self.paper_id}: claim_id required")
        if not self.allowed_wording:
            raise ContractError(
                f"{self.claim_id}: allowed_wording is mandatory so no unmatchable "
                "adjective ('best', 'causally improves') can be asserted"
            )
        if self.denominator is not None and self.denominator <= 0:
            raise ContractError(f"{self.claim_id}: denominator must be positive")
        if self.ci is not None:
            lo, hi = self.ci
            if not (0.0 <= lo <= hi <= 1.0):
                raise ContractError(f"{self.claim_id}: invalid CI {self.ci}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def sha256(self) -> str:
        return sha256_input(self.to_dict())


@dataclass(frozen=True)
class FrozenSplit:
    """A materially frozen train/calibration/dev/test partition."""

    paper_id: str
    protocol: str  # learner | course | time | skill | group
    split_ids: Mapping[str, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {"train", "calibration", "dev", "test"}
        if set(self.split_ids) != required:
            raise ContractError(
                f"{self.paper_id}: split_ids must define exactly {sorted(required)}, "
                f"got {sorted(self.split_ids)}"
            )
        seen: set[str] = set()
        for name, ids in self.split_ids.items():
            overlap = seen & set(ids)
            if overlap:
                raise ContractError(
                    f"{self.paper_id}: '{name}' leaks ids from another split: {sorted(overlap)[:5]}"
                )
            seen |= set(ids)

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "protocol": self.protocol,
            "split_ids": {k: list(v) for k, v in self.split_ids.items()},
        }

    def sha256(self) -> str:
        return sha256_input(self.to_dict())
