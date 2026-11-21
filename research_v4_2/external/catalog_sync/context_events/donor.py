"""Two-pass coding of exact causal donor hits and independently decoded exceptions."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from events import (HERE, ORDERS, canonical, compress, digest, edit_events, gaps, pack, prepare,
                    read, references, strategy, streams)


def span(before, after):
    lo = 0
    while lo < min(len(before),len(after)) and before[lo] == after[lo]:
        lo += 1
    tail = 0
    while tail < min(len(before),len(after))-lo and before[-1-tail]==after[-1-tail]:
        tail += 1
    src = before[lo:len(before)-tail]
    dst = after[lo:len(after)-tail]
    return lo,tail,src,dst


def predict(x, donor):
    before, after, (lo,tail,src,dst) = donor
    if src and src in x:
        return x.replace(src,dst)
    if not src and not lo:
        return dst+x
    if not src and not tail:
        return x+dst
    return None


def donor_selectors(order, keys, old, new, j):
    previous = None
    history = {}
    modes = [[],[],[]]
    for row in order:
        key = keys[row]
        x, y = old[key][j], new[key][j]
        choices = [0,0,0]
        if previous and previous[1] == y:
            choices[1] = choices[2] = 1
        elif x in history and history[x] == y:
            choices[2] = 2
        elif previous and predict(x,previous)==y:
            choices[2] = 3
        for codes,selection in zip(modes,choices,strict=True):
            codes.append(selection)
        previous = (x,y,span(x,y))
        history[x] = y
    return modes


def measure(a,b,prior,work):
    header, old = read(a)
    header_new,new = read(b)
    assert header==header_new and digest(a.read_bytes())==prior["base_sha256"]
    keys=sorted(old.keys() & new.keys())
    dropped=sorted(old.keys()-new.keys())
    added=[[k,new[k]] for k in sorted(new.keys()-old.keys())]
    base,target=work/"base",work/"target"
    base.write_bytes(canonical(header,old))
    target.write_bytes(canonical(header,new))
    assert digest(target.read_bytes())==prior["canonical_target_sha256"]
    columns={arm:[] for arm in ("reorder","preceding","dictionary")}
    diagnostics={arm:{} for arm in columns}
    for j in range(len(header)-1):
        if all(old[k][j]==new[k][j] for k in keys):
            continue
        codes,rules=prepare(keys,old,new,j)
        info={}
        for row,code in codes.items():
            k=keys[row]
            if isinstance(code,str):
                sel,src=0,""
            elif code[0]=="e":
                sel,src=1,old[k][j]
            else:
                sel=code[:-1]
                src=dict(references(j,old[k],new[k]))[tuple(sel)]
            info[row]=(sel,src,edit_events(src,new[k][j]))
        legacy=["legacy",*strategy(codes,rules,"substring")]
        plain=["plain",gaps(list(codes)),list(codes.values())]
        choices={arm:[legacy,plain] for arm in columns}
        for ordering in dict.fromkeys([-1,0,j]):
            permutation = range(len(keys)) if ordering==-1 else sorted(range(len(keys)),key=lambda i:old[keys[i]][ordering])
            positions=[p for p,row in enumerate(permutation) if row in codes]
            order=[permutation[p] for p in positions]
            for arm,marks in zip(columns, donor_selectors(order,keys,old,new,j),strict=True):
                anchors=[row for row,mark in zip(order,marks,strict=True) if mark==0]
                selectors=[info[row][0] for row in anchors]
                sources=[info[row][1] for row in anchors]
                edits=[info[row][2] for row in anchors]
                detail=[["codes",[codes[row] for row in anchors]]]
                detail.extend(["events",selectors,*streams(sources,edits,mode)] for mode in ORDERS)
                lead=["batch",ordering,gaps(positions),marks if any(marks) else 0]
                options=[[*lead,item] for item in detail]
                # Minimize real column bytes under the same outer compressor.
                choices[arm].append(min(options,key=lambda opt:len(compress(opt))))
        for arm in columns:
            # A superset search permits both historical arms' exact representations.
            allowed=list(choices[arm])
            if arm!="reorder": allowed.extend(choices["reorder"])
            if arm=="dictionary": allowed.extend(choices["preceding"])
            selected=min(allowed,key=lambda opt:len(compress(opt)))
            columns[arm].append([j,selected])
            diagnostics[arm][header[j+1]]=(dict(order=selected[1],hits=sum(bool(m) for m in selected[3]) if selected[3] else 0,
                                           residual=selected[4][2] if selected[4][0]=="events" else "codes")
                                           if selected[0]=="batch" else selected[0])
    sizes={**prior["bytes"]}
    hashes={}
    for arm,cols in columns.items():
        wire=compress([dropped,added,cols])
        path=work/"patch.xz"
        path.write_bytes(wire)
        subprocess.run(["node",HERE/"verify.mjs",base,path,target],check=True)
        sizes[arm]=len(wire)
        hashes[arm]=digest(wire)
    return dict(base_sha256=prior["base_sha256"],target_csv_sha256=digest(b.read_bytes()),
                canonical_target_sha256=prior["canonical_target_sha256"],rows=len(new),
                bytes=sizes,wire_sha256=hashes,selected=diagnostics,
                passed=all(sizes["dictionary"] <= .95*v for k,v in sizes.items() if k!="dictionary"))


if __name__=="__main__":
    a,b,c,out=map(Path,sys.argv[1:])
    prior=json.loads((HERE/"result.json").read_text())
    with tempfile.TemporaryDirectory() as tmp:
        results=[]
        for source,target,control in zip((a,b),(b,c),prior,strict=True):
            assert digest(target.read_bytes())==control["target_csv_sha256"]
            results.append(measure(source,target,control,Path(tmp)))
            print(results[-1]["bytes"],flush=True)
    out.write_text(json.dumps(results,indent=2)+"\n")
