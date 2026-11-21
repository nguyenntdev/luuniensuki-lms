# Conditioning a sparse catalogue update on earlier fields

The contextual codec produced 53,832 and 62,188 byte updates on the two Tate development intervals. The corresponding own-field codec used 54,140 and 63,288 bytes. Conditioning saved 0.57% and 1.74%, both below the 5% margin. The existing shared substring codec achieved 34,268 and 32,412 bytes. These observations end this candidate's development screen. [Protocol](design.md) · [Byte counts, wire digests and selected orders](result.json) · [Shared substring baseline](../shared_edits/README.md)

| Complete wire bytes | January–June | June–October |
|---|---:|---:|
| HDiffPatch | 65,637 | 70,840 |
| Own-cell edits, XZ | 48,828 | 55,416 |
| Earlier within-row codec | 48,852 | 32,876 |
| Shared substring rules | 34,268 | 32,412 |
| Sparse VCDIFF, own-field contexts | 54,140 | 63,288 |
| Sparse VCDIFF, all field contexts | 53,832 | 62,188 |

Each wire specifies any schema change, inserted and removed identifiers, the changed columns in target order and two choices for each column. The first describes its changed-row set as rank gaps in the order of a known field. The second specifies the row order and choice of literal cells or a VCDIFF byte stream against a reconstructible dictionary. The full method can transmit the symmetric difference with any earlier change mask. Its dictionaries can also include earlier reconstructed fields, the other original cells in that row, and candidate substitutions induced by the previous edits in that row. Candidate orders use the old table projected into the new schema. Empty original cells stand in for new rows or fields. The encoder uses zlib to estimate representation size locally and XZ to compress the complete framed patch. The compressed-size search is heuristic.

The JavaScript decoder reconstructs the schema, ordered identifiers and every string from the base file and wire. Only then does it read the expected canonical target. Both codec variants passed on both 69,201-object targets. An additional 101-row fixture exercised a removed column, reordered fields, a new field, inserted and removed objects, embedded NUL, multibyte and supplementary characters. The endpoint is an exact table of Unicode strings in canonical identifier order. This comparison used the development publisher. Computational cost and unseen-publisher performance remain unmeasured. [Decoder](verify.mjs) · [Schema fixture](test_schema.py)

Run the following from the repository root with Bash, Python 3.12, Node, XZ and the existing xdelta3 3.0.11 binary. Supply the same pinned Tate CSVs used in the baseline. Inputs must match the saved base and canonical-target digests. The previous baseline measurements and their replay commands are linked above. Python and Node use one application process each while the external xdelta3 tool may use helper threads.
    
```bash
set -eu
d=research_v4_2/external/catalog_sync/conditional
xdelta=$(command -v xdelta3)
out=$(mktemp)
taskset -c 24-27 node --check "$d/verify.mjs"
taskset -c 24-27 python "$d/test_schema.py" "$xdelta"
taskset -c 24-27 python "$d/codec.py" "$xdelta" "$data/jan.csv" "$data/jun.csv" "$data/oct.csv" "$out"
cmp "$out" "$d/result.json"
```
