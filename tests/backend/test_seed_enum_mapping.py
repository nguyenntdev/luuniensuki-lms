import json
from pathlib import Path

from backend.models import MotifCategory
from backend.models import MotifRarity
from backend.seed import coerce_enum


def test_coerce_enum_accepts_common_variants():
    category, ok = coerce_enum(MotifCategory, "thao_moc", MotifCategory.thao_moc)
    assert category == MotifCategory.thao_moc
    assert ok is True

    category, ok = coerce_enum(MotifCategory, "Thảo mộc", MotifCategory.thao_moc)
    assert category == MotifCategory.thao_moc
    assert ok is True

    rarity, ok = coerce_enum(MotifRarity, "Legendary", MotifRarity.common)
    assert rarity == MotifRarity.legendary
    assert ok is True

    rarity, ok = coerce_enum(MotifRarity, "mythic", MotifRarity.common)
    assert rarity == MotifRarity.common
    assert ok is False


def test_seed_json_category_and_rarity_map_cleanly():
    repo_root = Path(__file__).resolve().parents[2]
    data_dir = repo_root / "data"
    assert data_dir.exists()

    for file_path in sorted(data_dir.glob("*.json")):
        data = json.loads(file_path.read_text(encoding="utf-8"))
        assert isinstance(data, list)

        for item in data:
            category_raw = item.get("category")
            if category_raw is not None:
                _, ok = coerce_enum(MotifCategory, category_raw, MotifCategory.thao_moc)
                assert ok is True

            rarity_raw = item.get("rarity")
            if rarity_raw is not None:
                _, ok = coerce_enum(MotifRarity, rarity_raw, MotifRarity.common)
                assert ok is True

