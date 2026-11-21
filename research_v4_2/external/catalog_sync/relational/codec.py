"""Encode table edits using changed positions and optional within-row reference strings."""
import argparse
import difflib
import hashlib
import json
import lzma
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from screen import canonical, pack, read


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def edit(src, target):
    ops = difflib.SequenceMatcher(None, src, target, autojunk=False).get_matching_blocks()
    chunks = []
    offset = 0
    for a, b, size in ops:
        if size < 3:
            continue
        if b > offset:
            chunks.append(target[offset:b])
        chunks.append([a, size])
        offset = b + size
    if offset < len(target):
        chunks.append(target[offset:])
    return chunks


def apply(src, chunks):
    return "".join(part if isinstance(part, str) else src[part[0]:sum(part)] for part in chunks)


def references(j, old, new):
    # These references are known to both ends before applying edits to column j.
    # The wire carries the column and transformation index selected by the sender.
    for k, value in enumerate(old):
        if k != j and value:
            yield ("o", k), value
    for k, value in enumerate(new[:j]):
        if value:
            yield ("n", k), value
        if value == old[k] or not value:
            continue
        for i, transform in enumerate((str, slug)):
            before = transform(old[k])
            if before and before in old[j]:
                yield ("r", k, i), old[j].replace(before, transform(value))


def choose(old, new, j, cross):
    x = old[j]
    y = new[j]
    candidates = [y, ["e", edit(x, y)]]
    if cross:
        for key, source in references(j, old, new):
            if source == y:
                candidates.append([*key, None])
            elif len(source) >= 8 and len(y) >= 8:
                # Avoid running the edit aligner on clearly unrelated cells.
                if source[:6] == y[:6] or source[-6:] == y[-6:]:
                    candidates.append([*key, edit(source, y)])
    return min(candidates, key=lambda c: len(pack(c)))


def encode(old, new, cross):
    shared = sorted(old.keys() & new.keys())
    removed = sorted(old.keys() - new.keys())
    inserts = [[k, new[k]] for k in sorted(new.keys() - old.keys())]
    cols = {}
    last = {}
    for i, key in enumerate(shared):
        for j, (x, y) in enumerate(zip(old[key], new[key], strict=True)):
            if x != y:
                positions, instructions = cols.setdefault(j, ([], []))
                positions.append(i - last.get(j, 0))
                instructions.append(choose(old[key], new[key], j, cross))
                last[j] = i
    return lzma.compress(pack([removed, inserts, sorted(cols.items())]), preset=6)


def decode(old, wire):
    removed, inserted, columns = json.loads(lzma.decompress(wire))
    result = {k: row.copy() for k, row in old.items()}
    for k in removed:
        del result[k]
    keys = sorted(result)
    for j, (deltas, codes) in columns:
        i = 0
        for d, c in zip(deltas, codes, strict=True):
            i += d
            k = keys[i]
            if isinstance(c, str):
                value = c
            elif c[0] == "e":
                value = apply(old[k][j], c[1])
            else:
                ref = dict(references(j, old[k], result[k]))[tuple(c[:-1])]
                value = ref if c[-1] is None else apply(ref, c[-1])
            result[k][j] = value
    result.update(inserted)
    return result


def measure(a, b, binaries, work, summary):
    schema, old = read(a)
    layout, new = read(b)
    assert schema == layout
    original = canonical(schema, old)
    target = canonical(schema, new)
    src, dst = work / "base", work / "target"
    src.write_bytes(original)
    dst.write_bytes(target)
    sizes = {}
    for name, cross in [("own_cell", False), ("within_row", True)]:
        wire = encode(old, new, cross)
        assert canonical(schema, decode(old, wire)) == target
        patch = work / (name + ".xz")
        patch.write_bytes(wire)
        subprocess.run(["node", Path(__file__).with_name("verify.mjs"), src, patch, dst], check=True)
        sizes[name] = len(wire)
    delta, restored = work / "patch", work / "restored"
    for name, enc, dec in (
        ("bsdiff", ["bsdiff", src, dst, delta], ["bspatch", src, restored, delta]),
        ("xdelta3", ["xdelta3", "-f", "-9", "-e", "-s", src, dst, delta],
         ["xdelta3", "-f", "-d", "-s", src, delta, restored]),
    ):
        for cmd in (enc, dec):
            subprocess.run([binaries / cmd[0], *cmd[1:]], check=True)
        assert restored.read_bytes() == target
        sizes[name] = delta.stat().st_size
    assert hashlib.sha256(target).hexdigest() == summary["canonical_target_sha256"]
    assert sizes["xdelta3"] == summary["bytes"]["vcdiff"]
    sizes.update({k: n for k, n in summary["bytes"].items() if k != "vcdiff"})
    return dict(base_sha256=hashlib.sha256(a.read_bytes()).hexdigest(),
                target_sha256=hashlib.sha256(b.read_bytes()).hexdigest(),
                canonical_target_sha256=summary["canonical_target_sha256"],
                bytes=sizes, pass_screen=all(sizes["within_row"] <= n*.95
                    for k, n in sizes.items() if k != "within_row"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binaries", type=Path)
    parser.add_argument("snapshots", nargs=3, type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    old = json.loads((Path(__file__).resolve().parents[1] / "development.json").read_text())
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        for a, b, s in zip(args.snapshots[:-1], args.snapshots[1:], old, strict=True):
            results.append(measure(a, b, args.binaries, Path(tmp), s))
            print(json.dumps(results[-1]), flush=True)
    args.out.write_text(json.dumps(results, indent=2) + "\n")
