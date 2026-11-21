"""Rank essays for a third read in pools held out at the writer level."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

TRAITS = ["task_achievement", "coherence_cohesion", "lexical_resource", "grammar_accuracy"]
RANKERS = ["candidate","matched","peer_gap","ai_gap","ai_spread","equal_gaps","oracle"]


def digest(txt):
    return hashlib.sha256(txt.encode()).hexdigest()


def cases(path):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == "3cb2afa8048b2924dbc0b91d4993fe697375fce8c616b52a10d4de59dd2cc877"
    source = pd.read_csv(path)
    writers = sorted(source.student_id.unique(),key=lambda w:digest("p11-triage-1:"+w))
    assert len(writers)==38
    fold = {w:i//19 for i,w in enumerate(writers)}
    rows, features = [], []
    for (w,task), essay in source.groupby(["student_id","task"]):
        humans = essay.loc[essay.rater_type=="Human"].set_index("rater_id")[TRAITS].sort_index()
        automated = essay.loc[essay.rater_type=="AI",TRAITS].to_numpy()
        assert humans.shape==(3,4) and automated.shape==(4,4)
        for target in humans.index:
            p,q = humans.drop(target).to_numpy()
            midpoint = (p+q)/2
            ai = automated.mean(axis=0)
            dispersion = automated.std(axis=0)
            peer_gap, ai_gap = abs(p-q), abs(ai-midpoint)
            discrepancy = abs(humans.loc[target].to_numpy()-midpoint).mean()
            outside = ((ai<np.minimum(p,q)) | (ai>np.maximum(p,q))).mean()
            extra = [abs(np.mean(ai-midpoint)), outside, abs(np.mean(p-q))]
            features.append([task-1,*peer_gap,*ai_gap,*dispersion,*midpoint,*extra])
            rows.append(dict(writer=w,task=task,fold=fold[w],target=target,value=discrepancy,
                             tie=digest(f"review-order:{w}:{task}"),peer_gap=peer_gap.mean(),
                             ai_gap=ai_gap.mean(),ai_spread=dispersion.mean(),
                             equal_gaps=(peer_gap.mean()+ai_gap.mean())/2))
    return pd.DataFrame(rows),np.array(features)


def run(path,out):
    data, features = cases(path)
    pools = []
    for (fold,rater), test in data.groupby(["fold","target"]):
        train = (data.fold!=fold)&(data.target==rater)
        assert len(test)==train.sum()==38
        assert set(test.writer).isdisjoint(data.loc[train,"writer"])
        for name, width in [("candidate",20),("matched",17)]:
            model=make_pipeline(StandardScaler(),Ridge(alpha=10))
            model.fit(features[train,:width],data.loc[train,"value"])
            data.loc[test.index,name]=model.predict(features[test.index,:width])
        records=data.loc[test.index].copy()
        records["oracle"]=records.value
        k=len(records)//5
        for name in RANKERS:
            chosen=records.sort_values([name,"tie"],ascending=[False,True]).index[:k]
            data.loc[test.index,"chosen_"+name]=test.index.isin(chosen).astype(int)
            pools.append([fold,rater,name,k,data.loc[chosen,"value"].sum(),test.value.sum()])
        pools.append([fold,rater,"random_expectation",k,k*test.value.mean(),test.value.sum()])
    stats=pd.DataFrame(pools,columns=["fold","target","ranker","budget","captured","available"])
    by=stats.groupby("ranker")[["budget","captured","available"]].sum()
    metric=(by.captured/by.budget)
    folded=stats.groupby(["fold","ranker"])[["budget","captured"]].sum()
    means=(folded.captured/folded.budget).unstack()
    comparisons={m:dict(gain=metric.candidate-value,
                        both_folds_positive=bool((means.candidate>means[m]).all()))
                 for m,value in metric.items() if m not in ("candidate","oracle")}
    passed=all(c["gain"]>=.05 and c["both_folds_positive"] for c in comparisons.values())
    out.mkdir(parents=True,exist_ok=True)
    data.to_csv(out/"decisions.csv",index=False)
    stats.to_csv(out/"pools.csv",index=False)
    report=dict(writers=data.writer.nunique(),essays=76,rotations=len(data),per_method=int(by.budget.iloc[0]),
                mean_discovered=metric.to_dict(),share=(by.captured/by.available).to_dict(),
                contrasts=comparisons,advance=passed)
    (out/"result.json").write_text(json.dumps(report,indent=2)+"\n")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("out",type=Path)
    a=p.parse_args()
    run(a.source,a.out)
