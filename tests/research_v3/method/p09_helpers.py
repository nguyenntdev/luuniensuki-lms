"""Shared helpers for P09 method tests (frozen corpus + tiny synthetic fixtures)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RUN_DIR = REPO_ROOT / "research_artifacts_v3" / "runs" / "p09"

from research_v3.methods.p09 import (  # noqa: E402
    Claim,
    Locator,
    ProvenanceCorpus,
    SourceRef,
    propose_surface,
    verify_claim,
)


def make_source(
    source_id: str = "Q975568",
    *,
    license: str = "CC0-1.0",
    sha256: str | None = None,
    kind: str = "wikidata_entity",
    title: str = "Thiên Mụ Temple",
) -> SourceRef:
    return SourceRef(
        source_id=source_id,
        kind=kind,
        title=title,
        url=f"https://www.wikidata.org/wiki/{source_id}",
        license=license,
        retrieved_at="2026-11-15T00:00:00Z",
        sha256=sha256,
    )


GUID = "Q975568$11111111-2222-4333-8444-555555555555"


def make_claim(
    claim_id: str = "P09-TEST-001",
    *,
    source: SourceRef | None = None,
    locator: Locator | None = None,
    epistemic: str = "verified",
    entity_qid: str = "Q975568",
    text: str = "Thiên Mụ Temple part of Q10810560",
    property_id: str | None = "P361",
) -> Claim:
    source = source or make_source()
    locator = locator or Locator(source.source_id, "statement_guid", GUID)
    return Claim(
        claim_id=claim_id,
        entity_qid=entity_qid,
        text=text,
        source=source,
        locator=locator,
        epistemic=epistemic,
        property_id=property_id,
    )


def make_corpus(*, guids: frozenset[str] | None = None) -> ProvenanceCorpus:
    corpus = ProvenanceCorpus()
    corpus.add_source(make_source(), guids if guids is not None else frozenset({GUID}))
    return corpus


def load_frozen_claims() -> list[Claim]:
    """Load the real built corpus claims from the run directory (skips if absent)."""
    path = RUN_DIR / "corpus" / "claims.jsonl"
    if not path.exists():
        return []
    claims: list[Claim] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        src = record["source"]
        loc = record["locator"]
        claims.append(
            Claim(
                claim_id=record["claim_id"],
                entity_qid=record["entity_qid"],
                text=record["text"],
                source=SourceRef(
                    source_id=src["source_id"],
                    kind=src["kind"],
                    title=src["title"],
                    url=src["url"],
                    license=src["license"],
                    retrieved_at=src["retrieved_at"],
                    sha256=src["sha256"],
                ),
                locator=Locator(loc["source_id"], loc["kind"], loc["value"]),
                epistemic=record["epistemic"],
                property_id=record.get("property_id"),
            )
        )
    return claims
