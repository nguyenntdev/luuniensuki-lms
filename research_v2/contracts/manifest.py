"""Data manifest schema and helpers for Research V2 datasets."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from .canonical_hash import sha256_bytes, sha256_file, STANDARD_NAME


class ManifestError(ValueError):
    """Raised when a dataset manifest violates the V2 schema."""


@dataclass(frozen=True)
class DatasetEntry:
    dataset_id: str
    study_id: str
    tier: str  # T1 | T2 | T3
    path: str
    sha256: str
    cases: int
    license: str
    provenance: str  # "synthetic" | "external-licensed" | "blocked"
    source_url: str | None = None
    version: str | None = None
    split_strategy: str | None = None
    blocked_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DataManifest:
    hash_standard: str
    entries: tuple[DatasetEntry, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hash_standard": self.hash_standard,
            "entries": [e.to_dict() for e in self.entries],
        }

    def by_study(self, study_id: str, tier: str | None = None) -> list[DatasetEntry]:
        out = [e for e in self.entries if e.study_id == study_id]
        if tier is not None:
            out = [e for e in out if e.tier == tier]
        return out

    def blocked(self) -> list[DatasetEntry]:
        return [e for e in self.entries if e.provenance == "blocked"]


def load_manifest(path: Path) -> DataManifest:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("hash_standard") != STANDARD_NAME:
        raise ManifestError(
            f"manifest hash_standard must be {STANDARD_NAME!r}, got {data.get('hash_standard')!r}"
        )
    entries = []
    for raw in data.get("entries", []):
        try:
            entries.append(DatasetEntry(**raw))
        except TypeError as exc:
            raise ManifestError(f"invalid manifest entry {raw!r}: {exc}") from exc
    manifest = DataManifest(hash_standard=STANDARD_NAME, entries=tuple(entries))
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: DataManifest) -> None:
    seen: set[str] = set()
    for entry in manifest.entries:
        if entry.dataset_id in seen:
            raise ManifestError(f"duplicate dataset_id: {entry.dataset_id}")
        seen.add(entry.dataset_id)
        if entry.tier not in {"T1", "T2", "T3"}:
            raise ManifestError(f"{entry.dataset_id}: invalid tier {entry.tier!r}")
        if entry.provenance not in {"synthetic", "external-licensed", "blocked"}:
            raise ManifestError(f"{entry.dataset_id}: invalid provenance {entry.provenance!r}")
        if entry.provenance == "external-licensed" and not entry.source_url:
            raise ManifestError(f"{entry.dataset_id}: external data requires source_url")
        if entry.provenance == "blocked" and not entry.blocked_reason:
            raise ManifestError(f"{entry.dataset_id}: blocked data requires blocked_reason")
        if not entry.license:
            raise ManifestError(f"{entry.dataset_id}: missing license")


def write_manifest(manifest: DataManifest, path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def fingerprint_rows(rows: Iterable[Mapping[str, Any]]) -> str:
    """Deterministic dataset fingerprint over canonicalized rows."""
    import hashlib

    digest = hashlib.sha256()
    for row in rows:
        payload = json.dumps(
            row, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
        digest.update(payload)
        digest.update(b"\n")
    return digest.hexdigest()


def file_fingerprint(path: Path) -> str:
    return sha256_file(path)
