"""Replay the frozen analysis with every test-release page excluded from development."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import tempfile

import pandas as pd

import challenge


def development_rows(raw):
    release = raw / "vitaminc"
    with (release / "test.jsonl").open() as stream:
        test_titles = {json.loads(line)["page"] for line in stream}
    with (release / "dev.jsonl").open() as stream:
        rows = [row for line in stream if (row := json.loads(line))["revision_type"] == "real"
                and row["page"] not in test_titles]
    titles = sorted({r["page"] for r in rows}, key=lambda s: challenge.hashlib.sha256(s.encode()).digest())
    selected = set(titles[:192])
    return [r for r in rows if r["page"] in selected]


def run(raw, output, model):
    original = output.parent
    desired = development_rows(raw)
    dev_ids = {r["unique_id"] for r in desired}
    initial_ids = set(challenge.cohort(raw, "dev").unique_id)
    delta = pd.DataFrame([r for r in desired if r["unique_id"] not in initial_ids])
    if (len(dev_ids), len(delta), len(initial_ids - dev_ids)) != (1766, 22, 56):
        raise ValueError("Unexpected development-set membership")
    extra = output / "additional_dev"
    if model:
        challenge.collect(raw, delta, model, extra / f"{model}.csv")
        return
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        (work / "vitaminc").mkdir()
        (work / "vitaminc/test.jsonl").symlink_to((raw / "vitaminc/test.jsonl").resolve())
        with (work / "vitaminc/dev.jsonl").open("w") as stream:
            for row in desired:
                stream.write(json.dumps(row) + "\n")
        stage = work / "out"
        (stage / "dev").mkdir(parents=True)
        (stage / "test").symlink_to((original / "test").resolve())
        for name in challenge.MODELS:
            table = {}
            for directory in (original / "dev", extra):
                with (directory / f"{name}.csv").open() as stream:
                    reader = csv.reader(stream)
                    header = next(reader)
                    if header != ["id", *challenge.LABELS]:
                        raise ValueError(f"Unexpected columns in {name}")
                    for values in reader:
                        if values[0] in table:
                            raise ValueError(f"Duplicate ID in {name}")
                        table[values[0]] = values
            with (stage / "dev" / f"{name}.csv").open("w", newline="") as stream:
                writer = csv.writer(stream, lineterminator="\n")
                writer.writerow(["id", *challenge.LABELS])
                writer.writerows(table[r["unique_id"]] for r in desired)
        challenge.compare(work, stage)
        for fname in ("predictions.csv", "result.json"):
            shutil.copyfile(stage / fname, output / fname)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("output", type=Path, help="A subdirectory under the original run directory")
    parser.add_argument("--model", choices=challenge.MODELS)
    args = parser.parse_args()
    run(args.raw, args.output, args.model)
