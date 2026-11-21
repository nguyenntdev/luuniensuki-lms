# Shared string rewrites for lossless catalogue updates

The full method used **34,468 and 32,816 bytes**, respectively. Against the earlier within-row codec the savings were 29.44% and 0.18%. It cleared the 5% margin against 12 of 13 controls on the first interval and 9 of 13 on the second. The substring-only codec produced the smaller second update at 32,412 bytes. All eight compressed updates reconstructed all 69,201 target artworks. The all-control development criterion failed on both intervals. [Byte counts, program counts and checksums](result.json)

| Codec, complete update bytes | January–June | June–October |
|---|---:|---:|
| HDiffPatch | 65,637 | 70,840 |
| Preceding within-row edits | 48,852 | 32,876 |
| Whole-value rules | 46,816 | 32,876 |
| Substring rules | 34,268 | 32,412 |
| Both rule types, absolute selectors | 37,908 | 32,804 |
| Both rule types, adaptive selectors | 34,468 | 32,816 |

The encoder learns replacements separately for each updated column. For a changed old/new pair it finds their longest common prefix and suffix, then proposes replacing the intervening span, optionally preserving two characters of neighboring context. An instruction can require a start or end anchor, replace every occurrence, or map an exact old cell to a new value. Repeated edits therefore carry their text once. This is a development study of the cost of encoding the rows to which these rules apply. It does not establish priority for rule-based table deltas. [Prior work and published codec configurations](../relational/README.md#prior-work)

For each rule class, at most 32 proposals with at least four nominations are evaluated per column. Rules are prioritized by the number of exact target cells they would produce. The encoder can select absolute changed-row indices, indices into the currently eligible rows, or exceptions within that list. In each case indices are gap-coded. Every remaining change uses the earlier literal, own-value edit or within-row copy/edit instruction. For each column the encoder compares the compressed proposal with a residual-only representation before choosing. The full update is one XZ stream. This greedy procedure does not solve for an optimal compressed patch.

## Reproduction

Acquire the three pinned CSV files through the Tate acquisition instructions. From the repository root, run the following with Python 3.12, Node and xz. Set `data` to the directory containing the snapshots. The evaluator checks both endpoints against the previous experiment's raw and canonical SHA-256 digests. It reproduces all four new codec variants and combines their sizes with verified earlier baseline measurements. To regenerate those baselines, use the preceding experiment's tool versions and commands. The JavaScript verifier receives only the original canonical file and the compressed wire for reconstruction, then compares each object and cell with the canonical target. [Tate source commands](../../catalog_revisions/manuscript.md#reproduction) · [Baseline replay](../relational/README.md#reproduction) · [Experimental design](design.md)

```bash
set -eu
e=research_v4_2/external/catalog_sync/shared_edits
out=$(mktemp)
taskset -c 20-23 node --check "$e/verify.mjs"
taskset -c 20-23 python "$e/encode.py" "$data/jan.csv" "$data/jun.csv" "$data/oct.csv" "$out"
cmp "$e/result.json" "$out"
```
