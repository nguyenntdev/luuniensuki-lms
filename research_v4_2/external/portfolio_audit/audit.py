"""Extract decisive contrasts from frozen external study results."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sources = {}


def read(path):
    data = (ROOT / path).read_bytes()
    sources[path] = hashlib.sha256(data).hexdigest()
    if path.endswith(".csv"):
        return list(csv.DictReader(data.decode().splitlines()))
    return json.loads(data)


def strongest(contrasts, gain):
    name = min(contrasts, key=lambda key: contrasts[key][gain])
    return {name: contrasts[name]}


rows = {}
coverage = read("coverage/secondary_run/results.json")["oulad"]
rows["P01"] = {key: coverage[key] for key in
               ("accepted", "gate_correct", "label_effect", "interval95", "top_k_selector_different_ids")}
rows["P02"] = strongest(read("replanning/corridor/result.json")["gains"], "p95")
rows["P04"] = {k: v["ap"] for k, v in read("curriculum_shift/assessment/run/result.json")["methods"].items()}
rows["P05"] = strongest(read("knowledge_tracing/run/result.json")["comparisons"], "gain")
rows["P06"] = read("allocation/confirmatory/run/contrasts.csv")
rows["P10"] = {k: v["mean_added"] for k, v in read("curriculum_plan/run/result.json").items()}
rows["P11"] = strongest(read("rater_agreement/essay_panel/run/scores.json")["contrasts"], "gain")
rows["P12"] = read("catalog_revisions/lineage/renames/results.json")["correct"]
rows["P13"] = strongest(read("landmark/federated/run/summary.json")["contrasts"], "auc_gain")
rows["P14"] = strongest(read("accessibility/confirmatory/result.json")["paired"], "delta")
print(json.dumps({"source_sha256": sources, "comparisons": rows}, indent=2))
