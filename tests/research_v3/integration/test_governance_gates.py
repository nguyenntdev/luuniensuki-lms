"""V3-G01/G02/G03: claims ledger, license gate, contract round-trip tests."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from research_v2.contracts.canonical_hash import sha256_input
from research_v3.contracts.cards import ContractError, DatasetCard
from research_v3.scripts.claims import build_ledger, extract_claims
from research_v3.scripts.verify_licenses import load_paper_requirements, verify

REPO_ROOT = Path(__file__).resolve().parents[3]

H64 = "a" * 64


# ---------------------------------------------------------------- G01


def test_claims_ledger_built_from_manuscripts():
    rows = build_ledger(REPO_ROOT / "manuscripts_v5")
    papers = {r["paper_id"] for r in rows}
    assert {"LN-01", "LN-06", "LN-09"} <= papers
    for row in rows:
        assert row["claim_id"]
        assert row["source_file"].startswith("manuscripts_v5/")
        assert row["overlap_paper_ids"] != "" or "no overlap" in row["overlap_note"]
        # read-only: no row claims evidence it does not have
        assert row["evidence_status"] == "UNVERIFIED"


def test_claims_cli_writes_csv_and_missing_root_fails(tmp_path):
    out = tmp_path / "ledger.csv"
    ok = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.claims", "--output", str(out)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert ok.returncode == 0, ok.stderr
    with out.open() as fh:
        rows = list(csv.DictReader(fh))
    assert rows

    bad = subprocess.run(
        [
            sys.executable, "-m", "research_v3.scripts.claims",
            "--manuscripts-root", str(tmp_path / "nope"), "--output", str(tmp_path / "x.csv"),
        ],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert bad.returncode == 4
    assert not (tmp_path / "x.csv").exists()


# ---------------------------------------------------------------- G02


def test_license_gate_blocks_unapproved_papers():
    requirements = load_paper_requirements()
    ok, report = verify({"P06": ["oulad-2013-2014"]})
    assert ok is True and report["papers"]["P06"]["ok"] is True

    ok, report = verify({"P01": ["assistments"]})
    assert ok is False
    assert report["violations"][0]["paper_id"] == "P01"
    assert report["registry_summary"]["by_status"].get("BLOCKED", 0) >= 1

    # unknown dataset id is a violation, not a silent pass
    ok, report = verify({"P99": ["definitely-not-registered"]})
    assert ok is False
    assert report["unknown_dataset_ids"] == ["definitely-not-registered"]


def test_license_cli_exit_codes():
    ok = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.verify_licenses", "--paper", "P06"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert ok.returncode == 0
    blocked = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.verify_licenses", "--all"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert blocked.returncode == 6
    unknown = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.verify_licenses", "--paper", "PZZ"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert unknown.returncode == 7


# ---------------------------------------------------------------- G03


def _approved_card(**over):
    base = dict(
        dataset_id="d", provider="p", source_url="https://example.org", doi=None,
        version="1", retrieved_at="t", license_text_sha256=H64,
        allowed_uses=("academic_analysis",), redistribution_policy="CC BY 4.0",
        original_sha256=H64, transformed_sha256=None, sample_count=3,
        schema_version="1", consent_basis="public", units="u", group_keys=("g",),
        time_key=None, leakage_audit="done", source_attribution="cite",
        status="APPROVED",
    )
    base.update(over)
    return base


def test_card_roundtrip_is_stable_and_mutation_detectable():
    card = DatasetCard(**_approved_card())
    h1 = card.sha256()
    h2 = sha256_input(json.loads(json.dumps(card.to_dict())))
    assert h1 == h2  # append-only: round-trip preserves the hash
    mutated = dict(card.to_dict())
    mutated["sample_count"] = 99
    assert sha256_input(mutated) != h1


def test_validate_contracts_cli_positive_and_negative(tmp_path):
    ok = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.validate_contracts"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert ok.returncode == 0, ok.stderr

    bad_card = _approved_card()
    bad_card["status"] = "MAYBE"
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad_card))
    bad = subprocess.run(
        [sys.executable, "-m", "research_v3.scripts.validate_contracts", "--no-registry", "--cards", str(p)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert bad.returncode == 8


def test_invalid_status_raises_typed_error():
    with pytest.raises(ContractError):
        DatasetCard(**_approved_card(status="NOPE"))
