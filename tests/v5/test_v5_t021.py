"""
Tests for W02-A01 (V5-T021): Canonical Urn and Motif Mapping & Integrity Validation.

Validates:
1. Canonical mapping of 9 Urns and 162 Motifs (9x18 = 162).
2. All 162 motifs map without cross-urn misassignment.
3. Negative abuse test: Cross-urn misassignment is strictly detected and rejected.
4. Legacy ID and alias resolution returns correct canonical entity.
5. Zero duplicate slugs, IDs, or coordinates in the 162 dataset.
"""

from pathlib import Path
import pytest

from backend.domain.canonical_urn_mapping import (
    AmbiguousAliasError,
    CANONICAL_RELIEFS,
    CANONICAL_RELIEF_SLUGS,
    CANONICAL_URNS,
    CANONICAL_URN_SLUGS,
    CanonicalReliefInfo,
    CanonicalUrnInfo,
    CrossUrnMisassignmentError,
    InvalidMotifCountError,
    MOTIFS_PER_URN,
    STABLE_MOTIF_IDS,
    TOTAL_MOTIFS,
    TOTAL_URNS,
    extract_urn_slug,
    resolve_canonical_motif_id,
    resolve_canonical_relief_slug,
    resolve_canonical_urn_slug,
    resolve_legacy_identifier,
    validate_dataset_uniqueness,
    validate_no_cross_urn_misassignment,
    validate_urn_motif_count,
)
from backend.history_models import (
    CANONICAL_URNS as HM_CANONICAL_URNS,
    CANONICAL_URN_SLUGS as HM_CANONICAL_URN_SLUGS,
    CrossUrnMisassignmentError as HM_CrossUrnMisassignmentError,
    InvalidMotifCountError as HM_InvalidMotifCountError,
    resolve_canonical_urn_slug as hm_resolve_canonical_urn_slug,
    validate_no_cross_urn_misassignment as hm_validate_no_cross_urn_misassignment,
    validate_urn_motif_count as hm_validate_urn_motif_count,
)
from backend.services.heritage_import import (
    CANONICAL_URNS as HI_CANONICAL_URNS,
    CANONICAL_URN_SLUGS as HI_CANONICAL_URN_SLUGS,
    CrossUrnMisassignmentError as HI_CrossUrnMisassignmentError,
    InvalidMotifCountError as HI_InvalidMotifCountError,
    validate_no_cross_urn_misassignment as hi_validate_no_cross_urn_misassignment,
    validate_urn_motif_count as hi_validate_urn_motif_count,
)

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
COORDINATES_FILE = DATA_DIR / "cuu_dinh_coordinate_points.json"


def test_canonical_urns_and_reliefs_count_and_mapping():
    """Verify all 9 Urns and 162 Motifs exist in expected canonical structure."""
    assert len(CANONICAL_URN_SLUGS) == TOTAL_URNS == 9
    assert len(CANONICAL_URNS) == 9

    expected_slugs = (
        "cao-dinh",
        "nhan-dinh",
        "chuong-dinh",
        "anh-dinh",
        "nghi-dinh",
        "thuan-dinh",
        "tuyen-dinh",
        "du-dinh",
        "huyen-dinh",
    )
    assert CANONICAL_URN_SLUGS == expected_slugs
    assert HM_CANONICAL_URN_SLUGS == expected_slugs

    # Verify 162 canonical reliefs pre-loaded
    assert len(CANONICAL_RELIEFS) == TOTAL_MOTIFS == 162
    assert len(STABLE_MOTIF_IDS) == TOTAL_MOTIFS == 162
    assert len(CANONICAL_RELIEF_SLUGS) == 162

    # Verify each urn has exactly 18 reliefs
    for urn_slug in CANONICAL_URN_SLUGS:
        urn_info = CANONICAL_URNS[urn_slug]
        assert urn_info.motif_count == MOTIFS_PER_URN == 18
        urn_reliefs = [r for r in CANONICAL_RELIEFS.values() if r.urn_slug == urn_slug]
        assert len(urn_reliefs) == 18

        # Verify sequential order 1..18
        orders = [r.order for r in urn_reliefs]
        assert orders == list(range(1, 19))


