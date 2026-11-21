# Does sentence position improve SciFact evidence retrieval?

Given a claim and its cited abstract, the learned position prior raised mean reciprocal rank (MRR) from .70085 to .78624 on 129 claim–document pairs from 85 source components. The paired improvement over the selected lexical baseline was .08539 (familywise 95% interval [.01198, .16232]). Giving the same position scores to sentences in increasing order of index reached .77009 MRR. The learned prior's advantage over that control was .01615 (interval [−.01102, .04567]), so the study did not meet its prespecified screen. These comparisons use internal development partitions of the official SciFact training data. The official development release remains reserved. [Protocol](protocol.md) · [Results](run/metrics.json)

| Ranker | MRR | Recall@3 |
| --- | ---: | ---: |
| Word TF-IDF | .68405 | .68669 |
| Character TF-IDF, selected lexical ranker | .70085 | .71899 |
| Tuned BM25 | .72081 | .72933 |
| Lexical + learned position | .78624 | .79134 |
| Lexical + matched later-first position | .77009 | .78811 |
| Lexical + matched earlier-first position | .70085 | .71899 |
| Lexical + matched hash-order position | .70085 | .71899 |
| Learned position alone | .55571 | .58721 |
| Later-first position alone | .52638 | .56525 |
| Earlier-first position alone | .22624 | .16990 |

The earlier experiment measured lexical matches in neighboring sentences and selected its weight within the same official training release. This follow-up fits evidence-label rates by relative sentence position. Source components keep claims and cited documents together across fitting (317 pairs), selection (118), and screening (129). The refitted rate peaks in the fourth of five position bins. The lexical search selected character TF-IDF and the learned and later-first offsets each used a weight of .40. The earlier-first and hash-order controls both selected zero and therefore reproduce the lexical baseline. Standalone BM25 had the highest screen MRR among the purely lexical rankers. Its score is descriptive because the paired analysis prespecified the selection winner as the lexical comparator. [Earlier study](../README.md) · [Selection scores and counts](run/metrics.json)

MRR scores the first relevant sentence in the supplied abstract. Recall@3 counts the fraction of annotated sentences retrieved in three ranks. The learned and later-first methods differed by .00323 in recall@3 (descriptive paired 95% interval [−.02778, .03519]). Resampling source components accounts for claims linked by citations within this development split and conditions on the fitted ranking rules. The experiment supplies the document and evaluates individual annotated sentences. A full rationale, stance decision, or search over documents would require a different endpoint. The training data overlaps with earlier SciFact experiments in this repository. [Saved rankings and pair outcomes](run/predictions.jsonl)

## Reproduction

Use the original SciFact archive at `private_data/raw/scifact/data.tar.gz`. Follow the archive download step in the [parent instructions](../../README.md). The evaluator verifies the archive and frozen protocol before running and reads only the corpus and official training members. The saved run contains IDs, ranks, derived outcome measures and aggregate counts. Keep source files in the raw cache outside Git.

Run from the repository root. The saved run used Python 3.12.3, NumPy 2.4.4, SciPy 1.17.1 and scikit-learn 1.8.0.

```bash
set -eu
p=research_v4_2/external/archival_retrieval/evidence_sentences/position
out=$(mktemp -d)
(cd "$p" && sha256sum -c protocol.sha256)
taskset -c 0-11 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python "$p/evaluate.py" --out "$out"
diff -u "$p/run/metrics.json" "$out/metrics.json"
cmp "$p/run/predictions.jsonl" "$out/predictions.jsonl"
taskset -c 0-11 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python -m pytest tests/research_v4_2 -q
```
