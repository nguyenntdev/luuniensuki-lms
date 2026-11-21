"""Construct the fixed day-60 roster and verify temporal features against parent totals."""
import argparse
import sys
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evaluate import FEATURES, KEY, prepare


def extract(source, output):
    frame = prepare(source)
    future = frame.code_presentation.eq("2014J")
    use = (future | ~frame.id_student.isin(frame.loc[future, "id_student"])) & frame.eligible
    rows = frame.loc[use].copy()
    rows["learner"] = pd.factorize(rows.id_student, sort=True)[0]
    rows["row"] = np.arange(len(rows))
    rows["split"] = np.where(rows.code_presentation.eq("2014J"), "dev", "train")
    with ZipFile(source) as archive, archive.open("studentVle.csv") as stream:
        chunks = []
        for chunk in pd.read_csv(stream, usecols=KEY + ["date", "sum_click"], chunksize=250000):
            observed = chunk[chunk.date.between(0, 60)]
            chunks.append(observed.groupby(KEY + ["date"]).sum_click.sum())
    daily = pd.concat(chunks).groupby(level=KEY + ["date"]).sum().rename("volume").reset_index()
    daily["bin"] = np.maximum(0, (daily.date - 1) // 10)
    windows = daily.groupby(KEY + ["bin"]).agg(volume=("volume", "sum"), active=("date", "size")).unstack()
    windows.columns = [f"{measure}_{bin_id}" for measure, bin_id in windows.columns]
    rows = rows.join(windows, on=KEY, validate="one_to_one")
    extra = list(windows.columns)
    rows[extra] = rows[extra].fillna(0).astype(int)
    for measure, parent in [("volume", "clicks"), ("active", "days")]:
        assert rows.filter(regex=f"^{measure}_").sum(axis=1).eq(rows[parent]).all()
    rows["y"] = rows.outcome.astype(int)
    keys = ["row", "learner", "code_module", "code_presentation"]
    test = rows.split.eq("dev")
    assert sum(test) == 8815 and sum(~test) == 16063
    assert set(rows.loc[test,"learner"]).isdisjoint(rows.loc[~test,"learner"])
    output.mkdir(parents=True, exist_ok=True)
    rows.loc[test, keys + ["y"]].to_csv(output/"labels.csv", index=False)
    rows.loc[test, ["row","code_module"]+FEATURES+extra].to_csv(output/"dev.csv", index=False)
    rows.loc[~test, ["code_module"]+FEATURES+extra+["y"]].to_csv(output/"train.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    extract(args.source, args.output)
