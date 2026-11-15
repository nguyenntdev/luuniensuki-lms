"""P10 corpus loader: documented Cửu Đỉnh objects -> learning objects.

READ-ONLY reuse of the repo's documented heritage data:
- ``data/0x_Data_*.json`` — 9 urns x 18 motifs = 162 motifs (AGENTS.md ground truth)
- ``data/imperial/curriculum_units_gdpt2018_hue.json`` — GDPT-2018-aligned catalog

No media/permission claims: only factual object identities (ids, names,
categories) enter the research corpus. Every loaded motif is flagged
``is_ai_generated`` as the source data states — recorded honestly.

Category -> grade/layer/Bloom assignment follows METHOD.md §2.3 (fixed
constraints, preregistered): the 9 documented motif categories are distributed
over the three spiral layers with rising Bloom depth:
  layer 1 (grade 10, Bloom 1-2)  linh_thu, dong_vat, thao_moc, thien_van
  layer 2 (grade 11, Bloom 3-4)  kien_truc, giao_thuong, nong_nghiep
  layer 3 (grade 12, Bloom 5)    dia_ly, vo_bi
Layer-3 categories carry the sovereignty/argumentation themes (địa lý: rivers/
mountains/sea-territory inscriptions; võ bị: military power of the dynasty)
that the grade-12 evaluation layer targets. This distribution is a DESIGN
HYPOTHESIS and inherits needs_expert_review status from the category anchors.
"""
from __future__ import annotations

import json
from pathlib import Path

from .anchors import LearningObject, P10ContractError
from .registry import build_anchor_registry

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"

URN_FILES: tuple[tuple[str, str], ...] = (
    ("05_Data_CaoDinh.json", "cao-dinh"),
    ("06_Data_NhanDinh.json", "nhan-dinh"),
    ("07_Data_ChuongDinh.json", "chuong-dinh"),
    ("08_Data_AnhDinh.json", "anh-dinh"),
    ("09_Data_NghiDinh.json", "nghi-dinh"),
    ("10_Data_ThuanDinh.json", "thuan-dinh"),
    ("11_Data_TuyenDinh.json", "tuyen-dinh"),
    ("12_Data_DuDinh.json", "du-dinh"),
    ("13_Data_HuyenDinh.json", "huyen-dinh"),
)

# Fixed (preregistered) category -> (grade, layer) spiral placement.
CATEGORY_SPIRAL_PLACEMENT: dict[str, tuple[int, int]] = {
    # layer 1 — identify (grade 10, Bloom 1-2)
    "dong_vat": (10, 1),
    "linh_thu": (10, 1),
    "thao_moc": (10, 1),
    "thien_van": (10, 1),
    # layer 2 — corroborate (grade 11, Bloom 3-4)
    "giao_thuong": (11, 2),
    "kien_truc": (11, 2),
    "nong_nghiep": (11, 2),
    # layer 3 — evaluate (grade 12, Bloom 5)
    "dia_ly": (12, 3),
    "vo_bi": (12, 3),
}

# Anchor per (grade, category): documented for grade 10 (the Chuyên đề
# bảo tồn di sản exists in Lịch sử 10); pending expert review elsewhere.
DOCUMENTED_GRADE = 10
DOCUMENTED_ANCHOR_G10 = "LS10-CHUYENDE-BAO_TON_DI_SAN"


