# Does matching the most relevant sentence improve retrieval of cited papers?

A reader with a scientific claim may need its source paper before verifying a supporting passage. We evaluate retrieval from SciFact's 5,183 abstracts. Each training claim contributes when the authors annotated at least one paper supporting or refuting it. Relevance is binary at document level. Retrieved abstracts without a recorded evidence judgment receive zero gain. A plausible but uncited source may therefore be penalized. This task does not measure retrieval from historical museum archives or the faithfulness of a generated answer. [SciFact paper](https://aclanthology.org/2020.emnlp-main.609/) · [Original data](https://github.com/allenai/scifact)

## Question and comparators

The candidate combines three ranks for each document: whole-document BM25, BGE-small cosine similarity, and the best score obtained by a title or individual abstract sentence under sentence-level BM25. All three signals receive the same query. The hypothesis is that a short technical claim can be diluted by unrelated sentences in the paper. Tuning and screening use different groups of cited sources. The public archive contains separate official development and test files. The evaluator reads only the training claims and corpus. [Protocol](protocol.md) · [Evaluator](screen.py)

The original VeriSci pipeline used n-gram TF-IDF for open abstract retrieval. Our implementation uses the authors' English stopword and unigram–bigram settings with an explicit delimiter between title and abstract and stable document-ID ties. We also tune BM25 and run a BGE-small-en-v1.5 ONNX quantization, with the recommended query prefix, normalized CLS embeddings, and 512-token cap. The dense document encoder sees the title and abstract in order. The sparse methods can access tokens beyond the dense length cap. A dense–BM25 fusion compares against the same constituent signals and fusion-weight search. A lexical-fusion ablation measures the contribution from the dense encoder. MultiVerS studies full-document verification downstream of evidence retrieval. Its classification scores answer a different question from document ranking. [VeriSci retriever](https://github.com/allenai/scifact/blob/master/verisci/inference/abstract_retrieval/tfidf.py) · [BGE model card](https://huggingface.co/BAAI/bge-small-en-v1.5) · [MultiVerS](https://github.com/dwadden/multivers)

Reciprocal rank fusion and passage-based ranking both precede this study. The proposed weighting and evaluation on disjoint citation groups test an empirical question; the component methods supply no algorithmic priority claim. BEIR includes SciFact among its public benchmarks, so the experiment cannot establish that the pretrained encoder developers had no exposure to the collection. Only the local method-selection split is controlled. [Passage Retrieval Revisited](https://doi.org/10.1145/278459.258561) · [Reciprocal rank fusion](https://doi.org/10.1145/1571941.1572114) · [BEIR](https://openreview.net/forum?id=wCu6T5xFjeJ)

## Development results

The candidate achieved mean nDCG@10 of .88027 on 157 screening claims. Document BM25 with BGE scored .88341. Adding the sentence signal gave a difference of −.00314, with simultaneous 95% interval [−.02125, .01375]. Four of six comparisons cleared the .02 screen and a positive simultaneous lower endpoint. BGE alone also missed the required margin. The independent source check recovered all 505 eligible training queries. A later controlled cross-encoder experiment also favoured its simpler full-abstract comparator. The official development release remains reserved. [Paired scores and uncertainty](run/result.json) · [Cross-encoder experiment](rerank/README.md)

## Reproduction

Run in Bash from the repository root in Python 3.12 with NumPy, pandas, SciPy, scikit-learn, onnxruntime and tokenizers. Only the raw cache contains source text and model weights. The source archive, quantized model, and tokenizer are checksum-verified before inference. The author repository gives CC BY 4.0 for claims and evidence annotations and ODC-By 1.0 for abstracts. The BGE checkpoint is distributed under MIT. [SciFact source license](https://github.com/allenai/scifact/blob/master/LICENSE.md) · [ONNX conversion](https://huggingface.co/Xenova/bge-small-en-v1.5/tree/ea104dacec62c0de699686887e3f920caeb4f3e3)

```bash
set -eu
e=research_v4_2/external/archival_retrieval
r=private_data/raw/scifact
o=$(mktemp -d)
mkdir -p "$r/bge"
curl -fsSL --retry 3 https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz -o "$r/data.tar.gz"
base=https://huggingface.co/Xenova/bge-small-en-v1.5/resolve/ea104dacec62c0de699686887e3f920caeb4f3e3
curl -fsSL --retry 3 "$base/tokenizer.json" -o "$r/bge/tokenizer.json"
curl -fsSL --retry 3 "$base/onnx/model_quantized.onnx" -o "$r/bge/model_quantized.onnx"
(cd "$e" && sha256sum -c protocol.sha256)
export OPENBLAS_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
python "$e/dense.py" "$r"
python "$e/screen.py" "$r" "$o"
node "$e/verify.mjs" "$o"
node "$e/check_source.mjs" "$r" "$o"
```

The recorded environment used NumPy 2.4.4, pandas 3.0.2, SciPy 1.17.1, scikit-learn 1.8.0, ONNX Runtime 1.23.2 and tokenizers 0.21.4. Screening intervals resample whole source components. They condition on the particular training collection, tuned retrieval rules and pretrained weights. Because related claims may describe the same finding, treating each paraphrase as an independent resampling unit would give misleading precision.
