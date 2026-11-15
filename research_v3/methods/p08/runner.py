"""P08 frozen campaign runner: builds fixtures, runs the defender, computes
metrics, writes the results bundle. Deterministic end-to-end.

Usage:
    python -m research_v3.methods.p08.runner --out research_artifacts_v3/runs/p08
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .attestation import AttestationKey
from .defender import PolicyConfig, RewardIntegrityDefender, VelocityPolicy
from .fixtures import (
    DUPLICATE_STRESS_COUNT,
    FARMING_BURST_SIZE,
    POLICY_VERSION,
    SEED,
    STALE_POLICY_VERSION,
    adversarial_deliveries,
    captured_valid_delivery,
    duplicate_stress_delivery,
    farming_burst_deliveries,
    honest_control_deliveries,
)
from .metrics import campaign_metrics
from .types import AwardDecision

DELIVERIES_PER_VECTOR = 500
HONEST_CONTROL_COUNT = 1000


def run_campaign() -> dict:
    server_key = AttestationKey.derive_from_seed("p08-campaign-key-1", SEED)
    attacker_key = AttestationKey.derive_from_seed("attacker-weak-key", SEED + ":attacker")

    config = PolicyConfig(
        policy_version=POLICY_VERSION,
        attestation_key=server_key,
        velocity=VelocityPolicy(window_seconds=60, max_submissions_per_learner=5),
    )

    honest = honest_control_deliveries(server_key)
    adversarial = adversarial_deliveries(server_key, attacker_key, DELIVERIES_PER_VECTOR)

    # --- main defender pass over adversarial streams ---
    # Each vector runs as an independent attack campaign against a defender
    # whose policy epoch ALREADY contains the original honest award: the
    # attacker replays a delivery that was captured AFTER the learner
    # legitimately earned the award (that is the threat scenario in
    # pre_registration.yaml). The captured delivery is therefore delivered
    # once (honestly) into each defender before the attack stream begins.
    captured = captured_valid_delivery(server_key)
    per_vector_verdicts: dict[str, list] = {}
    for vector_id, deliveries in sorted(adversarial.items()):
        defender = RewardIntegrityDefender(config)
        _original_verdict = defender.evaluate([captured])  # legitimate award
        per_vector_verdicts[vector_id] = defender.evaluate(deliveries)

    # --- honest control pass (separate defender: honest traffic evaluated on
    # its own, no adversarial contamination of velocity windows) ---
    honest_defender = RewardIntegrityDefender(config)
    honest_verdicts = honest_defender.evaluate(honest)

    # --- stress strata ---
    # SS1: 100x duplicate -> exactly 1 award
    ss1_defender = RewardIntegrityDefender(config)
    ss1_verdicts = ss1_defender.evaluate(duplicate_stress_delivery(server_key))
    idempotency_awards = sum(1 for v in ss1_verdicts if v.decision == AwardDecision.AWARD)

    # SS2: 30 distinct-evidence burst from one learner under velocity window
    ss2_defender = RewardIntegrityDefender(config)
    ss2_verdicts = ss2_defender.evaluate(farming_burst_deliveries(server_key))
    burst_grants = sum(1 for v in ss2_verdicts if v.decision == AwardDecision.AWARD)

    metrics = campaign_metrics(
        per_vector_verdicts, honest_verdicts,
        idempotency_award_count=idempotency_awards,
        farming_burst_grants=burst_grants,
    )

    result = {
        "campaign": "P08_reward_integrity",
        "evaluation_class": "SOFTWARE_SECURITY_EVALUATION",
        "human_outcomes_measured": False,
        "seed": SEED,
        "policy_version": POLICY_VERSION,
        "stale_policy_version": STALE_POLICY_VERSION,
        "deliveries": {
            "adversarial_per_vector": DELIVERIES_PER_VECTOR,
            "adversarial_total": DELIVERIES_PER_VECTOR * 6,
            "honest_control": len(honest),
            "duplicate_stress": DUPLICATE_STRESS_COUNT,
            "farming_burst": FARMING_BURST_SIZE,
        },
        "metrics": metrics.as_dict(),
        "per_vector_verdict_histogram": {
            vid: _verdict_histogram(seq) for vid, seq in per_vector_verdicts.items()
        },
        "stress": {
            "SS1_100x_duplicate": {
                "deliveries": len(ss1_verdicts),
                "awards": idempotency_awards,
                "verdict_histogram": _verdict_histogram(ss1_verdicts),
            },
            "SS2_fast_click_farming": {
                "deliveries": len(ss2_verdicts),
                "grants": burst_grants,
                "verdict_histogram": _verdict_histogram(ss2_verdicts),
            },
            "SS3_deceptive_badge_copy": {
                "status": "NOT_APPLICABLE",
                "reason": "human-perception stratum; software-security evaluation; human claims BLOCKED",
            },
        },
        "primary_gate": _primary_gate(metrics),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return result


def _verdict_histogram(verdicts) -> dict[str, int]:
    hist: dict[str, int] = {}
    for v in verdicts:
        hist[v.decision.value] = hist.get(v.decision.value, 0) + 1
    return dict(sorted(hist.items()))


def _primary_gate(metrics) -> dict:
    """Frozen acceptance bounds from pre_registration.yaml, exact counts."""
    total_adv = sum(v.deliveries for v in metrics.per_vector)
    misses = total_adv - round(metrics.pooled_detection_recall * total_adv)
    checks = {
        "false_award_count_zero": metrics.false_award_count == 0,
        "duplicate_award_count_zero": metrics.duplicate_award_count == 0,
        "pooled_recall_ge_0999": metrics.pooled_detection_recall >= 0.999,
        "honest_false_rejections_le_1": metrics.honest_false_rejection_count <= 1,
        "idempotency_100x_exactly_1_award": metrics.idempotency_award_count == 1,
        "farming_burst_within_velocity_cap": metrics.farming_burst_grants <= 5,
    }
    weakest_vector = min(metrics.per_vector, key=lambda v: v.detection_recall)
    checks["every_vector_recall_ge_0999"] = weakest_vector.detection_recall >= 0.999
    return {
        "checks": checks,
        "passed": all(checks.values()),
        "weakest_vector": weakest_vector.as_dict(),
        "adversarial_total": total_adv,
        "recall_misses_allowed": 3,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="P08 frozen campaign")
    parser.add_argument("--out", type=Path,
                        default=Path("research_artifacts_v3/runs/p08"))
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()

    result = run_campaign()
    payload = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True)
    if args.stdout:
        print(payload)
    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "evaluation_results.json").write_text(payload + "\n", encoding="utf-8")
    print(f"wrote {out_dir / 'evaluation_results.json'}")


if __name__ == "__main__":
    main()
