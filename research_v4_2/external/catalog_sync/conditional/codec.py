"""Base-dependent filters and dictionaries for sparse table deltas."""
import argparse
import base64
import hashlib
import json
import lzma
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zlib

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from screen import pack, canonical, read


def binary(values):
    return b"".join(value.encode("utf8").replace(b"\x00", b"\xff") + b"\x00" for value in values)


def varints(values):
    out = bytearray()
    last = 0
    for pos in values:
        delta = pos-last
        last = pos
        while delta >= 128:
            out.append(128 | (delta & 127))
            delta >>= 7
        out.append(delta)
    return base64.b64encode(out).decode()


def size(value):
    return len(zlib.compress(pack(value),6))


def vcdiff(source, target, temp, xdelta):
    if not source or not target:
        return None
    (temp/"src").write_bytes(source)
    result = subprocess.run([xdelta,"-9","-S","none","-A","-n","-e","-c","-s",str(temp/"src")],
                            input=target,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,
                            env={**os.environ,"XDELTA":""})
    return base64.b64encode(result.stdout).decode()


def replace_span(src, before, after):
    if before == after:
        return []
    i = 0
    while i < min(len(before),len(after)) and before[i] == after[i]:
        i += 1
    t = 0
    while t < min(len(before),len(after))-i and before[-t-1] == after[-t-1]:
        t += 1
    results = []
    # Preserve a little context when both sides share in-field text.
    for padding in (0,2):
        a,b=max(0,i-padding),max(0,t-padding)
        x,y = before[a:len(before)-b], after[a:len(after)-b]
        if x and x in src:
            results.append(src.replace(x,y))
    return results


def dictionary(kind, source_rows, rows, old, new, j):
    if kind=="own":
        return binary(old[i][j] for i in rows)
    if kind=="all":
        return binary(sorted({row[j] for row in source_rows}))
    out=[]
    for i in rows:
        before,after=old[i],new[i]
        own=before[j]
        words=[own]
        if kind=="relation":
            for k in range(j):
                if before[k] != after[k]:
                    words.extend(replace_span(own,before[k],after[k]))
                    words.append(after[k])
            words.extend(before)
        out.extend(dict.fromkeys(words))
    return binary(out)


def bounds(header, before_header, before, after):
    if len(set(header))!=len(header) or len(set(before_header))!=len(before_header):
        raise ValueError("Ambiguous column name")
    if header[0]!=before_header[0]:
        raise ValueError("Object identity changed")
    removed=sorted(before.keys()-after.keys())
    inserted=sorted(after.keys()-before.keys())
    keys=sorted(after)
    fields={name:i for i,name in enumerate(before_header[1:])}
    layout=[fields.get(k) for k in header[1:]]
    old=[[before[id][i] if id in before and i is not None else "" for i in layout] for id in keys]
    new=[after[id] for id in keys]
    return old,new,[header if header!=before_header else None,removed,inserted]


def encode(schema0, before, schema, after, xdelta, work, contextual):
    old,new,prefix=bounds(schema,schema0,before,after)
    n=len(old)
    fields=len(schema)-1
    orders={-1:list(range(n))}
    for j in range(fields):
        orders[j]=sorted(range(n),key=lambda i:old[i][j])
    inverse={}
    for j,order in orders.items():
        ranks=[0]*n
        for i,p in enumerate(order): ranks[p]=i
        inverse[j]=ranks
    masks=[]
    columns=[]
    for j in range(fields):
        mask={i for i in range(n) if old[i][j]!=new[i][j]}
        if not mask:
            masks.append(mask)
            continue
        allowed=orders if contextual else [-1,j]
        choices=[]
        for previous in ([-1]+list(range(j)) if contextual else [-1]):
            diff=mask if previous==-1 else mask^masks[previous]
            for sort in allowed:
                deltas=varints(sorted(inverse[sort][i] for i in diff))
                desc=[sort,previous,deltas]
                choices.append((size(desc),desc))
        maskcode=min(choices,key=lambda c:c[0])[1]
        masks.append(mask)
        # Keep the three best orders under a cheap compression probe to limit xdelta calls.
        rows_by_sort={}
        for sort in allowed:
            rs=tuple(sorted(mask,key=inverse[sort].__getitem__))
            rows_by_sort.setdefault(rs,sort)
        proposals=[]
        rankings=[]
        for rs,sort in rows_by_sort.items():
            values=[new[i][j] for i in rs]
            literals=[sort,"literal",values]
            proposals.append(literals)
            ranked=size(literals)
            rankings.append((ranked,sort,rs))
        own_orders=[rs for rs,order in rows_by_sort.items() if order in (-1,j)]
        limit=list(dict.fromkeys(own_orders+[rs for _,_,rs in sorted(rankings)[:3]]))
        for rs in limit:
            sort=rows_by_sort[rs]
            target=binary(new[i][j] for i in rs)
            for kind in (("own","all","relation") if contextual else ("own","all")):
                src=dictionary(kind,old,rs,old,new,j)
                delta=vcdiff(src,target,work,xdelta)
                if delta is not None:
                    proposals.append([sort,kind,delta])
        value=min(proposals,key=size)
        columns.append([j,maskcode,value])
    wire=lzma.compress(pack([*prefix,columns]),preset=6)
    return wire,[[c[0],*c[1][:2],*c[2][:2]] for c in columns]


def compare(paths, xdelta, output):
    previous=json.loads((ROOT.parent/"shared_edits/result.json").read_text())
    results=[]
    with tempfile.TemporaryDirectory() as d:
        work=Path(d)
        for a,b,controls in zip(paths[:-1],paths[1:],previous,strict=True):
            sa,old=read(a)
            sb,new=read(b)
            target=canonical(sb,new)
            assert controls["base_sha256"]==hashlib.sha256(a.read_bytes()).hexdigest()
            assert controls["canonical_target_sha256"]==hashlib.sha256(target).hexdigest()
            (work/"base").write_bytes(canonical(sa,old))
            (work/"target").write_bytes(target)
            r=dict(base_sha256=controls["base_sha256"], target_sha256=controls["canonical_target_sha256"],
                   rows=len(new),bytes=controls["bytes"].copy(),wire_sha256={},selectors={})
            for name,flag in [("own_sorted",False),("conditional",True)]:
                wire,selectors=encode(sa,old,sb,new,xdelta,work,flag)
                (work/"patch.xz").write_bytes(wire)
                subprocess.run(["node",ROOT/"verify.mjs",work/"base",work/"patch.xz",work/"target",xdelta],check=True)
                r["bytes"][name]=len(wire)
                r["wire_sha256"][name]=hashlib.sha256(wire).hexdigest()
                r["selectors"][name]=selectors
                print(a.name,name,len(wire),flush=True)
            r["pass"]=all(r["bytes"]["conditional"]<=n*.95 for k,n in r["bytes"].items() if k!="conditional")
            results.append(r)
    output.write_text(json.dumps(results,indent=2)+"\n")


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("xdelta",type=Path)
    ap.add_argument("snapshots",nargs=3,type=Path)
    ap.add_argument("output",type=Path)
    args=ap.parse_args()
    compare(args.snapshots,args.xdelta.resolve(),args.output)
