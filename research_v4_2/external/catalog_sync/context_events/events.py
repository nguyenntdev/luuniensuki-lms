"""Sparse string edit events in decoder-reconstructible coordinate systems."""
from collections import defaultdict
import difflib
import hashlib
import json
import lzma
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared_edits"))
from encode import canonical, gaps, pack, prepare, read, strategy
from codec import references

ORDERS = ("row", "start", "end", "character", "context")


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def compress(obj):
    return lzma.compress(pack(obj), preset=6)


def char_class(s):
    if not s:
        return 0
    if "0" <= s <= "9":
        return 1
    if "A" <= s <= "Z":
        return 2
    if "a" <= s <= "z":
        return 3
    return 4 if s == " " else 5


def group_key(mode, text, pos):
    if mode == "row":
        return 0
    if mode == "start":
        return pos
    if mode == "end":
        return len(text) - pos
    ch = ord(text[pos]) + 1 if pos < len(text) else 0
    if mode == "character":
        return ch
    left = char_class(text[pos-1]) if pos else 0
    right = char_class(text[pos+1]) if pos+1 < len(text) else 0
    return (ch * 6 + left) * 6 + right


def edit_events(source, target):
    matcher = difflib.SequenceMatcher(None, source, target, autojunk=False)
    return {i:(k-i, target[j:l]) for tag,i,k,j,l in matcher.get_opcodes() if tag != "equal"}


def streams(texts, changes, mode):
    # Only store changed positions; count all sites to determine their coordinates.
    counts = defaultdict(int)
    by_group = defaultdict(list)
    for source, edits in zip(texts, changes, strict=True):
        for pos in range(len(source)+1):
            group = group_key(mode, source, pos)
            if pos in edits:
                by_group[group].append((counts[group], *edits[pos]))
            counts[group] += 1
    positions, lengths, inserted = [], [], []
    offset = 0
    for group in sorted(counts):
        for local,length,addition in by_group[group]:
            positions.append(offset+local)
            lengths.append(length)
            inserted.append(addition)
        offset += counts[group]
    return [mode, gaps(positions), lengths, inserted]


def field_options(old, new, keys, j, codes, found):
    rows = list(codes)
    # All selected references are reconstructible before decoding this column.
    selectors, texts, changed = [], [], []
    for row in rows:
        before, after = old[keys[row]], new[keys[row]]
        code = codes[row]
        if isinstance(code, str):
            selector, source = 0, ""
        elif code[0] == "e":
            selector, source = 1, before[j]
        else:
            selector = code[:-1]
            source = dict(references(j, before, after))[tuple(selector)]
        selectors.append(selector)
        texts.append(source)
        changed.append(edit_events(source, after[j]))
    mask = gaps(rows)
    control = ["legacy", *strategy(codes, found, "substring")]
    # Transposed legacy instructions also form a common fallback in both arms.
    options = [control, ["plain", mask, list(codes.values())]]
    best = {}
    for mode in ORDERS:
        options.append(["events", mask, selectors, *streams(texts, changed, mode)])
        if mode in ("row", "context"):
            best[mode] = min(options, key=lambda obj:len(compress(obj)))
    return best


def measure(a, b, prior, working):
    header, old = read(a)
    next_header, new = read(b)
    assert header == next_header
    keys = sorted(old.keys() & new.keys())
    removed = sorted(old.keys()-new.keys())
    added = [[k,new[k]] for k in sorted(new.keys()-old.keys())]
    src, target = working/"base", working/"target"
    src.write_bytes(canonical(header,old))
    target.write_bytes(canonical(header,new))
    assert digest(a.read_bytes()) == prior["base_sha256"]
    assert digest(target.read_bytes()) == prior["canonical_target_sha256"]
    fields = {"row":[], "context":[]}
    for j in range(len(header)-1):
        if all(old[k][j] == new[k][j] for k in keys):
            continue
        codes, found = prepare(keys, old, new, j)
        choices = field_options(old,new,keys,j,codes,found)
        for mode, op in choices.items():
            fields[mode].append([j,op])
    sizes = prior["bytes"].copy()
    hashes, selected = {}, {}
    for mode, cols in fields.items():
        wire = compress([removed, added, cols])
        wire_path = working/"wire.xz"
        wire_path.write_bytes(wire)
        subprocess.run(["node",HERE/"verify.mjs",src,wire_path,target],check=True)
        sizes[mode], hashes[mode] = len(wire), digest(wire)
        selected[mode] = {header[j+1]:(op[3] if op[0]=="events" else op[0]) for j,op in cols}
    return dict(base_sha256=prior["base_sha256"],target_csv_sha256=digest(b.read_bytes()),
                canonical_target_sha256=prior["canonical_target_sha256"], rows=len(new),
                bytes=sizes, wire_sha256=hashes, selected=selected,
                passed=all(sizes["context"] <= v*.95 for k,v in sizes.items() if k!="context"))


if __name__ == "__main__":
    a,b,c,out = map(Path,sys.argv[1:])
    prior = json.loads((HERE.parent/"relational/result.json").read_text())
    for record, conditional in zip(prior,json.loads((HERE.parent/"conditional/result.json").read_text()),strict=True):
        record["bytes"] = conditional["bytes"]
        assert record["canonical_target_sha256"] == conditional["target_sha256"]
    with tempfile.TemporaryDirectory() as tmp:
        results = []
        for source,target,control in zip((a,b),(b,c),prior,strict=True):
            assert digest(target.read_bytes()) == control["target_sha256"]
            results.append(measure(source,target,control,Path(tmp)))
            print(results[-1]["bytes"],flush=True)
    out.write_text(json.dumps(results,indent=2)+"\n")
