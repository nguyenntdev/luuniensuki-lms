# Compressing catalogue changes with source-character contexts

Both 2014 Tate development intervals produced smaller updates when the encoder could order edit events by context. The 5% margin against the matched row-major codec was reached on January–June only. Each result includes the complete wire and describes an exact update to a canonical table of 69,201 records. [Screen protocol](design.md) · [Counts and wire digests](result.json)

| Wire bytes | January–June | June–October |
|---|---:|---:|
| HDiffPatch | 65,637 | 70,840 |
| Shared substring programs | 34,268 | 32,412 |
| Matched edit events in row order | 34,424 | 32,260 |
| Source-context edit events | 30,632 | 31,800 |

The sender aligns the target cell to a string the receiver can reconstruct from the base row or earlier fields. Every difference contributes a start position, a number of deleted code points and an inserted string. Reordering possible start positions by character, neighboring character classes or distance to an endpoint lets the outer compressor exploit repeated editorial operations. The decoder derives the permutation from the reference strings. For each column the sender can transmit the prior substring rules or plain instructions if their compressed representation is shorter. Comparing actual XZ-compressed alternatives within each column is a heuristic for minimizing the size of the entire compressed update.

In the first interval the contextual order represented title punctuation changes, while reverse offsets represented URL changes. In the second interval only the title and URL columns selected a context order. Their aggregate saving relative to the row-major arm fell to 460 bytes (1.43%). Both source-context updates were independently decoded in JavaScript and compared against all target keys and fields. We forced all five event orders through a separate fixture containing combining marks, supplementary code points, embedded NUL, deletions and row insertions. [Encoder](events.py) · [Decoder](verify.mjs) · [Boundary fixture](check_events.py)

## Reusing earlier edits across records

A second encoder first restores the exceptional cells from their independent edits. It then reconstructs every changed cell in a transmitted order, copying the preceding updated value, reusing the last mapping from this original value, or transferring the preceding record's changed substring. Each column can use identifier order, old first-field order or old own-value order. The earlier experiment suggested this extension. Both intervals informed its design. [Extension protocol](donor_design.md) · [Complete wire sizes and selected predictors](donor_result.json)

| Wire bytes | January–June | June–October |
|---|---:|---:|
| Reordering and context events | 29,408 | 30,924 |
| Also copy preceding target | 29,128 | 30,232 |
| Also reuse old-value mappings and transfer the preceding edit | **27,680** | **30,080** |

The complete method saved 19.23% and 7.19% against the previously strongest shared-substring codec. Its closest matched comparator, which can copy the preceding target, cost only 1,448 and 152 extra bytes. These differences represent 4.97% and 0.50%, below the 5% margin in both intervals. Reordering alone accounted for substantial savings. More complex donor transfer currently lacks a practically distinct advantage over the simpler copy mechanism on these data. An independent JavaScript decoder reconstructed all six donor-study targets and a separate Unicode fixture forced all three donor modes. A third-party publisher test remains reserved. [Encoder](donor.py) · [Donor fixture](check_donor.py)

## Reproduction

Supply the three pinned Tate CSVs from the [catalogue revision study](../../catalog_revisions/manuscript.md#reproduction). Python 3.12, Node and XZ suffice. The programs verify the raw and canonical input digests before reporting sizes. The earlier rows in each JSON table use the pinned byte counts from the [relational](../relational/README.md), [shared-rule](../shared_edits/README.md) and [conditional](../conditional/README.md) comparisons. No additional downloads are needed to replay this experiment when the pinned CSVs are available. The sender and receiver assume the column layout stays constant.

```bash
set -eu
d=research_v4_2/external/catalog_sync/context_events
out=$(mktemp -d)
taskset -c 14-25 node --check "$d/verify.mjs"
taskset -c 14-25 python "$d/check_events.py"
taskset -c 14-25 python "$d/check_donor.py"
taskset -c 14-25 python "$d/events.py" "$data/jan.csv" "$data/jun.csv" "$data/oct.csv" "$out/result.json"
cmp "$d/result.json" "$out/result.json"
taskset -c 14-25 python "$d/donor.py" "$data/jan.csv" "$data/jun.csv" "$data/oct.csv" "$out/donor_result.json"
cmp "$d/donor_result.json" "$out/donor_result.json"
```
