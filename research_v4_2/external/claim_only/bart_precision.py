"""Check the quantized BART result against the original published checkpoint."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
import torch
from tokenizers import Tokenizer
from transformers import BartForSequenceClassification, PreTrainedTokenizerFast


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("fever", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    original = args.fever / "nli/bart-original"
    tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(original / "tokenizer.json"), pad_token="<pad>")
    converted = Tokenizer.from_file(str(args.fever / "nli/bart-large-mnli/tokenizer.json"))
    model = BartForSequenceClassification.from_pretrained(original, local_files_only=True).eval()
    torch.set_num_threads(3)
    args.output.mkdir(exist_ok=True, parents=True)
    for split in ("dev", "test"):
        rows = [json.loads(line) for line in (args.fever / f"symmetric_{split}.jsonl").read_text().splitlines()]
        with (args.output / f"original-{split}.csv").open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["id", "contradiction", "neutral", "entailment"])
            with torch.inference_mode():
                for i in range(0, len(rows), 8):
                    batch = rows[i:i + 8]
                    pairs = [(r["evidence"], r["claim"]) for r in batch]
                    enc = tokenizer(pairs, padding=True, return_tensors="pt", return_token_type_ids=False)
                    converted_ids = [e.ids for e in converted.encode_batch(pairs)]
                    for row, mask, other in zip(enc.input_ids, enc.attention_mask, converted_ids, strict=True):
                        if row[mask.bool()].tolist() != other:
                            raise ValueError("Tokenization differs between source and conversion")
                    scores = model(**enc).logits.numpy()
                    order = [model.config.label2id[name] for name in ("contradiction", "neutral", "entailment")]
                    for row, score in zip(batch, scores[:, order], strict=True):
                        writer.writerow([row["id"], *score.tolist()])
