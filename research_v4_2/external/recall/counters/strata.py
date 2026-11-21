"""Describe availability of reconciliation and its measured gains by stratum."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from fit import loss


def analyze(prepared, out):
    df=pd.read_csv(prepared,usecols=["user_id","bucket","gold","prev_seen","excess_seen","excess_correct","clock_difference"]).query("bucket==13").reset_index(drop=True)
    predictions=pd.read_csv(out/"forecasts.csv.gz")
    assert np.array_equal(pd.factorize(df.user_id,sort=True)[0],predictions.learner)
    np.testing.assert_allclose(df.gold,predictions.y)
    known=df.prev_seen.notna()
    exact=known & (df.excess_seen==0)&(df.excess_correct==0)&(df.clock_difference==0)
    pos=known & (df.excess_seen>0)&df.excess_correct.between(0,df.excess_seen)
    flags={"unavailable":~known,"all_reconcile":exact,"admissible_extra_counts":pos,
           "other_counter_or_clock_difference":known & ~exact & ~pos}
    assert (sum(m.astype(int) for m in flags.values())==1).all()
    w=1/df.groupby("user_id").user_id.transform("size")
    delta=loss(df.gold,predictions.matched)-loss(df.gold,predictions.reconciled)
    result={s:dict(rows=int(m.sum()),learners=int(df.user_id[m].nunique()),learner_weight=float(w[m].sum()/w.sum()),
                   conditional_gain=float(np.average(delta[m],weights=w[m])),
                   contribution=float((w[m]*delta[m]).sum()/w.sum())) for s,m in flags.items()}
    summed=sum(v["contribution"] for v in result.values())
    assert abs(summed-json.loads((out/"result.json").read_text())["gains"]["matched"])<1e-10
    (out/"strata.json").write_text(json.dumps(result,indent=2)+"\n")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prepared",type=Path);parser.add_argument("out",type=Path)
    args=parser.parse_args()
    analyze(args.prepared,args.out)
