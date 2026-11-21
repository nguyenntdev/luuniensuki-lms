"""Run from this directory with the MRBench v3 devset path as argument."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline

raw = Path(sys.argv[1]).read_bytes()
assert hashlib.sha256(raw).hexdigest() == "a395feab801de50d44b73e1e9b88f84824a1f1d92e15ae86842d90c2b6dbf33c"
texts = {(str(r["conversation_id"]), t): v["response"] for r in json.loads(raw)
         for t, v in r["tutor_responses"].items()}
scores = pd.read_csv("../run/grader_scores.csv", dtype={"case": str})
scores = scores[scores.split.str.startswith("fold")].copy()
scores["text"] = [texts[k] for k in zip(scores.case, scores.tutor)]
scores["question"] = scores.text.str.contains("?", regex=False)
assert scores.groupby("group").split.nunique().max() == 1
controls = list(scores.loc[:, "identity":"minilm_mlp"])
rows = []
for fold in range(5):
    test = scores[scores.split == f"fold{fold}"].copy()
    train = scores[~scores.split.isin([f"fold{fold}", f"fold{(fold-1)%5}"])]
    fixed = train.groupby("tutor").yes.mean().idxmax()
    grader = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2),
                           Ridge(alpha=1, solver="lsqr"))
    grader.fit(train.text, train.label)
    test["ordinal"] = grader.predict(test.text)
    base = train[train.tutor == fixed].set_index("case")
    lookup = {}
    for tutor, part in train[train.tutor != fixed].groupby("tutor"):
        pairs = part.set_index("case").copy()
        pairs["diff"] = pairs.yes - base.yes
        pairs["base_q"] = base.question
        for flags, subset in pairs.groupby(["base_q", "question"]):
            mean = subset["diff"].mean()
            residual = (subset["diff"] - mean).groupby(subset.group).sum()
            n = len(residual)
            se = np.sqrt(n / (n-1) * (residual**2).sum()) / len(subset) if n > 1 else np.inf
            lookup[tutor, *flags] = mean, n >= 10 and mean - 2.58 * se > .02
    for case, part in test.groupby("case"):
        p = part.set_index("tutor").sort_index()
        picks = {k: p[k].idxmax() for k in controls + ["ordinal"]}
        assert picks["identity"] == fixed
        contrasts = [(lookup.get((t, p.at[fixed,"question"], p.at[t,"question"]), (0,False)), t)
                     for t in p.index if t != fixed]
        for name in ["ungated", "gated"]:
            eligible = [(m,t) for (m,g),t in contrasts if m > 0 and (g or name == "ungated")]
            picks[name] = min(eligible, key=lambda x: (-x[0], x[1]))[1] if eligible else fixed
        for name,t in picks.items():
            rows.append((fold, case, p.group.iloc[0], name, t, p.at[t,"yes"]))
out = pd.DataFrame(rows, columns=["fold","case","group","policy","tutor","yes"])
out.to_csv("predictions.csv", index=False)
wide = out.pivot(index=["case","group"], columns="policy", values="yes")
for k in wide:
    diff = wide.gated - wide[k]
    a = diff.groupby(level="group").agg(["sum","size"]).to_numpy()
    boot = a[np.random.default_rng(42).integers(len(a),size=(10000,len(a)))].sum(axis=1)
    print(k, wide[k].sum(), (diff>0).sum(), (diff<0).sum(), np.quantile(boot[:,0]/boot[:,1],[.025,.975]))
