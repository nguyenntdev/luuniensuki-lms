"""P09 rights/integrity tests: licenses, hashes, blocked datasets, prereg consistency."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = REPO_ROOT / "research_artifacts_v3" / "runs" / "p09"
CORPUS_AVAILABLE = (RUN_DIR / "corpus" / "corpus_manifest.json").exists()

from research_v3.methods.p09.corpus import DISCOVERY_QUERY, sha256_bytes  # noqa: E402


def test_wikidata_is_the_only_used_source_and_is_cc0():
    if not CORPUS_AVAILABLE:
        pytest.skip("real corpus not built yet")
    card = json.loads((RUN_DIR / "corpus" / "corpus_manifest.json").read_text(encoding="utf-8"))
    assert card["dataset_id"] == "wikidata-hue-heritage-mini"
    assert card["license"] == "CC0-1.0"
    assert "not primary" in card["license_note"].lower() or "secondary" in card["license_note"].lower()
    # Blocked alternatives must be recorded honestly, not silently dropped.
    assert card["blocked_alternatives"]["hue-heritage-corpus"].startswith("BLOCKED")
    assert card["blocked_alternatives"]["europeana"].startswith("BLOCKED")


def test_registry_card_for_hue_corpus_remains_blocked_untouched():
    registry = (REPO_ROOT / "research_v3" / "datasets" / "registry.yaml").read_text(encoding="utf-8")
    hue_block = registry.split("- dataset_id: hue-heritage-corpus")[1].split("- dataset_id:")[0]
    assert "status: BLOCKED" in hue_block
    assert "wikidata" not in hue_block.lower()  # we did not sneak approval in


def test_every_entity_snapshot_has_valid_sha_and_entity_file():
    if not CORPUS_AVAILABLE:
        pytest.skip("real corpus not built yet")
    card = json.loads((RUN_DIR / "corpus" / "corpus_manifest.json").read_text(encoding="utf-8"))
    for qid, recorded_sha in card["entity_snapshot_sha256"].items():
        assert re.fullmatch(r"[0-9a-f]{64}", recorded_sha)
        path = RUN_DIR / "corpus" / "entity_json" / f"{qid}.json"
        assert path.exists(), qid
        assert sha256_bytes(path.read_bytes()) == recorded_sha, qid


def test_discovery_response_hash_matches_recorded():
    if not CORPUS_AVAILABLE:
        pytest.skip("real corpus not built yet")
    card = json.loads((RUN_DIR / "corpus" / "corpus_manifest.json").read_text(encoding="utf-8"))
    raw = (RUN_DIR / "corpus" / "discovery_response.json").read_bytes()
    assert sha256_bytes(raw) == card["discovery_response_sha256"]
    query_on_disk = (RUN_DIR / "corpus" / "query.sparql").read_text(encoding="utf-8")
    assert query_on_disk == DISCOVERY_QUERY


def test_prereg_declares_primary_endpoint_and_blocked_tasks():
    prereg = (REPO_ROOT / "research_v3" / "experiments" / "p09" / "pre_registration.yaml").read_text(encoding="utf-8")
    assert "unsupported_claim_surfacing_rate" in prereg
    assert "P09-T19" in prereg and "BLOCKED" in prereg
    assert "P09-T20" in prereg and "P09-T21" in prereg
    assert "INDEPENDENT_HUMAN_AUDITOR" in prereg
    # no fabricated human approvals anywhere
    assert "expert consensus" not in prereg.lower()
    assert "ethics approval obtained" not in prereg.lower()


def test_manifest_hashes_round_trip():
    if not CORPUS_AVAILABLE:
        pytest.skip("real corpus not built yet")
    manifest = json.loads((RUN_DIR / "manifest.json").read_text(encoding="utf-8"))
    for key, rel in [
        ("claims_sha256", RUN_DIR / "corpus" / "claims.jsonl"),
        ("verification_outcomes_sha256", RUN_DIR / "eval" / "verification_outcomes.json"),
        ("metrics_sha256", RUN_DIR / "eval" / "metrics.json"),
        ("audit_sample_sha256", RUN_DIR / "audit" / "audit_sample.json"),
    ]:
        assert re.fullmatch(r"[0-9a-f]{64}", manifest[key]), key
        assert sha256_bytes(rel.read_bytes()) == manifest[key], key


def test_no_expert_label_or_consent_claims_in_artifacts():
    if not CORPUS_AVAILABLE:
        pytest.skip("real corpus not built yet")
    audit = (RUN_DIR / "audit" / "audit_sample.json").read_text(encoding="utf-8")
    assert "expert_verified" not in audit.lower()
    assert "auditor_fields" in audit  # left null for the human auditor
    sample = json.loads(audit)
    for row in sample["sample"]:
        assert all(v is None for v in row["auditor_fields"].values())
