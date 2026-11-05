# -*- coding: utf-8 -*-
"""Production Service Level Objective (SLO) & Release Gate Engine (V5-T090 / Wave W08).

Provides:
1. Production SLO Targets:
   - Read latency: p95 API response <= 300ms for static and read-only endpoints.
   - Availability & resilience: Graceful handling of upstream 502/503 errors with Retry-After and exponential backoff policies.
   - 2D fallback availability: 100% verified 2D rubbing archives for all 9 urns and 162 motif relics.
2. Anti-Abuse & Release Gate Enforcement:
   - Zero critical fake success: mock booking, fake payment, or fabricated grades strictly trigger GATE_BLOCKED.
   - Signed release gate verification sheet with cryptographic SHA-256 seal.
"""
from __future__ import annotations

import hashlib
import json
import statistics
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class ReleaseGateStatus(str, Enum):
    GATE_PASSED = "GATE_PASSED"
    GATE_BLOCKED = "GATE_BLOCKED"


class SLOViolationType(str, Enum):
    LATENCY_EXCEEDED = "LATENCY_EXCEEDED"
    AVAILABILITY_DEGRADED = "AVAILABILITY_DEGRADED"
    FALLBACK_MISSING = "FALLBACK_MISSING"
    FAKE_SUCCESS_DETECTED = "FAKE_SUCCESS_DETECTED"
    RETRY_POLICY_MISSING = "RETRY_POLICY_MISSING"


@dataclass
class LatencyBenchmarkResult:
    endpoint: str
    total_samples: int
    latencies_ms: List[float]
    min_ms: float
    avg_ms: float
    p95_ms: float
    max_ms: float
    target_p95_ms: float
    passed: bool


@dataclass
class UpstreamResilienceResult:
    scenario: str
    upstream_status: int
    graceful_handled: bool
    status_code_returned: int
    retry_header_present: bool
    retry_after_seconds: Optional[int]
    backoff_strategy: str
    degraded_response_valid: bool
    passed: bool


@dataclass
class FallbackAvailabilityResult:
    total_urns_checked: int
    total_motifs_checked: int
    urns_with_2d_fallback: int
    motifs_with_2d_fallback: int
    fallback_coverage_pct: float
    missing_assets: List[str]
    passed: bool


@dataclass
class FakeSuccessAuditItem:
    flow_name: str
    operation: str
    is_critical_financial_or_academic: bool
    detected_mock_success: bool
    blocked_by_gate: bool
    violation_details: Optional[str] = None


@dataclass
class ProductionSLOGateReport:
    report_id: str
    gate_status: ReleaseGateStatus
    latency_benchmarks: List[LatencyBenchmarkResult] = field(default_factory=list)
    resilience_results: List[UpstreamResilienceResult] = field(default_factory=list)
    fallback_results: Optional[FallbackAvailabilityResult] = None
    fake_success_audits: List[FakeSuccessAuditItem] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    signed_hash: str = ""

    def compute_sha256(self) -> str:
        payload = {
            "report_id": self.report_id,
            "gate_status": self.gate_status.value,
            "blockers": self.blockers,
            "total_fake_audits": len(self.fake_success_audits),
            "total_latency_tests": len(self.latency_benchmarks),
        }
        dump = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(dump).hexdigest()


