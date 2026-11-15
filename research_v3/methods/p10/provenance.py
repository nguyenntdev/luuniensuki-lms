"""P10 provenance: SHA-256 of every raw input the design consumes.

P10-T02 (rights assessment) + P10-T04 (immutable provenance). Nothing is
copied or redistributed; the loader records hashes of the read-only repo files
plus the license/rights status of each source.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from research_v2.contracts.canonical_hash import sha256_input

from .corpus import DATA_DIR, REPO_ROOT, URN_FILES
from .registry import CITATION_BACKEND_CATALOG, CITATION_CV5512, CITATION_TT32


class ProvenanceError(RuntimeError):
    """Raised when a provenance record cannot be computed."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    path: str
    sha256: str
    bytes: int
    rights_status: str  # APPROVED_FOR_REFERENCE | BLOCKED (never APPROVED for redistribution)
    rights_note: str

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "path": self.path,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "rights_status": self.rights_status,
            "rights_note": self.rights_note,
        }


TT32_RIGHTS_NOTE = (
    "public ministerial document; cite the Thông tư text, quote sparingly"
)


def collect_source_records(repo_root: Path | None = None) -> list[SourceRecord]:
    """Hash every raw input P10 reads. Fail-closed on missing files."""
    root = Path(repo_root) if repo_root else REPO_ROOT
    records: list[SourceRecord] = []

    for filename, _urn in URN_FILES:
        path = root / "data" / filename
        if not path.is_file():
            raise ProvenanceError(f"missing corpus file {path}")
        records.append(
            SourceRecord(
                source_id=f"motifs:{path.name}",
                path=str(path.relative_to(root)),
                sha256=sha256_file(path),
                bytes=path.stat().st_size,
                rights_status="APPROVED_FOR_REFERENCE",
                rights_note=(
                    "repo-documented motif inventory (AGENTS.md: 9 urns / 162 motifs); "
                    "AI-generated descriptions flagged; no archival permission claimed; "
                    "object identities referenced read-only"
                ),
            )
        )

    catalog = root / "data" / "imperial" / "curriculum_units_gdpt2018_hue.json"
    if not catalog.is_file():
        raise ProvenanceError(f"missing curriculum catalog {catalog}")
    records.append(
        SourceRecord(
            source_id="curriculum:gdpt2018_hue_catalog",
            path=str(catalog.relative_to(root)),
            sha256=sha256_file(catalog),
            bytes=catalog.stat().st_size,
            rights_status="APPROVED_FOR_REFERENCE",
            rights_note=(
                "repo-local GDPT-2018-aligned catalog citing Thông tư 32/2018/TT-BGDĐT "
                "and Công văn 5512/BGDĐT-GDTrH; used to justify 'documented' anchors"
            ),
        )
    )

    backend_service = root / "backend" / "services" / "curriculum_competency.py"
    if backend_service.is_file():
        records.append(
            SourceRecord(
                source_id="curriculum:backend_competency_catalog",
                path=str(backend_service.relative_to(root)),
                sha256=sha256_file(backend_service),
                bytes=backend_service.stat().st_size,
                rights_status="APPROVED_FOR_REFERENCE",
                rights_note=(
                    "VN_GDPT_2018 standard competency catalog (V5-T095) referenced for "
                    "the four history competencies; expert re-check still required"
                ),
            )
        )
    return records


def provenance_manifest(repo_root: Path | None = None) -> dict:
    """Full P10-T02/T04 provenance payload (deterministic; hashable)."""
    records = collect_source_records(repo_root)
    manifest = {
        "paper_id": "P10",
        "spec": "LUU_NIEN_RESEARCH_V3_14_PAPERS_SPEC_20261115/05_PAPERS/P10_*.md",
        "citations": {
            "tt32_2018": CITATION_TT32,
            "cv5512": CITATION_CV5512,
            "backend_competency_catalog": CITATION_BACKEND_CATALOG,
        },
        "rights_positions": {
            "gdpt_2018_document": (
                "public ministerial document (Thông tư 32/2018/TT-BGDĐT); encodable, "
                "citable; specific competency codes beyond the certain set are marked "
                "needs_expert_review"
            ),
            "cuu_dinh_motifs": (
                "object identities (id/name/category) referenced READ-ONLY from repo "
                "data; descriptions flagged is_ai_generated=true (162/162); NO archival "
                "or media permission claimed; hue-heritage-corpus dataset card remains "
                "BLOCKED in research_v3/datasets/registry.yaml"
            ),
            "redistribution": "no corpus bytes are copied into research_v3 or artifacts; hashes only",
        },
        "sources": [r.to_dict() for r in records],
        "n_sources": len(records),
    }
    manifest["manifest_sha256"] = sha256_input(manifest)
    return manifest
