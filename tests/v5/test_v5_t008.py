"""
Tests for W00-A08 (V5-T008): 162 Relic Dataset Inventory.
Verifies the complete dataset of 9 Urns and 162 motifs in data/*Data*Dinh.json,
ensuring zero loss, 100% 3D coordinate coverage, and proper flagging of unvalidated Hán-Nôm.
"""

import json
from pathlib import Path
import pytest

ROOT_DIR = Path("/home/clue/Documents/luuniensuki-lms")
INVENTORY_PATH = ROOT_DIR / "artifacts/implementation/W00/W00_A08_162_relic_inventory.json"


def test_inventory_artifact_structure():
    """Verify inventory artifact exists and contains required metadata."""
    assert INVENTORY_PATH.exists(), f"Missing relic inventory at {INVENTORY_PATH}"
    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["version"] == "v6.0-w00"
    assert data["baseline_source_sha"] == "54da2beb71f3df70e1f00b215ae0fb1a850eb263"
    assert data["summary"]["total_urns"] == 9
    assert data["summary"]["total_motifs"] == 162
    assert data["summary"]["unique_motif_ids"] == 162
    assert data["summary"]["coordinates_coverage"] == "162/162"


def test_urns_count_and_distribution():
    """Verify all 9 urns are accounted for with exactly 18 motifs each."""
    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data["urns"]) == 9
    for urn in data["urns"]:
        assert urn["motif_count"] == 18, f"Urn {urn['slug']} has {urn['motif_count']} motifs, expected 18"


def test_all_162_motifs_have_coordinates():
    """Verify every motif in the inventory has corresponding 3D coordinates."""
    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    missing_coords = [m["id"] for m in data["motifs"] if not m["has_coordinates"]]
    assert not missing_coords, f"Motifs missing 3D coordinates: {missing_coords}"


def test_unvalidated_han_nom_properly_flagged():
    """Negative test: Ensure missing or unvalidated Hán-Nôm entries are flagged and not accepted as valid."""
    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    missing_items = data["missing_han_nom_motifs"]
    assert len(missing_items) == 4, f"Expected exactly 4 missing Hán-Nôm items, found {len(missing_items)}"

    missing_ids = {item["id"] for item in missing_items}
    expected_missing = {"urn_nghi_dinh_03", "urn_thuan_dinh_13", "urn_tuyen_dinh_11", "urn_huyen_dinh_12"}
    assert missing_ids == expected_missing

    # Ensure none of these 4 are falsely marked as having Hán-Nôm in the motif list
    for motif in data["motifs"]:
        if motif["id"] in expected_missing:
            assert motif["has_han_nom"] is False
            assert not motif["name_han_nom"].strip()


def test_categories_and_rarity_valid():
    """Verify that all motifs belong to authorized domain categories and rarity levels."""
    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    valid_categories = {
        "thao_moc", "vo_bi", "dong_vat", "thien_van",
        "nong_nghiep", "giao_thuong", "dia_ly", "kien_truc", "linh_thu"
    }

    valid_rarities = {"common", "uncommon", "rare", "epic", "legendary"}

    for m in data["motifs"]:
        assert m["category"] in valid_categories, f"Invalid category '{m['category']}' on motif {m['id']}"
        assert m["rarity"] in valid_rarities, f"Invalid rarity '{m['rarity']}' on motif {m['id']}"