def load_corpus(data_dir: Path | None = None) -> list[LearningObject]:
    """Load the 162 documented motifs as anchor-bearing learning objects.

    Fail-closed: every object must resolve its anchor in the frozen registry.
    """
    base = Path(data_dir) if data_dir else DATA_DIR
    registry = build_anchor_registry()
    objects: list[LearningObject] = []
    for filename, urn_slug in URN_FILES:
        path = base / filename
        if not path.is_file():
            raise P10ContractError(f"documented corpus file missing: {path}")
        with path.open(encoding="utf-8") as fh:
            motifs = json.load(fh)
        if len(motifs) != 18:
            raise P10ContractError(
                f"{filename}: expected 18 documented motifs, got {len(motifs)}"
            )
        for motif in motifs:
            category = motif["category"]
            placement = CATEGORY_SPIRAL_PLACEMENT.get(category)
            if placement is None:
                raise P10ContractError(
                    f"{motif['id']}: category {category!r} has no preregistered "
                    "spiral placement (refusing to invent one silently)"
                )
            grade, layer = placement
            if grade == DOCUMENTED_GRADE:
                anchor_code = DOCUMENTED_ANCHOR_G10
            else:
                anchor_code = f"P10-LOCAL-{category}-G{grade}"
            objects.append(
                LearningObject(
                    object_id=motif["id"],
                    urn_slug=urn_slug,
                    motif_name_vi=motif["name_vi"],
                    category=category,
                    grade=grade,
                    layer=layer,
                    bloom_level={"1": 2, "2": 4, "3": 5}[str(layer)],
                    anchor_code=anchor_code,
                    is_ai_generated=bool(motif.get("is_ai_generated", False)),
                )
            )
    if len(objects) != 162:
        raise P10ContractError(
            f"expected the documented 162-motif corpus, got {len(objects)}"
        )
    # Fail-closed anchor resolution for the whole corpus up front.
    for obj in sorted(objects, key=lambda o: o.object_id):
        anchor = registry.get(obj.anchor_code)
        if anchor is None:
            raise P10ContractError(f"{obj.object_id}: unknown anchor {obj.anchor_code!r}")
    return objects


def build_prerequisite_edges(
    objects: list[LearningObject],
    *,
    within_urn: bool = True,
    cross_layer_bridges: bool = True,
) -> list[PrerequisiteEdgeImport]:
    """Build the spiral DAG edges (deterministic).

    - Within each urn, layer 1 -> layer 2 -> layer 3 progression edges connect
      the urn's motifs across layers (each motif of layer k+1 depends on the
      same urn's layer-k motif with the lowest object_id — a deterministic,
      minimal bridge-per-urn policy).
    - Bridge edges connect each urn's layer-1 anchor motif to the layer-1
      motif of the *next* urn (alphabetical) so identification vocabulary is
      shared before depth rises (A1 ablation removes exactly these bridges).
    Edge count is O(#urns x #categories-per-urn) — small, inspectable.
    """
    # Local import to keep the module import graph acyclic in tooling terms.
    from .anchors import PrerequisiteEdge

    edges: list[PrerequisiteEdge] = []
    by_urn_layer: dict[tuple[str, int], list[LearningObject]] = {}
    for obj in sorted(objects, key=lambda o: o.object_id):
        by_urn_layer.setdefault((obj.urn_slug, obj.layer), []).append(obj)

    if within_urn:
        for _filename, urn_slug in URN_FILES:
            for layer in (1, 2):
                lower = by_urn_layer.get((urn_slug, layer), [])
                upper = by_urn_layer.get((urn_slug, layer + 1), [])
                if not lower or not upper:
                    continue
                anchor_tail = lower[0]  # sorted; deterministic representative
                for head in upper:
                    edges.append(
                        PrerequisiteEdge(
                            tail=anchor_tail.object_id,
                            head=head.object_id,
                            edge_kind="progression",
                        )
                    )
    if cross_layer_bridges:
        urns = sorted(slug for _, slug in URN_FILES)
        for layer in (1, 2, 3):
            reps: list[str] = []
            for urn_slug in urns:
                bucket = by_urn_layer.get((urn_slug, layer), [])
                if bucket:
                    reps.append(bucket[0].object_id)
            for tail, head in zip(reps, reps[1:]):
                edges.append(
                    PrerequisiteEdge(tail=tail, head=head, edge_kind="bridge")
                )
    return edges


# Type alias to avoid a circular import at module top; PrerequisiteEdge is
# defined in anchors.py alongside the other frozen types.
from .anchors import PrerequisiteEdge as PrerequisiteEdgeImport  # noqa: E402
