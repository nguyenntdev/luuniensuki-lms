"""Train the upstream attention model and matched clock/interference trees on CUDA."""
import argparse
import copy
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import torch
from catboost import CatBoostClassifier
from sklearn.metrics import log_loss
from prepare import BASE,CLOCK,INTERF


def sakt_forecast(raw,table,windows,train,tune):
    sys.path.insert(0,str(raw.resolve()))
    from upstream.sakt import SAKT
    keys=sorted(set(table.skill[train].astype(int)))
    mapping={k:i+1 for i,k in enumerate(keys)}
    length=(windows[:,:,0]!=-2).sum(axis=1)
    encoded=pd.Series(windows[:,:,0].ravel()).map(mapping).fillna(0).astype(int).to_numpy().reshape(-1,16)
    tensors=[torch.as_tensor(a,device="cuda",dtype=t) for a,t in [
        (encoded,torch.long),(windows[:,:,1],torch.long),
        (table.skill.astype(int).map(mapping).fillna(0).astype(int).to_numpy(),torch.long),
        (table.y.to_numpy(),torch.float32)]]
    q,r,current,gold=tensors
    net=SAKT(len(keys)+1,16,64,4,.1,num_en=1).cuda()
    opt=torch.optim.Adam(net.parameters(),lr=.001)
    rng=np.random.default_rng(732)
    def batches(mask,shuffle):
        groups=[]
        for count in range(1,17):
            ids=np.flatnonzero(mask & (length==count))
            if shuffle:
                rng.shuffle(ids)
            groups.extend((chunk,count) for chunk in np.array_split(ids,max(1,(len(ids)+511)//512)) if len(chunk))
        if shuffle:
            rng.shuffle(groups)
        return groups
    def forward(idx,L):
        x=torch.as_tensor(idx,device="cuda")
        queries=current[x,None].expand(-1,L)
        return net(q[x,:L],r[x,:L],queries)[:,-1],gold[x]
    def predict(mask):
        net.eval()
        out=np.full(len(table),np.nan)
        with torch.no_grad():
            for idx,L in batches(mask,False):
                pred,_=forward(idx,L);out[idx]=pred.cpu().numpy()
        return out
    best=np.inf; history=[]
    for epoch in range(5):
        net.train()
        for idx,L in batches(train,True):
            pred,y=forward(idx,L)
            opt.zero_grad()
            torch.nn.functional.binary_cross_entropy(pred,y).backward()
            opt.step()
        value=log_loss(table.y[tune],predict(tune)[tune])
        history.append(value)
        if value<best:
            best=value;state=copy.deepcopy(net.state_dict())
    net.load_state_dict(state)
    return predict(~train),history


def run(raw,out):
    assert torch.cuda.is_available()
    torch.manual_seed(732)
    table=pd.read_pickle(raw/"cache/rows.pkl")
    windows=np.load(raw/"cache/windows.npy")
    train=(table.bucket<60).to_numpy(); tune=table.bucket.between(60,69).to_numpy(); dev=(table.bucket>=70).to_numpy()
    assert table.bucket.max()<80 and np.all(np.isin(table.y,[0,1]))
    models={};weights={}
    models["sakt"],curve=sakt_forecast(raw,table,windows,train,tune)
    for name,extra in [("base",[]),("clock",CLOCK),("interference",INTERF),("joint",CLOCK+INTERF)]:
        cols=BASE+extra
        model=CatBoostClassifier(iterations=350,learning_rate=.1,depth=6,task_type="GPU",devices="0",
                                 gpu_ram_part=.25,thread_count=2,random_seed=732,allow_writing_files=False,
                                 cat_features=["part","question","skill"],verbose=False)
        model.fit(table.loc[train,cols],table.y[train])
        assert model.get_all_params()["task_type"]=="GPU"
        p=np.full(len(table),np.nan);p[~train]=model.predict_proba(table.loc[~train,cols])[:,1]
        models[name]=p
        grid=np.arange(5)/4
        w=grid[np.argmin([log_loss(table.y[tune],(w*models["sakt"]+(1-w)*p)[tune]) for w in grid])]
        weights[name]=w
        models["blend_"+name]=w*models["sakt"]+(1-w)*p
    pred=table.loc[dev,["uid","row","start","gap_s","y"]].copy()
    names=list(models)
    for n in names: pred[n]=models[n][dev]
    losses=pd.DataFrame({n:-(pred.y*np.log(np.clip(pred[n],1e-7,1-1e-7))+
              (1-pred.y)*np.log1p(-np.clip(pred[n],1e-7,1-1e-7))) for n in names})
    target="blend_joint";controls=[n for n in names if n!=target]
    sums=losses.groupby(pred.uid).sum()
    sizes=pred.groupby("uid").size().to_numpy()
    draws=np.random.default_rng(732).multinomial(len(sums),np.full(len(sums),1/len(sums)),size=5000)
    diffs=sums[controls].to_numpy()-sums[[target]].to_numpy()
    lo,hi=np.quantile((draws@diffs)/(draws@sizes)[:,None],[.025/len(controls),1-.025/len(controls)],axis=0)
    contrasts={n:dict(gain=losses[n].mean()-losses[target].mean(),ci=[lo[i],hi[i]]) for i,n in enumerate(controls)}
    def detail(mask):return dict(events=int(mask.sum()),learners=int(table.uid[mask].nunique()),positive=int(table.y[mask].sum()))
    strata={}
    for n,mask in [("under_hour",pred.gap_s<3600),("hour_to_day",pred.gap_s.between(3600,86400,inclusive="left")),("at_least_day",pred.gap_s>=86400)]:
        strata[n]=dict(events=int(mask.sum()),loss=losses[mask].mean().to_dict())
    result=dict(device=torch.cuda.get_device_name(0),train=detail(train),tune=detail(tune),screen=detail(dev),
        tuning_epochs=curve,weights=weights,loss=losses.mean().to_dict(),strata=strata,contrasts=contrasts,
        advance=all(c["gain"]>.015 and c["ci"][0]>0 for c in contrasts.values()))
    out.mkdir(parents=True,exist_ok=True)
    pred.to_csv(out/"screen.csv.gz",index=False,compression={"method":"gzip","mtime":0})
    (out/"result.json").write_text(json.dumps(result,indent=2)+"\n")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("raw",type=Path);p.add_argument("out",type=Path)
    args=p.parse_args(); run(args.raw,args.out)
