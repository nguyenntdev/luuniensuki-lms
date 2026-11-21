"""Run from repository root under taskset -c 0-11."""
import hashlib
import json
import re
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

out = Path(__file__).resolve().parent
archive = Path("private_data/raw/scifact/data.tar.gz")
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
assert digest == "11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be"
with tarfile.open(archive) as tar:
    def rows(name):
        return map(json.loads, tar.extractfile(f"data/{name}.jsonl"))
    corpus = {str(r["doc_id"]): r["abstract"] for r in rows("corpus")}
    claims = list(rows("claims_train"))

def selection(doc):
    return int(hashlib.sha256(doc.encode()).hexdigest(), 16) % 3 == 0

held = {r["id"] for r in claims if any(not selection(d) for d in r["evidence"])}
weights = [.25, .5, 1.]
records = []
for row in claims:
    for doc, annotations in row["evidence"].items():
        if selection(doc) and row["id"] in held:
            continue
        gold = sorted({i for a in annotations for i in a["sentences"]})
        sentences = corpus[doc]
        assert gold and 0 <= min(gold) <= max(gold) < len(sentences)
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = vec.fit_transform(sentences)
        center = (matrix @ vec.transform([row["claim"]]).T).toarray().ravel()
        tokens = lambda s: re.findall(r"\w+", s.lower())
        counts = [Counter(tokens(s)) for s in sentences]
        lengths = np.array([sum(c.values()) for c in counts])
        bm = np.zeros(len(sentences))
        for word in tokens(row["claim"]):
            tf = np.array([c[word] for c in counts])
            df = np.count_nonzero(tf)
            bm += np.log1p((len(tf)-df+.5)/(df+.5))*2.2*tf/(tf+1.2*(.25+.75*lengths/lengths.mean()))
        adjacent = np.array([np.mean(v) if (v := list(center[max(0,i-1):i])+list(center[i+1:i+2])) else 0 for i in range(len(center))])
        scores = {"bm25": bm, "tfidf": center, **{str(w): center+w*adjacent for w in weights}}
        rankings = {k: np.argsort(-s, kind="stable").tolist() for k,s in scores.items()}
        records.append(dict(doc=doc, claim=row["id"], gold=gold, selection=selection(doc), rankings=rankings))

def metrics(r, method):
    order = r["rankings"][method]
    return [1/(1+min(order.index(i) for i in r["gold"])), len(set(order[:3]) & set(r["gold"]))/len(r["gold"])]

sel = [r for r in records if r["selection"]]
ev = [r for r in records if not r["selection"]]
validation = {str(w): np.mean([metrics(r,str(w))[0] for r in sel]) for w in weights}
best = max(validation, key=validation.get)
methods = ["bm25","tfidf",best]
groups = defaultdict(list)
for r in ev:
    groups[r["doc"]].append([metrics(r,m)[0] for m in methods])
sums = np.array([np.sum(g,axis=0) for g in groups.values()])
sizes = np.array([len(g) for g in groups.values()])
rng = np.random.default_rng(42)
draws = rng.integers(len(groups),size=(5000,len(groups)))
boot = sums[draws].sum(axis=1)/sizes[draws].sum(axis=1)[:,None]
result = dict(archive_sha256=digest, selection_pairs=len(sel), evaluation_pairs=len(ev), evaluation_docs=len(groups), selection_mrr=validation, weight=best,
              mrr_recall3={m:np.mean([metrics(r,m) for r in ev],axis=0).tolist() for m in methods},
              paired_mrr_ci={f"{methods[i]} minus {methods[j]}":np.percentile(boot[:,i]-boot[:,j],[2.5,97.5]).tolist() for i,j in [(2,0),(2,1),(1,0)]})
(out/"metrics.json").write_text(json.dumps(result,indent=2)+"\n")
(out/"predictions.jsonl").write_text("".join(json.dumps(r)+"\n" for r in records))
