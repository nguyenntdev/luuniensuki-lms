"""Compare ordinary and paired inference with the VitaminC authors' checkpoint."""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from transformers import AlbertForSequenceClassification, AlbertTokenizer

TEST_SHA = "7ad1808dbc30c62e0a1427a53022d0dfaff668a1fde3c4b612a2d266edd753ad"


def paired_predictions(rows, logits):
    original = logits.argmax(axis=1)
    selected = original.copy()
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        groups[(row["case_id"], row["claim"])].append(i)
    pairs = [group for group in groups.values() if len(group) == 2]
    for indices in pairs:
        local = logits[indices]
        other = local[:, 1:].argmax(axis=1) + 1
        margins = local[:, 0] - local[np.arange(2), other]
        # Sorting the two release IDs makes the decision invariant to stream order in a tie.
        best = min(range(2), key=lambda j: (-margins[j], rows[indices[j]]["unique_id"]))
        selected[indices] = other
        selected[indices[best]] = 0
    return original, selected, pairs


def evaluate(root, output):
    with (root / "test.jsonl").open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != TEST_SHA:
            raise ValueError("Unexpected VitaminC release")
    records = [json.loads(line) for line in (root / "test.jsonl").read_text().splitlines()]
    real = [r for r in records if r["revision_type"] == "real"]
    pages = sorted({r["page"] for r in real}, key=lambda name: hashlib.sha256(name.encode()).digest())
    sample = set(pages[:128])
    rows = [r for r in real if r["page"] in sample]
    weights = root / "albert-base-vitaminc-fever"
    with Path(__file__).with_name("vitaminc_inputs.sha256").open() as manifest:
        for line in manifest:
            digest, filename = line.strip().split(maxsplit=1)
            with (weights / filename).open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
                    raise ValueError(f"Unexpected {filename}")
    tokenizer = AlbertTokenizer.from_pretrained(weights, local_files_only=True)
    model = AlbertForSequenceClassification.from_pretrained(weights, local_files_only=True).eval()
    labels = [model.config.id2label[i] for i in range(3)]
    if labels != ["SUPPORTS", "REFUTES", "NOT ENOUGH INFO"]:
        raise ValueError(f"Unexpected checkpoint labels {labels}")
    torch.set_num_threads(3)
    parts = []
    with torch.inference_mode():
        for first in range(0, len(rows), 8):
            batch = rows[first:first + 8]
            tokens = tokenizer([r["evidence"] for r in batch], [r["claim"] for r in batch],
                               padding=True, truncation=True, max_length=256, return_tensors="pt")
            parts.append(model(**tokens).logits.numpy())
    logits = np.concatenate(parts)
    base, paired, pairs = paired_predictions(rows, logits)
    gold = np.array([labels.index(r["label"]) for r in rows])
    ok = base == gold
    new_ok = paired == gold
    difference = new_ok.astype(int) - ok.astype(int)
    page_ids = np.array([pages[:128].index(r["page"]) for r in rows])
    counts = np.bincount(page_ids)
    gains = np.bincount(page_ids, weights=difference)
    indices = np.random.default_rng(42).integers(0, len(sample), (10000, len(sample)))
    draws = gains[indices].sum(axis=1) / counts[indices].sum(axis=1)
    report = dict(release_rows=len(records), real_rows=len(real), real_pages=len(pages),
                  sample_rows=len(rows), sample_pages=len(sample), claim_pairs=len(pairs),
                  gold_violates_one_support=sum(sum(gold[g] == 0) != 1 for g in pairs).item(),
                  independent_correct=int(ok.sum()), paired_correct=int(new_ok.sum()),
                  independent_per_label={label: int(ok[gold == i].sum()) for i, label in enumerate(labels)},
                  paired_per_label={label: int(new_ok[gold == i].sum()) for i, label in enumerate(labels)},
                  label_counts={label: int(sum(gold == i)) for i, label in enumerate(labels)},
                  rescued=int(sum(new_ok & ~ok)), regressed=int(sum(ok & ~new_ok)),
                  difference=float(difference.mean()), page_bootstrap_ci95=np.quantile(draws,[.025,.975]).tolist())
    output.mkdir(exist_ok=True, parents=True)
    with (output / "predictions.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["unique_id", "page_index", "gold", "independent", "paired", *labels])
        for i, row in enumerate(rows):
            writer.writerow([row["unique_id"], page_ids[i], labels[gold[i]], labels[base[i]],
                             labels[paired[i]], *logits[i].tolist()])
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vitaminc", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    evaluate(args.vitaminc, args.output)
