# 06_Data_and_Seeding.md (Seed Quality + Content Metadata)

## Goal

Make seeded content “game-ready”:

- correct categories (not all `thao_moc`)
- meaningful rarity distribution
- stable ordering
- thumbnails/silhouettes for collection UI
- (later) reliable 3D positions/radii for interaction validation

## Current State

- Seed inputs: 9 JSON files in `data/` (≈ 18 motifs each).
- Seed script: `backend/seed.py`
  - hardcodes `category=MotifCategory.thao_moc`
  - hardcodes `rarity=MotifRarity.common`
  - sets placeholder `pos_* = 0`, `bounding_radius = 1.0`
  - **thumbnail_url auto-mapping**: scans `ban-duc-noi/` (or `--image-path`) and sets `Motif.thumbnail_url` to `/assets/ban-duc-noi/...`
  - `display_order` is derived from the item `id` suffix (`*_01`, `*_02`, ...)

## Data Model Fields We Should Populate

For `Motif`:

- `category` (required)
- `rarity` (required)
- `display_order` (for stable ordering in UI)
- `thumbnail_url` (for unlocked cards)
- `silhouette_url` (for locked cards)
- `pos_x/pos_y/pos_z` + `bounding_radius` (for tap validation)

For `Urn`:

- `thumbnail_url` (explore grid)
- `description` / `represents` (optional but improves UX)

## Recommended Data Strategy (Non-breaking)

Keep the existing 9 JSON files as “content text source of truth”, and add a **separate enrichment mapping file**:

`data/motif_metadata.json`

Shape:

```json
{
  "mesh_urn_cao_dragon_v1": {
    "category": "linh_thu",
    "rarity": "epic",
    "display_order": 2,
    "thumbnail_url": "/assets/thumbs/mesh_urn_cao_dragon_v1.png",
    "silhouette_url": "/assets/silhouettes/mesh_urn_cao_dragon_v1.png",
    "pos": [0.12, 0.45, -0.33],
    "bounding_radius": 0.18
  }
}
```

This avoids constantly rewriting the original text dataset and lets 3D artists update positions independently.

## Rarity Distribution (Proposed MVP)

Per urn (~18 motifs):

- 10–12 common
- 4–5 uncommon
- 1–2 rare
- 0–1 epic
- 0–1 legendary

## Category Assignment (MVP Options)

Choose one:

1. **Manual mapping file** (recommended): curate category by mesh id.
2. **Heuristics by keyword**: brittle, but can bootstrap quickly.
3. Update the source JSON to include `category` and `rarity` fields (cleanest long-term, but requires re-exporting all).

## Tasks

### Seed Script Upgrades

- [ ] **DATA-SEED-01**: Extend `backend/seed.py` to load optional `data/motif_metadata.json`
- [ ] **DATA-SEED-02**: Apply mapping if present; otherwise keep safe defaults
- [ ] **DATA-SEED-03**: Add validation:
  - unknown categories/rarities fail fast
  - missing required keys logged with clear output
- [ ] **DATA-SEED-04**: Add `--dry-run` and `--strict` flags (optional)

### Content Enrichment

- [ ] **DATA-META-01**: Create initial `data/motif_metadata.json` (category + rarity + ordering)
- [ ] **DATA-META-02**: Add thumbnails/silhouettes pipeline
- [ ] **DATA-META-03**: Add 3D positions/radii from GLB extraction (connects to `docs/plan/05_3D_Assets_Integration.md`)

## Definition of Done (Seed v2)

- Categories are meaningful (not hardcoded).
- Rarity distribution is visible in UI (collection filters).
- Collection shows thumbnails for unlocked and silhouettes for locked.
- Seed is repeatable/idempotent (re-run updates existing rows safely).
