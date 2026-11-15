"""P09 corpus builder: real licensed Wikidata mini-corpus for Huế heritage.

Pipeline (all live requests recorded with hashes; see METHOD.md §7):
  1. Frozen SPARQL discovery query -> entity QIDs (response JSON saved + hashed).
  2. Per-entity Special:EntityData JSON snapshot -> raw bytes saved + SHA-256.
  3. Claims derived from snapshot statements, each with its REAL statement-GUID
     locator. Every claim starts badge='unverified' (unverified-until-linked).
  4. Deterministic verification rule materializes the frozen verified subset:
     a claim is marked verified iff its statement GUID resolves in the snapshot
     AND the statement carries at least one reference block. The rule is itself
     versioned and auditable; it is NOT expert adjudication.

Wikidata is CC0. Wikidata source statements are NOT primary evidence; this
corpus supports provenance-structure research only, not historical truth claims.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from .provenance import (
    Claim,
    Locator,
    ProvenanceCorpus,
    SourceRef,
)

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
ENTITYDATA_URL = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
USER_AGENT = "luuniensuki-research-v3-p09/1.0 (academic provenance research; CC0 data)"
LICENSE_WIKIDATA = "CC0-1.0"

# The frozen discovery query: heritage entities transitively part of the
# Complex of Huế Monuments (Q10810560), the UNESCO World Heritage property
# (P361+ follows member->sub-complex edges, e.g. royal tombs -> Imperial City).
# Instance-of classes cover palace/citadel/tomb/mausoleum/temple/gate/fortress/
# shrine/esplanade/structure families seen on those members.
# NOTE: claim retrieval is done per-entity from EntityData snapshots, NOT in
# SPARQL, so every claim binds to a real statement GUID.
DISCOVERY_QUERY = """# P09 frozen discovery query: heritage entities that are part of the
# Complex of Hué Monuments (Q10810560), a UNESCO World Heritage Site in Vietnam.
# P361+ is transitive part-of; the class filter restricts to built-heritage types.
SELECT DISTINCT ?item ?itemLabel WHERE {
  ?item wdt:P361+ wd:Q10810560 .
  ?item wdt:P31 ?cls .
  FILTER(?cls IN (
    wd:Q16560, wd:Q88291, wd:Q381885, wd:Q162875, wd:Q5393308,
    wd:Q618618, wd:Q88372, wd:Q57831, wd:Q697295, wd:Q41176,
    wd:Q53060, wd:Q18247357
  ))
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY ?item
"""

# Properties extracted as claims (all are factual statements about monuments).
CLAIM_PROPERTIES: dict[str, str] = {
    "P571": "inception",
    "P625": "coordinates",
    "P361": "part_of",
    "P31": "instance_of",
    "P17": "country",
    "P131": "located_in",
}

GUID_RE = re.compile(r"^Q\d+\$[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

VERIFICATION_RULE_VERSION = "p09-verification-rule-v1.0.0"
VERIFICATION_RULE_DOC = (
    "claim is verified iff its statement GUID resolves in the frozen snapshot AND "
    "the statement carries >= 1 reference block (snaks). This is a structural "
    "rule against the snapshot, NOT expert adjudication of historical truth."
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_sparql(query: str, *, timeout: int = 60) -> tuple[list[dict[str, Any]], bytes]:
    """Execute the frozen discovery query; return (bindings, raw_response_bytes)."""
    response = requests.get(
        SPARQL_ENDPOINT,
        params={"query": query, "format": "json"},
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    raw = response.content
    data = json.loads(raw.decode("utf-8"))
    return data["results"]["bindings"], raw


def discover_entities(bindings: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Extract sorted (qid, label) pairs from discovery bindings."""
    seen: dict[str, str] = {}
    for binding in bindings:
        uri = binding["item"]["value"]
        qid = uri.rsplit("/", 1)[-1]
        if not re.fullmatch(r"Q\d+", qid):
            continue
        label = binding.get("itemLabel", {}).get("value", qid)
        seen.setdefault(qid, label)
    return [{"qid": qid, "label": label} for qid, label in sorted(seen.items())]


def fetch_entity_snapshot(qid: str, *, timeout: int = 60) -> tuple[dict[str, Any], bytes]:
    """Fetch the immutable EntityData JSON snapshot for one entity."""
    url = ENTITYDATA_URL.format(qid=qid)
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    response.raise_for_status()
    raw = response.content
    data = json.loads(raw.decode("utf-8"))
    if qid not in data.get("entities", {}):
        raise ValueError(f"EntityData response missing entity {qid}")
    return data, raw


def statement_text(entity_data: dict[str, Any], qid: str, property_id: str, claim_entry: dict[str, Any]) -> str | None:
    """Render a human-readable claim text from one statement's datavalue."""
    value = claim_entry["mainsnak"].get("datavalue", {}).get("value")
    if value is None:
        return None
    labels = entity_data.get("entities", {}).get(qid, {}).get("labels", {})
    entity_label = labels.get("en", {}).get("value", qid)
    if property_id == "P571":
        return f"{entity_label} has inception date {str(value.get('time', ''))[:11]}"
    if property_id == "P625":
        return (
            f"{entity_label} has coordinates latitude {value.get('latitude')}, "
            f"longitude {value.get('longitude')}"
        )
    if property_id in ("P361", "P31", "P17", "P131"):
        target_qid = "Q" + str(value.get("numeric-id", ""))
        return f"{entity_label} {CLAIM_PROPERTIES[property_id].replace('_', ' ')} {target_qid}"
    return None


@dataclass
class BuiltCorpus:
    claims: list[Claim]
    corpus: ProvenanceCorpus
    entity_hashes: dict[str, str]
    discovery_sha256: str
    discovery_bindings_count: int
    entities: list[dict[str, str]]


def build_claims_from_snapshot(
    qid: str,
    entity_data: dict[str, Any],
    source: SourceRef,
) -> tuple[list[Claim], frozenset[str]]:
    """Derive claims + statement index from one entity snapshot (unverified-until-linked)."""
    entity = entity_data["entities"][qid]
    labels = entity.get("labels", {})
    entity_label = labels.get("en", {}).get("value", qid)
    claims: list[Claim] = []
    guids: set[str] = set()
    for property_id, prop_name in sorted(CLAIM_PROPERTIES.items()):
        for index, entry in enumerate(entity.get("claims", {}).get(property_id, [])):
            guid = entry.get("id", "")
            if not GUID_RE.fullmatch(guid):
                continue
            guids.add(guid)
            text = statement_text(entity_data, qid, property_id, entry)
            if text is None:
                continue
            claims.append(
                Claim(
                    claim_id=f"P09-{qid}-{property_id}-{index:02d}",
                    entity_qid=qid,
                    text=text,
                    source=source,
                    locator=Locator(
                        source_id=source.source_id, kind="statement_guid", value=guid
                    ),
                    epistemic="unverified",
                    property_id=property_id,
                )
            )
    return claims, frozenset(guids)


def apply_verification_rule(claims: list[Claim], snapshots: dict[str, dict[str, Any]]) -> list[Claim]:
    """Deterministic structural verification rule (see VERIFICATION_RULE_DOC).

    Materializes the frozen verified subset: GUID resolves in the snapshot AND
    the statement has >= 1 reference block. Everything else stays unverified.
    """
    verified_claims: list[Claim] = []
    for claim in claims:
        snapshot = snapshots.get(claim.entity_qid)
        entity = (snapshot or {}).get("entities", {}).get(claim.entity_qid, {})
        resolved: dict[str, dict[str, Any]] | None = None
        if entity:
            for property_id in CLAIM_PROPERTIES:
                for entry in entity.get("claims", {}).get(property_id, []):
                    if entry.get("id") == claim.locator.value:
                        resolved = entry
                        break
                if resolved:
                    break
        has_reference = bool(resolved and resolved.get("references"))
        if has_reference:
            verified_claims.append(
                Claim(
                    claim_id=claim.claim_id,
                    entity_qid=claim.entity_qid,
                    text=claim.text,
                    source=claim.source,
                    locator=claim.locator,
                    epistemic="verified",
                    property_id=claim.property_id,
                )
            )
        else:
            verified_claims.append(claim)
    return verified_claims


def build_corpus(out_dir: Path, *, allow_network: bool = True) -> BuiltCorpus:
    """Full corpus build. Writes raw artifacts + returns the in-memory corpus."""
    out_dir = Path(out_dir)
    entity_dir = out_dir / "entity_json"
    entity_dir.mkdir(parents=True, exist_ok=True)

    if not allow_network:
        return _load_corpus_from_disk(out_dir)

    bindings, discovery_raw = run_sparql(DISCOVERY_QUERY)
    discovery_sha = sha256_bytes(discovery_raw)
    (out_dir / "discovery_response.json").write_bytes(discovery_raw)
    entities = discover_entities(bindings)

    snapshots: dict[str, dict[str, Any]] = {}
    entity_hashes: dict[str, str] = {}
    all_claims: list[Claim] = []
    corpus = ProvenanceCorpus()
    for entity in entities:
        qid = entity["qid"]
        data, raw = fetch_entity_snapshot(qid)
        digest = sha256_bytes(raw)
        (entity_dir / f"{qid}.json").write_bytes(raw)
        snapshots[qid] = data
        entity_hashes[qid] = digest
        source = SourceRef(
            source_id=qid,
            kind="wikidata_entity",
            title=entity["label"],
            url=f"https://www.wikidata.org/wiki/{qid}",
            license=LICENSE_WIKIDATA,
            retrieved_at=_utc_now(),
            sha256=digest,
        )
        claims, guids = build_claims_from_snapshot(qid, data, source)
        corpus.add_source(source, guids)
        all_claims.extend(claims)

    all_claims = apply_verification_rule(all_claims, snapshots)
    return BuiltCorpus(
        claims=all_claims,
        corpus=corpus,
        entity_hashes=entity_hashes,
        discovery_sha256=discovery_sha,
        discovery_bindings_count=len(bindings),
        entities=entities,
    )


def _load_corpus_from_disk(out_dir: Path) -> BuiltCorpus:
    """Rebuild the in-memory corpus purely from frozen artifacts (determinism check)."""
    out_dir = Path(out_dir)
    discovery_raw = (out_dir / "discovery_response.json").read_bytes()
    data = json.loads(discovery_raw.decode("utf-8"))
    entities = discover_entities(data["results"]["bindings"])
    snapshots: dict[str, dict[str, Any]] = {}
    entity_hashes: dict[str, str] = {}
    all_claims: list[Claim] = []
    corpus = ProvenanceCorpus()
    for entity in entities:
        qid = entity["qid"]
        raw = (out_dir / "entity_json" / f"{qid}.json").read_bytes()
        digest = sha256_bytes(raw)
        snapshots[qid] = json.loads(raw.decode("utf-8"))
        entity_hashes[qid] = digest
        source = SourceRef(
            source_id=qid,
            kind="wikidata_entity",
            title=entity["label"],
            url=f"https://www.wikidata.org/wiki/{qid}",
            license=LICENSE_WIKIDATA,
            retrieved_at=_utc_now(),
            sha256=digest,
        )
        claims, guids = build_claims_from_snapshot(qid, snapshots[qid], source)
        corpus.add_source(source, guids)
        all_claims.extend(claims)
    all_claims = apply_verification_rule(all_claims, snapshots)
    return BuiltCorpus(
        claims=all_claims,
        corpus=corpus,
        entity_hashes=entity_hashes,
        discovery_sha256=sha256_bytes(discovery_raw),
        discovery_bindings_count=len(data["results"]["bindings"]),
        entities=entities,
    )
