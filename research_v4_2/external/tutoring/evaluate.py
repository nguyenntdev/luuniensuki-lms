"""Compare offline selection policies on the archived MRBench shared task dev set."""
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

TUTORS = sorted(["Sonnet","Llama318B","Llama31405B","GPT4","Mistral","Gemini"])
SOURCE_SHA = "a395feab801de50d44b73e1e9b88f84824a1f1d92e15ae86842d90c2b6dbf33c"


def run(path):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    items = []
    for record in json.loads(raw):
        convo = record["conversation_history"]
        prompt = re.split(r"\bstudent\s*:",convo,maxsplit=1,flags=re.I)[0]
        key = hashlib.sha256(" ".join(prompt.lower().split()).encode()).hexdigest()
        bucket = int(key[:8],16) % 100
        for name in TUTORS + ["Expert"]:
            res = record["tutor_responses"][name]
            label = res["annotation"]["Providing_Guidance"]
            assert label in {"Yes","No","To some extent"}
            items.append(dict(case=record["conversation_id"],group=key,bucket=bucket,tutor=name,
                              text=f'tutor_{name} '+res["response"], y=int(label=="Yes")))
    frame = pd.DataFrame(items)
    experts = frame.query("tutor == 'Expert'").set_index("case").y
    data = frame[frame.tutor.isin(TUTORS)]
    assert not data.duplicated(["case","tutor"]).any()
    train, dev, test = [data[data.bucket.between(lo,hi)].copy() for lo,hi in ((0,59),(60,79),(80,99))]
    fixed = train.groupby("tutor").y.mean().idxmax()
    vectorizer = TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True)
    x = vectorizer.fit_transform(train.text)
    best = -1
    trials = []
    for c in [.1,1.,10.]:
        model = LogisticRegression(C=c,max_iter=1000).fit(x,train.y)
        prob = pd.Series(model.predict_proba(vectorizer.transform(dev.text))[:,1],index=dev.index)
        score = dev.loc[prob.groupby(dev.case).idxmax()].y.mean()
        trials.append(dict(c=c,success=score))
        if score > best:
            best, selected = score, model
    scores = pd.Series(selected.predict_proba(vectorizer.transform(test.text))[:,1],index=test.index)
    picks = test.loc[scores.groupby(test.case).idxmax()].set_index("case")
    rows = picks[["group","tutor","y"]].rename(columns={"y":"candidate"}).copy()
    rows["fixed"] = test[test.tutor == fixed].set_index("case").y
    rows["expert"] = experts.reindex(rows.index)
    diff = rows.candidate - rows.fixed
    pos, neg = int((diff>0).sum()), int((diff<0).sum())
    groups = diff.groupby(rows.group).agg(["sum","size"]).to_numpy()
    boot = np.random.default_rng(42).choice(len(groups),(10000,len(groups)))
    ci = np.quantile(groups[boot,0].sum(axis=1)/groups[boot,1].sum(axis=1),[.025,.975])
    return rows, dict(snapshot=SOURCE_SHA, conversations=[f.case.nunique() for f in (train,dev,test)],
                      prompts=[f.group.nunique() for f in (train,dev,test)], baseline=fixed,trials=trials,
                      rates=rows[["candidate","fixed","expert"]].mean().to_dict(),gain=diff.mean(),ci95=ci.tolist(),
                      candidate_only=pos,baseline_only=neg,paired_case_p=binomtest(pos,pos+neg).pvalue if pos+neg else 1.)


if __name__ == "__main__":
    rows, result = run(Path(sys.argv[1]))
    out = Path(sys.argv[2])
    out.mkdir(parents=True,exist_ok=True)
    rows.to_csv(out/"decisions.csv")
    (out/"result.json").write_text(json.dumps(result,indent=2)+"\n")
