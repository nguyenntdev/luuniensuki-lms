"""Run fixed MNLI models on supplied FEVER evidence and compare decoding rules."""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import onnxruntime as ort
import scipy
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csc_matrix
from tokenizers import Tokenizer

MODELS = ("bart-large-mnli", "roberta-large-mnli")
SPLITS = ("dev", "test")


def score_rows(folder, rows):
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    session = ort.InferenceSession(str(folder / "model_quantized.onnx"), options,
                                   providers=["CPUExecutionProvider"])
    config = json.loads((folder / "config.json").read_text())
    labels = [config["id2label"][str(i)].lower() for i in range(3)]
    tokenizer = Tokenizer.from_file(str(folder / "tokenizer.json"))
    tokenizer.enable_padding(pad_id=config["pad_token_id"], pad_token="<pad>")
    scores = []
    for first in range(0, len(rows), 8):
        examples = rows[first:first + 8]
        encodings = tokenizer.encode_batch([(r["evidence"], r["claim"]) for r in examples])
        inputs = {"input_ids": np.array([e.ids for e in encodings], dtype=np.int64),
                  "attention_mask": np.array([e.attention_mask for e in encodings], dtype=np.int64)}
        logits, = session.run(["logits"], inputs)
        scores.extend(logits)
    order = [labels.index(name) for name in ("contradiction", "neutral", "entailment")]
    return np.asarray(scores, dtype=float)[:, order]


def string_groups(rows, key):
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        groups[row[key]].append(i)
    return list(groups.values())


def decode_balanced(margin, groups):
    if any(len(ids) % 2 for ids in groups):
        return None, "odd group size"
    row_idx = np.repeat(np.arange(len(groups)), [len(ids) for ids in groups])
    col_idx = np.concatenate(groups)
    incidence = csc_matrix((np.ones(len(col_idx)), (row_idx, col_idx)),
                           shape=(len(groups), len(margin)))
    quotas = np.array([len(ids) // 2 for ids in groups])
    result = milp(-margin, integrality=np.ones(len(margin)), bounds=Bounds(0, 1),
                  constraints=LinearConstraint(incidence, quotas, quotas),
                  options={"mip_rel_gap": 0})
    if not result.success:
        return None, result.message
    select = (result.x > .5).astype(int)
    if not np.array_equal(incidence @ select, quotas):
        raise ValueError("Decoded assignment violates a group quota")
    return select, "optimal"


def comparison(rows, logits):
    claims = string_groups(rows, "claim")
    evidence = string_groups(rows, "evidence")
    margin = logits[:, 2] - logits[:, 0]
    independent = (margin > 0).astype(int)
    choices = {"independent": (independent, "ok"),
               "claim_balance": decode_balanced(margin, claims),
               "joint_balance": decode_balanced(margin, claims + evidence)}
    gold = np.array([{"SUPPORTS": 1, "REFUTES": 0}[r["label"]] for r in rows])
    base_correct = independent == gold
    result = {"n": len(rows), "claims": len(claims), "evidence_strings": len(evidence),
              "unbalanced_gold_claim_groups": sum(2 * sum(gold[g]) != len(g) for g in claims).item(),
              "unbalanced_gold_evidence_groups": sum(2 * sum(gold[g]) != len(g) for g in evidence).item(),
              "three_way_correct": int(sum(logits.argmax(axis=1) == 2 * gold)), "methods": {}}
    fields = {"id": [r["id"] for r in rows], "supports_gold": gold,
              "contradiction": logits[:, 0], "neutral": logits[:, 1], "entailment": logits[:, 2]}
    for name, (pred, status) in choices.items():
        if pred is None:
            result["methods"][name] = {"status": status}
            continue
        correct = pred == gold
        result["methods"][name] = dict(status=status, correct=int(correct.sum()),
                                       complete_claims=sum(bool(correct[g].all()) for g in claims),
                                       rescued=int(sum(correct & ~base_correct)),
                                       regressed=int(sum(~correct & base_correct)))
        fields[name] = pred
    return result, fields


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fever", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=True, parents=True)
    with Path(__file__).with_name("paired_inputs.sha256").open() as manifest:
        for line in manifest:
            expected, filename = line.strip().split(maxsplit=1)
            with (args.fever / filename).open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != expected:
                    raise ValueError(f"Input differs from pinned release: {filename}")
    summary = {"onnxruntime": ort.__version__, "scipy": scipy.__version__, "models": {}}
    for model in MODELS:
        summary["models"][model] = {}
        for split in SPLITS:
            path = args.fever / f"symmetric_{split}.jsonl"
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            if len({r["id"] for r in rows}) != len(rows):
                raise ValueError(f"Nonunique row ID in {path}")
            scores = score_rows(args.fever / "nli" / model, rows)
            report, fields = comparison(rows, scores)
            summary["models"][model][split] = report
            with (args.output / f"{model}-{split}.csv").open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(fields)
                writer.writerows(zip(*fields.values(), strict=True))
    (args.output / "result.json").write_text(json.dumps(summary, indent=2) + "\n")
