"""P12 tests — determinism, baseline semantics (C0/C1), and the read-only
documented corpus audit (63 real documented claims from data/imperial/)."""
from __future__ import annotations

import json

from research_v3.methods.p12.baselines import baseline_c0, baseline_c1
from research_v3.methods.p12.ledger import audit_corpus
from test_p12_helpers import make_claim, make_registry, make_repo_ingest, ts_provider


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_audit_is_fully_deterministic_given_fixed_timestamps():
    registry = make_registry()
    claims_a = [make_claim(claim_id=f"claim-{i}", claim_text=f"fixture {i}") for i in range(5)]
    claims_b = [make_claim(claim_id=f"claim-{i}", claim_text=f"fixture {i}") for i in range(5)]
    r1 = audit_corpus(claims_a, registry, timestamp_provider=ts_provider)
    r2 = audit_corpus(claims_b, registry, timestamp_provider=ts_provider)
    r1["ledger_events"] = r2["ledger_events"] = None
    assert r1 == r2


def test_chain_digest_stable_across_repeated_runs():
    registry = make_registry()
    claims = [make_claim(claim_id=f"claim-{i}", claim_text=f"fixture {i}") for i in range(5)]
    d1 = audit_corpus(claims, registry, timestamp_provider=ts_provider)["chain_digest"]
    d2 = audit_corpus(claims, registry, timestamp_provider=ts_provider)["chain_digest"]
    assert d1 == d2


# ---------------------------------------------------------------------------
# Baselines
# ---------------------------------------------------------------------------

def test_c0_passes_everything_and_detects_nothing():
    claims = [make_claim(), make_claim(claim_id="c2", source_id=None)]
    c0 = baseline_c0(claims)
    assert c0["accepted"] == 2 and c0["rejected"] == []
    assert c0["unsourced_claim_rate"] == 0.0
    assert c0["contradiction_count"] == 0


def test_c1_accepts_any_citation_string_even_unresolvable():
    registry = make_registry()
    claims = [make_claim(claim_id="ok", source_id="src-fixture-primary"),
              make_claim(claim_id="unknown-but-present", source_id="src-nope")]
    c1 = baseline_c1(claims, registry)
    assert c1["rejected"] == []
    assert c1["accepted"] == 2  # presence-only blindness
    assert c1["contradiction_count"] == 0


def test_c1_rejects_fully_unsourced_claim():
    claims = [make_claim(claim_id="bare", source_id=None, locator=None)]
    c1 = baseline_c1(claims, {})
    assert c1["rejected"] == ["bare"]


def test_proposed_arm_strictly_dominates_c1_detection_power():
    """On the same inputs the proposed arm must reject what C1 wrongly accepts:
    unresolvable source with a locator, and sourced-but-unlocated claims."""
    registry = make_registry()
    claims = [
        make_claim(claim_id="unresolvable", source_id="src-nope"),
        make_claim(claim_id="unlocated", locator=None),
        make_claim(claim_id="good"),
    ]
    c1 = baseline_c1(claims, registry)
    proposed = audit_corpus(claims, registry, timestamp_provider=ts_provider)
    assert c1["rejected"] == []
    assert set(proposed["rejected_claims"]) == {"unresolvable", "unlocated"}


# ---------------------------------------------------------------------------
# Read-only documented corpus (real repo data; no fabrication)
# ---------------------------------------------------------------------------

def test_documented_corpus_ingests_63_claims_read_only():
    ingest = make_repo_ingest()
    assert ingest.provenance["mode"] == "READ_ONLY_DOCUMENTED_CLAIMS"
    assert len(ingest.claims) == 63
    assert len(ingest.sources) == 16
    assert ingest.skipped == []


def test_documented_corpus_hashes_are_recorded():
    ingest = make_repo_ingest()
    for entry in ingest.provenance["inputs"]:
        assert len(entry["sha256"]) == 64 and entry["size_bytes"] > 0


def test_documented_corpus_chain_and_metrics():
    ingest = make_repo_ingest()
    report = audit_corpus(
        ingest.claims, ingest.source_registry, timestamp_provider=ts_provider
    )
    assert report["chain"]["status"] == "PASS"
    assert report["n_claims"] == 63
    # The documented registry is internally consistent: no unsourced rows.
    assert report["unsourced_claim_count"] == 0
    assert report["locator_completeness_rate"] == 1.0
    # Honesty: inherited archival/expert/editor labels route to ABSTAIN.
    assert report["verdict_counts"]["ABSTAIN"] == 62
    assert report["verdict_counts"]["PASS"] == 1  # the one provisional_hypothesis row


def test_validator_does_not_mutate_corpus():
    ingest = make_repo_ingest()
    before = json.dumps([c.to_dict() for c in ingest.claims], ensure_ascii=False)
    audit_corpus(ingest.claims, ingest.source_registry, timestamp_provider=ts_provider)
    after = json.dumps([c.to_dict() for c in ingest.claims], ensure_ascii=False)
    assert before == after


# ---------------------------------------------------------------------------
# CLI end-to-end (writes artifacts; network only if --with-wikidata)
# ---------------------------------------------------------------------------

def test_cli_runs_and_writes_artifacts(tmp_path):
    from research_v3.methods.p12.audit_cli import main

    rc = main(["--out", str(tmp_path)])
    assert rc == 0
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["corpus"]["n_claims"] == 63
    assert summary["metrics"]["C0"]["contradiction_count"] == 0
    assert summary["metrics"]["PROPOSED"]["chain"]["status"] == "PASS"
    for task in ("P12-T19", "P12-T20", "P12-T21"):
        assert task in summary["blocked"]["tasks"]
    ledger_lines = (tmp_path / "run_proposed" / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(ledger_lines) == 63


def test_cli_artifacts_are_deterministic_given_same_timestamp(tmp_path):
    from research_v3.methods.p12.audit_cli import run_audit

    s1 = run_audit(tmp_path, with_wikidata=False, timestamp="2026-11-15T00:00:00Z")
    s2 = run_audit(tmp_path, with_wikidata=False, timestamp="2026-11-15T00:00:00Z")
    assert s1["metrics"] == s2["metrics"]
