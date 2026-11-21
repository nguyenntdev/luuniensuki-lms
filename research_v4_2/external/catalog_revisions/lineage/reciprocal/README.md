# P12 document-wide heading assignment

One-to-one matching with title, full body, local context and unchanged-heading anchors recovered 19 of 21 PEP renames and 12 of 13 Sphinx renames. The independent matcher using the same scores, locks and abstention rule recovered 20 and 12. Global assignment changed one labeled prediction across both cohorts and turned a correct PEP match into an error. The best published controls recovered 19 PEP renames and all 13 Sphinx renames. Both frozen cohorts are development evidence for this study. Sphinx served as transfer data in the preceding study and its results were already known here.

| Method | PEPs (21) | Sphinx (13) |
| --- | ---: | ---: |
| Published title + first 80 body tokens + context | 19 | 12 |
| Published first 80 body tokens alone | 17 | 13 |
| Independent full-body TF-IDF cosine | 19 | 12 |
| Published anchor interpolation | 17 | 10 |
| Title + full body + context, independent / global | 19 / 19 | 12 / 12 |
| Add soft anchor position only, independent / global | 20 / 19 | 12 / 12 |
| Add exact-title locks only, independent / global | 19 / 19 | 12 / 12 |
| Add both anchor features, independent / global | **20 / 19** | **12 / 12** |
| First 80 body tokens + exact-title locks, independent / global | 17 / 17 | 13 / 13 |

The full global rule has equal-file accuracy of 93.9% on PEPs and 88.9% on Sphinx across 11 and nine files. On rows with changed ASCII-normalized title anchors it scores 17/19 and 8/9. Results are conditional on an explicit label remaining unique in both snapshots and a literal title change. The frozen censuses had a further 143 PEP and 25 Sphinx source labels without a unique destination. Unlabeled matches and censored cases lack adjudicated targets. Commits and files can recur within one project history. No significance or generalization claim follows from these counts.

## Competition and the PEP 740 case

PEPs contribute 16 document revisions, two of which contain multiple labeled renames. Sphinx contributes 11 revisions with one multi-rename revision. A check of the frozen published predictions found a body-overlap collision in PEP 740 commit `72595af7b1`. Both source appendices chose destination 21. The five labeled targets in the PEP 622 revision and the three in the Sphinx configuration revision had distinct, correct body-overlap predictions. With exact-title locks applied, independent choices over the **whole document** collide in six PEP revisions and one Sphinx revision. Only PEP 740 has two labeled contenders for one destination under the primary score.

For PEP 740, source 16 has full-body cosine 0.944 with destination 21 and 0.050 with its label-preserving destination 22. The independent anchored rule picks 21 for both sources 15 and 16. The global rule gives 21 to source 16 and reassigns source 15 to 22, missing both labels. Forcing the observed label assignment lowers the sum of utilities by 0.0073534099. Published anchor projection recovers both, while Sphinx's PyPI installation heading moves from source 13 to target 1 and is correctly recovered by early body overlap. The full-body matcher picks destination 8 on that row.

The evaluator swaps the two destination labels in memory and verifies that the masked headings, styles and body tokens remain identical. The observed targets are `15 → 21` and `16 → 22`. Swapping labels makes the targets `15 → 22` and `16 → 21`. Both assignments satisfy the label-continuity rule in their respective versions. A method that only sees these masked snapshots receives identical inputs and must predict the same assignment for both. This establishes an identifiability limit for that input and target definition. The counterfactual is a witness, and only the observed revision contributes to accuracy.

## Method and reproduction

The evaluator uses the same parser, rights check and conservative label masking as the earlier PEP and Sphinx work. Masking removes case-folded occurrences of the pooled explicit label strings, including in text. The matcher receives only masked title and body tokens, heading styles and ordinals. All parsed headings enter the assignment, including unlabeled or deleted sources. Unique nonempty stripped masked titles present on both sides define fixed anchors in the locked variants. The same anchors provide soft positions in the position variants. Flanking anchors interpolate the expected destination ordinal, a single flank projects by its offset, and the projection is clipped to the destination range.

The base score averages title sequence similarity, full-section TF-IDF cosine and parent/adjacent-sibling title-token Jaccard. TF-IDF is computed over both snapshots with sublinear term frequency and smoothed inverse document frequency. The position term is `1 / (1 + distance)` from the projected ordinal and has equal weight when a projection exists. Real edges have utility equal to their score minus 0.20, rounded to 10 decimal places. Each source can instead take a zero-utility dummy. Nonpositive real matches count as abstentions. Independent matching selects the first positive maximum, and global matching maximizes summed utility with SciPy's rectangular assignment solver and the same scores, ordering, locks and abstentions. The locked early-body ablation uses Jaccard on the first 80 body tokens with the same two matching procedures. The rule and threshold were selected as development choices, without a holdout or an optimization sweep. The frozen outcomes enter only verification, metrics and the counterfactual audit.

With Git, Python 3.12 and SciPy 1.17.1, use full histories containing the revisions pinned in [the frozen protocol](../transfer/PROTOCOL.md) and [its evaluator](../transfer/evaluate.py). Run from this directory after obtaining the two upstream clones outside this repository. The commands use the CPU range assigned for this run.

```sh
taskset -c 20-29 git clone https://github.com/python/peps /tmp/p12-peps-repro
taskset -c 20-29 git clone --branch v8.2.3 https://github.com/sphinx-doc/sphinx /tmp/p12-sphinx-repro
taskset -c 20-29 python ../transfer/evaluate.py /tmp/p12-peps-repro peps > /tmp/p12-peps-repro.json
taskset -c 20-29 python ../transfer/evaluate.py /tmp/p12-sphinx-repro sphinx > /tmp/p12-sphinx-repro.json
cmp ../transfer/peps.json /tmp/p12-peps-repro.json
cmp ../transfer/sphinx.json /tmp/p12-sphinx-repro.json
taskset -c 20-29 python ../transfer/verify.py
taskset -c 20-29 python evaluate.py /tmp/p12-peps-repro /tmp/p12-sphinx-repro > /tmp/p12-reciprocal-repro.json
cmp results.json /tmp/p12-reciprocal-repro.json
```

[Saved results](results.json) include revision and blob IDs, target indices, every labeled prediction, collision counts, and the masked-input witness. The directory holds no upstream source text.
