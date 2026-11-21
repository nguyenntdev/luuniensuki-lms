"""Refit the DLSU Track 3 systems and compare six-way selection policies."""
import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from threadpoolctl import threadpool_limits
from tokenizers import Tokenizer
from xgboost import XGBClassifier

TUTORS = sorted(["Sonnet", "Llama318B", "Llama31405B", "GPT4", "Mistral", "Gemini"])
LABELS = ["No", "To some extent", "Yes"]
HASHES = {
    "gte-model.onnx": "947f31df7effaeec4edb57c50e4ed7e0f2034d9336063f92615b92e3e0d24d78",
    "gte-tokenizer.json": "6c8aaa9a542084f2457eab775d4eeb51f92a70c0fd9de28d5edb0ddec3c08d30",
    "model.onnx": "84c56795d395593cbee215e2d635a8f0ad3199ae99f99299c44cf1eaecff3ad4",
    "tokenizer.json": "be50c3628f2bf5bb5e3a7f17b1f74611b2561a3a27eeab05e5aa30f411572037",
    "mrbench_v3_devset.json": "a395feab801de50d44b73e1e9b88f84824a1f1d92e15ae86842d90c2b6dbf33c",
    "MRBench_V2.json": "a8792225075533d15c23e1c903d0c649f19708ee93f5c3d8267eaa6ab623aac1",
    "mrbench_v3_testset.json": "5a73434fd9e1dfc73026e146d3709f95f2483a51a5e5b354bc96d981448d92cd",
}


def normalized(text):
    return " ".join(text.lower().split())


def group_id(record):
    opening = re.split(r"\bstudent\s*:", record["conversation_history"], maxsplit=1, flags=re.I)[0]
    return hashlib.sha256(normalized(opening).encode()).hexdigest()


def load_frame(folder):
    for name, digest in HASHES.items():
        with (folder / name).open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
                raise ValueError(f"Source mismatch for {name}")
    official = json.loads((folder / "mrbench_v3_testset.json").read_bytes())
    assert len(official) == 191 and all("annotation" not in response
        for record in official for response in record["tutor_responses"].values())
    v2 = json.loads((folder / "MRBench_V2.json").read_bytes())
    records = json.loads((folder / "mrbench_v3_devset.json").read_bytes())
    sources = {(r["conversation_id"], normalized(r["conversation_history"])): r["Data"] for r in v2}
    groups = {group_id(r) for r in records}
    ids = {r["conversation_id"] for r in records}
    eligible = sum(r["conversation_id"] not in ids and group_id(r) not in groups for r in v2)
    rows = []
    for record in records:
        case = record["conversation_id"]
        group = group_id(record)
        domain = sources.get((case, normalized(record["conversation_history"])), "")
        for tutor in TUTORS:
            response = record["tutor_responses"][tutor]
            label = LABELS.index(response["annotation"]["Providing_Guidance"])
            rows.append((case, group, int(group[:8], 16) % 100 // 20, domain, tutor,
                         response["response"], label, int(label == 2)))
    frame = pd.DataFrame(rows, columns=["case", "group", "fold", "domain", "tutor", "text", "label", "yes"])
    assert len(ids) == len(records) and not frame.duplicated(["case", "tutor"]).any()
    return frame, {"v2_independent_cases": eligible, "official_unlabeled_cases": len(official),
                   "source_linked_cases": frame[frame.domain != ""].groupby("domain").case.nunique().to_dict()}


def encode(folder, texts, encoder):
    prefix = "gte-" if encoder == "gte" else ""
    tokenizer = Tokenizer.from_file(str(folder / (prefix + "tokenizer.json")))
    tokenizer.enable_padding(pad_id=tokenizer.token_to_id("[PAD]"))
    tokenizer.enable_truncation(max_length=8192 if encoder == "gte" else 128)
    options = ort.SessionOptions()
    options.intra_op_num_threads = 3
    model = ort.InferenceSession(str(folder / (prefix + "model.onnx")), options, providers=["CPUExecutionProvider"])
    vectors = []
    for start in range(0, len(texts), 16):
        batch = tokenizer.encode_batch(texts[start:start + 16])
        ids = np.array([item.ids for item in batch], dtype=np.int64)
        mask = np.array([item.attention_mask for item in batch], dtype=np.int64)
        inputs = {"input_ids": ids, "attention_mask": mask}
        if encoder == "gte":
            hidden, = model.run(None, inputs)
            vectors.append(hidden[:, 0])
            continue
        inputs["token_type_ids"] = np.zeros_like(ids)
        hidden, = model.run(None, inputs)
        pooled = (hidden * mask[:, :, None]).sum(axis=1) / mask.sum(axis=1)[:, None]
        vectors.append(pooled / np.linalg.norm(pooled, axis=1, keepdims=True))
    return np.vstack(vectors).astype("float32")


