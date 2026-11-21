"""Force all three causal donor operators and Unicode field-value ordering."""
from pathlib import Path
import tempfile
import subprocess

from events import HERE, canonical, compress, gaps

keys = list("ECADB")
old = dict(zip(keys,[["α","ab"],["β","cd"],["\ue000","unused"],["𐀀","ab"],["😀","zb"]],strict=True))
new = dict(zip(keys,[["α","ax"],["β","cx"],["\ue000","cx"],["𐀀","ax"],["😀","zx"]],strict=True))
# Both the first and second changed cells are literal anchors in this wire.
# The latest old→new mapping for 'ab' persists across two unrelated rows.
modes = [0,0,1,2,3]
with tempfile.TemporaryDirectory() as name:
    d = Path(name)
    (d/"base").write_bytes(canonical(["id","order","value"],old))
    (d/"target").write_bytes(canonical(["id","order","value"],new))
    wire = compress([[],[],[[1,["batch",0,gaps(list(range(5))),modes,["codes",["ax","cx"]]]]]])
    (d/"wire").write_bytes(wire)
    subprocess.run(["node",HERE/"verify.mjs",d/"base",d/"wire",d/"target"],check=True)
