"""Acquire pinned catalogue releases and verify single-snapshot identities."""
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
SOURCES = {
    "cleveland": ("ClevelandMuseumArt/openaccess", "master", "data.csv", "id"),
    "moma": ("MuseumofModernArt/collection", "main", "Artworks.csv", "ObjectID"),
    "nga": ("NationalGalleryOfArt/opendata", "main", "data/objects.csv", "objectid"),
}
CUTS = ["2026-01-01", "2026-04-01", "2026-07-01", "2026-10-01"]


def reply(url):
    return urlopen(Request(url, headers={"User-Agent": "catalogue-release-panel/1.0"}), timeout=150)


def api(url):
    with reply("https://api.github.com/" + url) as stream:
        return json.load(stream)


def discover():
    specs = []
    for provider, (repo, branch, path, key) in SOURCES.items():
        for cut in CUTS:
            q = urlencode(dict(path=path, sha=branch, until=cut+"T00:00:00Z", per_page=1))
            result, = api(f"repos/{repo}/commits?{q}")
            commit = result["sha"]
            contents = api(f"repos/{repo}/contents/{path}?ref={commit}")
            specs.append(dict(provider=provider, repo=repo, path=path, key=key, cutoff=cut, commit=commit,
                              date=result["commit"]["committer"]["date"], blob=contents["sha"]))
    print(json.dumps(specs, indent=2))


def fingerprint(path):
    with path.open("rb") as f:
        sha = hashlib.file_digest(f, "sha256").hexdigest()
    git = hashlib.sha1(f"blob {path.stat().st_size}\0".encode())
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            git.update(block)
    return sha, git.hexdigest()


def audit(path, key):
    seen = set()
    csv.field_size_limit(sys.maxsize)
    with path.open(encoding="utf-8-sig", newline="") as f:
        data = csv.reader(f)
        fields = next(data)
        if len(set(fields)) != len(fields) or key not in fields:
            raise ValueError(f"Invalid key or header at {path}: {fields}")
        index = fields.index(key)
        for n, row in enumerate(data, start=2):
            if len(row) != len(fields) or not row[index] or row[index] in seen:
                raise ValueError(f"Invalid row width or identity at {path}:{n}")
            seen.add(row[index])
    return dict(header=fields, records=len(seen), unique_ids=len(seen))


def fetch(url, target):
    with reply(url) as incoming, target.open("wb") as out:
        shutil.copyfileobj(incoming, out, length=1024*1024)


def acquire(cache, spec):
    directory = cache / spec["provider"]
    directory.mkdir(parents=True, exist_ok=True)
    stub = spec["repo"] + "/" + spec["commit"] + "/" + spec["path"]
    dest = directory / (spec["cutoff"] + ".csv")
    pointer_file = dest.with_suffix(".pointer")
    if not dest.exists():
        with tempfile.TemporaryDirectory(dir=directory) as temporary:
            tmp = Path(temporary) / "input"
            fetch("https://raw.githubusercontent.com/" + stub, tmp)
            if fingerprint(tmp)[1] != spec["blob"]:
                raise ValueError("Unmatched Git object")
            with tmp.open("rb") as f:
                first = f.readline(128).strip()
            if first == b"version https://git-lfs.github.com/spec/v1":
                pointer = tmp.read_bytes()
                match = re.fullmatch(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([a-f0-9]{64})\nsize (\d+)\n?",pointer)
                if not match:
                    raise ValueError("Invalid pointer")
                fetch("https://media.githubusercontent.com/media/" + stub,tmp)
                if fingerprint(tmp)[0] != match[1].decode() or tmp.stat().st_size != int(match[2]):
                    raise ValueError("Unmatched LFS payload")
                pointer_file.write_bytes(pointer)
            os.replace(tmp, dest)
    sha, git = fingerprint(dest)
    if pointer_file.exists():
        pointer = pointer_file.read_bytes()
        expect = f"version https://git-lfs.github.com/spec/v1\noid sha256:{sha}\nsize {dest.stat().st_size}\n".encode()
        assert pointer.rstrip(b"\n") == expect.rstrip(b"\n")
        assert fingerprint(pointer_file)[1] == spec["blob"]
    else:
        assert git == spec["blob"]
    return dict(provider=spec["provider"], cutoff=spec["cutoff"], bytes=dest.stat().st_size,
                sha256=sha, git_lfs=pointer_file.exists(), **audit(dest,spec["key"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=["discover","acquire"])
    parser.add_argument("cache",type=Path,nargs="?")
    args = parser.parse_args()
    if args.stage == "discover":
        discover()
    else:
        if args.cache is None:
            parser.error("acquire requires a raw cache directory")
        result = []
        for spec in json.loads((ROOT/"revisions.json").read_text()):
            result.append(acquire(args.cache,spec))
            print(spec["provider"],spec["cutoff"],result[-1]["records"],file=sys.stderr,flush=True)
        print(json.dumps(result,indent=2))
