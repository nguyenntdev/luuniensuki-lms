"""Replay frozen GPU forecasts under the same ranking and outcome contracts."""
import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import log_loss, roc_auc_score

from export import key_digest
from frontier import evaluate
from screen import prepare, report
from verify import verify


def evaluate_all(raw, forecasts, out):
    out.mkdir(parents=True,exist_ok=True)
    parent=Path(__file__).resolve().parents[1]/'run'
    logistic_frontier=json.loads((parent/'frontier.json').read_text())
    all_results, bounds, common, scores = {}, {}, {}, {}
    for name in ('oulad','uci697'):
        with np.load(forecasts/f'{name}_forecasts.npz') as f:
            matrix=f['scores']
            rows_digest=f['ordered_keys'].item()
        def frozen(train,test,cat,num,history):
            assert matrix.shape==(41,len(test)) and key_digest(test.key)==rows_digest
            assert np.all((matrix>0)&(matrix<1))
            return matrix
        results=report(name,raw,out,scorer=frozen)
        all_results[name]=results
        bounds[name]=evaluate(name,raw,results,scorer=frozen)
        fixed_floor=logistic_frontier[name]['required_captures']
        common[name]=evaluate(name,raw,results,scorer=frozen,required_captures=fixed_floor)
        data,baseline,labels,_=prepare(name,raw)
        assert key_digest(data.key)==rows_digest
        y=data.key.map(labels(set(data.key))).to_numpy()
        scores[name]={}
        for group,mask in [('all',np.ones(len(y),bool)),('female',data.female),('male',~data.female)]:
            scores[name][group]={kind:dict(auc=roc_auc_score(y[mask],p[mask]),loss=log_loss(y[mask],p[mask]))
                                 for kind,p in [('logistic',baseline[0]),('boosted',matrix[0])]}
    for filename,table in [('results',all_results),('frontier',bounds),('logistic_floor',common),('risk_scores',scores)]:
        (out/f'{filename}.json').write_text(json.dumps(table,indent=2)+'\n')
    verify(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('raw',type=Path)
    p.add_argument('forecasts',type=Path)
    p.add_argument('out',type=Path)
    a=p.parse_args()
    evaluate_all(a.raw,a.forecasts,a.out)