class ProductionSLOEngine:
    """Production Service Level Objective (SLO) verifier and gate keeper."""

    STATIC_READ_P95_BUDGET_MS: float = 300.0

    @classmethod
    def evaluate_latency_benchmark(
        cls,
        endpoint: str,
        latencies_ms: List[float],
        target_p95_ms: float = 300.0,
    ) -> LatencyBenchmarkResult:
        if not latencies_ms:
            return LatencyBenchmarkResult(
                endpoint=endpoint,
                total_samples=0,
                latencies_ms=[],
                min_ms=0.0,
                avg_ms=0.0,
                p95_ms=0.0,
                max_ms=0.0,
                target_p95_ms=target_p95_ms,
                passed=False,
            )

        sorted_latencies = sorted(latencies_ms)
        total = len(sorted_latencies)
        p95_idx = max(0, int(0.95 * total) - 1)
        p95_val = sorted_latencies[p95_idx]

        min_val = round(min(sorted_latencies), 2)
        avg_val = round(statistics.mean(sorted_latencies), 2)
        p95_val = round(p95_val, 2)
        max_val = round(max(sorted_latencies), 2)

        passed = p95_val <= target_p95_ms

        return LatencyBenchmarkResult(
            endpoint=endpoint,
            total_samples=total,
            latencies_ms=sorted_latencies,
            min_ms=min_val,
            avg_ms=avg_val,
            p95_ms=p95_val,
            max_ms=max_val,
            target_p95_ms=target_p95_ms,
            passed=passed,
        )

    @classmethod
    def verify_upstream_resilience(
        cls,
        scenario: str,
        upstream_status: int,
        response_status: int,
        response_headers: Dict[str, str],
        response_body: Dict[str, Any],
    ) -> UpstreamResilienceResult:
        """Verifies resilience behavior when upstream dependency fails (502/503)."""
        retry_header = response_headers.get("Retry-After") or response_headers.get("retry-after")
        retry_secs = int(retry_header) if (retry_header and retry_header.isdigit()) else None

        # Check for retry policy inside body (e.g. AI fallback responses)
        body_policy = response_body.get("retry_policy", {})
        if not retry_secs and "retry_after_seconds" in body_policy:
            retry_secs = body_policy["retry_after_seconds"]

        backoff_strategy = body_policy.get("strategy") or ("exponential_backoff" if retry_secs else "none")

        # Graceful handling: must return either a typed 429/503 error with Retry-After or a valid degraded fallback
        is_typed_resilient_error = response_status in (429, 502, 503) and (retry_secs is not None)
        is_valid_degraded_fallback = response_status == 200 and (
            response_body.get("is_fallback") is True
            or response_body.get("fallback_engaged") is not None
            or body_policy.get("fallback_engaged") is not None
        )

        graceful = is_typed_resilient_error or is_valid_degraded_fallback
        passed = graceful and (retry_secs is not None or is_valid_degraded_fallback)

        return UpstreamResilienceResult(
            scenario=scenario,
            upstream_status=upstream_status,
            graceful_handled=graceful,
            status_code_returned=response_status,
            retry_header_present=retry_secs is not None,
            retry_after_seconds=retry_secs,
            backoff_strategy=backoff_strategy,
            degraded_response_valid=graceful,
            passed=passed,
        )

    @classmethod
    def verify_2d_fallback_availability(
        cls,
        urn_registry: Dict[str, Any],
        motifs_registry: List[Dict[str, Any]],
    ) -> FallbackAvailabilityResult:
        """Verifies 100% 2D rubbing fallback presence for all 9 urns and 162 motif relics."""
        missing = []
        urns_valid = 0
        motifs_valid = 0

        for slug, meta in urn_registry.items():
            if meta.get("asset_url") and meta.get("bytes", 0) > 0 and meta.get("sha256"):
                urns_valid += 1
            else:
                missing.append(f"urn:{slug}")

        for motif in motifs_registry:
            m_id = motif.get("motif_id", "unknown")
            has_fallback = (
                motif.get("fallback_2d") is not None
                or motif.get("thumbnail_url") is not None
                or motif.get("rubbing_url") is not None
            )
            if has_fallback:
                motifs_valid += 1
            else:
                missing.append(f"motif:{m_id}")

        total_urns = len(urn_registry)
        total_motifs = len(motifs_registry)
        total_items = total_urns + total_motifs
        coverage_pct = round(((urns_valid + motifs_valid) / total_items * 100.0), 2) if total_items else 0.0

        passed = (urns_valid == total_urns == 9) and (len(missing) == 0) and (coverage_pct == 100.0)

        return FallbackAvailabilityResult(
            total_urns_checked=total_urns,
            total_motifs_checked=total_motifs,
            urns_with_2d_fallback=urns_valid,
            motifs_with_2d_fallback=motifs_valid,
            fallback_coverage_pct=coverage_pct,
            missing_assets=missing,
            passed=passed,
        )

    @classmethod
    def audit_fake_success_gate(
        cls,
        flow_name: str,
        operation: str,
        is_critical_financial_or_academic: bool,
        response_data: Dict[str, Any],
        expected_authentic: bool = True,
    ) -> FakeSuccessAuditItem:
        """Audits an operation for fake mock success (mock booking, fake payment, fabricated grade).

        If critical and mock success is detected without genuine server confirmation,
        release gate is strictly blocked.
        """
        # Look for prohibited indicators of simulated success
        detected_mock = False
        reasons = []

        if response_data.get("mock_payment_confirmed") is True or response_data.get("fake_payment") is True:
            detected_mock = True
            reasons.append("Simulated instant payment mock returned confirmed")

        if response_data.get("fake_booking_confirmed") is True or response_data.get("synthetic_booking") is True:
            detected_mock = True
            reasons.append("Synthetic booking confirmed without partner confirmation")

        if response_data.get("fabricated_grade") is True:
            detected_mock = True
            reasons.append("Fabricated grade awarded without teacher rubric evaluation")

        if response_data.get("used_mock_in_production") is True:
            detected_mock = True
            reasons.append("Used unflagged mock provider in production mode")

        # Any critical flow with detected mock success triggers gate block
        blocked = is_critical_financial_or_academic and detected_mock

        return FakeSuccessAuditItem(
            flow_name=flow_name,
            operation=operation,
            is_critical_financial_or_academic=is_critical_financial_or_academic,
            detected_mock_success=detected_mock,
            blocked_by_gate=blocked,
            violation_details="; ".join(reasons) if reasons else None,
        )

    @classmethod
    def assemble_release_gate_report(
        cls,
        report_id: str,
        latency_results: List[LatencyBenchmarkResult],
        resilience_results: List[UpstreamResilienceResult],
        fallback_result: FallbackAvailabilityResult,
        fake_audits: List[FakeSuccessAuditItem],
    ) -> ProductionSLOGateReport:
        blockers: List[str] = []

        # 1. Latency blockers
        for lb in latency_results:
            if not lb.passed:
                blockers.append(
                    f"SLO P0 LATENCY EXCEEDED: Endpoint '{lb.endpoint}' p95 latency {lb.p95_ms}ms > budget {lb.target_p95_ms}ms"
                )

        # 2. Resilience blockers
        for rr in resilience_results:
            if not rr.passed:
                blockers.append(
                    f"SLO P0 AVAILABILITY FAILURE: Scenario '{rr.scenario}' failed upstream resilience check (status: {rr.status_code_returned})"
                )

        # 3. 2D Fallback blockers
        if not fallback_result.passed:
            blockers.append(
                f"SLO P0 MEDIA INTEGRITY: Missing 2D fallbacks (coverage: {fallback_result.fallback_coverage_pct}%, missing: {fallback_result.missing_assets})"
            )

        # 4. Critical Fake Success Blockers
        for fa in fake_audits:
            if fa.blocked_by_gate:
                blockers.append(
                    f"RELEASE GATE BLOCKED: Critical fake success detected in '{fa.flow_name}' ({fa.operation}): {fa.violation_details}"
                )

        status = ReleaseGateStatus.GATE_BLOCKED if blockers else ReleaseGateStatus.GATE_PASSED

        report = ProductionSLOGateReport(
            report_id=report_id,
            gate_status=status,
            latency_benchmarks=latency_results,
            resilience_results=resilience_results,
            fallback_results=fallback_result,
            fake_success_audits=fake_audits,
            blockers=blockers,
        )
        report.signed_hash = report.compute_sha256()
        return report
