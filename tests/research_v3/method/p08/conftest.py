"""P08 shared fixtures: frozen keys, config, and builders."""
from __future__ import annotations

import pytest

from research_v3.methods.p08.attestation import AttestationKey
from research_v3.methods.p08.defender import PolicyConfig, RewardIntegrityDefender, VelocityPolicy
from research_v3.methods.p08.fixtures import POLICY_VERSION, SEED
from research_v3.methods.p08.types import Delivery, LearnerProfile, RewardEvent, Submission


@pytest.fixture(scope="session")
def server_key() -> AttestationKey:
    return AttestationKey.derive_from_seed("p08-campaign-key-1", SEED)


@pytest.fixture(scope="session")
def attacker_key() -> AttestationKey:
    return AttestationKey.derive_from_seed("attacker-weak-key", SEED + ":attacker")


@pytest.fixture(scope="session")
def config(server_key: AttestationKey) -> PolicyConfig:
    return PolicyConfig(
        policy_version=POLICY_VERSION,
        attestation_key=server_key,
        velocity=VelocityPolicy(window_seconds=60, max_submissions_per_learner=5),
    )


def make_submission(
    learner_id: str = "learner-t",
    comp: str = "S1",
    level: float = 0.9,
    task_id: str = "task-t",
    kind: str = "mastered",
    verified: bool = True,
) -> Submission:
    return Submission(
        learner=LearnerProfile(learner_id=learner_id, competencies={comp: level}),
        badge_id=f"badge-{comp}",
        requires_competency=comp,
        min_level=0.75,
        skill_evidence={comp: level},
        verified_task=verified,
        events=(RewardEvent(kind=kind, task_id=task_id, competency=comp, level=level),),
    )


def make_delivery(
    sub: Submission,
    server_key: AttestationKey,
    *,
    event_id: str = "evt-1",
    session_id: str = "sess-1",
    device_id: str = "dev-1",
    client_timestamp: str = "2026-11-15T09:00:00Z",
    policy_version: int = POLICY_VERSION,
    hmac_hex: str | None = None,
) -> Delivery:
    return Delivery(
        submission=sub,
        event_id=event_id,
        session_id=session_id,
        device_id=device_id,
        client_timestamp=client_timestamp,
        policy_version=policy_version,
        hmac_hex=hmac_hex if hmac_hex is not None else server_key.sign(sub, policy_version),
        evaluator_meta={},
    )


def new_defender(config: PolicyConfig) -> RewardIntegrityDefender:
    return RewardIntegrityDefender(config)
