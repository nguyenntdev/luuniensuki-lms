"""OULAD development experiment with synthetic anchor consensus and local shadow validation."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.nn import functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import importlib.util

def load_reference(path):
    spec = importlib.util.spec_from_file_location("previous_federation", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def bucket(learner):
    digest = hashlib.sha256(f"shadow-v1:{learner}".encode()).digest()
    return int.from_bytes(digest[:4], "big") % 5

def ramp(data):
    return torch.tensor(np.log1p(data)/4, device="cuda", dtype=torch.float64)

def anchor_features():
    rng = np.random.default_rng(91)
    days = rng.integers(1,62,size=512)
    recency = rng.integers(0,62-days)
    clicks = days + np.rint(np.expm1(rng.uniform(0,np.log(2049),512))).astype(int)
    sites = rng.integers(1,np.minimum(clicks,256)+1)
    a = np.column_stack((clicks, days, recency, sites))
    a[0] = [0,0,61,0]
    return ramp(a)

def network(arch):
    torch.manual_seed(73)
    layers = [nn.Linear(4,1)] if arch=="lr" else [nn.Linear(4,16),nn.Tanh(),nn.Linear(16,1)]
    return nn.Sequential(*layers,nn.Flatten(start_dim=0)).to(device="cuda",dtype=torch.float64)

def learn(net,x,y,steps,anchor=None,teacher=None):
    optimizer = torch.optim.Adam(net.parameters(),lr=.015)
    for _ in range(steps):
        optimizer.zero_grad()
        loss = F.binary_cross_entropy_with_logits(net(x),y)
        if teacher is not None:
            loss = .5*(loss+F.binary_cross_entropy_with_logits(net(anchor),teacher))
        loss.backward()
        optimizer.step()
    return net

def predictions(net, x):
    with torch.no_grad():
        return net(x).sigmoid()

def intercept(logits,y):
    offset=torch.zeros((),dtype=logits.dtype,device=logits.device)
    for _ in range(25):
        p=(logits+offset).sigmoid()
        offset-=((p-y).mean()/(p*(1-p)).mean().clamp_min(1e-8)).clamp(-1,1)
    return float(offset)

def gate(local, transferred, cal_size, y, calibrated):
    logits=[p.clamp(1e-10,1-1e-10).logit() for p in (local,transferred)]
    offsets=[intercept(v[:cal_size],y) if calibrated else 0. for v in logits]
    a,b=[(v+d).sigmoid() for v,d in zip(logits,offsets)]
    levels=torch.tensor([0.,.25,.5,.75,1.],dtype=a.dtype,device=a.device)
    mix=a[:,None]+(b-a)[:,None]*levels
    loss=F.binary_cross_entropy(mix[:cal_size],y[:,None].expand(-1,len(levels)),reduction="none")
    mean=loss.mean(dim=0)
    best=int(mean.argmin())
    cuts=torch.quantile(a[:cal_size],torch.tensor([1/3,2/3],device=a.device,dtype=a.dtype))
    strata=torch.bucketize(a.contiguous(),cuts)
    choices=[int((loss[strata[:cal_size]==j].sum(dim=0)+64*mean).argmin()) for j in range(3)]
    selected=torch.tensor(choices,device=a.device)[strata]
    output=dict(local=a,transfer=b,half=mix[:,2],single=mix[:,best],strata=mix.gather(1,selected[:,None])[:,0])
    meta=dict(offsets=offsets,cuts=cuts.tolist(),weights=[float(levels[j]) for j in choices],
              global_weight=float(levels[best]),cal_rows=cal_size)
    return output,meta

def main():
    parser=argparse.ArgumentParser()
    for k in ("source","reference","output"):parser.add_argument(k,type=Path)
    args=parser.parse_args()
    ref=load_reference(args.reference)
    rows=pd.read_csv(args.source)
    hist=rows[rows.split=="train"].copy()
    hist["cal"]=hist.learner.map(bucket)<2
    fit,cal=hist[~hist.cal],hist[hist.cal]
    dev=rows[rows.split=="dev"].copy()
    assert set(fit.learner).isdisjoint(cal.learner) and set(hist.learner).isdisjoint(dev.learner)
    modules=sorted(dev.code_module.unique())
    anchors=anchor_features()
    def xy(f):
        return ramp(f[ref.FEATURES].values),ref.tensor(f.y.values)
    groups={c:xy(fit[fit.code_module==c]) for c in modules}
    pooled_x,pooled_y=xy(fit)
    clients={c:(F.pad(x,(1,0),value=1),y) for c,(x,y) in groups.items()}
    start=ref.tensor(np.zeros(5))
    avg=ref.federate(clients,start,0)
    prox=ref.federate(clients,start,.1)
    base={}
    local={}
    import copy
    for arch in ("lr","mlp"):
        for c,(x,y) in groups.items():
            base[arch,c]=learn(network(arch),x,y,160)
            local[arch,c]=learn(copy.deepcopy(base[arch,c]),x,y,100)
        dev["pooled_"+arch]=predictions(learn(network(arch),pooled_x,pooled_y,160+100),xy(dev)[0]).cpu().numpy()
    prior={k:predictions(n,anchors) for k,n in base.items()}
    rosters={"mixed": ["lr","mlp","lr","mlp","lr","mlp","lr"],"lr":["lr"]*7,"mlp":["mlp"]*7}
    metadata={}
    cal_probes=[]
    for name,roster in rosters.items():
        for i,c in enumerate(modules):
            arch=roster[i]
            selector=dev.code_module==c
            cg=cal[cal.code_module==c]
            xc,yc=xy(cg)
            xd,_=xy(dev[selector])
            xx=torch.cat([xc,xd])
            # Same frozen local models supply all messages for this roster.
            consensus=torch.stack([prior[roster[j],d] for j,d in enumerate(modules) if j!=i]).mean(dim=0)
            x,y=groups[c]
            transfer=learn(copy.deepcopy(base[arch,c]),x,y,100,anchors,consensus)
            a,b=predictions(local[arch,c],xx),predictions(transfer,xx)
            prob,metadata[name,c]=gate(a,b,len(cg),yc,True)
            methods={name+"_"+k:v for k,v in prob.items()}
            if name=="mixed":
                uncal,metadata["raw",c]=gate(a,b,len(cg),yc,False)
                methods.update(raw_gate=uncal["strata"],raw_local=a,raw_transfer=b)
                z=F.pad(xx,(1,0),value=1)
                fit_x,fit_y=clients[c]
                for method,w in dict(fedavg=avg,fedprox=prox,weak_ridge=ref.adapt(fit_x,fit_y,avg,[1e-5]*5)).items():
                    methods[method]=(z@w).sigmoid()
            cal_probes.append(pd.DataFrame(dict(roster=name,row=cg.row,y=cg.y,code_module=c,raw_local=a[:len(cg)].tolist(),raw_transfer=b[:len(cg)].tolist())))
            for k,p in methods.items():
                dev.loc[selector,k]=p[len(cg):].tolist()
    dev.rename(columns={"mixed_strata":"adapted"},inplace=True)
    args.output.mkdir(parents=True,exist_ok=True)
    for file,data in [("predictions",dev.drop(columns=[*ref.FEATURES,"split"])),("calibration",pd.concat(cal_probes))]:
        with gzip.GzipFile(str(args.output/(file+".csv.gz")),"wb",mtime=0) as f:data.to_csv(f,index=False)
    config={"gpu":torch.cuda.get_device_name(),"pytorch":torch.__version__,"fit_learners":fit.learner.nunique(),"calibration_learners":cal.learner.nunique(),
            "anchor_upload_bytes_per_client":512*8,"anchor_download_bytes_per_client":512*8,"gate":{f"{r}/{c}":v for (r,c),v in metadata.items()}}
    (args.output/"gate.json").write_text(json.dumps(config,indent=2)+"\n")
if __name__=="__main__":
    main()
