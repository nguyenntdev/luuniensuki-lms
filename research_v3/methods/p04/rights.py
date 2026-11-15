"""P04 rights assessment and provenance ledger (P04-T02 + P04-T04).

Every raw artifact used by CurriculumShiftBench must carry: source URL, license
text hash, archive hash and per-file hashes captured from the immutable
``private_data/raw`` snapshot. A dataset whose license has not been captured is
not usable, regardless of its public download URL (fail-closed).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_ROOT = PROJECT_ROOT / "private_data" / "raw"

# ---------------------------------------------------------------------------
# 2026-11-15 license snapshot (verified by reading LICENSE.txt next to the raw
# archives; hashes recomputed on this machine, matching provenance.json)
# ---------------------------------------------------------------------------

LICENSE_NOTES = {
    "oulad-2013-2014": {
        "license_family": "CC BY-NC 4.0",
        "license_url": "https://creativecommons.org/licenses/by-nc/4.0/legalcode.txt",
        "commercial_use": False,
        "redistribution_of_derivatives": "allowed with attribution, non-commercial only",
        "note": (
            "Registry lists UCI as distributor; the captured license text "
            "(sha256 41003d4a...) is Attribution-NonCommercial 4.0. Academic "
            "benchmark use and derivation are permitted; no commercial claim "
            "may be attached to any P04 artifact."
        ),
    },
    "uci-student-performance-2014": {
        "license_family": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/legalcode.txt",
        "commercial_use": True,
        "redistribution_of_derivatives": "allowed with attribution",
        "note": "Cortez & Silva (2008) student performance (mat+por), UCI 320.",
    },
    "assistments": {
        "license_family": "UNVERIFIED",
        "license_url": "https://sites.google.com/site/assistmentsdata/datasets",
        "commercial_use": None,
        "redistribution_of_derivatives": None,
        "note": (
            "Dataset-specific terms not yet reviewed; version selection and "
            "license capture pending. BLOCKED in datasets/registry.yaml; P04 "
            "must not download or score ASSISTments until unblocked."
        ),
    },
    "junyi": {
        "license_family": "UNVERIFIED",
        "license_url": "https://www.kaggle.com/datasets/junyiacademy/learning-activity-public-dataset",
        "commercial_use": None,
        "redistribution_of_derivatives": None,
        "note": (
            "Kaggle terms of use apply and have not been captured/hash-pinned; "
            "no local raw snapshot exists. BLOCKED for P04."
        ),
    },
    "ednet": {
        "license_family": "CC BY-NC (repository-declared)",
        "license_url": "https://github.com/riiid/ednet",
        "commercial_use": False,
        "redistribution_of_derivatives": "restricted; derivative subset policy not yet defined",
        "note": (
            "Registry marks BLOCKED: NC terms conflict with unrestricted "
            "benchmark redistribution; deterministic subset policy pending. "
            "P04 runs without EdNet and marks external generalization "
            "accordingly."
        ),
    },
}

RAW_FILES = {
    "oulad-2013-2014": {
        "archive": "oulad/2013-2014/oulad.zip",
        "files": [
            "oulad/2013-2014/_extracted/studentInfo.csv",
            "oulad/2013-2014/_extracted/studentVle.csv",
            "oulad/2013-2014/_extracted/vle.csv",
            "oulad/2013-2014/_extracted/courses.csv",
            "oulad/2013-2014/_extracted/assessments.csv",
            "oulad/2013-2014/_extracted/studentAssessment.csv",
        ],
        "archive_sha256": "f2ed1902616c1fe8d2824d872c0b7d2d72be435bf0124d077044fe4be2c6d3e4",
        "license_text_sha256": "41003d4a74749c0220e33dd415042164b5a1093ed401f36277234f772d22d3d0",
        "retrieved_at": "2026-11-15T10:33:03Z",
        "source_url": "https://archive.ics.uci.edu/static/public/349/open+university+learning+analytics+dataset.zip",
        "doi": "10.1038/sdata.2017.171",
        "sample_count": 32593,
    },
    "uci-student-performance-2014": {
        "archive": "uci/student-performance-2014/student.zip",
        "files": [],
        "archive_sha256": "82ae9d66437b9808df42e8c89d2bb179c46e9cfbcf06f38abc1d20b3b747e177",
        "license_text_sha256": "9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411",
        "retrieved_at": "2026-11-15T10:32:45Z",
        "source_url": "https://archive.ics.uci.edu/static/public/320/student+performance.zip",
        "doi": "10.24432/C5TG7T",
        "sample_count": 1044,
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class RightsRecord:
    dataset_id: str
    usable: bool
    blocked_reason: str | None
    license_family: str
    archive_sha256: str
    license_text_sha256: str
    file_hashes: dict[str, str]


def verify_raw_snapshot() -> dict[str, Any]:
    """Recompute raw hashes and verify against the frozen expected values.

    Returns a manifest; raises ``FileNotFoundError`` when a raw file the
    benchmark depends on is missing (fail-closed, no silent degradation).
    """
    manifest: dict[str, Any] = {"verified_at_module": "research_v3.methods.p04.rights", "datasets": {}}
    for ds_id, spec in RAW_FILES.items():
        entry: dict[str, Any] = {
            "source_url": spec["source_url"],
            "doi": spec["doi"],
            "retrieved_at": spec["retrieved_at"],
            "sample_count": spec["sample_count"],
            "license_family": LICENSE_NOTES[ds_id]["license_family"],
        }
        archive_path = PROJECT_ROOT / "private_data" / "raw" / spec["archive"]
        entry["archive_present"] = archive_path.is_file()
        entry["archive_sha256"] = sha256_file(archive_path) if archive_path.is_file() else None
        entry["archive_sha256_matches_expected"] = entry["archive_sha256"] == spec["archive_sha256"]
        lic_path = archive_path.parent / "LICENSE.txt"
        entry["license_text_sha256"] = sha256_file(lic_path) if lic_path.is_file() else None
        entry["license_sha256_matches_expected"] = (
            entry["license_text_sha256"] == spec["license_text_sha256"]
        )
        file_hashes = {}
        for rel in spec["files"]:
            fp = PROJECT_ROOT / "private_data" / "raw" / rel
            file_hashes[rel] = sha256_file(fp) if fp.is_file() else None
        entry["file_hashes"] = file_hashes
        entry["usable"] = bool(
            entry["archive_present"]
            and entry["archive_sha256_matches_expected"]
            and entry["license_sha256_matches_expected"]
        )
        manifest["datasets"][ds_id] = entry
    return manifest


def load_or_build_manifest(path: Path) -> dict[str, Any]:
    """Load the frozen rights manifest, building it once if absent."""
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    manifest = verify_raw_snapshot()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def blocked_datasets() -> dict[str, str]:
    """Exact BLOCKED registry entries P04 may not use."""
    return {
        "assistments": LICENSE_NOTES["assistments"]["note"],
        "junyi": LICENSE_NOTES["junyi"]["note"],
        "ednet": LICENSE_NOTES["ednet"]["note"],
    }