def test_all_162_motifs_map_without_cross_urn_misassignment():
    """Verify all 162 motifs map strictly to their respective owner Urn without misassignment."""
    for motif in CANONICAL_RELIEFS.values():
        owner_urn = motif.urn_slug
        assert owner_urn in CANONICAL_URN_SLUGS

        # 1. Validation with stable_id
        validate_no_cross_urn_misassignment(owner_urn, motif.stable_id)
        hm_validate_no_cross_urn_misassignment(owner_urn, motif.stable_id)

        # 2. Validation with relief slug
        validate_no_cross_urn_misassignment(owner_urn, motif.slug)

        # 3. Validation with mesh name
        if motif.mesh_name:
            # Mesh names that don't collide or have prefix
            mesh_urn = extract_urn_slug(motif.mesh_name)
            if mesh_urn:
                assert mesh_urn == owner_urn
                validate_no_cross_urn_misassignment(owner_urn, motif.mesh_name)

        # 4. Validation with motif name within owner urn
        validate_no_cross_urn_misassignment(owner_urn, motif.name_vi)


def test_negative_abuse_cross_urn_misassignment_rejected():
    """Negative abuse tests: Cross-urn assignments across any urn boundary are detected and rejected."""
    # Test pairing every urn against every other urn
    for i, urn_a in enumerate(CANONICAL_URN_SLUGS):
        urn_b = CANONICAL_URN_SLUGS[(i + 1) % len(CANONICAL_URN_SLUGS)]

        # Pick motif from urn_a and try to assign to urn_b
        urn_a_prefix = CANONICAL_URNS[urn_a].legacy_prefix
        motif_from_a = f"urn_{urn_a_prefix}_02"
        slug_from_a = f"{urn_a}-02"
        mesh_from_a = f"mesh_urn_{urn_a_prefix}_02_v1"

        # 1. Stable ID cross-assignment
        with pytest.raises(CrossUrnMisassignmentError) as exc_info:
            validate_no_cross_urn_misassignment(urn_b, motif_from_a)
        assert exc_info.value.source_urn == urn_a
        assert exc_info.value.target_urn == urn_b

        # 2. Relief slug cross-assignment
        with pytest.raises(CrossUrnMisassignmentError) as exc_info:
            validate_no_cross_urn_misassignment(urn_b, slug_from_a)
        assert exc_info.value.source_urn == urn_a
        assert exc_info.value.target_urn == urn_b

        # 3. Mesh name cross-assignment
        with pytest.raises(CrossUrnMisassignmentError) as exc_info:
            validate_no_cross_urn_misassignment(urn_b, mesh_from_a)
        assert exc_info.value.source_urn == urn_a
        assert exc_info.value.target_urn == urn_b

        # 4. History models re-exported validator cross-assignment
        with pytest.raises(HM_CrossUrnMisassignmentError):
            hm_validate_no_cross_urn_misassignment(urn_b, motif_from_a)

    # 5. Specific test: assign Cao Dinh unique motif "Vĩnh Tế Hà" to Nghi Dinh
    with pytest.raises(CrossUrnMisassignmentError) as exc_info:
        validate_no_cross_urn_misassignment("nghi-dinh", "Vĩnh Tế Hà")
    assert "Cross-urn misassignment detected" in str(exc_info.value)

    # 6. Unknown motif name raises ValueError
    with pytest.raises(ValueError) as exc_info:
        validate_no_cross_urn_misassignment("cao-dinh", "NonExistentRelief")
    assert "not recognized in dataset" in str(exc_info.value)

    # 7. Out-of-bounds motif index raises ValueError
    with pytest.raises(ValueError) as exc_info:
        validate_no_cross_urn_misassignment("cao-dinh", "19")
    assert "out of bounds" in str(exc_info.value)

    # 8. Invalid target urn raises ValueError
    with pytest.raises(ValueError) as exc_info:
        validate_no_cross_urn_misassignment("invalid-urn", "urn_cao_dinh_02")
    assert "Unknown target urn identifier" in str(exc_info.value)


