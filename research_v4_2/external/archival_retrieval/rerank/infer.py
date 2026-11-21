"""Score the same claim--paper pairs using full and focused text on CUDA."""
import argparse
import csv
import json
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


def infer(rows, folder, dest):
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    if not torch.cuda.is_available():
        raise RuntimeError("This run requires the external CUDA device")
    tok = AutoTokenizer.from_pretrained(folder,local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(folder,local_files_only=True).to("cuda").eval()
    print(torch.cuda.get_device_name(),torch.__version__,flush=True)
    scores = {}
    with torch.inference_mode():
        for field in ("abstract","focus"):
            scores[field] = [None]*len(rows)
            # Stable length buckets reduce padding. Restore row order before saving.
            order = sorted(range(len(rows)),key=lambda i:len(rows[i][field]))
            for j in range(0,len(order),8):
                ix = order[j:j+8]
                batch = tok([rows[i]["claim"] for i in ix],[rows[i][field] for i in ix],
                            truncation=True,max_length=384,padding=True,return_tensors="pt").to("cuda")
                values = model(**batch).logits.flatten().cpu().tolist()
                for i,v in zip(ix,values,strict=True):
                    scores[field][i] = v
            print(field,len(rows),"peak bytes",torch.cuda.max_memory_allocated(),flush=True)
    with dest.with_suffix(".tmp").open("w",newline="") as f:
        writer = csv.writer(f,lineterminator="\n")
        writer.writerow(["query","doc","abstract","focus"])
        writer.writerows((r["query"],r["doc"],scores["abstract"][i],scores["focus"][i]) for i,r in enumerate(rows))
    dest.with_suffix(".tmp").replace(dest)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("input",type=Path)
    p.add_argument("model",type=Path)
    p.add_argument("dest",type=Path)
    a=p.parse_args()
    infer([json.loads(line) for line in a.input.open()],a.model,a.dest)
