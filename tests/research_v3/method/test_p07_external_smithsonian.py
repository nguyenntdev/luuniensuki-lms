"""P07 external Smithsonian adapter tests: rights honesty, no invention,
derivational-fact affordances, curator abstain for ambiguous records.

These tests read the cached raw snapshot from private_data/raw (gitignored).
If the snapshot is absent the suite skips — no synthetic stand-in is graded.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from research_v3.methods.p07.external import (
    LICENSE_TEXT_SHA256,
    RAW_DIR,
    adapt_record,
    inscription_status,
    load_external_objects,
)


def _raw_available() -> bool:
    return RAW_DIR.is_dir() and any(RAW_DIR.glob("fsg_*.txt"))


pytestmark = pytest.mark.skipif(not _raw_available(), reason="Smithsonian raw snapshot not cached")


def test_license_text_captured_and_hashed():
    lic = RAW_DIR / "si_license_CC0-1.0.txt"
    assert lic.is_file(), "CC0 license text must be captured, not just referenced"
    import hashlib

    assert hashlib.sha256(lic.read_bytes()).hexdigest() == LICENSE_TEXT_SHA256


def test_adapted_objects_are_all_cc0():
    objs = load_external_objects()
    assert objs, "adapter must find CC0 records in the cached snapshot"
    for o in objs:
        assert o["license_status"] == "CC0"
        assert o["provider"].startswith("Smithsonian")
        assert o["source_url"]


def test_no_invented_metadata_fields():
    objs = load_external_objects()
    for o in objs:
        # every object must trace to a real record id and URL copied from EDAN
        assert o["object_id"].startswith("si_fsg_")
        assert o["source_record_id"]
        assert o["media_url"].startswith("https://ids.si.edu/ids/deliveryService?id=")


def test_transcription_bearing_record_classified_true():
    """F1911.145a-c (archaic gu vase) states a transcription + translation."""
    objs = load_external_objects()
    gu = next(o for o in objs if o["object_id"] == "si_fsg_F1911.145a-c")
    assert gu["affordances"]["inscription_text"] is True
    assert gu["affordance_facts"]["inscription_text"] == "record_states_transcription_or_translation"


def test_no_inscription_field_classified_false():
    """F1907.115 (bodhisattva head) has NO Inscriptions field: verified absence."""
    objs = load_external_objects()
    bod = next(o for o in objs if o["object_id"] == "si_fsg_F1907.115")
    assert bod["affordances"]["inscription_text"] is False
    assert bod["affordance_facts"]["inscription_text"] == "no_inscription_field_in_record"


def test_ambiguous_inscription_records_are_curator_abstained():
    """F1909.172 ('Spurious inscription.') and F2017.13.4 (verse rendering
    without explicit transcription statement) must NOT be scored as True or
    False: they are excluded (abstain_requires_curator)."""
    objs = load_external_objects()
    ids = {o["object_id"] for o in objs}
    assert "si_fsg_F1909.172" not in ids
    assert "si_fsg_F2017.13.4" not in ids
    # and directly through the classifier:
    for line in (RAW_DIR / "fsg_01.txt").read_text().splitlines():
        if "F1909.172" in line:
            rec = json.loads(line)
            status, fact = inscription_status(rec)
            assert status is None
            assert fact == "abstain_requires_curator"
            break


def test_non_cc0_record_never_adapted():
    """A record whose rights field is not exactly CC0 is never adapted."""
    fake = {
        "id": "test-non-cc0",
        "content": {
            "freetext": {
                "objectRights": [{"label": "Restrictions & Rights", "content": "CC0"}],
                "notes": [],
            },
            "descriptiveNonRepeating": {
                "record_ID": "T1",
                "title": {"label": "Title", "content": "t"},
                "record_link": "https://asia.si.edu/object/T1/",
                "online_media": {
                    "media": [
                        {
                            "type": "Images",
                            "usage": {"access": "Usage conditions apply"},
                            "thumbnail": "https://ids.si.edu/ids/deliveryService?id=X",
                        }
                    ]
                },
            },
        },
    }
    assert adapt_record(fake) is None


def test_url_present_alone_never_grants_rights():
    """The C0 sanity lesson, enforced at the adapter: a media URL with NO
    usage declaration is 'unknown' rights -> never adapted."""
    fake = {
        "id": "test-no-usage",
        "content": {
            "freetext": {
                "objectRights": [{"label": "Restrictions & Rights", "content": "CC0"}],
                "notes": [],
            },
            "descriptiveNonRepeating": {
                "record_ID": "T2",
                "title": {"label": "Title", "content": "t"},
                "record_link": "https://asia.si.edu/object/T2/",
                "online_media": {
                    "media": [
                        {
                            "type": "Images",
                            "usage": {},
                            "thumbnail": "https://ids.si.edu/ids/deliveryService?id=Y",
                        }
                    ]
                },
            },
        },
    }
    assert adapt_record(fake) is None


def test_external_scored_cases_build_with_positive_and_negative_pools():
    from research_v3.methods.p07.external import build_external_case, external_golds

    objs = load_external_objects()
    pos = next(o for o in objs if o["affordances"]["inscription_text"] is True)
    negs = [o for o in objs if o["affordances"]["inscription_text"] is False][:2]
    case = build_external_case(
        [pos, *negs], "X-POS", "GX", ("inscription_text",), "analyze_epigraphy"
    )
    assert case is not None
    neg_case = {
        **case,
        "case_id": "X-NEG",
        "objects": negs,
    }
    golds = external_golds([case, neg_case])
    assert golds["X-POS"] == "select"
    assert golds["X-NEG"] == "reject_missing_affordance"


def test_external_dataset_file_matches_derivational_rule():
    from research_v3.methods.p07.runner import gold_from_cases, load_jsonl

    path = Path(__file__).resolve().parents[3] / (
        "research_v3/methods/p07/data/smithsonian_fsg_external.jsonl"
    )
    cases = load_jsonl(path)
    golds = gold_from_cases(cases)
    assert cases
    for c in cases:
        has_pos = any(
            o["affordances"].get("inscription_text") is True for o in c["objects"]
        )
        expected = "select" if has_pos else "reject_missing_affordance"
        assert golds[c["case_id"]] == expected
        assert c["synthetic"] is False
        assert c["license"].startswith("CC0 1.0 (Smithsonian Open Access)")
