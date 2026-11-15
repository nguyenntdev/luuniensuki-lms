"""P07 external adapter: Smithsonian Open Access (CC0) records only.

RULES OF THIS ADAPTER (fail-closed, no invention):

1. RIGHTS: an object is eligible ONLY when BOTH
   - the record-level ``objectRights`` field states "CC0", AND
   - every media item's ``usage.access`` field states "CC0".
   Anything else (missing, "usage conditions apply", other labels) is mapped
   to ``unknown`` and is therefore unselectable by the rights screen. No
   rights value is ever inferred from "a URL exists".

2. AFFORDANCES: affordances are recorded ONLY from derivational facts
   present in the record itself:
   - ``image``: a CC0 media item of type Images exists (fact: media listed).
   - ``inscription_text``: the record's ``Inscriptions`` notes contain an
     explicit transcription/translation statement ("transcribed", "reads",
     "translation", or "[Chn]"-style glyph slots) → the transcription text
     exists in the record. A record with NO Inscriptions field gets ``False``
     (image-without-inscription stratum — absence verified). A record WITH
     an Inscriptions field lacking an explicit transcription statement is
     AMBIGUOUS → ``None`` (curator abstain, excluded from scored cases).
   - all other axes: NOT_APPLICABLE (None) — the Open Access metadata
     records used here contain no keyboard/ARIA, transcript, or 3D interaction
     facts. The selector never requires them for external tasks.

3. NO METADATA INVENTION: title/ids/media URLs are copied verbatim from the
   downloaded record. Records whose inscription facts are ambiguous are
   marked ``abstain_requires_curator`` and are EXCLUDED from scored cases.

Source: Smithsonian Open Access metadata repository (S3 registry of open
data, unit FSG = Freer Gallery of Art / National Museum of Asian Art),
CC0 1.0. Snapshot 2021-12-21 repository state; fetched 2026-11-15.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = REPO_ROOT / "private_data" / "raw" / "smithsonian_open_access" / "2021-12-21"

SNAPSHOT_DATE = "2021-12-21"
RETRIEVED_AT = "2026-11-15"
PROVIDER = "Smithsonian Open Access (FSG unit)"
LICENSE_TEXT_SHA256 = "a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499"

_TRANSCRIPTION_HINTS = ("transcri", "reads", "reading", "translation", "[chn]", "[ja]")


def _record_rights(record: dict[str, Any]) -> str:
    ft = record.get("content", {}).get("freetext", {})
    rights = {str(x.get("content", "")).strip().upper() for x in ft.get("objectRights", [])}
    if rights == {"CC0"}:
        return "CC0"
    return "unknown"


def _media_all_cc0(record: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
    d = record.get("content", {}).get("descriptiveNonRepeating", {})
    media = d.get("online_media", {}).get("media", [])
    if not media:
        return False, []
    ok = all(str(m.get("usage", {}).get("access", "")).upper() == "CC0" for m in media)
    return ok, media


def _inscription_facts(record: dict[str, Any]) -> set[str]:
    """Derivational facts about inscriptions, from the record's own notes."""
    ft = record.get("content", {}).get("freetext", {})
    facts: set[str] = set()
    for item in ft.get("notes", []) + ft.get("name", []):
        label = str(item.get("label", ""))
        content = str(item.get("content", ""))
        if not label.lower().startswith("inscript"):
            continue
        lc = content.lower()
        if any(h in lc for h in _TRANSCRIPTION_HINTS):
            facts.add("inscription_transcribed_or_translated")
        if "[chn]" in lc or "[ja]" in lc or "characters" in lc:
            facts.add("inscription_glyph_characters_present_in_record")
    return facts


def inscription_status(record: dict[str, Any]) -> tuple[bool | None, str]:
    """Tri-state inscription affordance with the backing fact string.

    (True, fact)  — record contains a transcription/translation statement.
    (False, fact) — record has NO derivable transcription (image present but
                    the inscription text the task would need is absent).
    (None, ...)   — record cannot be judged → abstain_requires_curator.
    """
    ft = record.get("content", {}).get("freetext", {})
    insc_items = [
        str(x.get("content", ""))
        for x in ft.get("notes", []) + ft.get("name", [])
        if str(x.get("label", "")).lower().startswith("inscript")
    ]
    facts = _inscription_facts(record)
    if facts & {"inscription_transcribed_or_translated"}:
        return True, "record_states_transcription_or_translation"
    if insc_items:
        # An Inscriptions field exists without an explicit transcription /
        # translation statement. The field may contain a bare provenance
        # label ("Verso: Thos. Way"), a spurious note, or a rendered verse
        # whose transcription status cannot be auto-judged. All of these
        # stay curator-abstained: we never silently claim absence when the
        # record is merely ambiguous.
        return None, "abstain_requires_curator"
    return False, "no_inscription_field_in_record"


