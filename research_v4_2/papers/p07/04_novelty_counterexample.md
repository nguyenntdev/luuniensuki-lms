# P07 Novelty Counterexample

Consider a cultural heritage learning query for an imperial bronze urn inscription:
- Task: Requires `inscription_text` and `relief_depth`.
- Device: Low-bandwidth mobile device with `max_payload_kb = 200` and `webgl = False`.
- Candidates:
  1. `O1`: High-resolution 3D GLB mesh (1200 KB, AllRightsReserved, semantic_relevance = 0.95).
  2. `O2`: Color photograph (180 KB, CC-BY-4.0, semantic_relevance = 0.90, lacks `inscription_text`).
  3. `O3`: 2D Monochrome rubbing scan (120 KB, CC0, semantic_relevance = 0.88, affords `inscription_text` and `relief_depth` through high-contrast epigraphy).

**Prior Art (SIGLIP 2 / Greedy Reranker):**
Selects `O1` based on highest semantic similarity (0.95).
Result: Fails completely at runtime because WebGL is unavailable, payload budget is exceeded by 600%, and license forbids educational reuse.

**Classical Baseline C1 (Static Image Fallback):**
Falls back from 3D to `O2` (first static image), but silently drops the `inscription_text` affordance.
Result: Student cannot read the inscription, failing the pedagogical objective.

**Our Proposed Method (RAC-ILP):**
Prunes `O1` (rights + device failure), prunes `O2` (missing affordance), and selects `O3` (feasible, rights-cleared, affordance-complete).
Result: Preserves both copyright compliance and pedagogical integrity.
