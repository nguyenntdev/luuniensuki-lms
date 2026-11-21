"""Gate 1: Test Exit Validator (test_exit.py).

Ensures that any nonzero pytest exit code or hidden test failure behind pipes
strictly blocks merge and release. Detects masked test failures in CI logs.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from typing import List, Optional

from research_v4_2.contracts.types import GateResult


def parse_pytest_log(log_text: str) -> dict:
    """Analyze pytest output text for summary counts and failure banners."""
    failed_matches = re.findall(r"(\d+)\s+failed", log_text, re.IGNORECASE)
    error_matches = re.findall(r"(\d+)\s+error(?:s)?", log_text, re.IGNORECASE)
    passed_matches = re.findall(r"(\d+)\s+passed", log_text, re.IGNORECASE)
    skipped_matches = re.findall(r"(\d+)\s+skipped", log_text, re.IGNORECASE)

    num_failed = sum(int(x) for x in failed_matches) if failed_matches else 0
    num_errors = sum(int(x) for x in error_matches) if error_matches else 0
    num_passed = sum(int(x) for x in passed_matches) if passed_matches else 0
    num_skipped = sum(int(x) for x in skipped_matches) if skipped_matches else 0

    has_failure_banner = bool(re.search(r"=+ (?:FAILURES|ERRORS) =+", log_text))
    has_failed_prefix = bool(re.search(r"^FAILED\s+", log_text, re.MULTILINE))

    return {
        "num_failed": num_failed,
        "num_errors": num_errors,
        "num_passed": num_passed,
        "num_skipped": num_skipped,
        "has_failure_banner": has_failure_banner or has_failed_prefix,
    }


def validate_test_exit(
    exit_code: int = 0,
    log_content: Optional[str] = None,
    log_file: Optional[str] = None,
    pytest_args: Optional[List[str]] = None,
) -> GateResult:
    """Validate that pytest executed with exit code 0 and no unhandled failures exist in logs."""
    messages = []
    details = {"exit_code": exit_code}

    if pytest_args is not None:
        cmd = [sys.executable, "-m", "pytest"] + pytest_args
        proc = subprocess.run(cmd, capture_output=True, text=True)
        exit_code = proc.returncode
        log_content = proc.stdout + "\n" + proc.stderr
        details["command"] = " ".join(cmd)
        details["exit_code"] = exit_code

    if log_file:
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                log_content = f.read()
        except Exception as e:
            return GateResult(
                gate_name="test_exit",
                passed=False,
                messages=[f"Could not read log file {log_file}: {e}"],
                details=details,
            )

    if exit_code != 0:
        messages.append(f"Pytest exited with non-zero exit code: {exit_code}")

    if log_content:
        stats = parse_pytest_log(log_content)
        details.update(stats)
        if stats["num_failed"] > 0 or stats["num_errors"] > 0 or stats["has_failure_banner"]:
            if exit_code == 0:
                messages.append(
                    f"MASKED_TEST_FAILURE: Pytest exit code was 0, but log contains "
                    f"{stats['num_failed']} failures, {stats['num_errors']} errors."
                )
            else:
                messages.append(
                    f"Test log reports {stats['num_failed']} failures and {stats['num_errors']} errors."
                )

    passed = len(messages) == 0
    if passed:
        messages.append("Pytest execution verified clean (exit_code=0, 0 failures, 0 errors).")

    return GateResult(
        gate_name="test_exit",
        passed=passed,
        messages=messages,
        details=details,
    )


def main():
    parser = argparse.ArgumentParser(description="Validate pytest exit status and prevent masked failures.")
    parser.add_argument("--exit-code", type=int, default=0, help="Exit code of the test command.")
    parser.add_argument("--log-file", type=str, default=None, help="Path to pytest log output file.")
    parser.add_argument("--run-pytest", nargs="*", default=None, help="Directly run pytest with provided arguments.")

    args = parser.parse_args()
    result = validate_test_exit(
        exit_code=args.exit_code,
        log_file=args.log_file,
        pytest_args=args.run_pytest,
    )

    print(f"[{result.gate_name.upper()}] Passed: {result.passed}")
    for msg in result.messages:
        print(f"  - {msg}")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