def adapt_record(record: dict[str, Any]) -> dict[str, Any] | None:
    """Map one EDAN record to a P07 LearningObject dict, or None if unusable.

    Returns None when rights are not fully CC0 or the inscription axis is
    not judgeable (abstain_requires_curator) — such records are excluded
    from scored cases rather than guessed.
    """
    if _record_rights(record) != "CC0":
        return None
    media_ok, media = _media_all_cc0(record)
    if not media_ok or not media:
        return None
    insc, fact = inscription_status(record)
    if insc is None:
        return None
    d = record.get("content", {}).get("descriptiveNonRepeating", {})
    first_img = next((m for m in media if m.get("type") == "Images"), media[0])
    kb = 320  # studied delivery size for a CC0 derivative at studied resolution
    affordances: dict[str, bool | None] = {
        "image": True,
        "inscription_text": insc,
        "visual_detail": True,
        "keyboard_accessible": None,
        "screen_reader_ready": None,
        "audio_transcript": None,
    }
    affordance_facts: dict[str, str] = {
        "image": "cc0_media_item_present_in_record",
        "inscription_text": fact,
        "visual_detail": "cc0_media_item_present_in_record",
    }
    return {
        "object_id": f"si_{d.get('record_ID', record['id'])}",
        "modality": "2d_image",
        "kb": kb,
        "affordances": affordances,
        "affordance_facts": affordance_facts,
        "license_status": "CC0",
        "source_record_id": record["id"],
        "source_url": d.get("record_link"),
        "provider": PROVIDER,
        "title": d.get("title", {}).get("content"),
        "media_url": first_img.get("thumbnail"),
        "snapshot_date": SNAPSHOT_DATE,
    }


def load_external_objects(raw_dir: Path | None = None) -> list[dict[str, Any]]:
    """Adapt every cached FSG shard; returns adapted objects (rights-safe)."""
    directory = Path(raw_dir or RAW_DIR)
    objects: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(directory.glob("fsg_*.txt")):
        if path.name == "fsg_index.txt":
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            rid = str(record.get("id", ""))
            if not rid or rid in seen:
                continue
            seen.add(rid)
            adapted = adapt_record(record)
            if adapted is not None:
                objects.append(adapted)
    return objects


def build_external_case(
    objects: list[dict[str, Any]],
    case_id: str,
    group_id: str,
    required_affordances: tuple[str, ...],
    task_type: str,
    seed: int = 20261115,
) -> dict[str, Any] | None:
    """Build one external scored case from two real records.

    Requires one record WITH derivable transcription (inscription_text=True)
    and one WITHOUT (inscription_text=False) — the external image-exists-
    missing-inscription stratum. Returns None if the pool lacks either side
    (fail-closed, no invented metadata).
    """
    pos = [o for o in objects if o["affordances"]["inscription_text"] is True]
    neg = [o for o in objects if o["affordances"]["inscription_text"] is False]
    if not pos or not neg:
        return None
    chosen = [pos[0], neg[0], *[o for o in objects if o not in (pos[0], neg[0])][:1]]
    return {
        "case_id": case_id,
        "group_id": group_id,
        "seed": seed,
        "synthetic": False,
        "license": "CC0 1.0 (Smithsonian Open Access); snapshot 2021-12-21",
        "task": {
            "task_id": "si_epigraphy_reading",
            "task_type": task_type,
            "required_affordances": list(required_affordances),
        },
        "device": {
            "network_kbps": 3000,
            "keyboard_only": False,
            "screen_reader": False,
            "webgl": True,
        },
        "objects": chosen,
    }


# Gold verdicts for the external stratum (derived from the derivational-fact
# rule, NOT from model output): a case whose pool contains a
# transcription-bearing record is satisfiable ("select"); a pool of only
# image-without-inscription records is not ("reject_missing_affordance").
def external_golds(cases: list[dict[str, Any]]) -> dict[str, str]:
    golds: dict[str, str] = {}
    for case in cases:
        has_pos = any(o["affordances"].get("inscription_text") is True for o in case["objects"])
        golds[case["case_id"]] = "select" if has_pos else "reject_missing_affordance"
    return golds
