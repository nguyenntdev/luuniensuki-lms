"""V3-G19: double-blind external audit scaffold.

Writes a request artifact (the material an external auditor needs: release
pointer, method list, seed policy, verification commands) into
``research_v3/governance/audit_log/`` and BLOCKS until a human auditor returns
a completed review sheet (``review_<request_id>.json``) that satisfies the
schema: independent environment, verdict per claim, reviewer identity, and a
record hash. The scaffold NEVER fabricates a reviewer, a verdict, or a
"clean environment" result.

States: REQUESTED (artifact written) -> BLOCKED (no human review yet) ->
RECEIVED (a completed human review sheet exists and validates).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from research_v3.scripts._paths import AUDIT_LOG_DIR

HEX64 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_REVIEW_FIELDS = (
    "reviewer_name",
    "reviewer_affiliation",
    "clean_environment",
    "verdicts",
    "reviewed_at",
)

EXIT_OK = 0
EXIT_BLOCKED = 22
EXIT_INVALID_REVIEW = 23


class ExternalAuditError(RuntimeError):
    """Raised when the audit scaffold inputs are unusable."""


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(Path(__file__).resolve().parents[2]),
            text=True,
        ).strip()
    except Exception:  # pragma: no cover
        return "unknown"


def write_request(
    *,
    request_id: str,
    release_paths: list[Path],
    method_ids: list[str],
    seed_policy: str,
    audit_dir: Path | None = None,
) -> dict:
    """Create the double-blind rerun request artifact. Pure write, no verdicts."""
    target_dir = Path(audit_dir or AUDIT_LOG_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    request = {
        "schema": "research_v3.external_audit_request/v1",
        "task_id": "V3-G19",
        "request_id": request_id,
        "created_at_utc": now,
        "source_commit": _git_head(),
        "release_paths": [str(p) for p in release_paths],
        "methods_to_rerun": method_ids,
        "seed_policy": seed_policy,
        "verification_commands": [
            "python -m pytest -q tests/research_v3",
            "python -m research_v3.scripts.audit_repo --strict",
            "python -m research_v3.scripts.validate_contracts",
            "python -m research_v3.scripts.replicate --runs-root research_artifacts_v3/runs --kind <kind>",
        ],
        "blind_protocol": (
            "The auditor receives sealed predictions and gold WITHOUT method "
            "identities; identities are revealed only after verdicts are filed."
        ),
        "status": "REQUESTED",
        "human_review_pending": True,
        "note": (
            "BLOCKED until a human auditor returns review_%s.json with a signed "
            "verdict. The scaffold cannot and will not simulate that review." % request_id
        ),
    }
    path = target_dir / f"request_{request_id}.json"
    path.write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"request": request, "path": path}


def find_review(request_id: str, audit_dir: Path | None = None) -> tuple[Path | None, dict | None]:
    target_dir = Path(audit_dir or AUDIT_LOG_DIR)
    path = target_dir / f"review_{request_id}.json"
    if not path.is_file():
        return None, None
    try:
        return path, json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExternalAuditError(f"{path}: invalid review JSON: {exc}") from exc


def validate_review(review: dict) -> list[str]:
    findings: list[str] = []
    for field in REQUIRED_REVIEW_FIELDS:
        if field not in review or review[field] in (None, "", []):
            findings.append(f"missing required field {field!r}")
    if findings:
        return findings
    if review["clean_environment"] is not True:
        findings.append("clean_environment must be true (rerun in a fresh checkout/venv)")
    verdicts = review["verdicts"]
    if not isinstance(verdicts, dict) or not verdicts:
        findings.append("verdicts must be a non-empty mapping claim->VERIFIED|REFUTED|UNRESOLVED")
    else:
        for claim, verdict in verdicts.items():
            if verdict not in ("VERIFIED", "REFUTED", "UNRESOLVED"):
                findings.append(f"verdict for {claim!r} is {verdict!r}; use VERIFIED|REFUTED|UNRESOLVED")
    return findings


def audit_status(request_id: str, audit_dir: Path | None = None) -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    review_path, review = find_review(request_id, audit_dir)
    if review_path is None:
        return {
            "schema": "research_v3.external_audit_status/v1",
            "task_id": "V3-G19",
            "request_id": request_id,
            "checked_at_utc": now,
            "status": "BLOCKED",
            "reason": (
                f"No human review sheet review_{request_id}.json exists under the "
                "audit log. The external audit stays BLOCKED until a human "
                "returns it — never simulated."
            ),
        }
    findings = validate_review(review or {})
    if findings:
        return {
            "schema": "research_v3.external_audit_status/v1",
            "task_id": "V3-G19",
            "request_id": request_id,
            "checked_at_utc": now,
            "status": "INVALID_REVIEW",
            "review_path": str(review_path),
            "findings": findings,
        }
    return {
        "schema": "research_v3.external_audit_status/v1",
        "task_id": "V3-G19",
        "request_id": request_id,
        "checked_at_utc": now,
        "status": "RECEIVED",
        "review_path": str(review_path),
        "reviewer": review.get("reviewer_name"),
        "verdicts": review.get("verdicts"),
        "refuted": sorted(k for k, v in (review.get("verdicts") or {}).items() if v == "REFUTED"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research_v3.scripts.external_audit",
        description=(
            "Double-blind external audit scaffold: writes a rerun request "
            "artifact and stays BLOCKED until a human returns the review "
            "(V3-G19). Never fabricates a review."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    req = sub.add_parser("request", help="Write a new double-blind rerun request")
    req.add_argument("--request-id", required=True, help="Short id, e.g. 2026q1-rerun")
    req.add_argument("--release", type=Path, action="append", default=[], help="Release path to audit (repeatable)")
    req.add_argument("--method", action="append", default=[], help="Method id to rerun (repeatable)")
    req.add_argument("--seed-policy", default="5 independent seeds for stochastic; byte-identical for deterministic")
    req.add_argument("--audit-dir", type=Path, default=None)

    stat = sub.add_parser("status", help="Check whether the human review has arrived")
    stat.add_argument("--request-id", required=True)
    stat.add_argument("--audit-dir", type=Path, default=None)

    args = parser.parse_args(argv)

    if args.command == "request":
        result = write_request(
            request_id=args.request_id,
            release_paths=args.release,
            method_ids=args.method,
            seed_policy=args.seed_policy,
            audit_dir=args.audit_dir,
        )
        print(
            f"OK external_audit: request artifact written -> {result['path']} "
            "(status REQUESTED; BLOCKED until the human review is returned)"
        )
        return EXIT_BLOCKED

    try:
        status = audit_status(args.request_id, args.audit_dir)
    except ExternalAuditError as exc:
        print(f"FAIL external_audit: {exc}", file=sys.stderr)
        return EXIT_INVALID_REVIEW
    print(f"EXTERNAL AUDIT {args.request_id}: status={status['status']}")
    if status.get("reason"):
        print(f"REASON: {status['reason']}")
    for f in status.get("findings", []):
        print(f"FINDING: {f}", file=sys.stderr)
    if status["status"] == "RECEIVED":
        if status.get("refuted"):
            print(f"REFUTED CLAIMS: {status['refuted']}", file=sys.stderr)
            return EXIT_INVALID_REVIEW
        return EXIT_OK
    if status["status"] == "BLOCKED":
        return EXIT_BLOCKED
    return EXIT_INVALID_REVIEW


if __name__ == "__main__":
    sys.exit(main())
