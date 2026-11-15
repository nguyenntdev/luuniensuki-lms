"""P14 dataset rights assessment (P14-T02).

External media sources and their verified status in this environment. Fail-closed:
a source is usable only with an APPROVED card backed by captured license text
and file hashes. Neither external API is reachable without a key, so both stay
BLOCKED and the study falls back to the labelled synthetic manifest (PARTIAL).
"""
from __future__ import annotations

from typing import Any

from research_v3.contracts.cards import DatasetCard

H64 = "0" * 64  # placeholder hash is NOT used for APPROVED cards; BLOCKED only


def rights_cards() -> list[DatasetCard]:
    """Rights status for every P14-relevant media source (as of 2026-11-15)."""
    return [
        DatasetCard(
            dataset_id="smithsonian-open-access",
            provider="Smithsonian Institution",
            source_url="https://www.si.edu/openaccess/devtools",
            doi=None,
            version="api-v1.0",
            retrieved_at="2026-11-15T00:00:00Z",
            license_text_sha256="",
            allowed_uses=(),
            redistribution_policy=(
                "CC0-marked items only; API key required for data access "
                "(https://www.si.edu/openaccess/api/v1/terms)"
            ),
            original_sha256="",
            transformed_sha256=None,
            sample_count=0,
            schema_version="",
            consent_basis="",
            units="heritage-object-record",
            group_keys=("edan_id",),
            time_key=None,
            leakage_audit="not run",
            source_attribution="Smithsonian Open Access (CC0 items only)",
            status="BLOCKED",
            blocked_reason=(
                "API key unavailable in this environment: search endpoint returns "
                "HTTP 403 without api_key (verified 2026-11-15). CC0 gate requires "
                "item-level 'open access' filtering, which needs the key."
            ),
        ),
        DatasetCard(
            dataset_id="europeana-metadata",
            provider="Europeana Foundation",
            source_url="https://pro.europeana.eu/page/apis",
            doi=None,
            version="record-api-v2",
            retrieved_at="2026-11-15T00:00:00Z",
            license_text_sha256="",
            allowed_uses=(),
            redistribution_policy=(
                "Metadata CC0; item-level media rights vary per provider and must "
                "be checked per object (https://pro.europeana.eu/page/now-available)"
            ),
            original_sha256="",
            transformed_sha256=None,
            sample_count=0,
            schema_version="",
            consent_basis="",
            units="heritage-object-record",
            group_keys=("provider", "edm_id"),
            time_key=None,
            leakage_audit="not run",
            source_attribution="Europeana (metadata CC0; media item-level rights)",
            status="BLOCKED",
            blocked_reason=(
                "API key unavailable in this environment: search endpoint returns "
                "HTTP 401 without wskey (verified 2026-11-15). Item-level rights "
                "filtering cannot be verified without the key."
            ),
        ),
        DatasetCard(
            dataset_id="hue-heritage-corpus",
            provider="Hue Monuments Conservation Centre",
            source_url="https://www.hueworldheritage.org.vn/",
            doi=None,
            version="unspecified",
            retrieved_at="2026-11-15T00:00:00Z",
            license_text_sha256="",
            allowed_uses=(),
            redistribution_policy="unlicensed until written permission obtained",
            original_sha256="",
            transformed_sha256=None,
            sample_count=0,
            schema_version="",
            consent_basis="requires archive permission and page-level citations",
            units="heritage-object-record",
            group_keys=("page_id",),
            time_key=None,
            leakage_audit="not run",
            source_attribution="Huế World Heritage (unlicensed)",
            status="BLOCKED",
            blocked_reason=(
                "Study rule: copyrighted Huế imagery must not be reused; no "
                "written permission on file. Corpus is out of scope for P14."
            ),
        ),
    ]


def external_media_status() -> dict[str, Any]:
    """Machine-readable summary for artifacts and the manuscript."""
    cards = rights_cards()
    return {
        "external_media_status": "BLOCKED",
        "study_external_media_mark": "PARTIAL",
        "fallback": "documented synthetic manifest labelled 'synthetic, no third-party rights'",
        "verified_http_probes": {
            "smithsonian_no_key": "HTTP 403 (2026-11-15)",
            "europeana_no_key": "HTTP 401 (2026-11-15)",
        },
        "key_application_urls": {
            "smithsonian": "https://www.si.edu/openaccess/api/v1/request-account",
            "europeana": "https://pro.europeana.eu/page/get-api",
        },
        "cards": [c.to_dict() for c in cards],
        "hué_imagery_used": False,
    }
