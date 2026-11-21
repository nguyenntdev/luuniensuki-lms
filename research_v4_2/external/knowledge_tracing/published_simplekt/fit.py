"""Fit upstream simpleKT under the earlier EdNet development budget."""
import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np
import torch
from torch.nn.functional import binary_cross_entropy


def encode(values, training_tokens):
    vocab = np.unique(training_tokens)
    pos = np.searchsorted(vocab, values)
    matches = (pos < len(vocab)) & (vocab[np.minimum(pos, len(vocab)-1)] == values)
    return np.where(matches, pos+1, 0), len(vocab)


def evaluate(raw, out):
    sys.path.insert(0, str(raw.resolve()))
    from upstream.simplekt import simpleKT

    data = np.load(raw / "cache/simplekt.npz")
    fit = data["bucket"] < 60
    tune = (data["bucket"] >= 60) & (data["bucket"] < 70)
    dev = data["bucket"] >= 70
    assert data["bucket"].max() < 80 and [fit.sum(), tune.sum(),dev.sum()] == [56259,8025,8981]
    available = data["skills"] != -2
    lengths = available.sum(axis=1)
    assert np.all((lengths >= 1) & (lengths <= 16))
    skill = np.column_stack((data["skills"], data["skill"]))
    item = data["items"]
    known = np.column_stack((available, np.ones(len(fit),bool)))
    cs, nskill = encode(skill, skill[known & fit[:,None]])
    qs, nitem = encode(item, item[known & fit[:,None]])
    rs = np.column_stack((data["responses"], np.zeros(len(fit),dtype=int)))
    tensors = [torch.as_tensor(x, device="cuda", dtype=torch.long) for x in (qs,cs,rs)]
    target = torch.as_tensor(data["y"], device="cuda",dtype=torch.float32)
    out.mkdir(exist_ok=True, parents=True)
    summary = {}
    saved = {}
    for mode in ["items", "skill_only"]:
        torch.manual_seed(732)
        rng = np.random.default_rng(732)
        net = simpleKT(nskill+1, nitem if mode=="items" else 0, 64, 1, .1,
                       num_attn_heads=4, seq_len=17).cuda()
        opt = torch.optim.Adam(net.parameters(), lr=.001)
        def batches(mask, shuffle):
            chunks = []
            for length in range(1,17):
                rows = np.flatnonzero(mask & (lengths==length))
                if shuffle:
                    rng.shuffle(rows)
                chunks.extend((a,length) for a in np.array_split(rows,max(1,(len(rows)+511)//512)) if len(a))
            if shuffle:
                rng.shuffle(chunks)
            return chunks

        def forward(rows, length, flip=False):
            indices = torch.as_tensor(rows,device="cuda")
            sample = {}
            for name,tensor in zip(("qseqs","cseqs","rseqs"),tensors):
                old = tensor[indices,:length]
                current = tensor[indices,16:17]
                if name=="rseqs" and flip:
                    current = torch.ones_like(current)
                sample[name] = old
                sample["shft_"+name] = torch.cat([old[:,1:],current],dim=1)
            return net(sample)[:,-1]

        def forecast(mask, canary=False):
            net.eval()
            pred = np.full(len(fit),np.nan)
            with torch.no_grad():
                for ids,length in batches(mask,False):
                    p = forward(ids,length)
                    if canary:
                        torch.testing.assert_close(p,forward(ids,length,True),rtol=0,atol=0)
                    pred[ids] = p.cpu().numpy()
            return pred[mask]
        best = float("inf")
        curve = []
        for epoch in range(5):
            net.train()
            for ids,length in batches(fit,True):
                opt.zero_grad()
                p = forward(ids,length)
                binary_cross_entropy(p,target[ids]).backward()
                opt.step()
            p = np.clip(forecast(tune),1e-7,1-1e-7)
            y = data["y"][tune]
            loss = float(-(y*np.log(p)+(1-y)*np.log1p(-p)).mean())
            curve.append(loss)
            if loss < best:
                state = copy.deepcopy(net.state_dict())
                best = loss
        net.load_state_dict(state)
        saved[mode] = forecast(dev,canary=True)
        summary[mode] = dict(tuning_curve=curve, epoch=int(np.argmin(curve))+1,
                             parameters=sum(x.numel() for x in net.parameters()))
        print(mode,curve,flush=True)
    np.savetxt(out/"probabilities.csv",np.column_stack(list(saved.values())),delimiter=",",
               header=",".join(saved),comments="")
    (out/"fit.json").write_text(json.dumps(dict(device=torch.cuda.get_device_name(0),torch=torch.__version__,
        models=summary,tuning_learners=226,canary_rows=int(dev.sum()),vocab_items=nitem,vocab_skills=nskill),indent=2)+"\n")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw",type=Path)
    parser.add_argument("out",type=Path)
    args=parser.parse_args()
    evaluate(args.raw,args.out)
