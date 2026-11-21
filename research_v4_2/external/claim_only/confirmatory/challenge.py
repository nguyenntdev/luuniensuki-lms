"""Fit a paired verifier on dev pages and score a prespecified fresh page cohort."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import softmax
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

LABELS = ["SUPPORTS", "REFUTES", "NOT ENOUGH INFO"]
AUTHORS = [f"albert-{size}-vitaminc{extra}" for size in ["base", "xlarge"]
           for extra in ["", "-mnli", "-fever"]]
MODELS = AUTHORS + ["bart-original", "roberta-large-mnli"]


def sha(path):
    with path.open("rb") as fp:
        return hashlib.file_digest(fp, "sha256").hexdigest()


def cohort(root, split):
    def records(file):
        with (root / "vitaminc" / file).open() as fp:
            return [r for line in fp if (r := json.loads(line))["revision_type"] == "real"]
    test = records("test.jsonl")
    known = {r["page"] for r in test}
    rows = test if split == "test" else records("dev.jsonl")
    pages = known if split == "test" else {r["page"] for r in rows} - known
    ordered = sorted(pages, key=lambda p: hashlib.sha256(p.encode()).digest())
    retained = set(ordered[128:256] if split == "test" else ordered[:192])
    frame = pd.DataFrame([r for r in rows if r["page"] in retained]).reset_index(drop=True)
    if frame.empty or not frame.unique_id.is_unique:
        raise ValueError("Empty cohort or duplicate IDs")
    return frame


def collect(root, frame, model_name, output):
    is_author = model_name in AUTHORS
    folder = (root / "vitaminc" / model_name if is_author else root / "fever/nli" / model_name)
    texts = list(zip(frame.evidence, frame.claim))
    if model_name == "roberta-large-mnli":
        import onnxruntime as ort
        from tokenizers import Tokenizer
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 4
        session = ort.InferenceSession(str(folder / "model_quantized.onnx"), opts, providers=["CPUExecutionProvider"])
        tok = Tokenizer.from_file(str(folder / "tokenizer.json"))
        tok.enable_truncation(max_length=256)
        tok.enable_padding(pad_id=1, pad_token="<pad>")
        blocks = []
        for k in range(0, len(texts), 8):
            ids = tok.encode_batch(texts[k:k+8])
            feeds = dict(input_ids=np.array([e.ids for e in ids], dtype=np.int64),
                         attention_mask=np.array([e.attention_mask for e in ids], dtype=np.int64))
            logits, = session.run(["logits"], feeds)
            blocks.append(logits[:, [2, 0, 1]])
        scores = np.vstack(blocks)
    else:
        import torch
        from transformers import AlbertTokenizer, AutoModelForSequenceClassification, PreTrainedTokenizerFast
        torch.set_num_threads(4)
        model = AutoModelForSequenceClassification.from_pretrained(folder, local_files_only=True).eval()
        if is_author:
            tokenizer = AlbertTokenizer.from_pretrained(folder, local_files_only=True)
            order = [int(model.config.label2id[k]) for k in LABELS]
        else:
            tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(folder/"tokenizer.json"), pad_token="<pad>")
            order = [int(model.config.label2id[k]) for k in ["entailment", "contradiction", "neutral"]]
        tokens = tokenizer(texts, truncation=True, max_length=256, return_token_type_ids=is_author)
        lengths = np.array([len(v) for v in tokens.input_ids])
        sequence = np.argsort(lengths, kind="stable")
        scores = np.empty((len(frame), 3))
        with torch.inference_mode():
            for k in range(0, len(sequence), 8):
                idx = sequence[k:k+8]
                samples = [{key: values[i] for key, values in tokens.items()} for i in idx]
                batch = tokenizer.pad(samples, return_tensors="pt")
                scores[idx] = model(**batch).logits.numpy()[:, order]
    if not np.isfinite(scores).all():
        raise ValueError(f"Invalid logits from {model_name}")
    table = pd.DataFrame(scores, columns=LABELS)
    table.insert(0, "id", frame.unique_id)
    output.parent.mkdir(exist_ok=True, parents=True)
    temp = output.with_suffix(".partial")
    table.to_csv(temp, index=False)
    temp.replace(output)


def partners(frame):
    partner = np.full(len(frame), -1)
    for group in frame.groupby(["case_id", "claim"]).indices.values():
        if len(group) == 2:
            a, b = group
            partner[[a,b]] = [b,a]
    return partner


def assign(logits, partner, ids):
    pred = logits.argmax(axis=1)
    for i,j in enumerate(partner):
        if j < 0 or i >= j:
            continue
        idx = np.array([i,j])
        pair = logits[idx]
        alternative = pair[:,1:].argmax(axis=1) + 1
        margins = pair[:,0] - pair[np.arange(2), alternative]
        winner = min(range(2), key=lambda h: (-margins[h], ids[idx[h]]))
        pred[idx] = alternative
        pred[idx[winner]] = 0
    return pred


def meta_features(matrices, partner, include_context):
    own = np.hstack(matrices)
    if not include_context:
        return own
    mask = partner >= 0
    other = np.zeros_like(own)
    other[mask] = own[partner[mask]]
    return np.column_stack([own, other, own-other, mask])


def tune(x, y, groups):
    trials = {}
    for c in (.01,.1,1.):
        out = np.empty((len(y),3))
        for train, val in GroupKFold(n_splits=3).split(x, y, groups):
            model = make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=2500, tol=1e-8))
            model.fit(x[train], y[train])
            out[val] = model.predict_proba(x[val])
        trials[c] = log_loss(y, out, labels=[0,1,2])
    chosen = min(trials, key=trials.get)
    fitted = make_pipeline(StandardScaler(), LogisticRegression(C=chosen, max_iter=2500, tol=1e-8))
    return fitted.fit(x,y), trials


def compare(raw, output):
    sets = {s: cohort(raw, s) for s in ("dev", "test")}
    mats = {}
    for s, frame in sets.items():
        mats[s] = {}
        for model in MODELS:
            df = pd.read_csv(output/s/(model+".csv"), dtype={"id":str})
            if not np.array_equal(df.id, frame.unique_id):
                raise ValueError(f"ID mismatch {model} / {s}")
            mats[s][model] = df[LABELS].to_numpy()
    neighbors = {s: partners(frame) for s,frame in sets.items()}
    test = sets["test"]
    gold = np.array([LABELS.index(k) for k in test.label])
    dev_gold = np.array([LABELS.index(k) for k in sets["dev"].label])
    test_ids = test.unique_id.to_numpy()
    scores = dict(mats["test"])
    scores["uniform_ensemble"] = np.mean([scores[n] for n in AUTHORS],axis=0)
    trials = {}
    for name, context in (("row_stack",False), ("context_stack",True)):
        x = {s:meta_features([mats[s][n] for n in AUTHORS],neighbors[s],context) for s in sets}
        model, trials[name] = tune(x["dev"],dev_gold,sets["dev"].page)
        scores[name] = model.decision_function(x["test"])
    pred = {}
    for model, values in scores.items():
        pred[model] = values.argmax(axis=1)
        pred[model + "_paired"] = assign(values, neighbors["test"], test_ids)
    candidate = "context_stack_paired"
    page, page_idx = np.unique(test.page,return_inverse=True)
    sizes = np.bincount(page_idx)
    rng = np.random.default_rng(42)
    draws = rng.integers(0,len(page),(10000,len(page)))
    flips = rng.choice([-1,1],(20000,len(page)))
    contrasts = {}
    for name, decision in pred.items():
        if name == candidate:
            continue
        d = (pred[candidate] == gold).astype(int)-(decision == gold).astype(int)
        grouped = np.bincount(page_idx,weights=d)
        ci = np.quantile(grouped[draws].sum(axis=1)/sizes[draws].sum(axis=1),[.025,.975])
        p = (1 + sum(np.abs(flips @ grouped) >= abs(d.sum())))/(len(flips)+1)
        contrasts[name] = dict(gain=float(d.mean()), ci95=ci.tolist(), p=float(p))
    maximum = 0.
    for i, r in enumerate(sorted(contrasts.values(),key=lambda v:v["p"])):
        maximum = max(maximum,min(1.,(len(contrasts)-i)*r["p"]))
        r["holm_p"] = maximum
        r["pass"] = r["gain"] >= .01 and r["ci95"][0] > 0 and maximum < .05
    pd.DataFrame(dict(id=test_ids,page=page_idx,gold=gold,**pred)).to_csv(output/"predictions.csv",index=False)
    report = dict(rows={s:len(f) for s,f in sets.items()}, pages={s:f.page.nunique() for s,f in sets.items()},
                  correct={n:int(sum(v==gold)) for n,v in pred.items()},trials=trials,contrasts=contrasts,
                  all_pass=all(v["pass"] for v in contrasts.values()),candidate=candidate)
    (output/"result.json").write_text(json.dumps(report,indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--model", choices=MODELS)
    args = parser.parse_args()
    if args.model:
        for split in ("dev","test"):
            collect(args.raw, cohort(args.raw,split), args.model, args.output/split/(args.model+".csv"))
    else:
        compare(args.raw, args.output)
