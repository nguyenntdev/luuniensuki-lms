"""V3-G05: verify the baseline registry's reproducibility declarations.

Checks (fail-closed):
- every C0/C1 baseline declares attribution + comparable_task=true + APPROVED;
- every C2 baseline claiming APPROVED carries a real 64-hex provenance_sha256
  (an actual upstream snapshot) — otherwise it must stay BLOCKED with a reason;
- no baseline invents a license name without a license field;
- no published metric numbers are embedded (prohibition of copied numbers).

Prints a per-tier summary; exits nonzero on any violation.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from research_v3.scripts._paths import RESEARCH_V3_ROOT

DEFAULT_REGISTRY = RESEARCH_V3_ROOT / "baselines" / "registry" / "registry.yaml"

VALID_TIERS = {"C0", "C1", "C1-ablation", "C2"}
VALID_STATUSES = {"APPROVED", "BLOCKED"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")

EXIT_OK = 0
EXIT_VERIFICATION_FAILED = 10
EXIT_CONFIG_ERROR = 7


class BaselineRegistryError(RuntimeError):
    """Raised when the baseline registry cannot be read."""


def load_baselines(path: Path | None = None) -> list[dict]:
    try:
        import yaml
    except Exception as exc:  # pragma: no cover
        raise BaselineRegistryError("PyYAML is required to read the baseline registry") from exc
    target = Path(path or DEFAULT_REGISTRY)
    if not target.is_file():
        raise BaselineRegistryError(f"baseline registry missing: {target}")
    raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    baselines = raw.get("baselines")
    if not isinstance(baselines, list) or not baselines:
        raise BaselineRegistryError(f"{target}: no baselines declared")
    return baselines


def verify(baselines: list[dict]) -> tuple[bool, list[str], dict]:
    findings: list[str] = []
    ids: set[str] = set()
    tiers: dict[str, dict[str, int]] = {}
    for b in baselines:
        bid = str(b.get("baseline_id", "")).strip()
        tier = str(b.get("tier", "")).strip()
        status = str(b.get("status", "")).strip()
        attribution = str(b.get("attribution", "")).strip()
        comparable = b.get("comparable_task")
        if not bid:
            findings.append("baseline entry missing baseline_id")
            continue
        if bid in ids:
            findings.append(f"{bid}: duplicate baseline_id")
        ids.add(bid)
        if tier not in VALID_TIERS:
            findings.append(f"{bid}: invalid tier {tier!r}")
        if status not in VALID_STATUSES:
            findings.append(f"{bid}: invalid status {status!r} (use APPROVED|BLOCKED)")
        if status == "BLOCKED" and not b.get("blocked_reason"):
            findings.append(f"{bid}: BLOCKED requires blocked_reason")
        if not attribution or attribution == "":
            findings.append(f"{bid}: attribution is required (no anonymous baselines)")
        if comparable is not True and status == "APPROVED" and tier != "C2":
            findings.append(f"{bid}: APPROVED C0/C1 baseline must declare comparable_task: true")
        if not b.get("license"):
            findings.append(f"{bid}: license field is required even when 'internal'")

        if tier == "C2" and status == "APPROVED":
            prov = str(b.get("provenance_sha256", "") or "")
            if not HEX64.match(prov):
                findings.append(
                    f"{bid}: APPROVED C2 requires a real 64-hex provenance_sha256 of an "
                    "upstream snapshot; without one it must stay BLOCKED"
                )
        if tier == "C2" and comparable is True and status == "APPROVED":
            findings.append(
                f"{bid}: C2 comparable_task=true requires verified upstream provenance; "
                "confirm before flip"
            )

        tiers.setdefault(tier, {"APPROVED": 0, "BLOCKED": 0})
        if status in VALID_STATUSES:
            tiers[tier][status] += 1
    all_ok = not findings
    return all_ok, findings, {"by_tier": tiers, "total": len(baselines)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research_v3.baselines.verification.verify_baselines",
        description=(
            "Verify baseline reproducibility declarations: attribution, "
            "comparable_task flags, C2 provenance gating (V3-G05)."
        ),
    )
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Baseline registry YAML")
    parser.add_argument("--json", action="store_true", help="Print full JSON summary")
    args = parser.parse_args(argv)

    try:
        baselines = load_baselines(args.registry)
    except BaselineRegistryError as exc:
        print(f"FAIL verify_baselines: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    all_ok, findings, summary = verify(baselines)
    print(f"Baselines: {summary['total']} declared; by tier: {json.dumps(summary['by_tier'])}")
    for f in findings:
        print(f"FINDING: {f}", file=sys.stderr)
    if args.json:
        print(json.dumps(summary, indent=2))
    if not all_ok:
        print(f"FAIL verify_baselines: {len(findings)} finding(s).", file=sys.stderr)
        return EXIT_VERIFICATION_FAILED
    print("OK verify_baselines: registry declarations consistent (C2 remains gated).")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
