import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

FILES = {"train":"eba7e8f87076753f8494718b9a857827af7bf73e76c9e4b75420207d26e588b6",
         "shared_task_dev":"e89865bfe1b4dd054e03dd57d7241a6fde24862905f31117cf0cd719f7c78df7"}


def run(root,out):
    tables = []
    for name,sha in FILES.items():
        path = root/(name+".jsonl")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == sha
        tables.append(pd.read_json(path,lines=True)[["id","claim","label"]])
    train,test = tables
    normalize = lambda col: col.str.casefold().str.split().str.join(" ")
    train = train.loc[~normalize(train.claim).isin(normalize(test.claim))]
    gold = test.label.to_numpy()
    predictions = test[["id","label"]].copy()
    majority = np.repeat(train.label.mode()[0],len(test))
    result = {"n_train":len(train),"n_dev":len(test),"majority_accuracy":accuracy_score(gold,majority)}
    for n in [1,2]:
        vec = TfidfVectorizer(ngram_range=(1,n),sublinear_tf=True,min_df=3,max_features=120000)
        x = vec.fit_transform(train.claim)
        model = LogisticRegression(C=1.,max_iter=500).fit(x,train.label)
        p = model.predict_proba(vec.transform(test.claim))
        labels = model.classes_[p.argmax(axis=1)]
        high = (p.max(axis=1)>=.9) & (labels=="SUPPORTS")
        result[str(n)] = dict(accuracy=accuracy_score(gold,labels),macro_f1=f1_score(gold,labels,average="macro"),
                              support_high_count=int(high.sum()),
                              support_high_precision=float((gold[high]=="SUPPORTS").mean()) if high.any() else None)
        predictions["prediction_"+str(n)] = labels
        predictions["confidence_"+str(n)] = p.max(axis=1)
    out.mkdir(parents=True,exist_ok=True)
    predictions.to_csv(out/"predictions.csv.gz",index=False,compression={"method":"gzip","mtime":0})
    (out/"result.json").write_text(json.dumps(result,indent=2)+"\n")


if __name__ == "__main__":
    run(Path(sys.argv[1]),Path(sys.argv[2]))
