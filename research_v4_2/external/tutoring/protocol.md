# Offline tutor response selection

## Data and decisions

Use the 300 conversations in the BEA 2025 MRBench development release. The six candidates with complete coverage are Gemini, GPT4, Llama31405B, Llama318B, Mistral and Sonnet. In each conversation a policy chooses one response. Score one success when its released Providing_Guidance label equals “Yes”. Expert is a separate reference in the original holdout. Inspect the 191-record official test release for annotation availability only. Its responses carry no gold annotations. The input hashes are verified before training. The authors distribute MRBench under CC BY-SA 4.0. [Dataset and provenance](https://github.com/kaushal0494/UnifyingAITutorEvaluation/tree/bbef521ddb875f2cc8a5ee798f4066965a7cfd8a)

## Splits and fitting

Lowercase and collapse whitespace in the prefix before the first case-insensitive student turn marker. Group on the SHA-256 of that string. A shared empty opening forms one group. Convert the first eight hexadecimal digits to an integer, take the remainder modulo 100, and form five consecutive buckets of width 20. The original holdout uses bucket 4 for testing, 3 for tuning, and 0–2 for fitting. The extension rotates that assignment through all five buckets. For test bucket k, development is (k−1) mod 5. Each of the 300 conversations appears in the pooled evaluation once. The original holdout is part of the pooled evaluation. Opening-group disjointness allows mathematically similar problems with different text to appear across folds.

- **Identity only.** Rank generators by their fraction of fully guiding responses on training cases. Since each generator occurs once per case, this policy selects the same tutor throughout a split.
- **Response words, with and without an identity token.** Train binary logistic regression on TF-IDF unigrams and bigrams with sublinear term frequency and minimum document frequency two. Select C from 0.1, 1, and 10 in ascending order by development selection success. Keep the first value on ties.
- **DLSU guidance graders.** Refit the four frozen-embedding classifier configurations in Tables 4 and 5 of the DLSU paper using all three released label classes. Embed the candidate response alone. Rank the six responses by the predicted probability of “Yes”. Use the authors’ Track 3 settings for the XGBoost and single-hidden-layer MLP heads. Use frozen full-precision ONNX exports, attention-mask mean pooling plus L2 normalization for MiniLM (128 tokens) and the unnormalized CLS representation for GTE (8192 tokens). The local MLP iteration cap is 1000, with seed 42. The saved split metadata records actual iteration counts. Local fits use the six eligible tutors and the group-disjoint training portion only. These are method reproductions. DLSU selected its hyperparameters using the same underlying development archive, which limits independence from prior model selection. [DLSU system paper](https://aclanthology.org/2025.bea-1.101/) · [MiniLM release](https://huggingface.co/sentence-transformers/all-MiniLM-L12-v2/tree/a50ef00143b4d5391434df20ae11632588ac25be) · [GTE release](https://huggingface.co/Alibaba-NLP/gte-modernbert-base/tree/e7f32e3c00f91d699e8c43b53106206bcc72bb22)
- **Selection and uncertainty.** Break score ties by alphabetical tutor name. The oracle counts conversations with at least one “Yes” among the same six responses. Report observed successes, fixed-policy misses recovered and fixed-policy successes lost. For paired intervals resample complete opening groups 10,000 times with seed 42, preserving case weighting. Intervals condition on fitted predictions and omit model-refit uncertainty.
- **Source transfer.** Recover MathDial and Bridge provenance by matching both conversation ID and normalized full history against V2. For each direction, test on all linked target-source cases. Exclude any overlapping target groups from the origin sample, use bucket 3 of the origin for tuning and the remaining origin groups for fitting. The evaluation uses V3 labels throughout. The source-linked cases also appear in the pooled analysis.

## Reproduce

Run from the repository root with Python 3.12 and curl. The downloads require about 740 MB. The two result files contain the paired summaries and the six candidate scores for every held-out decision.

```bash
study=research_v4_2/external/tutoring
inputs=$(mktemp -d)
python3.12 -m venv "$inputs/venv"
py="$inputs/venv/bin/python"
"$py" -m pip install numpy==2.4.4 pandas==3.0.2 scipy==1.17.1 scikit-learn==1.8.0 onnxruntime==1.22.1 tokenizers==0.21.4 xgboost-cpu==3.0.4
data=https://raw.githubusercontent.com/kaushal0494/UnifyingAITutorEvaluation/bbef521ddb875f2cc8a5ee798f4066965a7cfd8a
for name in mrbench_v3_devset mrbench_v3_testset; do
  curl -fLsS "$data/BEA_Shared_Task_2025_Datasets/$name.json" -o "$inputs/$name.json"
done
curl -fLsS "$data/MRBench/MRBench_V2.json" -o "$inputs/MRBench_V2.json"
mini=https://huggingface.co/sentence-transformers/all-MiniLM-L12-v2/resolve/a50ef00143b4d5391434df20ae11632588ac25be
gte=https://huggingface.co/Alibaba-NLP/gte-modernbert-base/resolve/e7f32e3c00f91d699e8c43b53106206bcc72bb22
for name in tokenizer.json onnx/model.onnx; do
  curl -fLsS "$mini/$name?download=true" -o "$inputs/${name##*/}"
  curl -fLsS "$gte/$name?download=true" -o "$inputs/gte-${name##*/}"
done
"$py" "$study/evaluate.py" "$inputs/mrbench_v3_devset.json" "$inputs/original"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 "$py" "$study/compare.py" "$inputs" "$inputs/replay"
diff "$study/run/comparison.json" "$inputs/replay/comparison.json"
```

Scores may differ at floating-point precision across hardware and library builds. The primary selection totals can also be reconstructed by choosing the greatest score for each split, case, and policy in the archived CSV.
