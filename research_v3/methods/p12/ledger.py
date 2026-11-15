"""P12 — Source–claim–locator provenance ledger with append-only hash chain.

Implements the apparatus specified in ``research_v3/methods/p12/METHOD.md``
(frozen 2026-11-15). This module is the *apparatus* only: it audits internal
consistency of historical-claim citations. It never verifies historical truth,
never invents citations or page numbers, and never touches the Vietnamese
primary archives (BLOCKED for automated ingestion — see the dataset cards).

Hash standard: ``research_v2.contracts.canonical_hash`` —
``sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False))``
so every research wave shares one canonical hash convention.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from research_v2.contracts.canonical_hash import canonical_json, sha256_input

__all__ = [
    "STANCES",
    "CONFIDENCE_STATUSES",
    "EVIDENCE_KINDS",
    "LEDGER_ACTIONS",
    "VALID_VERDICTS",
    "NOT_APPLICABLE",
    "ABSTAIN",
    "LedgerError",
    "Locator",
    "SourceRecord",
    "ClaimEntry",
    "LedgerEvent",
    "ClaimLedger",
    "ValidationVerdict",
    "validate_claim",
    "audit_corpus",
    "verify_chain",
]


STANCES = frozenset({"supports", "refutes", "undetermined"})
CONFIDENCE_STATUSES = frozenset(
    {"archival_primary", "expert_verified", "editor_reviewed", "provisional_hypothesis"}
)
EVIDENCE_KINDS = frozenset({"primary", "secondary", "translation", "exhibition_copy"})
LEDGER_ACTIONS = frozenset({"append", "annotate"})
VALID_VERDICTS = frozenset({"PASS", "REJECT", ABSTAIN := "ABSTAIN"})
NOT_APPLICABLE = "NOT_APPLICABLE"


class LedgerError(ValueError):
    """Raised when a claim, source or ledger event violates the P12 contract."""


def _require_non_empty(owner: str, name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LedgerError(f"{owner}: {name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class Locator:
    """Where inside a source the claim is anchored. All parts required."""

    edition: str
    volume: str
    page: str

    def __post_init__(self) -> None:
        for part in ("edition", "volume", "page"):
            _require_non_empty(f"Locator({self})", part, getattr(self, part))

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class SourceRecord:
    """One documented source in the sources registry (never fabricated here)."""

    source_id: str
    title: str
    source_type: str
    edition: str
    rights_status: str
    verification_status: str
    catalog_sha256: str | None = None  # sha256 of the registry row it came from

    def __post_init__(self) -> None:
        for part in ("source_id", "title", "source_type", "edition", "rights_status", "verification_status"):
            _require_non_empty(f"SourceRecord({self.source_id})", part, getattr(self, part))
        if self.catalog_sha256 is not None and len(self.catalog_sha256) != 64:
            raise LedgerError(f"{self.source_id}: catalog_sha256 must be a sha256 hex digest")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClaimEntry:
    """One historical claim bound to (at most) one source anchor per entry."""

    claim_id: str
    claim_text: str
    source_id: str | None = None
    locator: Locator | None = None
    stance: str = "undetermined"
    confidence_status: str = "provisional_hypothesis"
    evidence_kind: str = "secondary"

    def __post_init__(self) -> None:
        _require_non_empty("ClaimEntry", "claim_id", self.claim_id)
        _require_non_empty(f"claim {self.claim_id}", "claim_text", self.claim_text)
        if self.stance not in STANCES:
            raise LedgerError(f"{self.claim_id}: stance {self.stance!r} not in {sorted(STANCES)}")
        if self.confidence_status not in CONFIDENCE_STATUSES:
            raise LedgerError(
                f"{self.claim_id}: confidence_status {self.confidence_status!r} "
                f"not in {sorted(CONFIDENCE_STATUSES)}"
            )
        if self.evidence_kind not in EVIDENCE_KINDS:
            raise LedgerError(
                f"{self.claim_id}: evidence_kind {self.evidence_kind!r} not in {sorted(EVIDENCE_KINDS)}"
            )
        if self.locator is not None and not isinstance(self.locator, Locator):
            raise LedgerError(f"{self.claim_id}: locator must be a Locator instance")

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "source_id": self.source_id,
            "locator": self.locator.to_dict() if self.locator else None,
            "stance": self.stance,
            "confidence_status": self.confidence_status,
            "evidence_kind": self.evidence_kind,
        }


@dataclass(frozen=True)
class LedgerEvent:
    """One immutable entry in the append-only audit chain."""

    seq: int
    timestamp_utc: str
    action: str
    payload: Mapping[str, Any]
    prev_hash: str
    entry_hash: str = ""

    def __post_init__(self) -> None:
        if self.action not in LEDGER_ACTIONS:
            raise LedgerError(f"event {self.seq}: action {self.action!r} not in {sorted(LEDGER_ACTIONS)}")

    def compute_hash(self) -> str:
        body = {
            "seq": self.seq,
            "timestamp_utc": self.timestamp_utc,
            "action": self.action,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
        }
        return sha256_input(body)


@dataclass
class ClaimLedger:
    """Append-only ledger. Appends never rewrite history; a new timestamp may
    not precede the previous event's timestamp (monotonic clock discipline).

    ``timestamp_provider`` may be injected for deterministic tests.
    """

    timestamp_provider: Any = field(default=None, repr=False)
    events: list[LedgerEvent] = field(default_factory=list)

    def _now(self) -> str:
        if self.timestamp_provider is not None:
            return str(self.timestamp_provider())
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def append(self, claim: ClaimEntry) -> LedgerEvent:
        return self._record("append", claim.to_dict(), claim.claim_id)

    def annotate(self, claim_id: str, annotation: Mapping[str, Any]) -> LedgerEvent:
        if not claim_id:
            raise LedgerError("annotate: claim_id required")
        payload = {"claim_id": claim_id, "annotation": dict(annotation)}
        return self._record("annotate", payload, claim_id)

    def _record(self, action: str, payload: Mapping[str, Any], owner: str) -> LedgerEvent:
        prev_hash = self.events[-1].entry_hash if self.events else "GENESIS"
        ts = self._now()
        if self.events and ts < self.events[-1].timestamp_utc:
            raise LedgerError(
                f"{owner}: timestamp {ts!r} precedes previous event "
                f"{self.events[-1].timestamp_utc!r}; append-only chain must be monotonic"
            )
        event = LedgerEvent(
            seq=len(self.events) + 1,
            timestamp_utc=ts,
            action=action,
            payload=dict(payload),
            prev_hash=prev_hash,
        )
        event = LedgerEvent(
            seq=event.seq,
            timestamp_utc=event.timestamp_utc,
            action=event.action,
            payload=event.payload,
            prev_hash=event.prev_hash,
            entry_hash=event.compute_hash(),
        )
        self.events.append(event)
        return event

    def chain_digest(self) -> str:
        """Digest over the whole chain; changes if any byte of history changes."""
        return sha256_input([e.__dict__ | {"entry_hash": e.entry_hash} for e in self.events])

    def export(self) -> list[dict[str, Any]]:
        return [e.__dict__ | {"payload": dict(e.payload)} for e in self.events]


def verify_chain(events: Iterable[LedgerEvent]) -> dict[str, Any]:
    """Fail-closed re-verification of the whole hash chain (METHOD §3 V5)."""
    prev = "GENESIS"
    n = 0
    for n, event in enumerate(events, 1):
        if event.seq != n:
            raise LedgerError(f"chain: sequence break at position {n} (seq={event.seq})")
        if event.prev_hash != prev:
            raise LedgerError(
                f"chain: event {event.seq} prev_hash {event.prev_hash[:12]}… "
                f"does not link to previous hash {prev[:12]}…"
            )
        if event.entry_hash != event.compute_hash():
            raise LedgerError(f"chain: event {event.seq} entry_hash mismatch (payload tampered)")
        prev = event.entry_hash
    return {"events": n, "chain_head": prev, "status": "PASS" if n else "EMPTY"}


@dataclass(frozen=True)
class ValidationVerdict:
    """Result of validating one claim. ABSTAIN ≠ REJECT ≠ NOT_APPLICABLE."""

    claim_id: str
    verdict: str  # PASS | REJECT | ABSTAIN
    failures: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.verdict not in VALID_VERDICTS:
            raise LedgerError(f"{self.claim_id}: verdict {self.verdict!r} not in {sorted(VALID_VERDICTS)}")
        if self.verdict == "REJECT" and not self.failures:
            raise LedgerError(f"{self.claim_id}: REJECT requires at least one failure code")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_claim(
    claim: ClaimEntry,
    registry: Mapping[str, SourceRecord],
    *,
    fail_on_missing_locator: bool = True,
) -> ValidationVerdict:
    """Fail-closed validation (METHOD §3, rules V1–V4 per single claim).

    Never mutates the claim, never repairs data, never invents a citation.
    ABSTAIN is returned when the claim is internally consistent but its
    confidence status asserts something (archival/expert/editor review) that no
    human has performed in this apparatus — routed to human review instead.
    """
    failures: list[str] = []
    notes: list[str] = []

    # V1 — sourced
    if not claim.source_id:
        failures.append("missing_source")
    # V2 — resolvable
    elif claim.source_id not in registry:
        failures.append("unknown_source")
    # V3 — locator present (only meaningful once the source resolves)
    if claim.source_id and claim.source_id in registry and fail_on_missing_locator:
        if claim.locator is None:
            failures.append("missing_locator")

    if failures:
        return ValidationVerdict(claim.claim_id, "REJECT", tuple(failures), tuple(notes))

    # V4 — stance vocabulary is enforced at construction; a claim asserting a
    # human-verified confidence status without the blocked human phase is
    # provisional inside this apparatus: abstain, route to human review.
    if claim.confidence_status in {"archival_primary", "expert_verified", "editor_reviewed"}:
        notes.append(
            f"confidence_status={claim.confidence_status} inherited from documented "
            "registry; human archival verification pending (P12-T19)"
        )
        return ValidationVerdict(claim.claim_id, ABSTAIN, (), tuple(notes))

    return ValidationVerdict(claim.claim_id, "PASS", (), tuple(notes))


def _contradiction_index(
    claims: Iterable[ClaimEntry], registry: Mapping[str, SourceRecord]
) -> list[dict[str, Any]]:
    """V4 — stance contradictions routed to human adjudication.

    Two finding types:
      - ``cross_source_conflict``: claim_text supported by one resolvable source
        and refuted by a *different* resolvable source.
      - ``same_source_transcription_defect``: the same resolvable source carries
        both a supports and a refutes entry for one claim_text — a transcription
        defect that must be resolved by a human, never silently averaged.
    ``undetermined`` never contradicts anything (first-class abstention).
    """
    by_text: dict[str, dict[str, set[str]]] = {}
    for c in claims:
        if c.stance == "undetermined" or not c.source_id or c.source_id not in registry:
            continue
        bucket = by_text.setdefault(c.claim_text.strip(), {"supports": set(), "refutes": set()})
        bucket[c.stance].add(c.source_id)
    findings: list[dict[str, Any]] = []
    for text, bucket in by_text.items():
        if bucket["supports"] and bucket["refutes"]:
            cross = bucket["supports"] - bucket["refutes"]
            same = bucket["supports"] & bucket["refutes"]
            if cross:
                findings.append(
                    {
                        "type": "cross_source_conflict",
                        "claim_text": text,
                        "supporting_sources": sorted(bucket["supports"]),
                        "refuting_sources": sorted(bucket["refutes"]),
                        "resolution": "HUMAN_ADJUDICATION_BLOCKED",
                    }
                )
            if same:
                findings.append(
                    {
                        "type": "same_source_transcription_defect",
                        "claim_text": text,
                        "conflicted_sources": sorted(same),
                        "resolution": "HUMAN_ADJUDICATION_BLOCKED",
                    }
                )
    return findings


def audit_corpus(
    claims: Iterable[ClaimEntry],
    registry: Mapping[str, SourceRecord],
    *,
    timestamp_provider: Any = None,
) -> dict[str, Any]:
    """Full proposed-arm audit: append to ledger, validate, chain-verify, metrics.

    Returns a JSON-serializable manifest dict. Raises ``LedgerError`` only on
    internal contract violations (chain tamper); per-claim defects are *data*,
    reported in the verdicts, never silently repaired.
    """
    ledger = ClaimLedger(timestamp_provider=timestamp_provider)
    claim_list = list(claims)
    for c in claim_list:
        ledger.append(c)

    verdicts = [validate_claim(c, registry) for c in claim_list]
    contradictions = _contradiction_index(claim_list, registry)
    chain = verify_chain(ledger.events)

    n = len(claim_list)
    n_reject = sum(1 for v in verdicts if v.verdict == "REJECT")
    unsourced = sum(1 for v in verdicts if "missing_source" in v.failures or "unknown_source" in v.failures)
    sourced = sum(1 for c in claim_list if c.source_id)
    located = sum(1 for c in claim_list if c.source_id and c.locator is not None)
    abstain = sum(1 for v in verdicts if v.verdict == "ABSTAIN")

    return {
        "n_claims": n,
        "n_sources_in_registry": len(registry),
        "unsourced_claim_count": unsourced,
        "unsourced_claim_rate": (unsourced / n) if n else None,
        "sourced_claim_count": sourced,
        "locator_complete_count": located,
        "locator_completeness_rate": (located / sourced) if sourced else None,
        "contradiction_count": len(contradictions),
        "contradictions": contradictions,
        "rejected_claims": [v.claim_id for v in verdicts if v.verdict == "REJECT"],
        "abstain_count": abstain,
        "verdict_counts": {
            "PASS": sum(1 for v in verdicts if v.verdict == "PASS"),
            "REJECT": n_reject,
            "ABSTAIN": abstain,
        },
        "chain": chain,
        "chain_digest": ledger.chain_digest(),
        "ledger_events": ledger.export(),
    }
