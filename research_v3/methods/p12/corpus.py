"""P12 read-only ingestion of the repo's *already-documented* heritage claims.

Sources of truth (never modified, never fabricated):
  - ``data/imperial/historical_sources_extended.json``   (16-entry source registry, v5.1.0)
  - ``data/imperial/monument_claims_matrix.json``        (63 documented claims, v5.1.0)
  - ``data/imperial/heritage_provenance_audit_report.json`` (provenance audit, v1.0.0)

Rights posture (see dataset card ``research_v3/methods/p12/dataset_cards.yaml``):
  - Vietnamese primary archives are BLOCKED for automated ingestion; this
    adapter performs **no network access and no scraping**.
  - The JSON files are repo-internal documentation of claims pending human
    archival verification (P12-T19 BLOCKED); confidence statuses are inherited
    as-is and never upgraded by this code.
  - Wikidata (CC0) may add external entity links only via
    ``research_v3/methods/p12/wikidata_probe.py`` with recorded query + SHA.

Every claim that cannot be mapped without invention is reported in
``skipped`` with a reason — fail-closed, never silently dropped or repaired.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from research_v2.contracts.canonical_hash import sha256_file, sha256_input
from research_v3.methods.p12.ledger import ClaimEntry, Locator, SourceRecord

__all__ = ["CorpusIngest", "ingest_repo_corpus", "REPO_DATA_DIR"]

REPO_ROOT = Path(__file__).resolve().parents[3]
REPO_DATA_DIR = REPO_ROOT / "data" / "imperial"

SOURCES_FILE = REPO_DATA_DIR / "historical_sources_extended.json"
CLAIMS_FILE = REPO_DATA_DIR / "monument_claims_matrix.json"
AUDIT_FILE = REPO_DATA_DIR / "heritage_provenance_audit_report.json"

REQUIRED_SOURCE_FIELDS = ("id", "title", "source_type", "edition", "rights_status", "verification_status")
REQUIRED_CLAIM_FIELDS = ("claim_id", "statement_vi", "source_id", "epistemic_certainty")
STANCE_BY_CLAIM_TYPE = {
    # The documented registry has no conflicting transcriptions: every claim row
    # documents a single supporting source, so the honest stance mapping is
    # "supports" for rows WITH a resolvable source. Rows without any source
    # field cannot be given a stance without invention and are skipped.
}
VALID_EPISTEMIC = frozenset(
    {"archival_primary", "expert_verified", "editor_reviewed", "provisional_hypothesis"}
)


@dataclass(frozen=True)
class CorpusIngest:
    sources: dict[str, SourceRecord]
    claims: list[ClaimEntry]
    skipped: list[dict[str, Any]]
    provenance: dict[str, Any]

    @property
    def source_registry(self) -> dict[str, SourceRecord]:
        return self.sources


def _file_sha(path: Path) -> dict[str, Any]:
    return {"path": str(path.relative_to(REPO_ROOT)), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def ingest_repo_corpus(data_dir: Path | None = None) -> CorpusIngest:
    """Read-only ingestion. Raises ``FileNotFoundError`` if inputs are absent;
    raises ``ValueError`` on schema drift so silent contract breakage fails."""
    global REPO_DATA_DIR, SOURCES_FILE, CLAIMS_FILE, AUDIT_FILE
    if data_dir is not None:
        SOURCES_FILE = data_dir / "historical_sources_extended.json"
        CLAIMS_FILE = data_dir / "monument_claims_matrix.json"
        AUDIT_FILE = data_dir / "heritage_provenance_audit_report.json"

    sources_doc = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    claims_doc = json.loads(CLAIMS_FILE.read_text(encoding="utf-8"))
    audit_doc = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))

    provenance = {
        "mode": "READ_ONLY_DOCUMENTED_CLAIMS",
        "network_access": "none",
        "inputs": [_file_sha(SOURCES_FILE), _file_sha(CLAIMS_FILE), _file_sha(AUDIT_FILE)],
        "sources_registry_version": sources_doc.get("version"),
        "claims_matrix_version": claims_doc.get("version"),
        "audit_report_version": audit_doc.get("version"),
        "ingest_hash": sha256_input(
            {"sources": sources_doc.get("version"), "claims": claims_doc.get("version")}
        ),
    }

    sources: dict[str, SourceRecord] = {}
    for row in sources_doc["bibliography"]:
        missing = [f for f in REQUIRED_SOURCE_FIELDS if not row.get(f)]
        if missing:
            raise ValueError(f"source registry schema drift: {row.get('id')} missing {missing}")
        sources[row["id"]] = SourceRecord(
            source_id=row["id"],
            title=row["title"],
            source_type=row["source_type"],
            edition=row["edition"],
            rights_status=row["rights_status"],
            verification_status=row["verification_status"],
            catalog_sha256=sha256_input(row),
        )

    claims: list[ClaimEntry] = []
    skipped: list[dict[str, Any]] = []
    for row in claims_doc["claims"]:
        cid = row.get("claim_id", "<missing-id>")
        missing = [f for f in REQUIRED_CLAIM_FIELDS if not row.get(f)]
        if missing:
            skipped.append({"claim_id": cid, "reason": f"missing fields {missing}"})
            continue
        if row["epistemic_certainty"] not in VALID_EPISTEMIC:
            skipped.append(
                {"claim_id": cid, "reason": f"unknown epistemic_certainty {row['epistemic_certainty']!r}"}
            )
            continue
        if row["source_id"] not in sources:
            # Fail-closed: do NOT invent a substitute source.
            skipped.append({"claim_id": cid, "reason": f"unresolvable source_id {row['source_id']!r}"})
            continue

        vol = row.get("volume") or row.get("volume_archive")
        page = row.get("page_locator")
        if not vol or not page:
            # Fail-closed: do NOT fabricate a locator.
            skipped.append({"claim_id": cid, "reason": "missing volume or page locator in documented row"})
            continue

        edition = sources[row["source_id"]].edition
        claims.append(
            ClaimEntry(
                claim_id=row["claim_id"],
                claim_text=row["statement_vi"],
                source_id=row["source_id"],
                locator=Locator(edition=edition, volume=vol, page=page),
                stance="supports",
                confidence_status=row["epistemic_certainty"],
                evidence_kind="primary"
                if row["epistemic_certainty"] == "archival_primary"
                else "secondary",
            )
        )

    return CorpusIngest(sources=sources, claims=claims, skipped=skipped, provenance=provenance)
