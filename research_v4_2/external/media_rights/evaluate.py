"""Count the decisions supported by catalog licenses and explicit per-image grants."""
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


def audit(root):
    tate = root/"tate/artwork_data.csv"
    counts = Counter()
    with tate.open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            counts["records"] += 1
            if r["thumbnailUrl"].strip():
                counts["thumbnail_links"] += 1
                counts["linked_with_copyright_notice"] += bool(r["thumbnailCopyright"].strip())
    si = Counter()
    hashes = {tate.name:hashlib.sha256(tate.read_bytes()).hexdigest()}
    for i in range(6):
        path = root/f"smithsonian_open_access/2021-12-21/fsg_0{i}.txt"
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        for line in path.read_text().splitlines():
            rec = json.loads(line)["content"]["descriptiveNonRepeating"]
            si["records"] += 1
            for media in rec.get("online_media",{}).get("media",[]):
                if media.get("type")!="Images" or not media.get("content"):
                    continue
                si["image_entries"] += 1
                si["explicit_cc0"] += media.get("usage",{}).get("access")=="CC0"
    return dict(tate=dict(counts),smithsonian=dict(si),source_sha256=hashes)


if __name__ == "__main__":
    print(json.dumps(audit(Path(sys.argv[1])),indent=2))
