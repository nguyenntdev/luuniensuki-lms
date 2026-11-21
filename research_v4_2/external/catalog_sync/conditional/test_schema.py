"""Exercise schema projection and reconstruction, including escaped cell terminators."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from codec import ROOT, canonical, encode

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("xdelta",type=Path)
args = p.parse_args()
schema = ["id","deleted","artist","name"]
new_schema = ["id","name","place","artist"]
before = {str(i):["empty",f"Artist {i%5}", f"Title 🍊 {i}"] for i in range(99)}
before["gone"] = ["","Removed",""]
after = {str(i):[f"Title 🍊 {i}", "古\0館", f"Artist {i%5}"] for i in range(100)}
after["😀"] = ["A\nB","古\0館","Quotation \" and backslash \\"]
with tempfile.TemporaryDirectory() as temp:
    work = Path(temp)
    (work/"base").write_bytes(canonical(schema,before))
    (work/"target").write_bytes(canonical(new_schema,after))
    for mode in (False,True):
        wire,choices=encode(schema,before,new_schema,after,args.xdelta.resolve(),work,mode)
        (work/"patch").write_bytes(wire)
        subprocess.run(["node",ROOT/"verify.mjs",work/"base",work/"patch",work/"target",args.xdelta.resolve()],check=True)
