"""Audit saved predictions and summarize within-project dependence."""
from collections import defaultdict
from pathlib import Path
import json

root = Path(__file__).resolve().parent
published = json.loads((root.parent / "renames/results.json").read_text())
for project in ("peps", "sphinx"):
    run = json.loads((root / f"{project}.json").read_text())
    rows = run["rows"]
    if project == "peps":
        assert len(rows) == len(published["rows"]) == 21
        for row, reference in zip(rows, published["rows"]):
            assert all(row[k] == reference[k] for k in ("commit","path","source","target"))
            assert all(row["predictions"][k] == v for k,v in reference["predictions"].items())
    files = defaultdict(list)
    for row in rows:
        files[row["path"]].append(row)
        assert 0 <= row["target"] < row["candidates"]
        assert all(p is None or 0 <= p < row["candidates"] for p in row["predictions"].values())
    print(project, len(rows), "rows,", len(files), "files,", len(run["censored"]), "censored")
    for method, count in run["correct"].items():
        hits = lambda group: sum(r["predictions"][method] == r["target"] for r in group)
        assert hits(rows) == count
        print(method, count, round(sum(hits(group)/len(group) for group in files.values())/len(files), 4))
