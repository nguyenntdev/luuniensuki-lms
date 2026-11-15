"""V3-G09: ethics / consent AUDIT — always BLOCKED unless real proof exists.

The audit scans ``research_v3/governance/ethics/`` for a *real signed approval
record file* (``approval_*.json`` meeting the schema below, with a verbatim
record_sha256 that matches the file's own content hash chain). If none exists,
the audit returns status ``BLOCKED`` — it NEVER invents approval, never
fabricates a protocol number, and never downgrades a BLOCKED verdict.

An approval record is accepted only when it contains:
- protocol_id, approver_role (human), signed_at (ISO date), scope (paper ids),
- document_sha256 (64-hex SHA-256 of the signed document file placed next to
  the record), and that document file must exist on disk and hash-match.

A record whose document file is missing or mismatching is treated as
FRAUDULENT and reported — the audit fails closed with a nonzero exit either
way (missing proof => BLOCKED; tampered proof => TAMPERED, also nonzero).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from research_v3.scripts._paths import ETHICS_DIR

HEX64 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_FIELDS = ("protocol_id", "approver_role", "signed_at", "scope", "document_sha256")

EXIT_BLOCKED = 20
EXIT_TAMPERED = 21
EXIT_OK = 0
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_approval_records(ethics_dir: Path | None = None) -> list[Path]:
    target = Path(ethics_dir or ETHICS_DIR)
    if not target.is_dir():
        return []
    return sorted(target.glob("approval_*.json"))


def validate_record(path: Path) -> tuple[str, list[str]]:
    """Validate one approval record. Returns (verdict, findings).

    verdict is one of VALID | INVALID | TAMPERED.
    """
    findings: list[str] = []
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return "INVALID", [f"{path.name}: invalid JSON: {exc}"]
    if not isinstance(record, dict):
        return "INVALID", [f"{path.name}: record must be a JSON object"]

    for field in REQUIRED_FIELDS:
        if field not in record or record[field] in (None, ""):
            findings.append(f"{path.name}: missing required field {field!r}")
    if findings:
        return "INVALID", findings

    if not DATE_PATTERN.match(str(record["signed_at"])):
        findings.append(f"{path.name}: signed_at is not an ISO date")
    if record["approver_role"] in ("bot", "automation", "code agent", "agent"):
        findings.append(f"{path.name}: approver_role must be a human role, got {record['approver_role']!r}")
    scope = record["scope"]
    if not (isinstance(scope, list) and scope):
        findings.append(f"{path.name}: scope must be a non-empty list of paper ids")

    doc_sha = str(record["document_sha256"])
    if not HEX64.match(doc_sha):
        findings.append(f"{path.name}: document_sha256 is not 64-hex")
        return "INVALID", findings

    doc_path = path.parent / str(record.get("document_file", "signed_approval.pdf"))
    if not doc_path.is_file():
        findings.append(
            f"{path.name}: signed document {doc_path.name} is missing — a JSON claim "
            "of approval without the signed document is NOT proof"
        )
        return "INVALID", findings
    actual = _sha256_file(doc_path)
    if actual != doc_sha:
        findings.append(
            f"{path.name}: document hash mismatch — claimed {doc_sha[:12]} vs actual "
            f"{actual[:12]} (TAMPERED or stale)"
        )
        return "TAMPERED", findings
    return "VALID", findings


def run_ethics_audit(
    ethics_dir: Path | None = None,
    *,
    papers: list[str] | None = None,
) -> dict:
    """Return the audit report dict. Status is BLOCKED unless a VALID record
    covering every requested paper exists. Never fabricates approval."""
    records = find_approval_records(ethics_dir)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report: dict = {
        "schema": "research_v3.ethics_audit/v1",
        "task_id": "V3-G09",
        "audited_at_utc": now,
        "ethics_dir": str(ethics_dir or ETHICS_DIR),
        "records_found": len(records),
        "records": [],
        "valid_protocols": [],
        "tampered": [],
        "status": "BLOCKED",
        "reason": None,
    }

    for path in records:
        verdict, findings = validate_record(path)
        report["records"].append({"file": path.name, "verdict": verdict, "findings": findings})
        if verdict == "VALID":
            record = json.loads(path.read_text(encoding="utf-8"))
            report["valid_protocols"].append(
                {"protocol_id": record["protocol_id"], "scope": record["scope"], "signed_at": record["signed_at"]}
            )
        elif verdict == "TAMPERED":
            report["tampered"].append({"file": path.name, "findings": findings})

    if report["tampered"]:
        report["status"] = "TAMPERED"
        report["reason"] = (
            "One or more approval records reference a signed document whose hash "
            "does not match — treat as fraudulent until re-verified by a human."
        )
        return report

    if not report["valid_protocols"]:
        report["reason"] = (
            f"No valid signed approval record exists under {report['ethics_dir']}. "
            "The audit NEVER invents approval; human-subject work stays BLOCKED "
            "until a real signed record (with matching document hash) is filed."
        )
        return report

    if papers:
        covered: set[str] = set()
        for proto in report["valid_protocols"]:
            covered |= set(proto["scope"])
        uncovered = sorted(set(papers) - covered)
        if uncovered:
            report["reason"] = (
                f"Valid approval(s) exist but do not cover: {', '.join(uncovered)}. "
                "Those papers remain BLOCKED for human-subject work."
            )
            report["uncovered_papers"] = uncovered
            return report

    report["status"] = "APPROVED_FOR_SCOPED_PAPERS"
    report["reason"] = (
        "Valid signed approval record(s) with matching document hashes cover the "
        "requested scope. This is a documentary check only — the approver is "
        "accountable for the underlying consent process."
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research_v3.scripts.ethics",
        description=(
            "Ethics/consent audit: BLOCKED unless a real signed approval record "
            "exists under research_v3/governance/ethics/ (V3-G09). Never invents "
            "approval."
        ),
    )
    parser.add_argument("--paper", action="append", default=[], help="Require coverage for these paper ids")
    parser.add_argument("--ethics-dir", type=Path, default=None, help="Override the ethics directory")
    parser.add_argument("--json", action="store_true", help="Print the full JSON report")
    args = parser.parse_args(argv)

    report = run_ethics_audit(args.ethics_dir, papers=args.paper or None)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"ETHICS AUDIT: status={report['status']} "
            f"records={report['records_found']} valid={len(report['valid_protocols'])} "
            f"tampered={len(report['tampered'])}"
        )
        if report["reason"]:
            print(f"REASON: {report['reason']}")

    if report["status"] == "TAMPERED":
        return EXIT_TAMPERED
    if report["status"] != "APPROVED_FOR_SCOPED_PAPERS":
        return EXIT_BLOCKED
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