def compare_split(frame, vectors, train, dev, test, split):
    parts = [set(p.group) for p in (train, dev, test)]
    assert all(parts[i].isdisjoint(parts[j]) for i, j in [(0, 1), (1, 2), (0, 2)])
    # Rows within each case are in alphabetical tutor order, including on ties.
    scores = test[["case", "group", "tutor", "label", "yes"]].copy()
    scores.insert(0, "split", split)
    scores["identity"] = test.tutor.map(train.groupby("tutor").yes.mean())
    choices = {}
    for policy in ["lexical", "identity_lexical"]:
        texts = frame.text if policy == "lexical" else "tutor_" + frame.tutor + " " + frame.text
        vocab = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
        train_x = vocab.fit_transform(texts.loc[train.index])
        dev_x = vocab.transform(texts.loc[dev.index])
        best = -1
        for c in [0.1, 1.0, 10.0]:
            model = LogisticRegression(C=c, max_iter=1000).fit(train_x, train.yes)
            prob = pd.Series(model.predict_proba(dev_x)[:, 1], index=dev.index)
            rate = dev.loc[prob.groupby(dev.case).idxmax()].yes.mean()
            if rate > best:
                best, choices[policy] = rate, c
                scores[policy] = model.predict_proba(vocab.transform(texts.loc[test.index]))[:, 1]
    classifiers = {
        "gte_mlp": MLPClassifier(hidden_layer_sizes=(150,), activation="relu", solver="adam",
                                 alpha=0.01, learning_rate="constant", max_iter=1000, random_state=42),
        "gte_xgb": XGBClassifier(n_estimators=100, max_depth=7, learning_rate=0.2,
                                 subsample=1.0, colsample_bytree=0.8, n_jobs=2, random_state=42),
        "minilm_xgb": XGBClassifier(n_estimators=50, max_depth=5, learning_rate=0.2,
                                    subsample=1.0, colsample_bytree=1.0, n_jobs=2, random_state=42),
        "minilm_mlp": MLPClassifier(hidden_layer_sizes=(150,), activation="tanh", solver="sgd",
                                    alpha=0.0001, learning_rate="constant", max_iter=1000, random_state=42),
    }
    for name, classifier in classifiers.items():
        features = vectors[name.split("_")[0]]
        classifier.fit(features[train.index], train.label)
        scores[name] = classifier.predict_proba(features[test.index])[:, list(classifier.classes_).index(2)]
    return scores, {"cases": [p.case.nunique() for p in (train, dev, test)],
                    "groups": list(map(len, parts)), "chosen_C": choices,
                    "mlp_iterations": {k: clf.n_iter_ for k, clf in classifiers.items() if k.endswith("_mlp")}}


def summarize(scores):
    outcomes = scores.groupby("case").yes.agg(["sum", "max"])
    groups = scores.groupby("case").group.first()
    policies = {}
    for name in ["identity", "lexical", "identity_lexical", "minilm_xgb", "minilm_mlp", "gte_mlp", "gte_xgb"]:
        picked = scores.loc[scores.groupby("case")[name].idxmax()].set_index("case")
        if name == "identity":
            fixed = picked.yes
        diff = picked.yes - fixed
        clustered = diff.groupby(groups).agg(["sum", "size"]).to_numpy()
        sample = np.random.default_rng(42).choice(len(clustered), (10000, len(clustered)))
        intervals = np.quantile(clustered[sample, 0].sum(axis=1) / clustered[sample, 1].sum(axis=1), [.025, .975])
        policies[name] = {"successes": int(picked.yes.sum()), "rescued": int((diff > 0).sum()),
                          "lost": int((diff < 0).sum()), "gain_ci95": intervals.tolist(),
                          "selections": picked.tutor.value_counts().to_dict()}
    return {"cases": len(outcomes), "groups": groups.nunique(), "oracle": int(outcomes["max"].sum()),
            "number_of_yes_histogram": outcomes["sum"].value_counts().sort_index().to_dict(),
            "policies": policies}


def main(folder, output):
    frame, audit = load_frame(folder)
    vectors = {name: encode(folder, frame.text.tolist(), name) for name in ["minilm", "gte"]}
    scores, details = [], {}
    def evaluate(split, train, dev, test):
        result, details[split] = compare_split(frame, vectors, train, dev, test, split)
        scores.append(result)
    for test in range(5):
        dev = (test - 1) % 5
        evaluate(f"fold{test}", frame[~frame.fold.isin([dev, test])], frame[frame.fold == dev], frame[frame.fold == test])
    for target, source in [("Bridge", "MathDial"), ("MathDial", "Bridge")]:
        test = frame[frame.domain == target]
        origin = frame[(frame.domain == source) & ~frame.group.isin(test.group)]
        evaluate("to_" + target, origin[origin.fold != 3], origin[origin.fold == 3], test)
    pooled = pd.concat(scores[:5])
    assert len(pooled) == len(frame) and not pooled.duplicated(["case", "tutor"]).any()
    results = {part.split.iloc[0]: summarize(part) for part in scores}
    results["pooled"] = summarize(pooled)
    output.mkdir(parents=True, exist_ok=True)
    pd.concat(scores).to_csv(output / "grader_scores.csv", index=False, float_format="%.12g")
    (output / "comparison.json").write_text(json.dumps({"sources": HASHES, "audit": audit, "splits": details,
                                                        "results": results}, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with threadpool_limits(limits=1, user_api="blas"):
        main(args.inputs, args.output)
