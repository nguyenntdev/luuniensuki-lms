"""P09 experiment runner CLI.

Two stages, independently runnable and deterministic:

  build   — live build of the licensed Wikidata Huế mini-corpus:
            frozen SPARQL discovery query + per-entity EntityData snapshots,
            all raw bytes and SHA-256 hashes written to the run directory.
  evaluate — offline matrix over the frozen corpus: verification sidecar from
            the frozen gate, C0/C1/proposed decisions, metrics with zero-error
            CIs, deterministic human-audit sample (unlabeled), adversarial
            counterexamples, and the full manifest with hashes.

Scientific labeling: deterministic rules only; produces an UNLABELED audit
sample for an independent human auditor; no expert labels are generated here.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research_v3.methods.p09 import (
    C0_METHOD_ID,
    C1_METHOD_ID,
    METHOD_ID,
    METHOD_VERSION,
    Claim,
    Locator,
    ProvenanceCorpus,
    SourceRef,
    audit_sample,
    c0_surface_everything,
    c1_keyword_match,
    evaluate_method,
    propose_surface,
    verify_claim,
    write_audit_sample,
)
from research_v3.methods.p09.baselines import C0_METHOD_VERSION, C1_METHOD_VERSION
from research_v3.methods.p09.corpus import (
    CLAIM_PROPERTIES,
    DISCOVERY_QUERY,
    VERIFICATION_RULE_DOC,
    VERIFICATION_RULE_VERSION,
    build_corpus,
    sha256_bytes,
)
from research_v3.methods.p09.provenance import ProvenanceError

RUN_DIR = Path("research_artifacts_v3/runs/p09")


# ---------------------------------------------------------------- stage: build


def stage_build(run_dir: Path) -> dict:
    built = build_corpus(run_dir / "corpus")
    claims_path = run_dir / "corpus" / "claims.jsonl"
    claims_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for claim in built.claims:
        lines.append(json.dumps(claim.to_dict(), ensure_ascii=False, sort_keys=True))
    claims_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (run_dir / "corpus" / "query.sparql").write_text(DISCOVERY_QUERY, encoding="utf-8")
    corpus_card = {
        "dataset_id": "wikidata-hue-heritage-mini",
        "provider": "Wikidata (Wikimedia Foundation)",
        "source_url": "https://query.wikidata.org/sparql + https://www.wikidata.org/wiki/Special:EntityData/",
        "license": "CC0-1.0",
        "license_note": (
            "Wikidata declares CC0 for structured data; snapshots stored verbatim "
            "with per-byte SHA-256. Source statements are secondary evidence, NOT "
            "primary archival sources; no historical truth inferred from Wikidata alone."
        ),
        "discovery_query_sha256": sha256_bytes(DISCOVERY_QUERY.encode("utf-8")),
        "discovery_response_sha256": built.discovery_sha256,
        "discovery_bindings": built.discovery_bindings_count,
        "entities": built.entities,
        "entity_snapshot_sha256": built.entity_hashes,
        "n_claims": len(built.claims),
        "claim_properties": sorted(CLAIM_PROPERTIES),
        "verification_rule_version": VERIFICATION_RULE_VERSION,
        "verification_rule": VERIFICATION_RULE_DOC,
        "blocked_alternatives": {
            "hue-heritage-corpus": "BLOCKED: no written archival permission (registry card unchanged).",
            "europeana": "BLOCKED: no API key; item-level media rights unresolved (registry card unchanged).",
        },
    }
    (run_dir / "corpus" / "corpus_manifest.json").write_text(
        json.dumps(corpus_card, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return corpus_card


# ------------------------------------------------------------- stage: evaluate


def _load_claims(run_dir: Path) -> tuple[list[Claim], ProvenanceCorpus]:
    claims: list[Claim] = []
    corpus = ProvenanceCorpus()
    claims_path = run_dir / "corpus" / "claims.jsonl"
    for line in claims_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        source = record["source"]
        locator = record["locator"]
        claims.append(
            Claim(
                claim_id=record["claim_id"],
                entity_qid=record["entity_qid"],
                text=record["text"],
                source=SourceRef(
                    source_id=source["source_id"],
                    kind=source["kind"],
                    title=source["title"],
                    url=source["url"],
                    license=source["license"],
                    retrieved_at=source["retrieved_at"],
                    sha256=source["sha256"],
                ),
                locator=Locator(
                    source_id=locator["source_id"], kind=locator["kind"], value=locator["value"]
                ),
                epistemic=record["epistemic"],
                property_id=record.get("property_id"),
            )
        )
    entity_manifest = json.loads(
        (run_dir / "corpus" / "corpus_manifest.json").read_text(encoding="utf-8")
    )
    for entity in entity_manifest["entities"]:
        qid = entity["qid"]
        source = claims_by_entity_source(claims, qid)
        if source is None:
            continue
        guids = frozenset(
            c.locator.value for c in claims if c.entity_qid == qid
        )
        corpus.add_source(source, guids)
    return claims, corpus


def claims_by_entity_source(claims: list[Claim], qid: str) -> SourceRef | None:
    for claim in claims:
        if claim.entity_qid == qid:
            return claim.source
    return None


def _counterexamples(corpus: ProvenanceCorpus, claims: list[Claim]) -> list[dict]:
    """Deterministic adversarial mutation cases (paper spec §5 stress strata)."""
    cases: list[dict] = []
    base = claims[0]
    # 1. false citation: real source, well-formed but unresolvable GUID.
    cases.append(
        {
            "name": "false_citation",
            "claim": Claim(
                claim_id="P09-ADV-001-false-citation",
                entity_qid=base.entity_qid,
                text=base.text,
                source=base.source,
                locator=Locator(base.source.source_id, "statement_guid", base.entity_qid + "$00000000-0000-0000-0000-000000000000"),
                epistemic="verified",
                property_id=base.property_id,
            ),
            "expected_decision": "reject_invalid_source",
        }
    )
    # 2. nonexistent source id.
    ghost = SourceRef(
        source_id="Q999999999",
        kind="wikidata_entity",
        title="Non-existent source",
        url="https://www.wikidata.org/wiki/Q999999999",
        license="CC0-1.0",
        retrieved_at="2026-11-15T00:00:00Z",
        sha256=None,
    )
    cases.append(
        {
            "name": "nonexistent_source_id",
            "claim": Claim(
                claim_id="P09-ADV-002-nonexistent-source",
                entity_qid=base.entity_qid,
                text=base.text,
                source=ghost,
                locator=Locator("Q999999999", "property", "P571"),
                epistemic="verified",
            ),
            "expected_decision": "reject_invalid_source",
        }
    )
    # 3. forged statement GUID: well-formed shape but does not resolve.
    forged = base.entity_qid + "$deadbeef-dead-4ead-8bed-deadbeefdead"
    cases.append(
        {
            "name": "forged_statement_guid",
            "claim": Claim(
                claim_id="P09-ADV-003-forged-guid",
                entity_qid=base.entity_qid,
                text=base.text,
                source=base.source,
                locator=Locator(base.source.source_id, "statement_guid", forged),
                epistemic="verified",
                property_id=base.property_id,
            ),
            "expected_decision": "reject_invalid_source",
        }
    )
    # 4. missing rights statement: empty license must fail gate.
    no_rights = SourceRef(
        source_id=base.source.source_id,
        kind=base.source.kind,
        title=base.source.title,
        url=base.source.url,
        license="",
        retrieved_at=base.source.retrieved_at,
        sha256=base.source.sha256,
    )
    try:
        no_rights_claim = Claim(
            claim_id="P09-ADV-004-missing-rights",
            entity_qid=base.entity_qid,
            text=base.text,
            source=no_rights,
            locator=base.locator,
            epistemic="verified",
            property_id=base.property_id,
        )
        cases.append(
            {
                "name": "missing_rights_statement",
                "claim": no_rights_claim,
                "expected_decision": "reject_invalid_source",
                "construction_error": None,
            }
        )
    except ProvenanceError as exc:
        cases.append(
            {
                "name": "missing_rights_statement",
                "claim": None,
                "expected_decision": "reject_invalid_source",
                "construction_error": str(exc),
            }
        )
    return cases


def stage_evaluate(run_dir: Path) -> dict:
    claims, corpus = _load_claims(run_dir)
    methods = {
        METHOD_ID: propose_surface,
        C0_METHOD_ID: c0_surface_everything,
        C1_METHOD_ID: c1_keyword_match,
    }
    decisions_by_method = {
        mid: [fn(claim, corpus).to_dict() for claim in claims] for mid, fn in methods.items()
    }
    # Verification sidecar: computed by the frozen gate from the frozen corpus
    # state; used ONLY as the scoring reference, never as policy input.
    verification = {c.claim_id: verify_claim(c, corpus).to_dict() for c in claims}
    outcomes = {cid: v["outcome"] for cid, v in verification.items()}

    eval_dir = run_dir / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    (eval_dir / "verification_outcomes.json").write_text(
        json.dumps(verification, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for mid, decisions in decisions_by_method.items():
        (eval_dir / f"decisions_{mid}.jsonl").write_text(
            "\n".join(json.dumps(d, ensure_ascii=False, sort_keys=True) for d in decisions) + "\n",
            encoding="utf-8",
        )
    metric_reports = {
        mid: evaluate_method(mid, decisions, outcomes)
        for mid, decisions in decisions_by_method.items()
    }
    (eval_dir / "metrics.json").write_text(
        json.dumps(metric_reports, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # Human-audit sample: produced UNLABELED for an independent human auditor.
    sample_rows = audit_sample(
        [c.to_dict() for c in claims],
        decisions_by_method,
        seed=42,
        fraction=0.2,
        min_n=8,
    )
    audit_sha = write_audit_sample(sample_rows, run_dir / "audit" / "audit_sample.json")
    (run_dir / "audit" / "README.md").write_text(
        "# P09 manual audit sample\n\n"
        "`audit_sample.json` is an UNLABELED sample for an independent human auditor.\n"
        "This pipeline does NOT produce expert labels; auditor_fields are left null.\n"
        "sha256 of audit_sample.json: " + audit_sha + "\n",
        encoding="utf-8",
    )

    # Adversarial counterexamples.
    counterexamples = []
    for case in _counterexamples(corpus, claims):
        claim = case["claim"]
        if claim is None:
            counterexamples.append(
                {
                    "name": case["name"],
                    "expected": case["expected_decision"],
                    "observed": "rejected_at_construction",
                    "construction_error": case["construction_error"],
                    "pass": True,
                }
            )
            continue
        decision = propose_surface(claim, corpus).to_dict()
        observed = decision["decision"]
        counterexamples.append(
            {
                "name": case["name"],
                "expected": case["expected_decision"],
                "observed": observed,
                "reason_codes": decision["reason_codes"],
                "pass": observed == case["expected_decision"],
            }
        )
    (eval_dir / "counterexamples.json").write_text(
        json.dumps(counterexamples, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # Manifest with hashes (T04/T15: no hand-entered metrics; checksum round trip).
    def _fsha(path: Path) -> str:
        return sha256_bytes(path.read_bytes()) if path.exists() else ""

    manifest = {
        "run_version": METHOD_VERSION,
        "method_id": METHOD_ID,
        "baselines": [C0_METHOD_ID, C1_METHOD_ID],
        "method_versions": {
            METHOD_ID: METHOD_VERSION,
            C0_METHOD_ID: C0_METHOD_VERSION,
            C1_METHOD_ID: C1_METHOD_VERSION,
        },
        "corpus_manifest_sha256": _fsha(run_dir / "corpus" / "corpus_manifest.json"),
        "claims_sha256": _fsha(run_dir / "corpus" / "claims.jsonl"),
        "verification_outcomes_sha256": _fsha(eval_dir / "verification_outcomes.json"),
        "metrics_sha256": _fsha(eval_dir / "metrics.json"),
        "counterexamples_sha256": _fsha(eval_dir / "counterexamples.json"),
        "audit_sample_sha256": audit_sha,
        "preregistration_path": "research_v3/experiments/p09/pre_registration.yaml",
        "matrix_path": "research_v3/experiments/p09/matrix.yaml",
        "n_claims": len(claims),
        "metrics": metric_reports,
        "counterexample_summary": {
            "n_cases": len(counterexamples),
            "n_pass": sum(1 for c in counterexamples if c["pass"]),
            "all_pass": all(c["pass"] for c in counterexamples),
        },
        "scientific_labeling": (
            "Deterministic rule evaluation on a real CC0 Wikidata corpus; audit "
            "sample is UNLABELED; no expert adjudication; no user study."
        ),
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P09 provenance-aware exploration runner")
    parser.add_argument("stage", choices=["build", "evaluate", "all"])
    parser.add_argument("--run-dir", type=Path, default=RUN_DIR)
    args = parser.parse_args(argv)
    run_dir: Path = args.run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    if args.stage in ("build", "all"):
        card = stage_build(run_dir)
        print(
            f"[p09 build] entities={len(card['entities'])} claims={card['n_claims']} "
            f"discovery_sha={card['discovery_response_sha256'][:16]}…"
        )
    if args.stage in ("evaluate", "all"):
        manifest = stage_evaluate(run_dir)
        primary = manifest["metrics"][METHOD_ID]
        print(
            f"[p09 evaluate] n={primary['n_claims']} "
            f"unsupported={primary['unsupported_claim_surfacing_rate']} "
            f"grounding={primary['citation_grounding_rate']:.3f} "
            f"abstention={primary['abstention_rate']:.3f} "
            f"counterexamples_all_pass={manifest['counterexample_summary']['all_pass']}"
        )
        if not manifest["counterexample_summary"]["all_pass"]:
            print("[p09] COUNTEREXAMPLE FAILURE", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
