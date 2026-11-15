"""P08 metrics: false-award rate, duplicate-award count, attack-detection
recall, honest false-rejection count, idempotency proof.

All metrics are exact counts over the frozen campaign; no resampling.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .types import AwardDecision, AwardVerdict


@dataclass
class VectorMetrics:
    vector_id: str
    deliveries: int
    rejected: int
    successful_attacks: int          # any AWARD granted to adversarial traffic
    detection_recall: float          # rejected / deliveries

    def as_dict(self) -> dict:
        return {
            "vector_id": self.vector_id,
            "deliveries": self.deliveries,
            "rejected": self.rejected,
            "successful_attacks": self.successful_attacks,
            "detection_recall": self.detection_recall,
        }


@dataclass
class CampaignMetrics:
    false_award_rate: float
    false_award_count: int
    duplicate_award_count: int
    honest_false_rejection_count: int
    honest_deliveries: int
    pooled_detection_recall: float
    per_vector: list[VectorMetrics] = field(default_factory=list)
    idempotency_award_count: int = 0     # awards across the 100x stress (must be 1)
    farming_burst_grants: int = 0        # grants in the 30-burst stress window
    decisions_histogram: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "false_award_rate": self.false_award_rate,
            "false_award_count": self.false_award_count,
            "duplicate_award_count": self.duplicate_award_count,
            "honest_false_rejection_count": self.honest_false_rejection_count,
            "honest_deliveries": self.honest_deliveries,
            "pooled_detection_recall": self.pooled_detection_recall,
            "per_vector": [v.as_dict() for v in self.per_vector],
            "idempotency_award_count": self.idempotency_award_count,
            "farming_burst_grants": self.farming_burst_grants,
            "decisions_histogram": dict(self.decisions_histogram),
        }


def _histogram(verdicts: Sequence[AwardVerdict]) -> dict[str, int]:
    hist: dict[str, int] = {}
    for v in verdicts:
        hist[v.decision.value] = hist.get(v.decision.value, 0) + 1
    return dict(sorted(hist.items()))


def vector_metrics(vector_id: str, verdicts: Sequence[AwardVerdict]) -> VectorMetrics:
    deliveries = len(verdicts)
    rejected = sum(1 for v in verdicts if v.decision != AwardDecision.AWARD)
    successful = sum(1 for v in verdicts if v.decision == AwardDecision.AWARD)
    recall = (rejected / deliveries) if deliveries else 1.0
    return VectorMetrics(
        vector_id=vector_id,
        deliveries=deliveries,
        rejected=rejected,
        successful_attacks=successful,
        detection_recall=recall,
    )


def duplicate_award_count(verdicts: Sequence[AwardVerdict]) -> int:
    """Awards beyond the first per dedup identity (0 == perfect idempotency)."""
    seen: set[str] = set()
    duplicates = 0
    for v in verdicts:
        if v.decision == AwardDecision.AWARD:
            key = v.dedup_key or ""
            if key in seen:
                duplicates += 1
            else:
                seen.add(key)
    return duplicates


def campaign_metrics(
    adversarial: dict[str, Sequence[AwardVerdict]],
    honest: Sequence[AwardVerdict],
    *,
    idempotency_award_count: int = 0,
    farming_burst_grants: int = 0,
) -> CampaignMetrics:
    adversarial_flat = [v for seq in adversarial.values() for v in seq]
    total_adv = len(adversarial_flat)
    false_awards = sum(1 for v in adversarial_flat if v.decision == AwardDecision.AWARD)
    per_vector = [vector_metrics(vid, seq) for vid, seq in adversarial.items()]
    rejected_total = sum(1 for v in adversarial_flat if v.decision != AwardDecision.AWARD)
    honest_rejections = sum(1 for v in honest if v.decision != AwardDecision.AWARD)
    all_verdicts = adversarial_flat + list(honest)
    return CampaignMetrics(
        false_award_rate=(false_awards / total_adv) if total_adv else 0.0,
        false_award_count=false_awards,
        duplicate_award_count=duplicate_award_count(adversarial_flat),
        honest_false_rejection_count=honest_rejections,
        honest_deliveries=len(honest),
        pooled_detection_recall=(rejected_total / total_adv) if total_adv else 1.0,
        per_vector=per_vector,
        idempotency_award_count=idempotency_award_count,
        farming_burst_grants=farming_burst_grants,
        decisions_histogram=_histogram(all_verdicts),
    )
