"""P12 Wikidata (CC0) entity-linking probe with full provenance recording.

Role in P12: Wikidata provides *external entity links* (e.g. QID for "Ngọ Môn",
"Minh Mạng") to enrich the ledger's source/claim records. Per the repo data
gate (03_DATA, Wikidata row): data is CC0 "generally", but source statements on
Wikidata require independent factual review — a Wikidata link can NEVER
establish historical truth and never substitutes for a primary source locator.

Honesty rules implemented here:
  - The exact SPARQL query text is recorded next to the response SHA-256.
  - Every entity label returned is stored as-is; nothing is inferred, no QID is
    guessed when the query fails or returns empty (returns ``None`` instead).
  - No archive scraping, no PII, no fabricated response when offline: failures
    are recorded as ``status: "error"`` with the exception class only.

The Vietnamese primary archives are NOT queried — they remain BLOCKED.
"""
from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from typing import Any

from research_v2.contracts.canonical_hash import sha256_input

__all__ = ["PROVENANCE_ENDPOINT", "build_entity_query", "query_wikidata_entity", "WikidataProbe"]

PROVENANCE_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "luuniensuki-research-p12/0.1 (academic source-auditing apparatus; no scraping)"
LICENSE_DECLARATION = "CC0-1.0 (as declared upstream at data gate time; snapshot recorded per response)"


def build_entity_query(label: str, *, language: str = "vi", limit: int = 1) -> str:
    """Deterministic SPARQL for exact-label entity lookup (no fuzzy guessing)."""
    return (
        "SELECT ?item ?itemLabel WHERE {\n"
        f'  ?item rdfs:label "{label}"@{language} .\n'
        '  SERVICE wikibase:label { bd:serviceParam wikibase:language "'
        + language
        + ',en" . }\n'
        "}\n"
        f"LIMIT {limit}"
    )


class WikidataProbe:
    """Records query text + response SHA for every call (BLOCKED if offline)."""

    def __init__(self, *, endpoint: str = PROVENANCE_ENDPOINT, timeout_seconds: float = 15.0):
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.calls: list[dict[str, Any]] = []

    def query_wikidata_entity(self, label: str, *, language: str = "vi") -> dict[str, Any]:
        query = build_entity_query(label, language=language)
        record: dict[str, Any] = {
            "endpoint": self.endpoint,
            "license": LICENSE_DECLARATION,
            "label": label,
            "language": language,
            "query": query,
            "query_sha256": sha256_input(query),
        }
        try:
            url = self.endpoint + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
            req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json", "User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                body = resp.read()
            payload = json.loads(body)
            bindings = payload.get("results", {}).get("bindings", [])
            if bindings:
                b = bindings[0]
                record.update(
                    {
                        "status": "ok",
                        "qid": b.get("item", {}).get("value", "").rsplit("/", 1)[-1],
                        "resolved_label": b.get("itemLabel", {}).get("value"),
                        "response_sha256": hashlib.sha256(body).hexdigest(),
                    }
                )
            else:
                record.update({"status": "no_match", "qid": None, "response_sha256": hashlib.sha256(body).hexdigest()})
        except Exception as exc:  # fail-closed: record the failure, never fake a QID
            record.update({"status": "error", "error_class": type(exc).__name__, "qid": None})
        self.calls.append(record)
        return record

    def export(self) -> dict[str, Any]:
        return {
            "probe": "wikidata_cc0_entity_linking",
            "note": "Entity links only; never evidence of historical truth; archives untouched.",
            "calls": self.calls,
        }
