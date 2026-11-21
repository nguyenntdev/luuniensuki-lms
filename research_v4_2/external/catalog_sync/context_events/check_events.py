"""Force each coordinate system through a multilingual mixed-edit fixture."""
from pathlib import Path
import subprocess
import tempfile

from events import HERE, ORDERS, canonical, compress, edit_events, gaps, streams


def check():
    schema = ["id","text"]
    before = {"0":["α😀é 🏺"],"1":["kitten"],"2":[""],"3":["a\x00b"],"4":["gone"],"6":["end"]}
    after = {"0":["α😀🌱 🏺!"],"1":["sitting"],"2":["漢"],"3":["b"],"5":["new"],"6":["ends"]}
    keys = sorted(before.keys() & after.keys())
    sources = [before[k][0] for k in keys]
    changes = [edit_events(source, after[k][0]) for k,source in zip(keys,sources,strict=True)]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root/"base").write_bytes(canonical(schema,before))
        (root/"target").write_bytes(canonical(schema,after))
        for mode in ORDERS:
            field = ["events",gaps(list(range(len(keys)))),[1]*len(keys),*streams(sources,changes,mode)]
            wire = compress([["4"],[["5",["new"]]],[[0,field]]])
            (root/"wire").write_bytes(wire)
            subprocess.run(["node",HERE/"verify.mjs",root/"base",root/"wire",root/"target"],check=True)


if __name__ == "__main__":
    check()
