"""Encode and verify shared field rewrites on previously studied development releases."""
import argparse
from collections import Counter
import hashlib
import json
import lzma
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "relational"))
from codec import canonical, choose, pack, read

MODES = ("whole", "substring", "absolute", "full")


def compress(data):
    return lzma.compress(pack(data), preset=6)


def gaps(positions):
    return [i-j for i,j in zip(positions, [0]+positions[:-1])]


def patterns(x, y):
    """Mine a single divergent span with zero or two context characters."""
    start = 0
    while start < min(len(x),len(y)) and x[start] == y[start]:
        start += 1
    stop = 0
    while stop < min(len(x),len(y))-start and x[-1-stop] == y[-1-stop]:
        stop += 1
    for ctx in (0,2):
        a = max(0,start-ctx)
        b = max(0,stop-ctx)
        src, dst = x[a:len(x)-b], y[a:len(y)-b]
        for kind in (["start", "sub"] if not a else []) + (["end"] if not b else []) + (["sub"] if a else []):
            if src or kind != "sub":
                yield kind, src, dst


def transform(kind, src, dst, text):
    if kind == "whole":
        return dst if src == text else None
    if kind == "sub":
        return text.replace(src, dst) if src in text else None
    if kind == "start":
        return dst+text[len(src):] if text.startswith(src) else None
    if kind == "end":
        return text[:len(text)-len(src)]+dst if text.endswith(src) else None
    raise ValueError(kind)


def prepare(keys, old, new, j):
    previous = [old[k][j] for k in keys]
    following = [new[k][j] for k in keys]
    changed = [i for i,(x,y) in enumerate(zip(previous,following)) if x!=y]
    codes = {i:choose(old[keys[i]],new[keys[i]],j,True) for i in changed}
    counts = Counter()
    for i in changed:
        x,y = previous[i],following[i]
        counts.update({("whole",x,y),*patterns(x,y)})
    found = {}
    # Build the expensive applicability lists only for the most frequent proposals.
    for typ in ("whole","substring"):
        pool = [r for r,n in counts.items() if n >= 4 and (r[0]=="whole")==(typ=="whole")]
        pool.sort(key=lambda r:(-counts[r],r))
        for rule in pool[:32]:
            applicable = []
            hits = []
            for i,x in enumerate(previous):
                value = transform(*rule,x)
                if value is not None and value != x:
                    applicable.append(i)
                    if value == following[i]:
                        hits.append(i)
            if len(hits)>=4:
                found[rule] = (applicable,hits)
    return codes,found


def strategy(codes, found, mode):
    left = set(codes)
    claimed = set()
    programs = []
    ordered = sorted(found, key=lambda r:(-len(found[r][1]),len(pack(r)),r))
    for rule in ordered:
        if mode == "whole" and rule[0] != "whole" or mode == "substring" and rule[0] == "whole":
            continue
        available, matches = found[rule]
        selected = [i for i in matches if i in left]
        if len(selected)<4:
            continue
        selector = ["a",gaps(selected)]
        if mode != "absolute":
            selected_set = set(selected)
            scope = [i for i in available if i not in claimed]
            on = [i for i,p in enumerate(scope) if p in selected_set]
            off = [i for i,p in enumerate(scope) if p not in selected_set]
            selector = min([selector,["i",gaps(on)],["x",gaps(off)]],key=lambda v:len(pack(v)))
        program = [*rule,*selector]
        if len(pack(program)) >= len(pack([gaps(selected),[codes[i] for i in selected]])):
            continue
        programs.append(program)
        claimed.update(selected)
        left.difference_update(selected)
    residual = sorted(left)
    candidate = [programs,gaps(residual),[codes[i] for i in residual]]
    plain = [[],gaps(list(codes)),list(codes.values())]
    return min([candidate,plain],key=lambda row:len(compress(row)))


def run(a,b,prior,hdiff):
    schema,old = read(a)
    layout,new = read(b)
    assert schema==layout
    shared = sorted(old.keys() & new.keys())
    removed = sorted(old.keys()-new.keys())
    inserted = [[k,new[k]] for k in sorted(new.keys()-old.keys())]
    cols = {m:[] for m in MODES}
    for j in range(len(schema)-1):
        codes, found = prepare(shared,old,new,j)
        if not codes:
            continue
        for mode in MODES:
            cols[mode].append([j,*strategy(codes,found,mode)])
    target = canonical(schema,new)
    src_hash = hashlib.sha256(a.read_bytes()).hexdigest()
    target_hash = hashlib.sha256(target).hexdigest()
    assert target_hash == prior["canonical_target_sha256"] == hdiff["canonical_target_sha256"]
    assert src_hash == prior["base_sha256"] and hashlib.sha256(b.read_bytes()).hexdigest()==prior["target_sha256"]
    sizes = {**prior["bytes"],"hdiff":hdiff["bytes"]}
    programs = {}
    hashes = {}
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        (tmp/"base").write_bytes(canonical(schema,old))
        (tmp/"target").write_bytes(target)
        for mode in MODES:
            wire=compress([removed,inserted,cols[mode]])
            (tmp/"wire.xz").write_bytes(wire)
            subprocess.run(["node",ROOT/"verify.mjs",tmp/"base",tmp/"wire.xz",tmp/"target"],check=True)
            sizes[mode]=len(wire)
            hashes[mode]=hashlib.sha256(wire).hexdigest()
            programs[mode]=dict(Counter(p[0] for _,rules,_,_ in cols[mode] for p in rules))
    return dict(base_sha256=src_hash, canonical_target_sha256=target_hash, target_rows=len(new),
                bytes=sizes, wire_sha256=hashes, programs=programs,
                passed=all(sizes["full"]<=.95*v for k,v in sizes.items() if k!="full"))


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshots",nargs=3,type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    controls=json.loads((ROOT.parent/"relational/result.json").read_text())
    hdiff=json.loads((ROOT.parent/"relational/hdiff.json").read_text())
    results=[]
    for a,b,c,d in zip(args.snapshots[:-1],args.snapshots[1:],controls,hdiff,strict=True):
        results.append(run(a,b,c,d))
        print(json.dumps(results[-1]),flush=True)
    args.output.write_text(json.dumps(results,indent=2)+"\n")
