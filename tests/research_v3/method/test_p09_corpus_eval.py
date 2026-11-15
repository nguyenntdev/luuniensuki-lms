"""P09 corpus + evaluation tests: real corpus (when built), baselines, metrics, audit sample."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from p09_helpers import RUN_DIR, load_frozen_claims, make_claim, make_corpus
from research_v3.methods.p09 import (
    C0_METHOD_ID,
    C1_METHOD_ID,
    METHOD_ID,
    audit_sample,
    c0_surface_everything,
    c1_keyword_match,
    evaluate_method,
    propose_surface,
    verify_claim,
    write_audit_sample,
)
from research_v3.methods.p09.corpus import (
    CLAIM_PROPERTIES,
    DISCOVERY_QUERY,
    GUID_RE,
    apply_verification_rule,
    discover_entities,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

CORPUS_AVAILABLE = (RUN_DIR / "corpus" / "claims.jsonl").exists() and (
    RUN_DIR / "corpus" / "corpus_manifest.json"
).exists()


def test_discovery_query_is_frozen_and_meaningful():
    assert "Q10810560" in DISCOVERY_QUERY          # Complex of Huế Monuments anchor
    assert "P361+" in DISCOVERY_QUERY              # transitive part-of
    assert DISCOVERY_QUERY.strip().startswith("#")  # provenance comment header


def test_guid_regex_shape():
    assert GUID_RE.fullmatch("Q975568$11111111-2222-4333-8444-555555555555")
    assert not GUID_RE.fullmatch("Q975568$not-a-guid")
    assert not GUID_RE.fullmatch("P31$11111111-2222-4333-8444-555555555555")


def test_discover_entities_dedupes_and_sorts():
    bindings = [
        {"item": {"value": "http://www.wikidata.org/entity/Q2"}, "itemLabel": {"value": "B"}},
        {"item": {"value": "http://www.wikidata.org/entity/Q1"}, "itemLabel": {"value": "A"}},
        {"item": {"value": "http://www.wikidata.org/entity/Q1"}, "itemLabel": {"value": "A"}},
    ]
    entities = discover_entities(bindings)
    assert entities == [{"qid": "Q1", "label": "A"}, {"qid": "Q2", "label": "B"}]


def test_verification_rule_is_conservative_default():
    """Default epistemic for every ingested claim is 'unverified' (unverified-until-linked)."""
    claim = make_claim(epistemic="unverified")
    rule_result = apply_verification_rule([claim], {})
    # Without snapshots the rule cannot verify anything; claim stays unverified.
    assert rule_result[0].epistemic == "unverified"


def test_c0_surfaces_everything_including_unsupported():
    corpus = make_corpus()
    unverified = make_claim("U1", epistemic="unverified")
    decision = c0_surface_everything(unverified, corpus)
    assert decision.decision == "surface"
    assert decision.method_id == C0_METHOD_ID


def test_c1_keyword_gate_is_text_only_and_leaky():
    corpus = make_corpus()
    hit = make_claim("K1", epistemic="unverified", text="The tomb was built in 1843")
    miss = make_claim("K2", epistemic="verified", text="Zenith angle 16.45 degrees, azimuth 107.54")
    assert c1_keyword_match(hit, corpus).decision == "surface"       # keyword hit, no source check
    assert c1_keyword_match(miss, corpus).decision == "abstain_unverified"  # verified but no keyword


def test_metrics_zero_unsupported_for_proposed_and_nonzero_for_baselines():
    corpus = make_corpus()
    claims = [
        make_claim("M1", epistemic="verified"),
        make_claim("M2", epistemic="unverified"),
        make_claim("M3", epistemic="unverified", text="no keywords here at all"),
    ]
    outcomes = {c.claim_id: verify_claim(c, corpus).outcome for c in claims}
    proposed = [propose_surface(c, corpus).to_dict() for c in claims]
    c0 = [c0_surface_everything(c, corpus).to_dict() for c in claims]
    c1 = [c1_keyword_match(c, corpus).to_dict() for c in claims]
    rep_p = evaluate_method(METHOD_ID, proposed, outcomes)
    rep_0 = evaluate_method(C0_METHOD_ID, c0, outcomes)
    rep_1 = evaluate_method(C1_METHOD_ID, c1, outcomes)
    assert rep_p["unsupported_claim_surfacing_rate"] == 0.0
    assert rep_0["unsupported_claim_surfacing_rate"] == pytest.approx(2 / 3)
    assert rep_1["unsupported_claim_surfacing_rate"] > 0.0
    # Zero-unsupported cells get a proper upper-bounded CI, never [0, 0].
    ci = rep_p["unsupported_ci95"]["clopper_pearson_ci_95"]
    assert ci[0] == 0.0 and ci[1] > 0.0


def test_audit_sample_is_deterministic_unlabeled_and_covered_by_both_methods():
    corpus = make_corpus()
    claims = [make_claim(f"A{i}", epistemic="verified" if i % 2 else "unverified") for i in range(10)]
    decisions = {
        METHOD_ID: [propose_surface(c, corpus).to_dict() for c in claims],
        C0_METHOD_ID: [c0_surface_everything(c, corpus).to_dict() for c in claims],
    }
    rows_a = audit_sample([c.to_dict() for c in claims], decisions, seed=42)
    rows_b = audit_sample([c.to_dict() for c in claims], decisions, seed=42)
    assert rows_a == rows_b                       # deterministic
    assert len(rows_a) >= 8                       # min_n floor
    for row in rows_a:
        assert set(row["auditor_fields"].values()) == {None}  # UNLABELED
        assert "expert" not in json.dumps(row["audit_task"]).lower()
        assert set(row["decisions"]) == {METHOD_ID, C0_METHOD_ID}


def test_audit_sample_writer_round_trips_with_sha(tmp_path: Path):
    corpus = make_corpus()
    claims = [make_claim(f"W{i}") for i in range(8)]
    decisions = {METHOD_ID: [propose_surface(c, corpus).to_dict() for c in claims]}
    rows = audit_sample([c.to_dict() for c in claims], decisions, seed=42)
    sha = write_audit_sample(rows, tmp_path / "audit_sample.json")
    import hashlib

    data = (tmp_path / "audit_sample.json").read_bytes()
    assert hashlib.sha256(data).hexdigest() == sha
    loaded = json.loads(data.decode("utf-8"))
    assert len(loaded["sample"]) == len(rows)


def test_all_claim_properties_have_locators_in_real_corpus():
    if not CORPUS_AVAILABLE:
        pytest.skip("real corpus not built yet (run research_v3/experiments/p09/run_p09.py build)")
    claims = load_frozen_claims()
    assert claims, "corpus file exists but empty"
    for claim in claims:
        assert claim.locator.kind == "statement_guid"
        assert GUID_RE.fullmatch(claim.locator.value)
        assert claim.locator.value.startswith(claim.entity_qid + "$")
        assert claim.property_id in CLAIM_PROPERTIES


@pytest.mark.skipif(not CORPUS_AVAILABLE, reason="real corpus not built yet")
def test_real_corpus_end_to_end_hypotheses():
    """H1-H4 against the REAL built Wikidata corpus (51 claims from 23 entities)."""
    claims = load_frozen_claims()
    corpus = __import__("research_v3.methods.p09.corpus", fromlist=["ProvenanceCorpus"]).ProvenanceCorpus()
    from research_v3.methods.p09.corpus import ProvenanceCorpus as _PC  # noqa: F401

    corpus = _PC()
    for claim in claims:
        if not corpus.has_source(claim.source.source_id):
            guids = frozenset(c.locator.value for c in claims if c.entity_qid == claim.entity_qid)
            corpus.add_source(claim.source, guids)
    outcomes = {c.claim_id: verify_claim(c, corpus).outcome for c in claims}
    proposed = [propose_surface(c, corpus).to_dict() for c in claims]
    c0 = [c0_surface_everything(c, corpus).to_dict() for c in claims]
    c1 = [c1_keyword_match(c, corpus).to_dict() for c in claims]
    rep_p = evaluate_method(METHOD_ID, proposed, outcomes)
    rep_0 = evaluate_method(C0_METHOD_ID, c0, outcomes)
    rep_1 = evaluate_method(C1_METHOD_ID, c1, outcomes)
    # H1: zero unsupported surfacing for proposed.
    assert rep_p["unsupported_claim_surfacing_rate"] == 0.0
    # H3: baselines leak on the same corpus.
    assert rep_0["n_unsupported_surfaced"] == sum(1 for o in outcomes.values() if o != "verified")
    assert rep_1["n_unsupported_surfaced"] > 0
    # H2: proposed surfaces exactly the gate-verified claims.
    n_verified = sum(1 for o in outcomes.values() if o == "verified")
    assert rep_p["n_surfaced"] == n_verified
    assert rep_p["citation_grounding_rate"] == pytest.approx(n_verified / len(claims))
