"""Executable Pydantic contracts for DatasetCard, BaselineCard, FailureCard, NoveltyCard, MethodCard, WinCard."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from research_v4_2.contracts.types import (
    ClaimStatus,
    WinType,
    canonical_hash,
    canonical_json_bytes,
)


class BaseContractCard(BaseModel):
    """Base class for all V4.2 contract cards supporting deterministic SHA-256 self-hashing."""
    card_sha256: Optional[str] = Field(default=None, description="Canonical SHA-256 hash of the card content.")

    def compute_sha256(self) -> str:
        """Compute the canonical SHA-256 hash excluding the card_sha256 field itself."""
        return canonical_hash(self.model_dump(), exclude_keys={"card_sha256"})

    def sign_hash(self) -> str:
        """Compute canonical hash and set card_sha256 on the model."""
        digest = self.compute_sha256()
        self.card_sha256 = digest
        return digest

    def verify_hash(self) -> bool:
        """Verify whether card_sha256 matches the current canonical content digest."""
        if not self.card_sha256:
            return False
        return self.card_sha256 == self.compute_sha256()

    def to_canonical_json(self) -> str:
        """Return the canonical UTF-8 JSON representation."""
        return canonical_json_bytes(self.model_dump()).decode("utf-8")


class DatasetCard(BaseContractCard):
    """DatasetCard: rights, license hashes, task ontology, label availability, group IDs, timestamps, file hashes, allowed use."""
    dataset_id: str
    paper_id: str
    task_ontology: Dict[str, Any] = Field(default_factory=dict)
    rights_and_license: Dict[str, Any] = Field(default_factory=dict)
    label_availability: Dict[str, Any] = Field(default_factory=dict)
    group_id_field: str = Field(default="group_id")
    timestamp_field: Optional[str] = Field(default=None)
    file_hashes: Dict[str, str] = Field(default_factory=dict)
    split_hashes: Dict[str, str] = Field(default_factory=dict)
    allowed_use: List[str] = Field(default_factory=list)
    ethics_clearance: Optional[Dict[str, Any]] = Field(default=None)


class BaselineCard(BaseContractCard):
    """BaselineCard: original repo source/weights, license, prereg eligibility and all trial receipts."""
    baseline_id: str
    paper_id: str
    family: str  # e.g., "C1", "C2", "tabular", "pykt", "exact_solver"
    repo_source: str
    commit_or_version: str
    license: str
    prereg_eligible: bool = True
    compute_budget: Dict[str, Any] = Field(default_factory=dict)
    trial_receipts: List[Dict[str, Any]] = Field(default_factory=list)
    weights_sha256: Optional[str] = None
    dev_score: Optional[float] = None


class FailureCard(BaseContractCard):
    """FailureCard: V3 predicted/gold IDs, suspected mechanism, diagnosed root causes, stratified baseline errors."""
    failure_card_id: str
    paper_id: str
    case_ids: List[str] = Field(default_factory=list)
    v3_predicted_gold: List[Dict[str, Any]] = Field(default_factory=list)
    suspected_mechanisms: List[str] = Field(default_factory=list)
    diagnosed_root_causes: List[str] = Field(default_factory=list)
    stratified_baseline_errors: Dict[str, Any] = Field(default_factory=dict)
    manifest_sha256: str = Field(default="")


class NoveltyCard(BaseContractCard):
    """NoveltyCard: >=3 closest works, direct overlaps, formal counterexample, N1..N7 criteria, independent human signoff."""
    novelty_card_id: str
    paper_id: str
    closest_works: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of at least 3 closest prior works with citation, DOI/URL, overlap and distinctions.",
    )
    direct_overlaps: List[str] = Field(default_factory=list)
    formal_counterexample: Optional[str] = Field(default=None)
    n1_to_n7_criteria: Dict[str, bool] = Field(default_factory=dict)
    independent_human_signoff: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Independent human expert sign-off dict containing 'signed': True, 'reviewer', 'date', 'affiliation'.",
    )


class MethodCard(BaseContractCard):
    """MethodCard: I/O features, objective, complexity, assumptions, active constraints, expected changed failure slices."""
    method_id: str
    paper_id: str
    io_features: List[str] = Field(default_factory=list)
    objective: str = ""
    complexity: str = ""
    assumptions: List[str] = Field(default_factory=list)
    active_constraints: List[str] = Field(default_factory=list)
    expected_changed_failure_slices: List[str] = Field(default_factory=list)
    code_sha256: Optional[str] = None


class WinCard(BaseContractCard):
    """WinCard: baseline champion, one-shot test hash, metric and delta, CIs, p_adjusted, safety invariants, replication, claim status."""
    claim_id: str
    paper_id: str
    claim_type: WinType
    estimand: str
    primary_metric: str
    delta_min: float
    baseline_champion_id: str
    baseline_candidates_all: List[str] = Field(default_factory=list)
    excluded_with_reasons: Dict[str, str] = Field(default_factory=dict)
    prereg_sha256: str
    train_dev_test_hashes: Dict[str, str] = Field(default_factory=dict)
    model_sha256: str
    dataset_rights: str
    effect: float
    ci95: List[float] = Field(description="[lower_bound, upper_bound]")
    p_raw: float
    p_adjusted: float
    constraint_pass: bool
    n_clusters: int
    independent_replication: bool
    negative_controls: bool
    human_approval: bool
    claim_status: ClaimStatus
