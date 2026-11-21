# Recovering displaced bibliographic fields

The DeepMatcher benchmarks include deliberately dirty variants of the DBLP–ACM and DBLP–Google Scholar linkage tasks. Ditto distributes the serialized pairs. We downloaded each training and validation split from commit 52985564a93fb11308439516d3e17a033d43ec8f. The published test files were left unopened. This question concerns identity matching when records are rearranged, and the Tate study concerns the granularity of revision alerts. [Source archive](https://github.com/megagonlabs/ditto/tree/52985564a93fb11308439516d3e17a033d43ec8f/data/er_magellan/Dirty) · [DeepMatcher](https://pages.cs.wisc.edu/~anhai/papers1/deepmatcher-sigmod18.pdf) · [Ditto](https://arxiv.org/abs/2004.00584)

We represented each field as a set of lowercase Unicode letter and number tokens after NFKD normalization. Comparisons include IDF-weighted directional containment, weighted Jaccard, and both log field masses. Each model uses the same gradient-boosted classifier and threshold-fitting budget. The all-field matrix contains 16 field pairs; the candidate also permits each field to match the union on the other side. An ablation keeps only the pooled features and flattened-text control. These operations recover partial token overlap without learning token order. [Development design](design.md)

## Development results

| Candidate pairs | Positive pairs | Flattened F1 | Aligned fields | All field pairs | Field to record | Combined candidate |
|---|---:|---:|---:|---:|---:|---:|
| DBLP–ACM, 2,473 | 444 | .9405 | .9469 | .9664 | .9654 | .9671 |
| DBLP–Google Scholar, 5,742 | 1,070 | .8819 | .8974 | .8935 | .8982 | .9012 |

The combined method led all four controls on both validation releases. Its advantage over the best control was **0.066 F1 percentage points** for ACM and **0.300 points** for Google Scholar. Both missed the fixed one-point advance criterion. The strongest ACM baseline already had F1 of .9664, leaving limited headroom. The Google Scholar result shows the same shortfall at a lower baseline score. Nine ACM validation pairs and 72 Google Scholar pairs exactly matched training-file pairs. Records can also recur across distinct pairs. These pair splits cannot establish performance on new bibliographic entities. The official test and the trained Ditto comparison were reserved at this stage. **Paper count contribution: zero.** [Full thresholds and scores](run/summary.json)

## Reproduction

Run from the repository root using Bash, Node, Python, NumPy, pandas and scikit-learn. Saved row identifiers refer to the source validation file's zero-based line numbers.

```bash
set -eu
study=research_v4_2/external/catalog_revisions/linkage
raw=private_data/raw/ditto-bibliography
base=https://raw.githubusercontent.com/megagonlabs/ditto/52985564a93fb11308439516d3e17a033d43ec8f/data/er_magellan/Dirty
mkdir -p "$raw"
for d in DBLP-ACM DBLP-GoogleScholar; do
  for split in train valid; do
    curl -fsSL --retry 3 "$base/$d/$split.txt" -o "$raw/$d-$split.txt"
  done
done
sha256sum -c "$study/inputs.sha256"
work=$(mktemp -d)
node "$study/features.mjs" "$raw" "$work"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=3 python "$study/screen.py" "$work" "$work/run"
node "$study/verify.mjs" "$raw" "$work/run"
diff -r "$study/run" "$work/run"
```

## Ordered-title follow-up

On the same development files, an ordered-prefix and approximate-token matcher raised Google Scholar F1 from .9012 to .9379 and ACM from .9671 to .9697. A matched ordered-prefix model achieved .9373 and .9696. The incremental gain from cross-field assignment missed the one-point threshold on both corpora. The study includes the published SecondString scorer and saves decisions for all 8,215 pairs. [Follow-up methods, results and reproduction](soft/README.md)
