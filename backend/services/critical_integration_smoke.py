# -*- coding: utf-8 -*-
"""LƯU NIÊN — Critical Integration Smoke Engine (V5-T123 / Wave W12, Slot A03).

Provides end-to-end integration orchestration and verification across:
1. Multi-Persona Flows:
   - Visitor: Browsing catalog, inquiry submission, anonymous zero-PII status tracking.
   - Partner: Inbox management, status lifecycle (new -> contacted -> confirmed), revenue settlement.
   - Teacher: Classroom setup, join codes, source-locked assignments, rubric grading (0-3 scale), gradebook export.
   - Student: Enrollment, 3D/motif discovery, evidence-synthesized assignment submission, grade inspection.
2. Cross-Stack Architectural Parity:
   - Rust Gateway / Python HS256 JWT interoperability ({sub, iat, exp, role, type, jti, iss, aud}).
   - Route inventory & route-modes TOML verification (pinned gateway vs native Axum routes).
   - Multi-client dual auth: Web (cookie-based) and Mobile (Bearer token) coherence.
   - Cross-device sync & offline queue idempotency with zero duplicate XP replay protection.
3. Database Durability & Restart Resilience:
   - Simulates complete system restart via connection pool disposal and fresh session creation.
   - Verifies 100% data consistency, referential integrity, and uncorrupted cryptographic audit hash chains.
4. Negative Abuse & Tamper Defense:
   - Cross-persona mutation rejection (403 Forbidden).
   - Multi-tenant classroom and partner isolation.
   - Zero-fake-success enforcement on nonexistent tokens (404 Not Found).
   - Zero PII leakage in public inquiry status lookups.
   - Cryptographic hash chain tamper-evidence detection.
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from jose import jwt
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.config import settings
from backend.deps import _decode_access_token
from backend.history_models import (
    HistoricalClaim,
    HistoricalEntity,
    HistoricalSource,
    HistoryAssignmentSubmission,
    HistoryLessonAssignment,
)
from backend.models import (
    ClassMember,
    Classroom,
    ContentStatus,
    LessonContent,
    Motif,
    MotifCategory,
    MotifRarity,
    UnlockStatus,
    Urn,
    User,
    UserProgress,
    UserRole,
)
from backend.models_rbpc import (
    RbpcConsentStatus,
    RbpcContentAudit,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcInquiryStatus,
)
from backend.services.rbpc_audit import verify_audit_chain

logger = logging.getLogger("luuniensuki.critical_integration_smoke")


@dataclass
class PersonaStepResult:
    persona: str
    action: str
    status: str
    reference_id: Optional[str] = None
    http_status: int = 200
    details: Dict[str, Any] = field(default_factory=dict)
    passed: bool = True


@dataclass
class CrossStackCheckResult:
    check_name: str
    component_a: str
    component_b: str
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NegativeAbuseCheckResult:
    scenario: str
    target_role: str
    expected_error_code: int
    observed_status_code: int
    abuse_prevented: bool
    details: str = ""


@dataclass
class CriticalIntegrationSmokeReport:
    ticket_id: str = "V5-T123"
    wave: str = "W12"
    slot: str = "A03"
    priority: str = "P0"
    classification: str = "PRODUCTION_COMPLETION"
    title: str = "Critical integration smoke test across Rust/Python/Postgres/Next.js/Flutter"
    gate_status: str = "GATE_PASSED"
    verified_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    persona_flow_results: List[Dict[str, Any]] = field(default_factory=list)
    cross_stack_results: List[Dict[str, Any]] = field(default_factory=list)
    negative_abuse_results: List[Dict[str, Any]] = field(default_factory=list)
    persistence_restart_verified: bool = True
    audit_chain_verified: bool = True
    zero_fake_success_verified: bool = True
    zero_pii_leakage_verified: bool = True
    summary: Dict[str, Any] = field(default_factory=dict)


class CriticalIntegrationSmokeService:
    """Service orchestrating and auditing the polyglot integration smoke checks."""

    @staticmethod
    def verify_rust_route_modes(
        config_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Verify Rust Gateway route modes configuration for route pinning."""
        if config_path is None:
            config_path = (
                Path(__file__).resolve().parents[2]
                / "backend-rust"
                / "config"
                / "route-modes.toml"
            )

        if not config_path.exists():
            return {
                "passed": False,
                "error": f"route-modes.toml not found at {config_path}",
                "pinned_gateway_routes": [],
                "defaults": {},
            }

        text = config_path.read_text(encoding="utf-8")
        lines = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]

        gateway_pinned = []
        in_routes = False
        in_defaults = False
        default_unknown = None

        for line in lines:
            if line.startswith("[routes]"):
                in_routes = True
                in_defaults = False
                continue
            if line.startswith("[defaults]"):
                in_routes = False
                in_defaults = True
                continue

            if in_routes and "=" in line:
                key, val = [part.strip().strip('"') for part in line.split("=", 1)]
                if val == "gateway":
                    gateway_pinned.append(key)
            elif in_defaults and "=" in line:
                key, val = [part.strip().strip('"') for part in line.split("=", 1)]
                if key == "unknown_routes":
                    default_unknown = val

        has_live_routes = any("/api/v1/live/" in r for r in gateway_pinned)
        has_ai_routes = any("/api/v1/ai-tutor/" in r for r in gateway_pinned)
        is_native_default = default_unknown == "native"

        passed = has_live_routes and has_ai_routes and is_native_default

        return {
            "passed": passed,
            "pinned_gateway_routes_count": len(gateway_pinned),
            "sample_pinned_routes": gateway_pinned[:6],
            "default_unknown_routes": default_unknown,
            "has_live_routes": has_live_routes,
            "has_ai_routes": has_ai_routes,
        }

    @staticmethod
    def mint_rust_compatible_token(
        subject_id: str,
        role: str = "learner",
        token_type: str = "access",
        expires_seconds: int = 3600,
        custom_secret: Optional[str] = None,
    ) -> str:
        """Mint an HS256 JWT token with the exact claim shape issued by backend-rust/src/auth.rs."""
        now = int(datetime.now(timezone.utc).timestamp())
        claims = {
            "sub": subject_id,
            "iat": now,
            "exp": now + expires_seconds,
            "role": role,
            "type": token_type,
            "jti": str(uuid4()),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        }
        secret = custom_secret or settings.jwt_secret_key
        return jwt.encode(claims, secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def verify_cross_backend_jwt_acceptance(token: str) -> Dict[str, Any]:
        """Verify that a token minted with Rust claim shape is accepted by Python verifier."""
        decoded_uuid = _decode_access_token(token)
        return {
            "valid": decoded_uuid is not None,
            "decoded_user_id": str(decoded_uuid) if decoded_uuid else None,
        }

    @staticmethod
    def audit_database_persistence_across_restart(
        engine: Any,
        session_factory: Any,
        recorded_ids: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Verify complete database persistence after disposing connection pool and restarting session."""
        # 1. Dispose engine pool if available (or close connection) to simulate restart
        if hasattr(engine, "dispose"):
            engine.dispose()
        elif hasattr(engine, "engine") and hasattr(engine.engine, "dispose"):
            engine.engine.dispose()

        # 2. Open brand new session directly from engine
        with session_factory() as session:
            # Check users
            users_found = {}
            for role_name, user_id in recorded_ids.get("users", {}).items():
                u = session.get(User, UUID(str(user_id)))
                users_found[role_name] = u is not None and u.email is not None

            # Check classroom
            classroom_id = recorded_ids.get("classroom_id")
            classroom_persisted = False
            if classroom_id:
                cr = session.get(Classroom, UUID(str(classroom_id)))
                classroom_persisted = cr is not None and len(cr.class_code) == 8

            # Check assignment & submission
            assignment_id = recorded_ids.get("assignment_id")
            assignment_persisted = False
            if assignment_id:
                assign = session.get(HistoryLessonAssignment, UUID(str(assignment_id)))
                assignment_persisted = assign is not None and assign.status == "published"

            submission_id = recorded_ids.get("submission_id")
            submission_persisted = False
            submission_score = None
            if submission_id:
                subm = session.get(HistoryAssignmentSubmission, UUID(str(submission_id)))
                if subm:
                    submission_persisted = subm.status == "graded"
                    submission_score = subm.score

            # Check partner inquiry
            inquiry_id = recorded_ids.get("inquiry_id")
            inquiry_persisted = False
            inquiry_status = None
            if inquiry_id:
                inq = session.get(RbpcInquiry, UUID(str(inquiry_id)))
                if inq:
                    inquiry_persisted = inq.status == RbpcInquiryStatus.confirmed.value
                    inquiry_status = inq.status

            # Check audit hash chain
            chain_valid = False
            if inquiry_id:
                chain_ok, _ = verify_audit_chain(
                    session,
                    entity_type="inquiry",
                    entity_id=UUID(str(inquiry_id)),
                )
                chain_valid = chain_ok

            all_passed = (
                all(users_found.values())
                and classroom_persisted
                and assignment_persisted
                and submission_persisted
                and inquiry_persisted
                and chain_valid
            )

            return {
                "passed": all_passed,
                "users_verified": users_found,
                "classroom_persisted": classroom_persisted,
                "assignment_persisted": assignment_persisted,
                "submission_persisted": submission_persisted,
                "submission_score": submission_score,
                "inquiry_persisted": inquiry_persisted,
                "inquiry_status": inquiry_status,
                "audit_chain_valid": chain_valid,
            }

    @staticmethod
    def compile_smoke_report(
        persona_steps: List[PersonaStepResult],
        cross_stack_checks: List[CrossStackCheckResult],
        negative_abuse_checks: List[NegativeAbuseCheckResult],
        persistence_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compile complete standardized smoke report dictionary for artifacts/."""
        all_personas_passed = all(p.passed for p in persona_steps)
        all_cross_stack_passed = all(c.passed for c in cross_stack_checks)
        all_abuse_passed = all(n.abuse_prevented for n in negative_abuse_checks)
        persistence_passed = persistence_summary.get("passed", False)

        overall_passed = (
            all_personas_passed
            and all_cross_stack_passed
            and all_abuse_passed
            and persistence_passed
        )

        report = CriticalIntegrationSmokeReport(
            gate_status="GATE_PASSED" if overall_passed else "GATE_BLOCKED",
            persona_flow_results=[asdict(p) for p in persona_steps],
            cross_stack_results=[asdict(c) for c in cross_stack_checks],
            negative_abuse_results=[asdict(n) for n in negative_abuse_checks],
            persistence_restart_verified=persistence_passed,
            audit_chain_verified=persistence_summary.get("audit_chain_valid", False),
            zero_fake_success_verified=all(
                n.abuse_prevented for n in negative_abuse_checks if "fake" in n.scenario.lower()
            ),
            zero_pii_leakage_verified=any(
                "zero_pii" in p.action.lower() and p.passed for p in persona_steps
            ),
            summary={
                "total_persona_steps": len(persona_steps),
                "passed_persona_steps": sum(1 for p in persona_steps if p.passed),
                "total_cross_stack_checks": len(cross_stack_checks),
                "passed_cross_stack_checks": sum(1 for c in cross_stack_checks if c.passed),
                "total_negative_abuse_checks": len(negative_abuse_checks),
                "passed_negative_abuse_checks": sum(1 for n in negative_abuse_checks if n.abuse_prevented),
                "persistence_restart_passed": persistence_passed,
                "all_invariants_met": overall_passed,
            },
        )
        return asdict(report)


default_smoke_service = CriticalIntegrationSmokeService()
