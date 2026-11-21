"""Fit distractor and matched categorical lag trees."""
import argparse
from pathlib import Path
import pandas as pd
from catboost import CatBoostClassifier

BASE = ["part","question","skill","n","right","nskill","rskill","nitem","ritem","last","lastskill",
        "gap","skillgap","itemgap","recenthour","recentday","skillday"]


def fit(data, output):
    rows = pd.read_csv(data, keep_default_na=False, dtype={k:str for k in ["part","question","skill"]})
    train = rows.bucket < 60
    dev = rows.bucket.between(70, 79)
    assert rows.bucket.max() < 80
    results = rows.loc[dev, ["uid","row","start","y"]].copy()
    lags = ["lag1","lag2","lag3","lag4"]
    # A completed response with no recorded letter gives neither arm a letter.
    rows[lags] = rows[lags].replace("", "missing")
    assert set(rows[lags].stack().unique()) <= {"a", "b", "c", "d", "correct", "missing"}
    for name in ["distractor", "lag_control"]:
        if name == "lag_control":
            rows[lags] = rows[lags].replace(dict.fromkeys("abcd", "incorrect"))
        cols = BASE + lags
        tree = CatBoostClassifier(iterations=350, learning_rate=.1, depth=6, random_seed=732,
            task_type="GPU", gpu_ram_part=.16, thread_count=2, devices="0", verbose=False,
            cat_features=["question","part","skill",*lags], allow_writing_files=False)
        tree.fit(rows.loc[train, cols], rows.y[train])
        assert tree.get_all_params()["task_type"] == "GPU"
        results[name] = tree.predict_proba(rows.loc[dev, cols])[:,1]
    results.to_csv(output, index=False, compression={"method":"gzip","mtime":0})


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("data", type=Path)
    p.add_argument("output", type=Path)
    a=p.parse_args()
    fit(a.data, a.output)
