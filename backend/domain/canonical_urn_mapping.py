# -*- coding: utf-8 -*-
"""Canonical Urn and Motif Mapping & Validation Domain (Cửu Đỉnh 9x18 = 162).

Enforces:
1. Canonical Urn Slugs (9): cao-dinh, nhan-dinh, chuong-dinh, anh-dinh, nghi-dinh,
   thuan-dinh, tuyen-dinh, du-dinh, huyen-dinh.
2. Canonical Relief Slugs (162): {urn_slug}-{01..18} (e.g. cao-dinh-01..18).
3. Stable Motif Identifiers (162): urn_{urn_slug_underscore}_{01..18} matching
   data/cuu_dinh_coordinate_points.json and data/*Data*Dinh.json.
4. Legacy redirect alias resolver with cross-urn misassignment prevention.
5. Strict dataset duplicate and integrity validators.
"""
from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("luuniensuki.canonical_urn_mapping")

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
COORDINATES_FILE = DATA_DIR / "cuu_dinh_coordinate_points.json"

TOTAL_URNS = 9
MOTIFS_PER_URN = 18
TOTAL_MOTIFS = 162


class CrossUrnMisassignmentError(ValueError):
    """Raised when an identifier or entity is misassigned across urn boundaries."""

    def __init__(
        self,
        message: str,
        source_urn: Optional[str] = None,
        target_urn: Optional[str] = None,
        identifier: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.source_urn = source_urn
        self.target_urn = target_urn
        self.identifier = identifier


class AmbiguousAliasError(ValueError):
    """Raised when an alias maps to multiple entities and requires an urn_context."""
    pass


class InvalidMotifCountError(ValueError):
    """Raised when an Urn has an invalid number of motifs (must be exactly 18)."""
    pass


@dataclass(frozen=True)
class CanonicalUrnInfo:
    slug: str
    order: int
    name_vi: str
    name_en: str
    name_han_nom: str
    legacy_prefix: str
    data_file: str
    coord_file: str
    model_3d: str
    reign_title: str
    temple_name: str
    motif_count: int = 18

    @property
    def slug_underscore(self) -> str:
        return self.slug.replace("-", "_")


@dataclass(frozen=True)
class CanonicalReliefInfo:
    slug: str
    stable_id: str
    urn_slug: str
    order: int
    name_vi: str
    name_en: Optional[str] = None
    name_han_nom: Optional[str] = None
    category: Optional[str] = None
    rarity: Optional[str] = None
    mesh_name: Optional[str] = None
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    pos_z: Optional[float] = None
    bounding_radius: Optional[float] = None

    @property
    def slug_underscore(self) -> str:
        return self.slug.replace("-", "_")


CANONICAL_URN_SLUGS: tuple[str, ...] = (
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

URN_ORDER: dict[str, int] = {slug: idx + 1 for idx, slug in enumerate(CANONICAL_URN_SLUGS)}

CANONICAL_URNS: dict[str, CanonicalUrnInfo] = {
    "cao-dinh": CanonicalUrnInfo(
        slug="cao-dinh",
        order=1,
        name_vi="Cao Đỉnh",
        name_en="The Urn of Height",
        name_han_nom="高鼎",
        legacy_prefix="cao_dinh",
        data_file="05_Data_CaoDinh.json",
        coord_file="motif-coordinates-cao-dinh.json",
        model_3d="CAO-DINH-v1.glb",
        reign_title="Gia Long",
        temple_name="Thế Tổ Cao Hoàng đế",
    ),
    "nhan-dinh": CanonicalUrnInfo(
        slug="nhan-dinh",
        order=2,
        name_vi="Nhân Đỉnh",
        name_en="The Urn of Benevolence",
        name_han_nom="仁鼎",
        legacy_prefix="nhan_dinh",
        data_file="06_Data_NhanDinh.json",
        coord_file="motif-coordinates-nhan-dinh.json",
        model_3d="NHAN-DINH-v1.glb",
        reign_title="Minh Mạng",
        temple_name="Thánh Tổ Nhân Hoàng đế",
    ),
    "chuong-dinh": CanonicalUrnInfo(
        slug="chuong-dinh",
        order=3,
        name_vi="Chương Đỉnh",
        name_en="The Urn of Clarity",
        name_han_nom="章鼎",
        legacy_prefix="chuong_dinh",
        data_file="07_Data_ChuongDinh.json",
        coord_file="motif-coordinates-chuong-dinh.json",
        model_3d="CHUONG-DINH-v1.glb",
        reign_title="Thiệu Trị",
        temple_name="Hiến Tổ Chương Hoàng đế",
    ),
    "anh-dinh": CanonicalUrnInfo(
        slug="anh-dinh",
        order=4,
        name_vi="Anh Đỉnh",
        name_en="The Urn of Heroism",
        name_han_nom="英鼎",
        legacy_prefix="anh_dinh",
        data_file="08_Data_AnhDinh.json",
        coord_file="motif-coordinates-anh-dinh.json",
        model_3d="ANH-DINH-v1.glb",
        reign_title="Tự Đức",
        temple_name="Dực Tông Anh Hoàng đế",
    ),
    "nghi-dinh": CanonicalUrnInfo(
        slug="nghi-dinh",
        order=5,
        name_vi="Nghị Đỉnh",
        name_en="The Urn of Resolution",
        name_han_nom="毅鼎",
        legacy_prefix="nghi_dinh",
        data_file="09_Data_NghiDinh.json",
        coord_file="motif-coordinates-nghi-dinh.json",
        model_3d="NGHI-DINH-v1.glb",
        reign_title="Kiến Phúc",
        temple_name="Giản Tông Nghị Hoàng đế",
    ),
    "thuan-dinh": CanonicalUrnInfo(
        slug="thuan-dinh",
        order=6,
        name_vi="Thuần Đỉnh",
        name_en="The Urn of Purity",
        name_han_nom="純鼎",
        legacy_prefix="thuan_dinh",
        data_file="10_Data_ThuanDinh.json",
        coord_file="motif-coordinates-thuan-dinh.json",
        model_3d="THUAN-DINH-v1.glb",
        reign_title="Đồng Khánh",
        temple_name="Cảnh Tông Thuần Hoàng đế",
    ),
    "tuyen-dinh": CanonicalUrnInfo(
        slug="tuyen-dinh",
        order=7,
        name_vi="Tuyên Đỉnh",
        name_en="The Urn of Proclamation",
        name_han_nom="宣鼎",
        legacy_prefix="tuyen_dinh",
        data_file="11_Data_TuyenDinh.json",
        coord_file="motif-coordinates-tuyen-dinh.json",
        model_3d="TUYEN-DINH-v1.glb",
        reign_title="Khải Định",
        temple_name="Hoằng Tông Tuyên Hoàng đế",
    ),
    "du-dinh": CanonicalUrnInfo(
        slug="du-dinh",
        order=8,
        name_vi="Dụ Đỉnh",
        name_en="The Urn of Abundance",
        name_han_nom="裕鼎",
        legacy_prefix="du_dinh",
        data_file="12_Data_DuDinh.json",
        coord_file="motif-coordinates-du-dinh.json",
        model_3d="DU-DINH-v1.glb",
        reign_title="Duy Tân",
        temple_name="Dụ Hoàng đế (dự định)",
    ),
    "huyen-dinh": CanonicalUrnInfo(
        slug="huyen-dinh",
        order=9,
        name_vi="Huyền Đỉnh",
        name_en="The Urn of Profundity",
        name_han_nom="玄鼎",
        legacy_prefix="huyen_dinh",
        data_file="13_Data_HuyenDinh.json",
        coord_file="motif-coordinates-huyen-dinh.json",
        model_3d="HUYEN-DINH-v1.glb",
        reign_title="Hàm Nghi",
        temple_name="Huyền Hoàng đế (dự định)",
    ),
}


def _normalize_str(text: str) -> str:
    """Strip diacritics and non-alphanumerics for robust fuzzy matching."""
    normalized = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    ascii_clean = stripped.lower().replace("đ", "d").replace("'", "").replace('"', "")
    return re.sub(r"[^a-z0-9]+", "-", ascii_clean).strip("-")


def _build_urn_alias_index() -> dict[str, str]:
    """Index all variations of Urn identifiers pointing to canonical urn_slug."""
    index: dict[str, str] = {}
    for slug, info in CANONICAL_URNS.items():
        # Canonical & variants
        index[slug] = slug
        index[slug.replace("-", "_")] = slug
        index[slug.replace("-", " ")] = slug
        index[f"urn_{info.legacy_prefix}"] = slug
        index[f"urn_{info.legacy_prefix}_01"] = slug
        index[f"urn_{info.legacy_prefix}_1"] = slug
        index[f"{slug}-01"] = slug
        index[f"{slug}-1"] = slug

        # Names
        index[info.name_vi.lower()] = slug
        index[_normalize_str(info.name_vi)] = slug
        index[info.name_han_nom.strip()] = slug
        index[info.name_en.lower()] = slug
        index[_normalize_str(info.name_en)] = slug

        # Order aliases
        index[f"urn-{info.order}"] = slug
        index[f"urn_{info.order}"] = slug
        index[f"dinh-{info.order}"] = slug
        index[f"dinh_{info.order}"] = slug
    return index


URN_ALIAS_INDEX: dict[str, str] = _build_urn_alias_index()


def extract_urn_slug(identifier: str) -> Optional[str]:
    """Extract intrinsic urn slug from an identifier if it encodes an urn."""
    clean = identifier.strip().lower()

    # Numeric indices do not encode an intrinsic urn
    if clean.isdigit():
        return None

    # Exact alias check
    if clean in URN_ALIAS_INDEX:
        return URN_ALIAS_INDEX[clean]

    # Pattern check: urn_<prefix>_<number> or mesh_urn_<prefix>_<number>
    m = re.match(r"^(?:mesh_)?urn_([a-z]+_[a-z]+)(?:_\d+)?(?:_v\d+)?$", clean)
    if m:
        prefix = m.group(1).replace("_", "-")
        if prefix in CANONICAL_URN_SLUGS:
            return prefix

    # Pattern check: <slug>-<number>
    m = re.match(r"^([a-z]+-[a-z]+)(?:-\d+)?$", clean)
    if m:
        prefix = m.group(1)
        if prefix in CANONICAL_URN_SLUGS:
            return prefix

    # Pattern check: <prefix>_<number>
    m = re.match(r"^([a-z]+_[a-z]+)(?:_\d+)?$", clean)
    if m:
        prefix = m.group(1).replace("_", "-")
        if prefix in CANONICAL_URN_SLUGS:
            return prefix

    return None


def resolve_canonical_urn_slug(alias: str) -> Optional[str]:
    """Resolve an alias, name, or identifier to canonical urn slug (e.g. 'cao-dinh')."""
    if not alias:
        return None
    raw = alias.strip()
    clean = raw.lower()

    if clean in URN_ALIAS_INDEX:
        return URN_ALIAS_INDEX[clean]

    norm = _normalize_str(raw)
    if norm in URN_ALIAS_INDEX:
        return URN_ALIAS_INDEX[norm]

    # Check extracted prefix
    extracted = extract_urn_slug(clean)
    if extracted:
        return extracted

    return None


def _load_canonical_dataset(
    data_dir: Optional[Path] = None,
    coords_path: Optional[Path] = None,
) -> tuple[dict[str, CanonicalReliefInfo], dict[str, CanonicalReliefInfo]]:
    """Load and index all 162 motifs from data files and coordinates."""
    d_dir = data_dir or DATA_DIR
    c_path = coords_path or COORDINATES_FILE

    coords_by_id: dict[str, dict[str, Any]] = {}
    if c_path.exists():
        try:
            with open(c_path, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            for c in c_data:
                coords_by_id[c["id"]] = c
        except Exception as e:
            logger.warning("Could not read coordinates from %s: %s", c_path, e)

    by_slug: dict[str, CanonicalReliefInfo] = {}
    by_stable_id: dict[str, CanonicalReliefInfo] = {}

    for urn_slug in CANONICAL_URN_SLUGS:
        urn_info = CANONICAL_URNS[urn_slug]
        file_path = d_dir / urn_info.data_file
        if not file_path.exists():
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            items = json.load(f)

        for idx, item in enumerate(items, start=1):
            stable_id = f"urn_{urn_info.legacy_prefix}_{idx:02d}"
            relief_slug = f"{urn_slug}-{idx:02d}"
            c = coords_by_id.get(stable_id, {})

            info = CanonicalReliefInfo(
                slug=relief_slug,
                stable_id=stable_id,
                urn_slug=urn_slug,
                order=idx,
                name_vi=item.get("name_vi", ""),
                name_en=item.get("name_en"),
                name_han_nom=item.get("name_han_nom"),
                category=item.get("category"),
                rarity=item.get("rarity"),
                mesh_name=c.get("mesh_name", item.get("name_vi")),
                pos_x=c.get("pos_x"),
                pos_y=c.get("pos_y"),
                pos_z=c.get("pos_z"),
                bounding_radius=c.get("bounding_radius", 0.08),
            )
            by_slug[relief_slug] = info
            by_stable_id[stable_id] = info

    return by_slug, by_stable_id


# Pre-load canonical reliefs
CANONICAL_RELIEFS, STABLE_MOTIF_IDS = _load_canonical_dataset()
CANONICAL_RELIEF_SLUGS: tuple[str, ...] = tuple(CANONICAL_RELIEFS.keys())


def validate_no_cross_urn_misassignment(urn_identifier: str, motif_identifier: str) -> None:
    """Validate that motif_identifier belongs to urn_identifier, rejecting cross-urn misassignment.

    Raises:
        CrossUrnMisassignmentError: If motif_identifier belongs to another Urn.
        ValueError: If urn_identifier or motif_identifier is unknown or invalid.
    """
    target_urn = resolve_canonical_urn_slug(urn_identifier)
    if not target_urn:
        raise ValueError(f"Unknown target urn identifier: '{urn_identifier}'")

    raw_motif = motif_identifier.strip()
    clean_motif = raw_motif.lower()

    # 1. Check if motif_identifier contains an explicit Urn prefix or slug
    intrinsic_urn = extract_urn_slug(clean_motif)
    if intrinsic_urn is not None:
        if intrinsic_urn != target_urn:
            raise CrossUrnMisassignmentError(
                f"Cross-urn misassignment detected: motif '{raw_motif}' belongs to urn '{intrinsic_urn}', "
                f"cannot be assigned to target urn '{target_urn}'",
                source_urn=intrinsic_urn,
                target_urn=target_urn,
                identifier=raw_motif,
            )
        return

    # 2. Check if motif_identifier is a motif name within the canonical dataset
    # Look across all reliefs to see where this name appears
    matched_urns: set[str] = set()
    norm_query = _normalize_str(raw_motif)
    for relief in CANONICAL_RELIEFS.values():
        if (
            relief.name_vi == raw_motif
            or relief.name_vi.lower() == clean_motif
            or _normalize_str(relief.name_vi) == norm_query
            or (relief.name_han_nom and relief.name_han_nom.strip() == raw_motif)
        ):
            matched_urns.add(relief.urn_slug)

    if matched_urns:
        if target_urn not in matched_urns:
            other_urns = ", ".join(sorted(matched_urns))
            raise CrossUrnMisassignmentError(
                f"Cross-urn misassignment detected: motif name '{raw_motif}' belongs to urn(s) [{other_urns}], "
                f"not found on target urn '{target_urn}'",
                source_urn=next(iter(matched_urns)),
                target_urn=target_urn,
                identifier=raw_motif,
            )
        return

    # If it's a numeric index, verify 1..18
    if raw_motif.isdigit():
        num = int(raw_motif)
        if not (1 <= num <= MOTIFS_PER_URN):
            raise ValueError(f"Motif index {num} out of bounds (1..{MOTIFS_PER_URN}) for urn '{target_urn}'")
        return

    # If unmatched anywhere, raise ValueError
    raise ValueError(f"Motif '{raw_motif}' not recognized in dataset for urn '{target_urn}'")


def validate_urn_motif_count(
    urn_identifier: str,
    count_or_motifs: int | list[Any],
) -> None:
    """Validate that an Urn has exactly 18 motifs.

    Args:
        urn_identifier: Urn slug or alias (e.g. 'cao-dinh', 'cao_dinh', 'Cao Đỉnh').
        count_or_motifs: Integer count of motifs or a list of motif records.

    Raises:
        InvalidMotifCountError: If count != MOTIFS_PER_URN (18).
        ValueError: If urn_identifier cannot be resolved.
    """
    slug = resolve_canonical_urn_slug(urn_identifier)
    if not slug:
        raise ValueError(f"Unknown urn identifier: '{urn_identifier}'")

    if isinstance(count_or_motifs, list):
        count = len(count_or_motifs)
    elif isinstance(count_or_motifs, int):
        count = count_or_motifs
    else:
        try:
            count = int(count_or_motifs)
        except (ValueError, TypeError):
            raise ValueError(f"count_or_motifs must be an int or list, got {type(count_or_motifs)}")

    if count != MOTIFS_PER_URN:
        raise InvalidMotifCountError(
            f"Invalid motif count for urn '{slug}': got {count}, expected exactly {MOTIFS_PER_URN}"
        )


def resolve_canonical_relief_slug(
    identifier: str,
    urn_context: Optional[str] = None,
) -> Optional[str]:
    """Resolve a relief slug, stable ID, mesh name, or alias to canonical relief slug (e.g. 'cao-dinh-02').

    If urn_context is supplied, validates zero cross-urn misassignment first.
    """
    if not identifier:
        return None
    raw = identifier.strip()
    clean = raw.lower()

    target_urn = resolve_canonical_urn_slug(urn_context) if urn_context else None

    # Enforce cross-urn protection when urn_context is present
    if target_urn:
        validate_no_cross_urn_misassignment(target_urn, raw)

    # 1. Exact match on canonical relief slug
    if clean in CANONICAL_RELIEFS:
        return clean

    # 2. Exact match on stable ID
    if clean in STABLE_MOTIF_IDS:
        return STABLE_MOTIF_IDS[clean].slug

    # 3. Check regex for non-padded IDs: urn_<prefix>_<n>
    m = re.match(r"^urn_([a-z]+_[a-z]+)_(\d+)$", clean)
    if m:
        prefix = m.group(1).replace("_", "-")
        n = int(m.group(2))
        if prefix in CANONICAL_URN_SLUGS and 1 <= n <= MOTIFS_PER_URN:
            candidate = f"{prefix}-{n:02d}"
            if target_urn and prefix != target_urn:
                raise CrossUrnMisassignmentError(
                    f"Cross-urn misassignment: '{raw}' is from '{prefix}', not '{target_urn}'",
                    source_urn=prefix,
                    target_urn=target_urn,
                    identifier=raw,
                )
            return candidate

    # 4. Check regex for mesh IDs: mesh_urn_<prefix>_<n>(_v\d+)?
    m = re.match(r"^mesh_urn_([a-z]+_[a-z]+)_(\d+)(?:_v\d+)?$", clean)
    if m:
        prefix = m.group(1).replace("_", "-")
        n = int(m.group(2))
        if prefix in CANONICAL_URN_SLUGS and 1 <= n <= MOTIFS_PER_URN:
            candidate = f"{prefix}-{n:02d}"
            if target_urn and prefix != target_urn:
                raise CrossUrnMisassignmentError(
                    f"Cross-urn misassignment: '{raw}' is from '{prefix}', not '{target_urn}'",
                    source_urn=prefix,
                    target_urn=target_urn,
                    identifier=raw,
                )
            return candidate

    # 5. Check non-padded or hyphenated slug: <urn-slug>-<n>
    m = re.match(r"^([a-z]+-[a-z]+)-(\d+)$", clean)
    if m:
        prefix = m.group(1)
        n = int(m.group(2))
        if prefix in CANONICAL_URN_SLUGS and 1 <= n <= MOTIFS_PER_URN:
            candidate = f"{prefix}-{n:02d}"
            if target_urn and prefix != target_urn:
                raise CrossUrnMisassignmentError(
                    f"Cross-urn misassignment: '{raw}' is from '{prefix}', not '{target_urn}'",
                    source_urn=prefix,
                    target_urn=target_urn,
                    identifier=raw,
                )
            return candidate

    # 5b. Check underscored slug: <urn-prefix>_<n> (e.g. cao_dinh_02 or cao_dinh_2)
    m = re.match(r"^([a-z]+_[a-z]+)_(\d+)$", clean)
    if m:
        prefix = m.group(1).replace("_", "-")
        n = int(m.group(2))
        if prefix in CANONICAL_URN_SLUGS and 1 <= n <= MOTIFS_PER_URN:
            candidate = f"{prefix}-{n:02d}"
            if target_urn and prefix != target_urn:
                raise CrossUrnMisassignmentError(
                    f"Cross-urn misassignment: '{raw}' is from '{prefix}', not '{target_urn}'",
                    source_urn=prefix,
                    target_urn=target_urn,
                    identifier=raw,
                )
            return candidate

    # 6. Check numeric string with urn_context (e.g. "02" or "2" with urn_context="cao-dinh")
    if target_urn and clean.isdigit():
        n = int(clean)
        if 1 <= n <= MOTIFS_PER_URN:
            return f"{target_urn}-{n:02d}"

    # 7. Match by name
    norm_query = _normalize_str(raw)
    candidates: list[CanonicalReliefInfo] = []
    for relief in CANONICAL_RELIEFS.values():
        if target_urn and relief.urn_slug != target_urn:
            continue
        if (
            relief.name_vi == raw
            or relief.name_vi.lower() == clean
            or _normalize_str(relief.name_vi) == norm_query
            or (relief.name_han_nom and relief.name_han_nom.strip() == raw)
            or (relief.name_en and relief.name_en.lower() == clean)
        ):
            candidates.append(relief)

    if len(candidates) == 1:
        return candidates[0].slug
    elif len(candidates) > 1:
        if target_urn:
            # Filter to target_urn
            urn_candidates = [c for c in candidates if c.urn_slug == target_urn]
            if len(urn_candidates) == 1:
                return urn_candidates[0].slug
        urns = ", ".join(sorted({c.urn_slug for c in candidates}))
        raise AmbiguousAliasError(
            f"Motif name '{raw}' is ambiguous across urns [{urns}]. Specify urn_context to disambiguate."
        )

    return None


def resolve_canonical_motif_id(
    identifier: str,
    urn_context: Optional[str] = None,
) -> Optional[str]:
    """Resolve any relief alias, slug, or mesh ID to stable motif ID (e.g. 'urn_cao_dinh_02')."""
    relief_slug = resolve_canonical_relief_slug(identifier, urn_context=urn_context)
    if relief_slug and relief_slug in CANONICAL_RELIEFS:
        return CANONICAL_RELIEFS[relief_slug].stable_id
    return None


def resolve_legacy_identifier(
    identifier: str,
    urn_context: Optional[str] = None,
) -> dict[str, Any]:
    """Comprehensive resolver returning full canonical mapping entity data.

    Returns dict with keys:
        entity_type: 'urn' or 'relief'
        canonical_slug: canonical entity slug
        stable_id: canonical stable ID (urn_..._xx)
        urn_slug: canonical urn slug
        name_vi: Vietnamese name
        order: position index (1..9 for urns, 1..18 for reliefs)
    """
    if not identifier:
        raise ValueError("Identifier must not be empty")

    raw = identifier.strip()

    # If it resolves to an urn directly and not a specific motif
    is_urn_alias = False
    urn_candidate = resolve_canonical_urn_slug(raw)
    clean = raw.lower()

    # Distinguish urn alias from relief alias (e.g. 'cao-dinh' vs 'cao-dinh-02')
    if urn_candidate and not re.search(r"-\d+$|_\d+$", clean):
        info = CANONICAL_URNS[urn_candidate]
        return {
            "entity_type": "urn",
            "canonical_slug": info.slug,
            "stable_id": f"urn_{info.legacy_prefix}",
            "urn_slug": info.slug,
            "name_vi": info.name_vi,
            "name_en": info.name_en,
            "name_han_nom": info.name_han_nom,
            "order": info.order,
        }

    # Resolve as relief
    relief_slug = resolve_canonical_relief_slug(raw, urn_context=urn_context)
    if relief_slug and relief_slug in CANONICAL_RELIEFS:
        r_info = CANONICAL_RELIEFS[relief_slug]
        u_info = CANONICAL_URNS[r_info.urn_slug]
        return {
            "entity_type": "relief",
            "canonical_slug": r_info.slug,
            "stable_id": r_info.stable_id,
            "urn_slug": r_info.urn_slug,
            "name_vi": r_info.name_vi,
            "name_en": r_info.name_en,
            "name_han_nom": r_info.name_han_nom,
            "order": r_info.order,
            "urn_name_vi": u_info.name_vi,
            "mesh_name": r_info.mesh_name,
            "coordinates": {
                "pos_x": r_info.pos_x,
                "pos_y": r_info.pos_y,
                "pos_z": r_info.pos_z,
                "bounding_radius": r_info.bounding_radius,
            },
        }

    # Fallback to Urn if urn_candidate exists (e.g. 'cao-dinh-01' mapped to urn)
    if urn_candidate:
        info = CANONICAL_URNS[urn_candidate]
        return {
            "entity_type": "urn",
            "canonical_slug": info.slug,
            "stable_id": f"urn_{info.legacy_prefix}",
            "urn_slug": info.slug,
            "name_vi": info.name_vi,
            "name_en": info.name_en,
            "name_han_nom": info.name_han_nom,
            "order": info.order,
        }

    raise ValueError(f"Unable to resolve legacy identifier '{raw}' to canonical entity")


def validate_dataset_uniqueness(
    data_dir: Optional[Path] = None,
    coords_path: Optional[Path] = None,
) -> dict[str, Any]:
    """Validate 9 Urns x 18 Motifs = 162 integrity and uniqueness.

    Ensures:
    1. Exactly 9 urn files exist.
    2. Each file has exactly 18 items.
    3. Exactly 162 unique motif IDs and relief slugs.
    4. Zero duplicate IDs, duplicate slugs, or cross-urn misassignments.
    5. Coordinates file has exactly 162 points with 100% ID correspondence.

    Raises:
        ValueError if any validation check fails.
    """
    d_dir = data_dir or DATA_DIR
    c_path = coords_path or COORDINATES_FILE

    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_slugs: set[str] = set()
    total_records = 0

    for urn_slug in CANONICAL_URN_SLUGS:
        urn_info = CANONICAL_URNS[urn_slug]
        file_path = d_dir / urn_info.data_file
        if not file_path.exists():
            errors.append(f"Missing data file: {urn_info.data_file} for urn {urn_slug}")
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                items = json.load(f)
        except Exception as e:
            errors.append(f"Failed to parse {urn_info.data_file}: {e}")
            continue

        try:
            validate_urn_motif_count(urn_slug, items)
        except InvalidMotifCountError as e:
            errors.append(
                f"Urn '{urn_slug}' in {urn_info.data_file} has {len(items)} items; expected exactly {MOTIFS_PER_URN}: {e}"
            )

        for idx, item in enumerate(items, start=1):
            total_records += 1
            item_id = item.get("id")
            name_vi = item.get("name_vi")

            expected_id = f"urn_{urn_info.legacy_prefix}_{idx:02d}"
            expected_slug = f"{urn_slug}-{idx:02d}"

            if not item_id:
                errors.append(f"Item #{idx} in {urn_info.data_file} is missing 'id'")
                continue

            if item_id != expected_id:
                errors.append(
                    f"Item #{idx} in {urn_info.data_file} has id '{item_id}'; expected '{expected_id}'"
                )

            # Check cross-urn misassignment within file
            id_urn = extract_urn_slug(item_id)
            if id_urn != urn_slug:
                errors.append(
                    f"Cross-urn misassignment in {urn_info.data_file}: item id '{item_id}' encodes urn '{id_urn}', expected '{urn_slug}'"
                )

            if item_id in seen_ids:
                errors.append(f"Duplicate motif id detected: '{item_id}'")
            seen_ids.add(item_id)

            if expected_slug in seen_slugs:
                errors.append(f"Duplicate relief slug detected: '{expected_slug}'")
            seen_slugs.add(expected_slug)

    # Validate coordinate points
    coord_count = 0
    if c_path.exists():
        try:
            with open(c_path, "r", encoding="utf-8") as f:
                coords = json.load(f)
            coord_count = len(coords)
            if coord_count != TOTAL_MOTIFS:
                errors.append(f"Coordinates file {c_path.name} contains {coord_count} points; expected {TOTAL_MOTIFS}")

            coord_ids = set()
            for c in coords:
                cid = c.get("id")
                if not cid:
                    errors.append(f"Coordinate entry missing 'id': {c}")
                    continue
                if cid in coord_ids:
                    errors.append(f"Duplicate coordinate entry id: {cid}")
                coord_ids.add(cid)

                c_urn = c.get("urn_slug")
                if c_urn not in CANONICAL_URN_SLUGS:
                    errors.append(f"Coordinate entry '{cid}' has unknown urn_slug: '{c_urn}'")

                # Verify coordinate numeric validity
                for axis in ("pos_x", "pos_y", "pos_z"):
                    if not isinstance(c.get(axis), (int, float)):
                        errors.append(f"Coordinate entry '{cid}' has non-numeric {axis}: {c.get(axis)}")

            missing_coords = seen_ids - coord_ids
            if missing_coords:
                errors.append(f"Motif IDs missing coordinates: {sorted(missing_coords)}")
        except Exception as e:
            errors.append(f"Error inspecting coordinates file: {e}")
    else:
        errors.append(f"Missing coordinate points file at {c_path}")

    if errors:
        raise ValueError(f"Dataset integrity verification failed ({len(errors)} errors):\n" + "\n".join(errors))

    return {
        "valid": True,
        "total_urns": TOTAL_URNS,
        "total_motifs": total_records,
        "unique_ids": len(seen_ids),
        "unique_relief_slugs": len(seen_slugs),
        "coordinates_count": coord_count,
        "canonical_urns": list(CANONICAL_URN_SLUGS),
    }
