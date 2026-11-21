"""Print reference-caption coverage for the pinned VizWiz challenge archive."""
import hashlib
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

archive = Path(sys.argv[1])
if hashlib.sha256(archive.read_bytes()).hexdigest() != "8df5f0799457b530dde3a55c09d6781daf768876669473a0f227c8b4e5dcd24b":
    raise ValueError("Unexpected challenge archive digest")

result = {}
with zipfile.ZipFile(archive) as source:
    for split in ("train", "val", "test"):
        data = json.loads(source.read(f"annotations/{split}.json"))
        counts = {image["id"]: 0 for image in data["images"]}
        summary = {"images": len(counts)}
        if "annotations" in data:
            annotations = data["annotations"]
            for annotation in annotations:
                if not (annotation["is_precanned"] or annotation["is_rejected"]):
                    counts[annotation["image_id"]] += 1
            summary.update(captions=len(annotations), eligible=sum(counts.values()),
                           images_by_eligible_count=dict(sorted(Counter(counts.values()).items())))
        result[split] = summary
print(json.dumps(result, indent=2))
