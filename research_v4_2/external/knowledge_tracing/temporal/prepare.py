"""Create a strict-before-bundle view of selected complete EdNet KT1 members."""
import argparse
import csv
import hashlib
import io
import math
import struct
import zipfile
import zlib
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

BASE = ["part","question","skill","n","right","nskill","rskill","nitem","ritem","last","lastskill"]
CLOCK = ["gap","skillgap","itemgap","recenthour","recentday","skillday"]
INTERF = ["n_since_skill","r_since_skill","other_part_rate","other_part_count","skill_switches"]


def members(path):
    blob=path.read_bytes()
    offset=0
    seen=0
    while blob[offset:offset+4]==b"PK\x03\x04" and seen<2500:
        _,_,flags,method,_,_,crc,size,raw,n,m=struct.unpack_from("<I5H3I2H",blob,offset)
        start=offset+30
        name=blob[start:start+n].decode()
        start+=n+m
        end=start+size
        if end>len(blob):
            break
        offset=end
        if not name.endswith(".csv"):
            continue
        seen+=1
        uid=Path(name).stem
        bucket=int.from_bytes(hashlib.sha256(uid.encode()).digest()[:4],"big")%100
        if bucket>=80:
            continue
        assert flags&8==0 and method==8 and uid.startswith("u")
        text=zlib.decompress(blob[start:end],-15)
        assert len(text)==raw and zlib.crc32(text)==crc
        yield uid,bucket,list(csv.DictReader(io.StringIO(text.decode())))
    assert seen==2500


def recency(history,now,tau):
    weights=[math.exp(-(now-row[0])/tau) for row in history]
    return (1+sum(w*r[4] for w,r in zip(weights,history)))/(2+sum(weights))


def build(root,out):
    with zipfile.ZipFile(root/"contents.zip") as z:
        meta={k["question_id"]:k for k in csv.DictReader(io.TextIOWrapper(z.open("contents/questions.csv")))}
    data=[];windows=[];seen=set()
    for uid,bucket,raw in members(root/"KT1.prefix"):
        assert uid not in seen
        seen.add(uid)
        ordered=sorted(enumerate(raw),key=lambda pair:(int(pair[1]["timestamp"]),pair[0]))
        clipped=ordered[:160]
        if len(ordered)>160:
            truncated_ids={r["solving_id"] for _,r in ordered[160:]}
            clipped=[(i,r) for i,r in clipped if r["solving_id"] not in truncated_ids]
        by_bundle=defaultdict(list)
        for i,r in clipped:
            q=meta[r["question_id"]]
            assert r["user_answer"] in "abcd" and int(r["elapsed_time"])>=0
            by_bundle[r["solving_id"]].append((int(r["timestamp"]),q["question_id"],int(q["tags"].split(";")[0] or -1),
                int(q["part"]),int(r["user_answer"]==q["correct_answer"]),int(r["elapsed_time"]),i))
        bounds={b:(min(r[0] for r in rs),max(r[0]+r[5] for r in rs)) for b,rs in by_bundle.items()}
        for b,rs in by_bundle.items():
            start=bounds[b][0]
            prior=sorted([r for j,v in by_bundle.items() if j!=b and bounds[j][1]<start for r in v],key=lambda r:(r[0],r[6]))
            if not prior:
                continue
            gap=(start-prior[-1][0])/1000
            for _,q,k,part,y,_,idx in rs:
                skill=[r for r in prior if r[2]==k];item=[r for r in prior if r[1]==q]
                lastpos=max((i for i,r in enumerate(prior) if r[2]==k),default=-1)
                since=prior[lastpos+1:]
                other=[r for r in prior[-16:] if r[3]==part and r[2]!=k]
                def delay(rows):
                    return math.log1p((start-rows[-1][0])/1000) if rows else -1
                row=[uid,idx,bucket,start,gap,y,str(part),q,str(k),len(prior),sum(r[4] for r in prior),
                   len(skill),sum(r[4] for r in skill),len(item),sum(r[4] for r in item),
                   prior[-1][4],skill[-1][4] if skill else -1,math.log1p(gap),delay(skill),delay(item),
                   recency(prior,start,3600000),recency(prior,start,86400000),recency(skill,start,86400000),
                   len(since),sum(r[4] for r in since),(1+sum(r[4] for r in other))/(2+len(other)),len(other),
                   sum(r[2]!=s[2] for r,s in zip(prior[-16:],prior[-16:][1:]))]
                data.append(row)
                window=[(r[2],r[4]) for r in prior[-16:]]
                windows.append(window+[(-2,0)]*(16-len(window)))
    table=pd.DataFrame(data,columns=["uid","row","bucket","start","gap_s","y",*BASE,*CLOCK,*INTERF])
    out.mkdir(exist_ok=True,parents=True)
    table.to_pickle(out/"rows.pkl")
    np.save(out/"windows.npy",np.array(windows,dtype=np.int32))
    print(table.groupby(pd.cut(table.bucket,[-1,59,69,79])).agg(rows=("y","size"),learners=("uid","nunique")))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("out",type=Path)
    args=p.parse_args()
    build(args.source,args.out)
