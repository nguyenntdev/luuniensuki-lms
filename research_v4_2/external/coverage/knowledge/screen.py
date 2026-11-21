"""Evaluate selective confidence rankings on the official development sheet only."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import xlrd
from scipy.optimize import minimize_scalar
from scipy.special import softmax
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

SOURCE = "26c0181d7f519582372ef5c09c533f809cdfb872bb0ad89f3f80cbcc1aecb2a7"


def load_training(path):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == SOURCE
    with ZipFile(path) as archive:
        book = xlrd.open_workbook(file_contents=archive.read(archive.namelist()[0]), on_demand=True)
    sheet = book.sheet_by_name("Training_Data")
    rows = [sheet.row_values(i)[:6] for i in range(1, sheet.nrows) if sheet.cell_value(i, 0) != ""]
    assert not book.sheet_loaded("Test_Data")
    return np.array([r[:5] for r in rows], dtype=float), LabelEncoder().fit_transform([r[5] for r in rows])


def fit_classifier(x, y):
    return make_pipeline(StandardScaler(), LogisticRegression(C=1, max_iter=500)).fit(x, y)


def summaries(probs, x):
    ordered = np.sort(probs, axis=1)
    ent = -(probs * np.log(probs)).sum(axis=1)/np.log(probs.shape[1])
    return np.column_stack([ordered[:, -1], ordered[:, -1]-ordered[:, -2], ent,
                            np.eye(probs.shape[1])[probs.argmax(axis=1)], x])


def fold_rankings(x, y, train, valid, fold):
    p = np.empty((len(train), len(np.unique(y[train]))))
    for a,b in StratifiedKFold(4, shuffle=True, random_state=257+fold).split(x[train], y[train]):
        p[b] = fit_classifier(x[train[a]], y[train[a]]).predict_proba(x[train[b]])
    full = fit_classifier(x[train], y[train])
    q = full.predict_proba(x[valid])
    right = p.argmax(axis=1) == y[train]
    scaler = StandardScaler().fit(x[train])
    z, v = scaler.transform(x[train]), scaler.transform(x[valid])
    detector = LogisticRegression(max_iter=500).fit(summaries(p,z),right)
    estimated = detector.predict_proba(summaries(q,v))[:,1]
    neighbors = NearestNeighbors(n_neighbors=15).fit(z).kneighbors(v,return_distance=False)
    local = (right[neighbors].sum(axis=1) + 2*right.mean())/17
    def nll(t):
        probs = softmax(np.log(p)/np.exp(t),axis=1)
        return -np.mean(np.log(probs[np.arange(len(train)), y[train]]))
    t = minimize_scalar(nll,bounds=(-3,3),method="bounded").x
    confidence = dict(blend=(estimated+local)/2, detector=estimated, local=local, max_softmax=q.max(axis=1),
                      temperature=softmax(np.log(q)/np.exp(t),axis=1).max(axis=1), margin=summaries(q,v)[:,1],
                      neighbor_agreement=(y[train][neighbors]==q.argmax(axis=1)[:,None]).mean(axis=1))
    return q.argmax(axis=1), confidence


def main(path, dest):
    x, y = load_training(path)
    dest.mkdir(parents=True,exist_ok=True)
    rows, risks = [], []
    for fold,(train,valid) in enumerate(StratifiedKFold(5,shuffle=True,random_state=257).split(x,y)):
        pred, conf = fold_rankings(x,y,train,valid,fold)
        row_risk = {}
        for name, scores in conf.items():
            order=np.lexsort((valid,-scores))
            errors=(pred!=y[valid])[order]
            row_risk[name]=float((np.cumsum(errors)/np.arange(1,len(errors)+1)).mean())
        risks.append(row_risk)
        for j,i in enumerate(valid):
            rows.append(dict(row=int(i),fold=fold,error=int(pred[j]!=y[i]),**{n:s[j] for n,s in conf.items()}))
    avg = {n:float(np.mean([r[n] for r in risks])) for n in risks[0]}
    gains={n:v-avg["blend"] for n,v in avg.items() if n!="blend"}
    with (dest/"rankings.csv").open("w") as out:
        writer=csv.DictWriter(out,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    result=dict(source_sha256=SOURCE,training_sheet_rows=len(x),folds=risks,errors=sum(r["error"] for r in rows),
                mean_aurc=avg,baseline_minus_blend=gains,passed=all(v>=.02 for v in gains.values()))
    (dest/"result.json").write_text(json.dumps(result,indent=2)+"\n")


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("archive",type=Path);ap.add_argument("out",type=Path)
    a=ap.parse_args();main(a.archive,a.out)
