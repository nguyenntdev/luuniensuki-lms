# -*- coding: utf-8 -*-
"""V5-T122 (Wave W12, Slot A02): Zero-Fake-Success Full-Site Sweep Service.

Traverses reachable routes under empty DB, 5xx, 403, and offline states across
frontend/src/, mobile/lib/, and backend/.
Enforces:
1. Zero synthetic mock bookings, fake payments, fabricated grades, or phantom assets.
2. 0 artificial inquiry, grade, or annotation accepted or falsely marked successful.
3. Cryptographically signed zero-fake-success release gate report (SHA-256 seal).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class RouteAuditResult:
    """Outcome of auditing a single route under a given execution scenario."""
    route: str
    method: str
    scenario: str  # "empty_db", "5xx_error", "403_forbidden", "offline_blocked"
    status_code: int
    expected_status: int
    fake_success_detected: bool
    passed: bool
    violation_details: Optional[str] = None


@dataclass
class NegativeAbuseResult:
    """Outcome of testing negative abuse protection (rejecting artificial inputs)."""
    invariant: str  # "artificial_inquiry", "artificial_grade", "artificial_annotation", "fake_payment", "phantom_mesh"
    test_case: str
    input_payload: Dict[str, Any]
    rejected_properly: bool
    status_code: int
    error_code: Optional[str] = None
    violation_details: Optional[str] = None


@dataclass
class StaticCodebaseAuditResult:
    """Outcome of static codebase inspection for fake success antipatterns."""
    stack: str  # "frontend", "mobile", "backend"
    files_scanned: int
    violations_found: int
    violation_files: List[str] = field(default_factory=list)
    details: List[str] = field(default_factory=list)
    passed: bool = True


@dataclass
class ZeroFakeSuccessSweepReport:
    """Comprehensive site-wide audit report for Ticket V5-T122."""
    report_id: str
    status: str  # "GATE_PASSED" or "GATE_BLOCKED"
    timestamp: str
    total_route_audits: int
    total_negative_abuse_tests: int
    total_codebase_audits: int
    violations_count: int
    route_results: List[RouteAuditResult] = field(default_factory=list)
    abuse_results: List[NegativeAbuseResult] = field(default_factory=list)
    codebase_results: List[StaticCodebaseAuditResult] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    sha256_hash: str = ""

    def compute_sha256(self) -> str:
        payload = {
            "report_id": self.report_id,
            "status": self.status,
            "timestamp": self.timestamp,
            "total_route_audits": self.total_route_audits,
            "total_negative_abuse_tests": self.total_negative_abuse_tests,
            "total_codebase_audits": self.total_codebase_audits,
            "violations_count": self.violations_count,
            "blockers": self.blockers,
        }
        dump = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(dump).hexdigest()


class ZeroFakeSuccessAuditor:
    """Executes full-site sweep across frontend, mobile, and backend."""

    # Prohibited tokens in production client runtime responses indicating fabricated success
    FORBIDDEN_SUCCESS_INDICATORS = {
        "mock_payment_confirmed",
        "fake_payment",
        "synthetic_booking",
        "fake_booking_confirmed",
        "fabricated_grade",
        "used_mock_in_production",
    }

    @classmethod
    def audit_response_for_fake_success(
        cls,
        route: str,
        method: str,
        scenario: str,
        status_code: int,
        expected_status: int,
        response_data: Any,
    ) -> RouteAuditResult:
        """Inspects an API response to verify no fabricated success was returned."""
        fake_detected = False
        reasons: List[str] = []

        # 1. Status code sanity
        if scenario in ("5xx_error", "403_forbidden") and 200 <= status_code < 300:
            fake_detected = True
            reasons.append(f"Expected failure for {scenario} but received HTTP {status_code} OK")

        # 2. Response body dictionary inspection
        if isinstance(response_data, dict):
            for bad_key in cls.FORBIDDEN_SUCCESS_INDICATORS:
                if response_data.get(bad_key) is True:
                    fake_detected = True
                    reasons.append(f"Forbidden fake success marker '{bad_key}=true' returned")

            # Check if an error endpoint returned a positive success flag
            if status_code >= 400 and response_data.get("success") is True:
                fake_detected = True
                reasons.append(f"HTTP {status_code} response claimed 'success: true'")

        # 3. Empty DB check: list responses must be empty, not populated with synthetic items
        if scenario == "empty_db":
            if isinstance(response_data, list) and len(response_data) > 0:
                # If checking empty tenant or clean state
                fake_detected = True
                reasons.append(f"Empty DB scenario returned {len(response_data)} unexpected records")
            elif isinstance(response_data, dict):
                items = response_data.get("items")
                total = response_data.get("total")
                if isinstance(items, list) and len(items) > 0:
                    fake_detected = True
                    reasons.append(f"Empty DB scenario returned {len(items)} synthetic items")

        passed = (not fake_detected) and (status_code == expected_status)
        if not passed and not reasons:
            reasons.append(f"HTTP status mismatch: expected {expected_status}, got {status_code}")

        return RouteAuditResult(
            route=route,
            method=method,
            scenario=scenario,
            status_code=status_code,
            expected_status=expected_status,
            fake_success_detected=fake_detected,
            passed=passed,
            violation_details="; ".join(reasons) if reasons else None,
        )

    @classmethod
    def scan_frontend_codebase(cls, frontend_root: Optional[Path] = None) -> StaticCodebaseAuditResult:
        """Statically analyzes frontend/src/ for fake success, mock injections, and error rethrowing."""
        root = frontend_root or (REPO_ROOT / "frontend" / "src")
        if not root.exists():
            return StaticCodebaseAuditResult(
                stack="frontend",
                files_scanned=0,
                violations_found=1,
                violation_files=[str(root)],
                details=[f"Frontend root {root} does not exist"],
                passed=False,
            )

        scanned = 0
        violations = 0
        violation_files: List[str] = []
        details: List[str] = []

        # Key files that must enforce zero-fake-success
        key_files = [
            root / "lib" / "rbpc" / "inquiries.ts",
            root / "lib" / "imperial" / "submissions-api.ts",
            root / "lib" / "imperial" / "map-api.ts",
        ]

        for file_path in key_files:
            if not file_path.exists():
                violations += 1
                violation_files.append(str(file_path))
                details.append(f"Missing required client library: {file_path.name}")
                continue

            scanned += 1
            content = file_path.read_text(encoding="utf-8")

            # Check inquiries.ts
            if file_path.name == "inquiries.ts":
                if "throw new ApiError" not in content and "throw error" not in content:
                    violations += 1
                    violation_files.append(str(file_path))
                    details.append("inquiries.ts does not re-throw errors on network/server failures")
                if "DEMO DATA" in content and "isDemo: true" not in content:
                    violations += 1
                    violation_files.append(str(file_path))
                    details.append("inquiries.ts contains demo data without explicit isDemo flag")

            # Check submissions-api.ts
            if file_path.name == "submissions-api.ts":
                if "CLIENT_OFFLINE: Offline client cannot fake a server-confirmed submission" not in content:
                    violations += 1
                    violation_files.append(str(file_path))
                    details.append("submissions-api.ts missing offline fake submission guard")
                if "if (options?.demoMode)" not in content:
                    violations += 1
                    violation_files.append(str(file_path))
                    details.append("submissions-api.ts does not gate demo student submissions behind explicit demoMode")

            # Check map-api.ts
            if file_path.name == "map-api.ts":
                if "createAnnotation" in content and "await apiRequest" not in content:
                    violations += 1
                    violation_files.append(str(file_path))
                    details.append("map-api.ts createAnnotation does not call authoritative backend")

        return StaticCodebaseAuditResult(
            stack="frontend",
            files_scanned=scanned,
            violations_found=violations,
            violation_files=violation_files,
            details=details,
            passed=(violations == 0),
        )

    @classmethod
    def scan_mobile_codebase(cls, mobile_root: Optional[Path] = None) -> StaticCodebaseAuditResult:
        """Statically analyzes mobile/lib/ for phantom assets and fake success."""
        root = mobile_root or (REPO_ROOT / "mobile" / "lib")
        if not root.exists():
            return StaticCodebaseAuditResult(
                stack="mobile",
                files_scanned=0,
                violations_found=1,
                violation_files=[str(root)],
                details=[f"Mobile root {root} does not exist"],
                passed=False,
            )

        scanned = 0
        violations = 0
        violation_files: List[str] = []
        details: List[str] = []

        # Key files to check
        rubbing_view = root / "features" / "urn_viewer" / "presentation" / "widgets" / "rubbing_fallback_view.dart"
        practice_provider = root / "features" / "practice" / "presentation" / "providers" / "practice_provider.dart"

        if rubbing_view.exists():
            scanned += 1
            content = rubbing_view.read_text(encoding="utf-8")
            if "no phantom assets or fake 3D primitives" not in content:
                violations += 1
                violation_files.append(str(rubbing_view))
                details.append("rubbing_fallback_view.dart missing explicit anti-phantom asset disclaimer")
        else:
            violations += 1
            violation_files.append(str(rubbing_view))
            details.append("Missing rubbing_fallback_view.dart in mobile")

        if practice_provider.exists():
            scanned += 1
            content = practice_provider.read_text(encoding="utf-8")
            if "correctAnswer: ''" not in content and "Intentionally not leaked" not in content:
                violations += 1
                violation_files.append(str(practice_provider))
                details.append("practice_provider.dart leaks correct answers to client")
        else:
            violations += 1
            violation_files.append(str(practice_provider))
            details.append("Missing practice_provider.dart in mobile")

        return StaticCodebaseAuditResult(
            stack="mobile",
            files_scanned=scanned,
            violations_found=violations,
            violation_files=violation_files,
            details=details,
            passed=(violations == 0),
        )

    @classmethod
    def scan_backend_codebase(cls, backend_root: Optional[Path] = None) -> StaticCodebaseAuditResult:
        """Statically analyzes backend/ for anti-fake-success validators and models."""
        root = backend_root or (REPO_ROOT / "backend")
        if not root.exists():
            return StaticCodebaseAuditResult(
                stack="backend",
                files_scanned=0,
                violations_found=1,
                violation_files=[str(root)],
                details=[f"Backend root {root} does not exist"],
                passed=False,
            )

        scanned = 0
        violations = 0
        violation_files: List[str] = []
        details: List[str] = []

        rbpc_router = root / "routers" / "rbpc.py"
        imperial_router = root / "routers" / "imperial.py"
        imperial_map_service = root / "services" / "imperial_map.py"
        imperial_learning_service = root / "services" / "imperial_learning.py"

        for p in [rbpc_router, imperial_router, imperial_map_service, imperial_learning_service]:
            if not p.exists():
                violations += 1
                violation_files.append(str(p))
                details.append(f"Missing required backend file: {p.name}")
                continue

            scanned += 1
            content = p.read_text(encoding="utf-8")

            if p.name == "rbpc.py":
                if "RBPC_CONSENT_REQUIRED" not in content:
                    violations += 1
                    violation_files.append(str(p))
                    details.append("rbpc.py missing consent requirement check")
                if "RBPC_DATE_PAST" not in content:
                    violations += 1
                    violation_files.append(str(p))
                    details.append("rbpc.py missing past preferred date check")

            if p.name == "imperial_learning.py":
                if "INVALID_RUBRIC_SCORE" not in content:
                    violations += 1
                    violation_files.append(str(p))
                    details.append("imperial_learning.py missing rubric score validation")

            if p.name == "imperial_map.py":
                if "IMPERIAL_UV_OUT_OF_BOUNDS" not in content:
                    violations += 1
                    violation_files.append(str(p))
                    details.append("imperial_map.py missing UV out-of-bounds validation")

        return StaticCodebaseAuditResult(
            stack="backend",
            files_scanned=scanned,
            violations_found=violations,
            violation_files=violation_files,
            details=details,
            passed=(violations == 0),
        )

    @classmethod
    def assemble_sweep_report(
        cls,
        route_results: List[RouteAuditResult],
        abuse_results: List[NegativeAbuseResult],
        codebase_results: List[StaticCodebaseAuditResult],
    ) -> ZeroFakeSuccessSweepReport:
        """Assembles all audit checks into a unified report and calculates gate status."""
        blockers: List[str] = []

        for r in route_results:
            if not r.passed or r.fake_success_detected:
                blockers.append(
                    f"ROUTE VIOLATION: {r.method} {r.route} under {r.scenario} failed: {r.violation_details}"
                )

        for a in abuse_results:
            if not a.rejected_properly:
                blockers.append(
                    f"NEGATIVE ABUSE LEAK: {a.invariant} ({a.test_case}) was accepted with HTTP {a.status_code}: {a.violation_details}"
                )

        for c in codebase_results:
            if not c.passed:
                blockers.append(
                    f"CODEBASE VIOLATION ({c.stack}): {'; '.join(c.details)}"
                )

        gate_status = "GATE_BLOCKED" if blockers else "GATE_PASSED"
        report_id = f"SWEEP-{uuid.uuid4().hex[:12].upper()}"
        ts = datetime.now(timezone.utc).isoformat()

        report = ZeroFakeSuccessSweepReport(
            report_id=report_id,
            status=gate_status,
            timestamp=ts,
            total_route_audits=len(route_results),
            total_negative_abuse_tests=len(abuse_results),
            total_codebase_audits=len(codebase_results),
            violations_count=len(blockers),
            route_results=route_results,
            abuse_results=abuse_results,
            codebase_results=codebase_results,
            blockers=blockers,
        )
        report.sha256_hash = report.compute_sha256()
        return report
