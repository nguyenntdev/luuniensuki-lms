# Reproducing the evidence-aware experiments

Run from the repository root with Python 3.12. The lexical FEVER run is described in the [portfolio instructions](../README.md). These commands download pinned data and weights, check their SHA-256 digests, and write into a fresh output directory. For the full model check allow several GB of free disk and a CPU runtime of several minutes. The published reference outputs were generated on x86-64 Linux. Hardware, BLAS and runtime builds can affect floating-point logits.

```bash
set -euo pipefail
E=research_v4_2/external
F="$E/claim_only"
R=private_data/raw
O=$(mktemp -d)
python3.12 "$E/fetch.py" "$R" --study claim_only --study paired --study bart_original --study vitaminc
python3.12 -m venv "$O/onnx"
"$O/onnx/bin/pip" install onnxruntime==1.23.2 tokenizers==0.22.1 scipy==1.17.1
"$O/onnx/bin/python" "$F/paired.py" "$R/fever" "$O/paired"
python3.12 -m venv "$O/torch"
"$O/torch/bin/pip" install --index-url https://download.pytorch.org/whl/cpu torch==2.7.1
"$O/torch/bin/pip" install transformers==4.51.3 sentencepiece==0.2.1
USE_TF=0 "$O/torch/bin/python" "$F/bart_precision.py" "$R/fever" "$O/paired"
USE_TF=0 "$O/torch/bin/python" "$F/vitaminc.py" "$R/vitaminc" "$O/vitaminc"
"$O/onnx/bin/python" "$F/components.py" "$R/fever" "$O/paired" > "$O/components.json"
diff "$F/run/paired/components.json" "$O/components.json"
diff "$F/run/vitaminc/result.json" "$O/vitaminc/result.json"
```

The initial ONNX run used an isolated venv. The original BART and VitaminC ALBERT runs used PyTorch 2.7.1+cu118 in CPU mode, Transformers 4.51.3, and SentencePiece 0.2.1. The dedicated CPU wheel above avoids installing CUDA for reruns. Each prediction file records the release ID. Recomputing the constrained and independent counts from the stored logits requires only the lightweight ONNX environment and the two symmetric JSONL files.

## Sources

- The [FEVER Symmetric release](https://github.com/TalSchuster/FeverSymmetric/tree/fa25d17e73ea0694edc78133ec654b9f32f6db73) and [VitaminC test release](https://huggingface.co/datasets/tals/vitaminc/tree/be6febb761b0b2807687e61e0b5282e459df2fa0) provide the claims, evidence and gold labels. Their Wikipedia attribution and share-alike terms apply.
- The [Xenova BART](https://huggingface.co/Xenova/bart-large-mnli/tree/71a9d2a7c389b1a812afc3cc1668f8c877681b00) and [Xenova RoBERTa](https://huggingface.co/Xenova/roberta-large-mnli/tree/f44e410851308d901c324c31af38793f50205e91) releases supply the quantized ONNX graphs and tokenizers.
- The authors’ [BART checkpoint](https://huggingface.co/facebook/bart-large-mnli/tree/d7645e127eaf1aefc7862fd59a17a5aa8558b8ce) and [VitaminC checkpoint](https://huggingface.co/tals/albert-base-vitaminc-fever/tree/15de029c9f4e929c8f6cc56bc39fcac22f6bdbc3) supply the original weights. The port uses the authors’ label order and inference inputs. We evaluated the base model described in their evaluation script. The xlarge model belongs to a separate comparison.

## Prospective VitaminC challenge

Use the 192-page development cohort only for choosing regularization and fitting the stacks. Score every registered method on the next 128 real-revision test pages. The additional run implements the literal exclusion of all test-release titles from development. The same test checkpoint scores serve both runs. Allow several CPU hours if executing checkpoints sequentially. The dataset and checkpoint inputs are reusable across runs. [Frozen protocol](confirmatory/protocol.md) · [Development exclusion](confirmatory/page_exclusion.md)

```bash
set -euo pipefail
F=research_v4_2/external/claim_only
E=research_v4_2/external
C="$F/confirmatory"
R=private_data/raw
O=$(mktemp -d)
python3.12 -m venv "$O/env"
PY="$O/env/bin/python"
"$PY" -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.7.1
"$PY" -m pip install numpy==2.4.4 pandas==3.0.2 scipy==1.17.1 scikit-learn==1.8.0 transformers==4.51.3 tokenizers==0.21.4 sentencepiece==0.2.1 onnxruntime==1.23.2
(cd "$C" && sha256sum -c protocol.sha256 && sha256sum -c page_exclusion.sha256)
"$PY" "$E/fetch.py" "$R" --study paired --study bart_original --study vitaminc
PYTHONPATH="$E" "$PY" - "$R" "$C/inputs.json" <<'PYCODE'
from pathlib import Path
import json, sys
from fetch import fetch
for item in json.loads(Path(sys.argv[2]).read_text()):
    fetch(item, Path(sys.argv[1]))
PYCODE
export USE_TF=0 OPENBLAS_NUM_THREADS=1
for m in albert-base-vitaminc albert-base-vitaminc-mnli albert-base-vitaminc-fever albert-xlarge-vitaminc albert-xlarge-vitaminc-mnli albert-xlarge-vitaminc-fever bart-original roberta-large-mnli; do
  "$PY" "$C/challenge.py" "$R" "$O/run" --model "$m"
  "$PY" "$C/page_exclusion.py" "$R" "$O/run/all_titles" --model "$m"
done
"$PY" "$C/challenge.py" "$R" "$O/run"
"$PY" "$C/page_exclusion.py" "$R" "$O/run/all_titles"
for results in "$O/run" "$O/run/all_titles"; do
  node "$C/verify.mjs" "$R" "$O/run" "$results"
  "$PY" "$C/verify_intervals.py" "$results"
done
```

To replay from the released scores, substitute the saved `confirmatory/run` directory for the fresh run directory. Skip the inference loop. The final analysis and independent scorers use NumPy, pandas, SciPy, scikit-learn, Node.js and the two VitaminC release files. Row-level tables contain release IDs, logits or predicted labels. The pinned manifests identify the upstream model and data providers.