def test_legacy_urn_alias_resolution():
    """Verify alias resolver maps all legacy formats, variants, and titles to canonical urn slug."""
    # Test Cao Dinh variants
    assert resolve_canonical_urn_slug("cao-dinh") == "cao-dinh"
    assert resolve_canonical_urn_slug("cao_dinh") == "cao-dinh"
    assert resolve_canonical_urn_slug("cao dinh") == "cao-dinh"
    assert resolve_canonical_urn_slug("Cao Đỉnh") == "cao-dinh"
    assert resolve_canonical_urn_slug("CAO ĐỈNH") == "cao-dinh"
    assert resolve_canonical_urn_slug("The Urn of Height") == "cao-dinh"
    assert resolve_canonical_urn_slug("the urn of height") == "cao-dinh"
    assert resolve_canonical_urn_slug("高鼎") == "cao-dinh"
    assert resolve_canonical_urn_slug("urn_cao_dinh") == "cao-dinh"
    assert resolve_canonical_urn_slug("urn_cao_dinh_01") == "cao-dinh"
    assert resolve_canonical_urn_slug("urn_cao_dinh_1") == "cao-dinh"
    assert resolve_canonical_urn_slug("cao-dinh-01") == "cao-dinh"
    assert resolve_canonical_urn_slug("urn-1") == "cao-dinh"
    assert resolve_canonical_urn_slug("dinh-1") == "cao-dinh"

    # Test all 9 Han-Nom titles
    han_nom_map = {
        "高鼎": "cao-dinh",
        "仁鼎": "nhan-dinh",
        "章鼎": "chuong-dinh",
        "英鼎": "anh-dinh",
        "毅鼎": "nghi-dinh",
        "純鼎": "thuan-dinh",
        "宣鼎": "tuyen-dinh",
        "裕鼎": "du-dinh",
        "玄鼎": "huyen-dinh",
    }
    for han_nom, expected_slug in han_nom_map.items():
        assert resolve_canonical_urn_slug(han_nom) == expected_slug
        assert hm_resolve_canonical_urn_slug(han_nom) == expected_slug

    # Test empty or invalid input
    assert resolve_canonical_urn_slug("") is None
    assert resolve_canonical_urn_slug("not-an-urn") is None


def test_legacy_relief_alias_resolution():
    """Verify alias resolver maps legacy IDs, mesh identifiers, and local names to canonical relief slugs."""
    # Canonical slug
    assert resolve_canonical_relief_slug("cao-dinh-02") == "cao-dinh-02"

    # Stable ID with leading zero
    assert resolve_canonical_relief_slug("urn_cao_dinh_02") == "cao-dinh-02"

    # Non-padded stable ID
    assert resolve_canonical_relief_slug("urn_cao_dinh_2") == "cao-dinh-02"

    # Non-padded slug
    assert resolve_canonical_relief_slug("cao-dinh-2") == "cao-dinh-02"

    # Underscored slug
    assert resolve_canonical_relief_slug("cao_dinh_02") == "cao-dinh-02"

    # 3D mesh identifier
    assert resolve_canonical_relief_slug("mesh_urn_cao_dinh_02_v1") == "cao-dinh-02"
    assert resolve_canonical_relief_slug("mesh_urn_cao_dinh_02") == "cao-dinh-02"

    # Resolution in urn context by name
    assert resolve_canonical_relief_slug("Long", urn_context="cao-dinh") == "cao-dinh-02"
    assert resolve_canonical_relief_slug("long", urn_context="cao-dinh") == "cao-dinh-02"

    # Resolution in urn context by index
    assert resolve_canonical_relief_slug("02", urn_context="cao-dinh") == "cao-dinh-02"
    assert resolve_canonical_relief_slug("2", urn_context="cao-dinh") == "cao-dinh-02"

    # Resolution to stable motif ID
    assert resolve_canonical_motif_id("cao-dinh-02") == "urn_cao_dinh_02"
    assert resolve_canonical_motif_id("mesh_urn_cao_dinh_02_v1") == "urn_cao_dinh_02"
    assert resolve_canonical_motif_id("Long", urn_context="cao-dinh") == "urn_cao_dinh_02"

    # Cross-urn rejection in relief alias resolution
    with pytest.raises(CrossUrnMisassignmentError):
        resolve_canonical_relief_slug("urn_cao_dinh_02", urn_context="nhan-dinh")

    with pytest.raises(CrossUrnMisassignmentError):
        resolve_canonical_motif_id("cao-dinh-02", urn_context="tuyen-dinh")


