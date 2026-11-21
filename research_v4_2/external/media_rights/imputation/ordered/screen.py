"""Development comparison of local label continuity under three catalogue orderings."""
import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import log_loss

module = importlib.util.spec_from_file_location("met_masking", Path(__file__).resolve().parents[1] / "screen.py")
masking = importlib.util.module_from_spec(module)
module.loader.exec_module(masking)

WINDOWS = (1, 4, 16)
CATEGORIES = ["family", "artist", "dept", "class", "name"]


def ordered_features(reference, query, group):
    """Count training labels on each side using offsets in a grouped sorted index."""
    if group == "global":
        rkeys = np.zeros(len(reference), dtype=int)
        qkeys = np.zeros(len(query), dtype=int)
    else:
        reference = reference.loc[reference[group].ne("")]
        rkeys, keys = pd.factorize(reference[group], sort=True)
        qkeys = keys.get_indexer(query[group])
    rids = reference.oid.to_numpy()
    order = np.lexsort((rids, rkeys))
    index_type = [("group", "i8"), ("oid", "i8")]
    points = np.empty(len(order), dtype=index_type)
    points["group"], points["oid"] = rkeys[order], rids[order]
    queries = np.empty(len(query), dtype=index_type)
    queries["group"], queries["oid"] = qkeys, query.oid.to_numpy()
    pos = np.searchsorted(points, queries)
    lo = np.searchsorted(points["group"], qkeys, side="left")
    hi = np.searchsorted(points["group"], qkeys, side="right")
    cumulative = np.r_[0, reference.y.to_numpy()[order].cumsum()]
    prior = reference.y.mean()
    output = {}
    for k in WINDOWS:
        left, right = np.maximum(pos-k, lo), np.minimum(pos+k, hi)
        for side, a, b in (("L", left, pos), ("R", pos, right)):
            size = b-a
            output[f"{group}_{side}{k}_rate"] = (cumulative[b]-cumulative[a]+2*prior)/(size+2)
            output[f"{group}_{side}{k}_n"] = size
        output[f"{group}_both{k}"] = (cumulative[right]-cumulative[left]+2*prior)/(right-left+2)
    near = []
    for side, ix, present in (("L", pos-1, pos>lo), ("R", pos, pos<hi)):
        rows = np.clip(ix, 0, len(points)-1)
        gap = np.abs(points["oid"][rows]-queries["oid"])
        output[f"{group}_{side}_gap"] = np.where(present, np.log1p(gap), np.nan)
        near.append(np.where(present, reference.y.to_numpy()[order][rows], np.nan))
    output[f"{group}_agrees"] = np.where(np.isfinite(near).all(axis=0), near[0]==near[1], np.nan)
    return pd.DataFrame(output, index=query.index)


def features(reference, query):
    assert not reference.oid.isin(query.oid).any()
    tables = [masking.neighbors(reference, query)]
    tables.extend(ordered_features(reference, query, group) for group in ("global", "family", "artist"))
    return pd.concat(tables, axis=1)


def run(source, out):
    data = masking.metadata(source)
    training = data[data.bucket < 60]
    dev = data[data.bucket >= 60]
    folds = [features(training[training.fold != k], training[training.fold == k]) for k in range(5)]
    table = data.join(pd.concat([*folds, features(training, dev)]))
    base = CATEGORIES + ["begin", "end", "year", "oid"]
    legacy = [f"{group}_{suffix}" for group in ("family", "artist", "joint")
              for suffix in ("rate", "count", "neighbor", "distance")]
    global_cols = [c for c in table if c.startswith("global_")]
    grouped = [c for c in table if c.startswith(("family_", "artist_")) and c not in legacy]
    variants = {"metadata_id": base, "nearest": base+legacy, "global": base+global_cols,
                "grouped": base+grouped, "full": base+legacy+global_cols+grouped}
    window_losses = {k:log_loss(training.y, table.loc[training.index,f"global_both{k}"]) for k in WINDOWS}
    selected = min(window_losses, key=window_losses.get)
    predictions = {"simple_window": table.loc[dev.index,f"global_both{selected}"].to_numpy()}
    for name, cols in variants.items():
        fit = CatBoostClassifier(iterations=350, depth=6, learning_rate=.12, task_type="GPU", devices="0", gpu_ram_part=.4,
                                 thread_count=3, random_seed=73, allow_writing_files=False,
                                 verbose=False, cat_features=CATEGORIES)
        fit.fit(table.loc[training.index,cols], training.y)
        assert fit.get_all_params()["task_type"] == "GPU"
        predictions[name] = fit.predict_proba(table.loc[dev.index,cols])[:,1]
        print(name, "GPU", flush=True)
    losses = {k:log_loss(dev.y,p) for k,p in predictions.items()}
    contrasts = {k:loss-losses["full"] for k,loss in losses.items() if k!="full"}
    out.mkdir(parents=True, exist_ok=True)
    dev[["oid","y"]].assign(**predictions).to_csv(out/"dev.csv.gz", index=False,
                                                  compression={"method":"gzip","mtime":0})
    result = dict(train=len(training), development=len(dev), positives=int(dev.y.sum()),
                  training_window_losses=window_losses, selected_window=selected, loss=losses,
                  gain=contrasts, pass_screen=all(v>=.005 for v in contrasts.values()))
    (out/"summary.json").write_text(json.dumps(result,indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("out",type=Path)
    args = parser.parse_args()
    run(args.source,args.out)
