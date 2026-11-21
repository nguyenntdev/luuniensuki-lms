"""Fetch and verify the public files used by the external benchmark runs."""
import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fetch(entry, root):
    path = root / entry["path"]
    digest = entry["sha256"]
    if path.is_file():
        if sha256(path) != digest:
            raise ValueError(f"Existing file differs from the cited release: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(entry["url"], headers={"User-Agent": "external-benchmark-reproduction/1"})
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temp:
        pending = Path(temp.name)
    try:
        with urlopen(request, timeout=120) as src, pending.open("wb") as out:
            shutil.copyfileobj(src, out, length=1024 * 1024)
        if sha256(pending) != digest:
            raise ValueError(f"Downloaded bytes differ from cited release: {entry['url']}")
        os.replace(pending, path)
    finally:
        pending.unlink(missing_ok=True)


if __name__ == "__main__":
    entries = json.loads(Path(__file__).with_name("downloads.json").read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--study", action="append", choices=sorted({r["study"] for r in entries}))
    args = parser.parse_args()
    for entry in entries:
        if not args.study or entry["study"] in args.study:
            fetch(entry, args.root)
            print(f"verified {entry['path']}", flush=True)
