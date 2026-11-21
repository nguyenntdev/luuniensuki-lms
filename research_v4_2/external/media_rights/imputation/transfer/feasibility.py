"""Audit training objects in two museum releases. Never parse dev/test object JSON."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import tarfile

OLD = "e51eafbfab4a59f5d864fd81d5ef899d0fd502e7"
NEW = "790eb625934680f2eeccb262391618d2ca948486"
PATH_ID = re.compile(r"collection-([a-f0-9]{40})/objects/(\d+)/(\d+)\.json$")


def training(oid):
    digest = hashlib.sha256(str(oid).encode("ascii")).hexdigest()
    return oid not in {1, 17} and int(digest[:12], 16) % 100 < 60


def accession_family(accession):
    parts = accession.split(".")
    return ".".join(parts[:-1]) if len(parts) >= 3 and all(parts) else ""


def snapshot(raw, commit):
    path = raw / f"{commit}.tar.gz"
    with path.open("rb") as stream:
        sha = hashlib.file_digest(stream, "sha256").hexdigest()
    table = {}
    skipped = Counter()
    with tarfile.open(path, "r|gz") as archive:
        for member in archive:
            match = PATH_ID.fullmatch(member.name)
            if not match:
                continue
            oid = int(match[3])
            assert match[1] == commit
            if not training(oid):
                continue
            if int(match[2]) != oid // 1000:
                skipped["conflicting_bucket"] += 1
                continue
            blob = archive.extractfile(member).read()
            if not blob.strip():
                skipped["empty_file"] += 1
                continue
            try:
                obj = json.loads(blob)
            except json.JSONDecodeError:
                skipped["invalid_json"] += 1
                continue
            if not isinstance(obj, dict) or "id" not in obj:
                skipped["missing_object_id"] += 1
                continue
            if str(obj["id"]).rsplit("/", 1)[-1] != str(oid):
                skipped["conflicting_object_id"] += 1
                continue
            assert oid not in table
            def field(key):
                return (obj.get(key) or "").strip()
            table[oid] = (field("rights_type"), accession_family(field("accession_number")),
                          bool(field("dated")), bool(field("artist")))
    return table, sha, dict(skipped)


def audit(old, new):
    declarations = Counter(r[0] for r in old.values())
    observed = {i: r for i, r in old.items() if r[0]}
    groups = defaultdict(list)
    for oid, (label, family, _, _) in observed.items():
        if family:
            groups[family].append((oid, label == "Public Domain"))
    repeated = [sorted(g) for g in groups.values() if len(g) >= 2]
    mixed = [g for g in repeated if len({y for _, y in g}) == 2]
    agree = 0
    for g in repeated:
        for j, (i, label) in enumerate(g):
            neighbors = g[max(0,j-1):j] + g[j+1:j+2]
            _, other = min(neighbors, key=lambda pair: (abs(pair[0]-i), pair[0]))
            agree += other == label
    changes = Counter()
    filled = Counter()
    for oid, (label, _, _, _) in old.items():
        if oid not in new:
            changes["no_valid_later_record"] += 1
            continue
        later = new[oid][0]
        if not label and later:
            filled[later] += 1
        if not label:
            changes["filled" if later else "still_blank"] += 1
        elif not later:
            changes["lost_label"] += 1
        elif label == later:
            changes["same"] += 1
        else:
            changes["revised"] += 1
    assert sum(changes.values()) == len(old)
    return {
        "early_train_objects": len(old), "late_train_objects": len(new),
        "late_only": len(new.keys() - old.keys()),
        "early_label_counts": dict(sorted(declarations.items())),
        "early_dated_nonblank": sum(row[2] for row in old.values()),
        "early_artist_nonblank": sum(row[3] for row in old.values()),
        "observed_early_labels": len(observed), "family_keys": len(groups),
        "repeated_families": len(repeated), "mixed_repeated_families": len(mixed),
        "objects_in_repeated_families": sum(map(len, repeated)),
        "objects_in_mixed_repeated_families": sum(map(len, mixed)),
        "objects_agreeing_with_nearest_other_family_member": agree,
        "largest_family": max(map(len, repeated), default=0),
        "transitions": dict(sorted(changes.items())),
        "later_labels_of_early_blank": dict(sorted(filled.items())),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    before, before_sha, before_skip = snapshot(args.raw, OLD)
    after, after_sha, after_skip = snapshot(args.raw, NEW)
    print(json.dumps(dict(archives={OLD:before_sha, NEW:after_sha}, excluded_training_files={OLD:before_skip, NEW:after_skip}, training=audit(before, after)),
                     indent=2, ensure_ascii=False))