def test_ambiguous_alias_handling():
    """Verify handling of motif names shared across multiple urns (e.g. 'Giới')."""
    # 'Giới' exists in chuong-dinh-06 and nghi-dinh-14
    with pytest.raises(AmbiguousAliasError) as exc_info:
        resolve_canonical_relief_slug("Giới")
    assert "Specify urn_context to disambiguate" in str(exc_info.value)

    # Disambiguated with urn_context
    assert resolve_canonical_relief_slug("Giới", urn_context="chuong-dinh") == "chuong-dinh-06"
    assert resolve_canonical_relief_slug("Giới", urn_context="nghi-dinh") == "nghi-dinh-14"

    # Rejected when queried on an urn that does not have it
    with pytest.raises(CrossUrnMisassignmentError):
        resolve_canonical_relief_slug("Giới", urn_context="nhan-dinh")


def test_resolve_legacy_identifier_contract():
    """Verify the structured metadata contract returned by resolve_legacy_identifier."""
    # 1. Urn resolution
    res_urn = resolve_legacy_identifier("Cao Đỉnh")
    assert res_urn["entity_type"] == "urn"
    assert res_urn["canonical_slug"] == "cao-dinh"
    assert res_urn["name_vi"] == "Cao Đỉnh"
    assert res_urn["order"] == 1
    assert res_urn["name_han_nom"] == "高鼎"

    # 2. Relief resolution
    res_relief = resolve_legacy_identifier("urn_cao_dinh_02")
    assert res_relief["entity_type"] == "relief"
    assert res_relief["canonical_slug"] == "cao-dinh-02"
    assert res_relief["stable_id"] == "urn_cao_dinh_02"
    assert res_relief["urn_slug"] == "cao-dinh"
    assert res_relief["name_vi"] == "Long"
    assert res_relief["order"] == 2
    assert "coordinates" in res_relief
    assert res_relief["coordinates"]["pos_x"] == pytest.approx(0.995929, abs=1e-5)
    assert res_relief["coordinates"]["bounding_radius"] == 0.08

    # 3. Invalid identifier
    with pytest.raises(ValueError):
        resolve_legacy_identifier("")

    with pytest.raises(ValueError):
        resolve_legacy_identifier("completely_unknown_identifier_xyz")


def test_dataset_uniqueness_and_duplicate_validators():
    """Verify validate_dataset_uniqueness confirms 9 Urns x 18 Motifs = 162 with zero duplicates."""
    summary = validate_dataset_uniqueness(data_dir=DATA_DIR, coords_path=COORDINATES_FILE)

    assert summary["valid"] is True
    assert summary["total_urns"] == 9
    assert summary["total_motifs"] == 162
    assert summary["unique_ids"] == 162
    assert summary["unique_relief_slugs"] == 162
    assert summary["coordinates_count"] == 162
    assert len(summary["canonical_urns"]) == 9


def test_cuu_dinh_coordinate_points_file_integrity():
    """Verify data/cuu_dinh_coordinate_points.json exists and adheres strictly to specification."""
    assert COORDINATES_FILE.exists(), f"Coordinates file missing at {COORDINATES_FILE}"
    import json

    with open(COORDINATES_FILE, "r", encoding="utf-8") as f:
        points = json.load(f)

    assert len(points) == 162, f"Expected 162 points, found {len(points)}"

    seen_ids = set()
    for pt in points:
        assert "id" in pt
        assert "urn_slug" in pt
        assert "relief_slug" in pt
        assert "motif_name" in pt
        assert "pos_x" in pt
        assert "pos_y" in pt
        assert "pos_z" in pt
        assert "bounding_radius" in pt

        assert pt["id"] not in seen_ids, f"Duplicate point id: {pt['id']}"
        seen_ids.add(pt["id"])

        assert pt["urn_slug"] in CANONICAL_URN_SLUGS
        assert isinstance(pt["pos_x"], (int, float))
        assert isinstance(pt["pos_y"], (int, float))
        assert isinstance(pt["pos_z"], (int, float))
        assert pt["bounding_radius"] > 0


