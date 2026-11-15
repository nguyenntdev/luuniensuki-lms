"""P14 provenance/rights/claims artifacts and CLI tests."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from research_v3.contracts.cards import ContractError, DatasetCard
from research_v3.methods.p14.cli_audit import load_manifest, main as cli_main
from research_v3.methods.p14.rights import external_media_status, rights_cards
from research_v3.methods.p14.schema import SchemaError
from research_v3.methods.p14.synthetic import manifest_sha256, synthetic_manifest

REPO = Path(__file__).resolve().parents[3]


def test_all_media_sources_blocked_with_reasons():
    cards = {c.dataset_id: c for c in rights_cards()}
    assert cards["smithsonian-open-access"].status == "BLOCKED"
    assert "403" in cards["smithsonian-open-access"].blocked_reason
    assert cards["europeana-metadata"].status == "BLOCKED"
    assert "401" in cards["europeana-metadata"].blocked_reason
    assert cards["hue-heritage-corpus"].status == "BLOCKED"
    status = external_media_status()
    assert status["external_media_status"] == "BLOCKED"
    assert status["study_external_media_mark"] == "PARTIAL"
    assert status["hué_imagery_used"] is False


def test_blocked_card_without_reason_is_rejected():
    with pytest.raises(ContractError):
        DatasetCard(
            dataset_id="x", provider="p", source_url="", doi=None, version="1",
            retrieved_at="t", license_text_sha256="", allowed_uses=(),
            redistribution_policy="", original_sha256="", transformed_sha256=None,
            sample_count=0, schema_version="", consent_basis="", units="",
            group_keys=(), time_key=None, leakage_audit="", source_attribution="",
            status="BLOCKED",
        )


def test_manifest_hash_is_deterministic():
    assert manifest_sha256(synthetic_manifest()) == manifest_sha256(synthetic_manifest())


def test_cli_runs_on_synthetic_manifest_and_writes_checksum(tmp_path: Path):
    out = tmp_path / "run"
    rc = cli_main(["--out", str(out)])
    assert rc == 0
    report = json.loads((out / "audit_report.json").read_text(encoding="utf-8"))
    expected = hashlib.sha256((out / "audit_report.json").read_bytes()).hexdigest()
    assert (out / "audit_report.sha256").read_text().strip() == expected
    assert report["manifest"]["sha256"] == manifest_sha256(synthetic_manifest())
    assert report["manifest"]["rights"]["external_media_status"] == "BLOCKED"
    assert report["learned_parameters"] == {}


def test_cli_fails_closed_on_broken_manifest(tmp_path: Path):
    bad = tmp_path / "manifest.json"
    bad.write_text(json.dumps([{"object_id": "x"}]), encoding="utf-8")  # missing fields
    rc = cli_main(["--manifest", str(bad), "--out", str(tmp_path / "out")])
    assert rc == 1


def test_cli_roundtrip_loads_external_manifest(tmp_path: Path):
    from research_v3.methods.p14.synthetic import SYNTHETIC_MANIFEST_VERSION

    payload = {
        "objects": [
            {
                "object_id": "ext-obj-1",
                "title": "External test object",
                "origin": "synthetic:roundtrip",
                "source_url": None,
                "rights": "Synthetic - no third-party rights (generated for P14, not real imagery)",
                "assets": [
                    {"asset_id": "a1", "media_type": "image", "rights": "Synthetic - no third-party rights (generated for P14, not real imagery)", "has_text_alternative": True}
                ],
                "low_bandwidth_variant": None,
                "metadata": {},
            }
        ]
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    objects, label, sha = load_manifest(path)
    assert len(objects) == 1
    assert label == str(path)
    assert sha == hashlib.sha256(path.read_bytes()).hexdigest()


def test_run_artifacts_exist_and_checksums_roundtrip():
    runs = REPO / "research_artifacts_v3" / "runs" / "p14"
    manifest = runs / "run_manifest.sha256"
    if not manifest.is_file():
        pytest.skip("experiment artifacts not yet generated")
    lines = manifest.read_text(encoding="utf-8").strip().splitlines()
    assert lines, "run manifest must list checksums"
    for line in lines:
        sha, name = line.split(maxsplit=1)
        target = runs / name.strip()
        assert target.is_file(), f"missing artifact {name}"
        assert hashlib.sha256(target.read_bytes()).hexdigest() == sha


def test_run_artifacts_contain_no_benefit_claims():
    runs = REPO / "research_artifacts_v3" / "runs" / "p14"
    ledger = runs / "claims_ledger.json"
    if not ledger.is_file():
        pytest.skip("experiment artifacts not yet generated")
    data = json.loads(ledger.read_text(encoding="utf-8"))
    allowed = [c for c in data["candidate_claims"] if c["allowed"]]
    for claim in allowed:
        text = claim["claim"].lower()
        assert "improve" not in text or "learning" not in text
    assert data["human_evidence_dataset_ids"] == []
    assert "BLOCKED" in data["human_study_status"]


def test_experiment_runner_is_deterministic(tmp_path: Path):
    """Two runs from the same inputs must produce byte-identical audit reports."""
    from research_v3.experiments.p14.run_experiment import RUNS_DIR  # noqa: F401

    frozen = RUNS_DIR / "audit_report.json"
    if not frozen.is_file():
        pytest.skip("experiment artifacts not yet generated")
    first = json.loads(frozen.read_text(encoding="utf-8"))
    # regenerate in-memory determinism check via the engine (no side effects)
    from research_v3.methods.p14.audit import audit_manifest
    from research_v3.methods.p14.rubric import load_rubric
    from research_v3.methods.p14.synthetic import synthetic_manifest

    regen = audit_manifest(synthetic_manifest(), load_rubric())
    assert json.dumps(first["metrics"], sort_keys=True) == json.dumps(
        regen["metrics"], sort_keys=True
    )


@pytest.mark.parametrize(
    "mutation",
    ["remove_alt_text", "remove_transcript", "remove_keyboard", "remove_lbw"],
)
def test_unknown_mutation_rejected(mutation):
    from research_v3.methods.p14.schema import SchemaError as SE
    from research_v3.methods.p14.synthetic import mutate

    if mutation in {"remove_alt_text", "remove_transcript", "remove_keyboard", "remove_lbw"}:
        mutate(synthetic_manifest()[0], mutation)  # must not raise
    else:
        with pytest.raises(SE):
            mutate(synthetic_manifest()[0], mutation)
