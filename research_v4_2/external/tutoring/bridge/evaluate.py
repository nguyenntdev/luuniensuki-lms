"""Evaluate response-only pairwise ranking on source-disjoint Bridge problem strings."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

HASH = {
    "train.parquet": "fbe29d64f4e11ec3e99ade4fc8375e2324c1f8c3fd3de58547bfab6dfed9acd4",
    "test.parquet": "65479ead3c79ba7c89af6dd9359bb581519c5ce33514e1a555c8c84fc7b9ce3a",
    "mrbench_v3_devset.json": "a395feab801de50d44b73e1e9b88f84824a1f1d92e15ae86842d90c2b6dbf33c",
}
POS, NEG = "teacher_response_positive", "teacher_response_negative"


def norm(text):
    return " ".join(text.lower().split())


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def features(train, test):
    configs = [dict(analyzer="word", ngram_range=(1, 2)), dict(analyzer="char_wb", ngram_range=(3, 5))]
    plans = {}
    for name, config in zip(["word", "char"], configs):
        vectorizer = TfidfVectorizer(min_df=2, sublinear_tf=True, **config)
        vectorizer.fit(pd.concat([train[POS], train[NEG]]))
        plans[name] = tuple(vectorizer.transform(d[POS])-vectorizer.transform(d[NEG]) for d in [train, test])
    plans["joint"] = tuple(sparse.hstack(x, format="csr") for x in zip(plans["word"], plans["char"]))
    return plans


def run(root, archive, out, topic=False):
    files = [root/"train.parquet", root/"test.parquet", archive]
    for p in files:
        assert hashlib.sha256(p.read_bytes()).hexdigest() == HASH[p.name]
    train, raw = [pd.read_parquet(p) for p in files[:2]]
    records = json.loads(archive.read_text())
    openings = [norm(re.split(r"\bstudent\s*:", r["conversation_history"], flags=re.I)[0]) for r in records]
    responses = {norm(v["response"]) for r in records for v in r["tutor_responses"].values()}
    for col in [POS, NEG]:
        responses.update(map(norm, train[col]))
    problems = set(map(norm, train.problem))
    if topic:
        field = "topic"
        history = lambda turns: norm(" ".join(t["text"] for t in turns))
        known = {history(turns) for turns in train.dialog_history}
        known.update(norm(re.sub(r"\b(?:tutor|student)\s*:", "", r["conversation_history"], flags=re.I)) for r in records)
        problems = set(map(norm, train.topic))
    else:
        field = "problem"
    groups, seen, kept, audit = [], set(), [], Counter()
    for i, r in raw.iterrows():
        key = norm(r[field])
        pair = tuple(sorted([norm(r[POS]), norm(r[NEG])]))
        if not key:
            reason = "blank_problem"
        elif key in problems or (not topic and any(key in s for s in openings)):
            reason = "shared_" + field
        elif topic and history(r.dialog_history) in known:
            reason = "shared_dialogue"
        elif any(s and s in responses for s in pair):
            reason = "shared_response"
        elif (key, pair) in seen:
            reason = "duplicate_pair"
        else:
            seen.add((key, pair))
            kept.append(i)
            groups.append(digest(key))
            reason = "included"
        audit[reason] += 1
    test = raw.loc[kept]
    summary = dict(sources=HASH, train=len(train), test_release=len(raw), exclusions_in_priority_order=dict(audit),
                   group_field=field, groups=len(set(groups)), archive_revision="d9dc0c40bf26f417e5eb1ab87d997d48364d1f78")
    out.mkdir(parents=True, exist_ok=True)
    if kept:
        first = (test[POS] <= test[NEG]).to_numpy()
        def choose(delta):
            return np.where(delta == 0, first, delta > 0)
        predictions = dict(first=first, known_expert=np.ones(len(test), dtype=bool))
        for name, metric in [("longer", len), ("questions", lambda t:t.count("?"))]:
            predictions[name] = choose(test[POS].map(metric)-test[NEG].map(metric))
        for name, (x, z) in features(train, test).items():
            model = LogisticRegression(C=1, fit_intercept=False, max_iter=1000, solver="liblinear", random_state=731)
            model.fit(sparse.vstack([x,-x]), np.repeat([1,0], len(train)))
            predictions[name] = choose(model.decision_function(z))
        outcomes = pd.DataFrame(predictions, dtype=int)
        outcomes.insert(0,"group",groups)
        outcomes.insert(0,"archive_index",kept)
        outcomes.to_csv(out/"decisions.csv",index=False)
        by_group = outcomes.groupby("group")
        sizes = by_group.size().to_numpy()
        rng = np.random.default_rng(731)
        draws = rng.multinomial(len(sizes), np.ones(len(sizes))/len(sizes), size=10000)
        denominators = draws @ sizes
        comparisons = {}
        for name in predictions.keys()-{"joint"}:
            d = (outcomes.joint-outcomes[name]).groupby(outcomes.group).sum().to_numpy()
            gain = float(d.sum()/len(test))
            # Reserve seven contrasts, including the unrun published reward model.
            ci = np.quantile((draws@d)/denominators,[.025/7,1-.025/7]).tolist()
            comparisons[name] = dict(gain=gain, ci=ci, passed=gain>.01 and ci[0]>0)
        summary.update(correct={k:int(v.sum()) for k,v in predictions.items()}, comparisons=comparisons)
    (out/"result.json").write_text(json.dumps(summary, indent=2, sort_keys=True)+"\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ["root","archive","out"]:
        p.add_argument(name,type=Path)
    p.add_argument("--by-topic", action="store_true")
    args = p.parse_args()
    run(args.root,args.archive,args.out,args.by_topic)
