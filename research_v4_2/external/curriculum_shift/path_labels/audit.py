"""Run from this directory with a local curriculum Git checkout."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

records = json.loads(Path("../catalog_events/records.json").read_bytes())
pins = dict(line.split() for line in Path("merges.tsv").read_text().splitlines())
assert set(pins) == {str(r["number"]) for r in records}
print("pr label files foundations sha256_nul_paths")
for row in records:
    number = row["number"]
    sha = pins[str(number)]
    raw = subprocess.check_output([
        "git", "-C", sys.argv[1], "diff", "--name-only", "--no-renames", "-z",
        sha + "^1", sha, "--",
    ])
    paths = raw.split(b"\0")[:-1]
    count = sum(p.startswith(b"foundations/") for p in paths)
    print(number, row["y"], len(paths), count, hashlib.sha256(raw).hexdigest())
