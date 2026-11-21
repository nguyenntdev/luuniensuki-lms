"""Round-trip sparse relational patches and standard delta compressors on two development intervals."""
import argparse
import csv
import hashlib
import json
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import sys
csv.field_size_limit(sys.maxsize)


def pack(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode()


def zstd(blob, decode=False):
    args = ["zstd", "-q", "-c", "-d" if decode else "-19"]
    return subprocess.run(args, input=blob, capture_output=True, check=True).stdout


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        records = csv.reader(handle)
        schema = next(records)
        data = {}
        for key, *values in records:
            assert key not in data and len(values) == len(schema)-1
            data[key] = values
    return schema, data


def canonical(schema, data):
    return b"\n".join([pack(schema), *(pack([k, *data[k]]) for k in sorted(data))]) + b"\n"


def assignments(changes):
    grouped = defaultdict(list)
    for index, value in changes:
        grouped[value].append(index)
    groups = [[value, [i-j for i,j in zip(indices, [0]+indices[:-1])]] for value, indices in grouped.items()]
    choices = [["s", changes], ["g", groups]]
    return min(choices, key=lambda choice: len(zstd(pack(choice))))


def unpack_assignments(payload):
    kind, content = payload
    if kind == "s":
        yield from content
    elif kind == "g":
        for value, deltas in content:
            idx = 0
            for d in deltas:
                idx += d
                yield idx, value
    else:
        raise ValueError(kind)


def patches(old, new):
    shared = sorted(old.keys() & new.keys())
    inserted = {k:new[k] for k in sorted(new.keys()-old.keys())}
    removed = sorted(old.keys()-new.keys())
    changes = [(i,j,b) for i,k in enumerate(shared) for j,(a,b) in enumerate(zip(old[k],new[k])) if a!=b]
    payloads = {"row_diff": changes, "column_diff": {}, "rule_diff": {}}
    columns = defaultdict(list)
    for i,j,value in changes:
        columns[j].append([i,value])
    for j, changed in columns.items():
        sparse = assignments(changed)
        payloads["column_diff"][j] = sparse
        counts = defaultdict(Counter)
        for k in shared:
            counts[old[k][j]][new[k][j]] += 1
        rules = {}
        for value, counter in counts.items():
            frequent, n = counter.most_common(1)[0]
            if n>1 and n>counter[value]:
                rules[value] = frequent
        residual = [[i,new[k][j]] for i,k in enumerate(shared) if rules.get(old[k][j],old[k][j]) != new[k][j]]
        options = [sparse, ["r", [rules, assignments(residual)]]]
        payloads["rule_diff"][j] = min(options, key=lambda v:len(zstd(pack(v))))
    return {name:zstd(pack([name, inserted, removed, body])) for name,body in payloads.items()}


def restore(old, encoded):
    name, inserted, removed, body = json.loads(zstd(encoded, True))
    data = {k:list(row) for k,row in old.items()}
    for k in removed:
        del data[k]
    shared = sorted(data)
    if name == "row_diff":
        for i,j,v in body:
            data[shared[i]][j] = v
    else:
        for col, ops in body.items():
            j = int(col)
            if ops[0] == "r":
                rules, ops = ops[1]
                for k in shared:
                    data[k][j] = rules.get(old[k][j], old[k][j])
            for i,value in unpack_assignments(ops):
                data[shared[i]][j] = value
    data.update(inserted)
    return data


def measure(first, second, xdelta):
    schema, old = read(first)
    next_schema, new = read(second)
    assert schema == next_schema
    target = canonical(schema, new)
    digest = hashlib.sha256(target).hexdigest()
    encoded = patches(old,new)
    sizes = {}
    for name, patch in encoded.items():
        assert canonical(schema,restore(old,patch)) == target
        sizes[name] = len(patch)
    plain = zstd(target)
    assert zstd(plain, True) == target
    sizes["zstd_full"] = len(plain)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        base, output = tmp/"base", tmp/"target"
        base.write_bytes(canonical(schema, old))
        output.write_bytes(target)
        for method, enc, dec in [
            ("zstd_patch", ["zstd","-q","-19","-c",f"--patch-from={base}",str(output)],
             ["zstd","-q","-d","-c",f"--patch-from={base}"]),
            ("vcdiff", [str(xdelta),"-9","-e","-c","-s",str(base),str(output)],
             [str(xdelta),"-d","-c","-s",str(base)])]:
            wire = subprocess.check_output(enc)
            assert subprocess.run(dec, input=wire, capture_output=True, check=True).stdout == target
            sizes[method] = len(wire)
    return dict(base_sha256=hashlib.sha256(first.read_bytes()).hexdigest(),
                source_target_sha256=hashlib.sha256(second.read_bytes()).hexdigest(),
                canonical_target_sha256=digest, rows=len(new), bytes=sizes,
                pass_screen=all(sizes["rule_diff"] <= .95*n for k,n in sizes.items() if k!="rule_diff"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("xdelta", type=Path)
    ap.add_argument("snapshots", nargs=3, type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    result = [measure(a,b,args.xdelta) for a,b in zip(args.snapshots,args.snapshots[1:])]
    args.output.write_text(json.dumps(result,indent=2)+"\n")
