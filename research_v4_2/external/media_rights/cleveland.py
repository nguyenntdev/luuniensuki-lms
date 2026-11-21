"""Cross-tabulate the publisher's rights status against web-image availability."""
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

path = Path(sys.argv[1])
counts = Counter()
with path.open(encoding="utf-8-sig", newline="") as stream:
    for row in csv.DictReader(stream):
        counts[row["share_license_status"], bool(row["image_web"].strip())] += 1
with path.open("rb") as stream:
    digest = hashlib.file_digest(stream, "sha256").hexdigest()
print(json.dumps({
    "sha256": digest,
    "records": sum(counts.values()),
    "cells": [
        {"status": status, "web_image": present, "records": count}
        for (status, present), count in sorted(counts.items())
    ],
}, indent=2))
