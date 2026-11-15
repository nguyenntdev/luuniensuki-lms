"""P12 shared test helpers — SELF-CONTAINED (no conftest dependency).

P12 owns only ``tests/research_v3/method/test_p12_*.py``; other P-paper agents
own ``conftest.py``, so these helpers are plain importable functions and the
fixtures live here as plain builders, following the repo's ``pXX_helpers.py``
pattern. All registry/claim values are synthetic test fixtures, NOT real
citations.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research_v3.methods.p12.baselines import baseline_c0, baseline_c1  # noqa: E402, F401
from research_v3.methods.p12.corpus import ingest_repo_corpus  # noqa: E402, F401
from research_v3.methods.p12.ledger import (  # noqa: E402, F401
    ClaimEntry,
    ClaimLedger,
    LedgerError,
    Locator,
    SourceRecord,
    validate_claim,
)

FIXED_TS = "2026-11-15T00:00:00Z"


def ts_provider(seq: int = 0) -> str:
    """Deterministic monotonic timestamps for tests (constant by default)."""
    return f"2026-11-15T00:00:{seq:02d}Z"


def make_registry() -> dict[str, SourceRecord]:
    """Two synthetic sources covering primary + secondary evidence kinds."""
    return {
        "src-fixture-primary": SourceRecord(
            source_id="src-fixture-primary",
            title="Fixture Royal Record (test only)",
            source_type="royal_record",
            edition="Fixture Edition 1900",
            rights_status="public_domain",
            verification_status="verified",
        ),
        "src-fixture-secondary": SourceRecord(
            source_id="src-fixture-secondary",
            title="Fixture Secondary Study (test only)",
            source_type="scholarly_book",
            edition="Fixture Edition 1990",
            rights_status="public_domain",
            verification_status="verified",
        ),
    }


def make_claim(**overrides) -> ClaimEntry:
    defaults = dict(
        claim_id="claim-fixture-01",
        claim_text="Fixture claim text (test only).",
        source_id="src-fixture-primary",
        locator=Locator(edition="Fixture Edition 1900", volume="Quyển 1", page="Tờ 5a"),
        stance="supports",
        confidence_status="provisional_hypothesis",
        evidence_kind="primary",
    )
    defaults.update(overrides)
    return ClaimEntry(**defaults)


def make_repo_ingest():
    """The real read-only documented corpus (63 claims) — used read-only."""
    return ingest_repo_corpus()
