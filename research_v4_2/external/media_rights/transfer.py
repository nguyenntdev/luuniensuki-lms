"""Build and score a reproducible object-level comparison across two catalogues."""
import argparse
import bz2
import csv
import gzip
import hashlib
import io
import json
import tarfile
from collections import Counter
from pathlib import Path

CLEVELAND_SHA = "cbcbec43a61f68cd34b514c87f6f9dd2b73ee4615722f5983c32b4bdc33c6efd"
CHICAGO_SHA = "632d9b8796015c577ca54120a5466a8cd916ad24ff522b2650a9ef29573f7892"
PROJECTION_SHA = "963ed46b8c97ec25d589aca29c50d05fb89689600ea98aca304917edafba3d78"
FIELDS = ("museum", "id", "declared", "image_locator", "copyright_notice")


def verify(path, expected):
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != expected:
            raise ValueError(f"Source version mismatch: {path}")


def filled(value):
    return bool(value and value.strip())


def cleveland(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for record in csv.DictReader(stream):
            declared = {"CC0": True, "Copyrighted": False}[record["share_license_status"]]
            yield ("Cleveland", int(record["id"]), declared,
                   filled(record["image_web"]), filled(record["copyright"]))


def chicago(path):
    with bz2.open(path, "rb") as stream, tarfile.open(fileobj=stream, mode="r|") as archive:
        for member in archive:
            name = Path(member.name)
            if (member.isfile() and name.parent.as_posix() == "artic-api-data/json/artworks"
                    and name.suffix == ".json"):
                record = json.load(archive.extractfile(member))
                declared = record["is_public_domain"]
                if type(declared) is not bool or int(name.stem) != record["id"]:
                    raise ValueError(f"Unexpected artwork ID or label in {name}")
                yield ("Chicago", record["id"], declared,
                       filled(record["image_id"]), filled(record["copyright_notice"]))


def build(cleveland_path, chicago_path, output):
    verify(cleveland_path, CLEVELAND_SHA)
    verify(chicago_path, CHICAGO_SHA)
    rows = sorted([*cleveland(cleveland_path), *chicago(chicago_path)])
    if len({row[:2] for row in rows}) != len(rows):
        raise ValueError("Duplicate provider/object key")
    if {row[0] for row in rows} != {"Chicago", "Cleveland"}:
        raise ValueError("Expected artworks from both providers")
    with output.open("wb") as raw, gzip.GzipFile(
        filename="", mode="wb", fileobj=raw, mtime=0
    ) as zipped, io.TextIOWrapper(zipped, encoding="ascii", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(FIELDS)
        for museum, object_id, *flags in rows:
            writer.writerow([museum, object_id, *map(int, flags)])


def score(path):
    with gzip.open(path, "rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != PROJECTION_SHA:
            raise ValueError("Unexpected projection contents")
    cells = Counter()
    matrices = {}
    with gzip.open(path, "rt", encoding="ascii", newline="") as stream:
        for row in csv.DictReader(stream):
            museum = row["museum"]
            declared, locator, notice = ({"0": False, "1": True}[row[k]] for k in FIELDS[2:])
            cells[museum, declared, locator, notice] += 1
            policies = {"all": True, "none": False, "locator": locator,
                        "blank_notice": not notice, "locator_blank_notice": locator and not notice}
            for policy, prediction in policies.items():
                counts = matrices.setdefault(museum, {}).setdefault(
                    policy, dict.fromkeys(("TP", "FP", "FN", "TN"), 0))
                key = ("T" if prediction == declared else "F") + ("P" if prediction else "N")
                counts[key] += 1
    return {"projection_uncompressed_sha256": PROJECTION_SHA,
            "source_sha256": {"Chicago": CHICAGO_SHA, "Cleveland": CLEVELAND_SHA},
            "cells": [dict(zip(FIELDS[:1] + FIELDS[2:], key), records=count)
                      for key, count in sorted(cells.items())],
            "policies": matrices}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("build")
    extract.add_argument("cleveland_csv", type=Path)
    extract.add_argument("chicago_archive", type=Path)
    extract.add_argument("output", type=Path)
    evaluate = commands.add_parser("score")
    evaluate.add_argument("projection", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        build(args.cleveland_csv, args.chicago_archive, args.output)
    else:
        print(json.dumps(score(args.projection), indent=2))
