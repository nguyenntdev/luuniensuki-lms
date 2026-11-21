# Can sentence selection improve a fixed cross-encoder's retrieval of cited papers?

The SciFact source-retrieval benchmark supplies claims, candidate abstracts and cited evidence. The two encodings ask whether a shortlist document is better represented by all its text up to the token limit or by its title and three claim-matched sentences. The same MS MARCO checkpoint scores both. A single paper-level result requires the gain to survive the matched single-view rerankers. [SciFact paper](https://aclanthology.org/2020.emnlp-main.609/) · [Checkpoint and training description](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2/tree/233902d25c440f23af6f7d6e94d2946bac0bee0a) · [Design and gate](protocol.md)

Each candidate pool contains the 16 highest BM25 abstracts. All eight policies rank that pool, and the denominator includes all annotated evidence for each eligible query. Documents without an annotation receive zero relevance credit. The focus view selects up to three sentences from the abstract using lexical overlap, then restores source order. This experiment measures claim-to-paper retrieval under the lexical first stage. It does not determine whether a highlighted sentence verifies the claim. The public scientific corpus and labels might have been seen by other model developers. [Corpus and annotation licences](https://github.com/allenai/scifact/blob/master/LICENSE.md)

## Results

The full-abstract cross-encoder scored **.85771 nDCG@10** on 157 screening claims. Adding a focused view and BM25 gave .84883, a paired difference of −.00889 (simultaneous 95% interval −.04238 to .02704). The candidate beat document BM25 by .04439 and the sentence-only lexical score by .11642. Those two lexical comparisons were the only comparisons to clear the .02 margin with positive simultaneous lower bounds. Sentence selection did not improve the strongest neural comparator in this development sample. The official development set remains unopened. [All paired results](run/result.json) · [Independent checks](run/verification.json)

| Method | nDCG@10 |
|---|---:|
| Document BM25 | .80443 |
| Sentence BM25 | .73241 |
| Cross-encoder, full abstract | .85771 |
| Cross-encoder, focused abstract | .85008 |
| BM25 plus full cross-encoder | .85490 |
| BM25 plus focused cross-encoder | .84929 |
| Full and focused cross-encoders | .84791 |
| Both cross-encoders plus BM25 | .84883 |

The common shortlist retained 178 of 189 annotated documents and omitted every annotated paper for eight queries. Its oracle nDCG@10 was .94305. All 16,160 neural evaluations (8,080 pairs, two views) ran on an RTX 4060 Ti in float32 with PyTorch 2.6.0+cu124. The 348 tuning queries selected fusion weights. The screen spanned 101 source components. An independent implementation checked the fit-split optimum for each fusion grid and recomputed all seven source-component bootstrap intervals. [Pool audit](run/pool.json) · [Pair scores](run/scores.csv) · [Per-query scores](run/metrics.csv)

## Replay

From the repository root, obtain the pinned SciFact archive as described in the [retrieval reproduction instructions](../README.md). Use NumPy, pandas, scikit-learn, onnxruntime and tokenizers for local preprocessing, and PyTorch and Transformers on a CUDA machine. Only preprocessing imports the sibling module that loads the SciFact archive. The inference machine requires the model, pair list and infer.py. Keep input text and weights in private storage.

```bash
set -eu
e=research_v4_2/external/archival_retrieval/rerank
raw=private_data/raw/scifact
r="$raw/rerank"
mkdir -p "$r/model"
base=https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2/resolve/233902d25c440f23af6f7d6e94d2946bac0bee0a
for f in README.md config.json model.safetensors special_tokens_map.json tokenizer.json tokenizer_config.json vocab.txt; do
  curl --retry 3 -fsSL "$base/$f" -o "$r/model/$f"
done
sha256sum --ignore-missing -c "$e/input.sha256"
model_hashes=$(realpath "$e/model.sha256")
(cd "$r/model" && sha256sum -c "$model_hashes")
(cd "$e" && sha256sum -c protocol.sha256)
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
python "$e/prepare.py" "$raw" "$r/inputs.jsonl"
sha256sum -c "$e/input.sha256"
out=$(mktemp -d)
# Run the next line on the GPU host and return scores.csv for local evaluation.
python "$e/infer.py" "$r/inputs.jsonl" "$r/model" "$out/scores.csv"
python "$e/evaluate.py" "$r/inputs.jsonl" "$out/scores.csv" "$out"
node "$e/verify.mjs" "$r/inputs.jsonl" "$out/scores.csv" "$out"
python "$e/verify_selection.py" "$r/inputs.jsonl" "$out"
python "$e/pool.py" "$raw/data.tar.gz" "$r/inputs.jsonl"
```
