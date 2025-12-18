# 05_3D_Assets_Integration.md (WebGL / R3F)

## Goal

Upgrade from the current “fallback spheres” to real **GLB urn models**, while preserving a graceful fallback if assets are missing or fail to load.

## Current State

- `UrnViewer` loads `Urn.model_url` via `useGLTF()` and falls back to a simple cylinder + spheres if the GLB is missing or fails to load.
- Motif click logic works (mesh name → backend motif → sidebar).
- Production uses same-origin model URLs under `/assets/models/...` (served/proxied by Nginx).

## Asset Contract (Required for Production Models)

### File URLs / naming

There are 2 supported strategies:

**A) Proxy from the model store (current prod approach)**

- `Urn.model_url` points to `/assets/models/<FILENAME>.glb`
- Nginx proxies `/assets/models/*` → `https://store.histolab.icu/*` to avoid CORS issues.
- Example (available today):
  - `/assets/models/CAO-DINH-v1.glb`
  - `/assets/models/CHUONG-DINH-v1.glb`

**B) Self-host models**

- Put GLBs under Nginx `/var/www/assets/models/` and keep `Urn.model_url=/assets/models/<file>.glb`

### Mesh naming (critical)

- Each clickable motif mesh **must have a stable unique name** that matches DB `Motif.mesh_name`.
- Avoid auto-generated names like `Mesh_001` unless those are what we store.

### Optional: Draco compression

If using Draco:

- provide decoder files in `frontend/public/draco/`
- configure `DRACOLoader` in ThreeJS

## Interaction Contract (Backend Validation)

Backend can optionally validate click/tap position using:

- `Motif.pos_x/pos_y/pos_z`
- `Motif.bounding_radius`

For this to work with real models:

1. Extract motif positions from the GLB scene.
2. Store in DB (seed/mapping script).
3. On click, send `e.point` to backend (`tap_position`).

## Implementation Approach (Recommended)

### A) Progressive enhancement

1. Attempt to load the GLB model.
2. If it fails: render fallback scene.
3. Either way, keep the same click handler contract:
   - `event.object.name` is the mesh_name

### B) Clickable mesh selection

- Traverse loaded scene once:
  - gather meshes whose `name` exists in the motifs list
  - attach pointer handlers only to those meshes
- Highlight on hover:
  - use `useCursor`
  - material change or outline effect (later)

## Task Breakdown

### Assets / Pipeline

- [ ] **3D-ASSET-01**: Deliver / confirm 9 GLB files on `store.histolab.icu` (or self-host under `/assets/models/`)
- [ ] **3D-ASSET-02**: Export checklist for artists:
  - correct mesh naming
  - scale/unit consistency
  - pivot/origin sanity
  - triangle count budgets
- [ ] **3D-ASSET-03** (optional): Draco compress + decoder placement

### Frontend (R3F)

- [ ] **FE-3D-01**: Add GLB loader path + fallback on error
- [ ] **FE-3D-02**: Mesh traversal + register clickable meshes by name
- [ ] **FE-3D-03**: Hover highlight + tooltip (mesh name / motif name)
- [ ] **FE-3D-04**: Add “hotspot” markers for small motifs (optional)
- [ ] **FE-3D-05**: Add camera presets per urn (optional; improves UX)

### Backend/Data Alignment

- [ ] **DATA-3D-01**: Create script to extract mesh positions + bounding radius from GLB and output JSON
- [ ] **DATA-3D-02**: Extend seed process to update `pos_*` and `bounding_radius`
- [ ] **BE-3D-01**: Enable strict tap validation once positions are reliable (config flag)

## Definition of Done (3D MVP)

- `/urns/{slug}` loads the GLB model if present.
- Clicking a motif mesh opens sidebar and calls `/progress/unlock`.
- Fallback scene still works if GLB is missing.