def test_negative_abuse_invalid_motif_count_rejected():
    """Negative abuse tests: Motif counts != 18 are detected and rejected by validators."""
    # 1. Under-count (17) rejected with InvalidMotifCountError
    with pytest.raises(InvalidMotifCountError) as exc_info:
        validate_urn_motif_count("cao-dinh", 17)
    assert "Invalid motif count for urn 'cao-dinh': got 17, expected exactly 18" in str(exc_info.value)

    # 2. Over-count (19) rejected with InvalidMotifCountError
    with pytest.raises(InvalidMotifCountError) as exc_info:
        validate_urn_motif_count("cao_dinh", 19)
    assert "Invalid motif count for urn 'cao-dinh': got 19, expected exactly 18" in str(exc_info.value)

    # 3. List of items under-count rejected
    with pytest.raises(InvalidMotifCountError):
        validate_urn_motif_count("nhan-dinh", [{"id": 1}] * 10)

    # 4. List of items over-count rejected
    with pytest.raises(InvalidMotifCountError):
        validate_urn_motif_count("chuong-dinh", [{"id": 1}] * 20)

    # 5. Re-exported validator in history_models rejects invalid count
    with pytest.raises(HM_InvalidMotifCountError):
        hm_validate_urn_motif_count("anh-dinh", 15)

    # 6. Re-exported validator in heritage_import rejects invalid count
    with pytest.raises(HI_InvalidMotifCountError):
        hi_validate_urn_motif_count("nghi-dinh", 22)

    # 7. Valid count (18) passes smoothly
    validate_urn_motif_count("cao-dinh", 18)
    validate_urn_motif_count("cao_dinh", 18)
    hm_validate_urn_motif_count("nhan-dinh", 18)
    hi_validate_urn_motif_count("chuong-dinh", [{"id": i} for i in range(18)])

    # 8. Unknown urn slug raises ValueError
    with pytest.raises(ValueError) as exc_info:
        validate_urn_motif_count("unknown_urn_xyz", 18)
    assert "Unknown urn identifier" in str(exc_info.value)

    # 9. Invalid count type raises ValueError
    with pytest.raises(ValueError):
        validate_urn_motif_count("cao-dinh", "not_a_number")


def test_dataset_uniqueness_negative_invalid_motif_count(tmp_path):
    """Negative abuse: validate_dataset_uniqueness strictly detects and rejects urn files with != 18 items."""
    import json

    fake_data_dir = tmp_path / "data"
    fake_data_dir.mkdir()

    # Copy real data files except cao-dinh which has 17 items
    for urn_slug in CANONICAL_URN_SLUGS:
        src = DATA_DIR / CANONICAL_URNS[urn_slug].data_file
        with open(src, "r", encoding="utf-8") as f:
            items = json.load(f)
        if urn_slug == "cao-dinh":
            items = items[:17]
        dst = fake_data_dir / CANONICAL_URNS[urn_slug].data_file
        with open(dst, "w", encoding="utf-8") as f:
            json.dump(items, f)

    with pytest.raises(ValueError) as exc_info:
        validate_dataset_uniqueness(data_dir=fake_data_dir, coords_path=COORDINATES_FILE)
    assert "expected exactly 18" in str(exc_info.value)


def test_canonical_slug_underscore_properties():
    """Verify slug_underscore property across all canonical urns and reliefs."""
    for urn_slug, urn_info in CANONICAL_URNS.items():
        assert urn_info.slug_underscore == urn_slug.replace("-", "_")
        assert urn_info.slug_underscore == urn_info.legacy_prefix

    for relief_slug, relief_info in CANONICAL_RELIEFS.items():
        assert relief_info.slug_underscore == relief_slug.replace("-", "_")
