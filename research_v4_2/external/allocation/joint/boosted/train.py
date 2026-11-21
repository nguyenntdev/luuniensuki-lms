"""Fit all primary and bootstrap risk scores on the GPU, without evaluation outcomes."""
import json
from pathlib import Path
import sys

from catboost import CatBoostClassifier
import numpy as np
import pandas as pd


def fit(folder, name):
    meta = json.loads((folder/f'{name}.json').read_text())
    dtype = {key:str for key in meta['cat']}
    train = pd.read_csv(folder/f'{name}_train.csv.gz', dtype=dtype)
    test = pd.read_csv(folder/f'{name}_test.csv.gz', dtype=dtype)
    labels = train.pop('y')
    assert list(train) == list(test) == meta['cat'] + meta['num']
    rng = np.random.default_rng(314)
    forecasts = []
    for trial in range(41):
        ix = rng.integers(len(train),size=len(train)) if trial else np.arange(len(train))
        model = CatBoostClassifier(iterations=300, depth=4, learning_rate=.05, random_seed=1701,
                                   cat_features=meta['cat'], task_type='GPU', devices='0', thread_count=2,
                                   verbose=False, allow_writing_files=False)
        model.fit(train.iloc[ix], labels.iloc[ix])
        forecasts.append(model.predict_proba(test)[:,1])
    np.savez_compressed(folder/f'{name}_forecasts.npz', scores=np.array(forecasts),
                        ordered_keys=meta['ordered_keys'])
    print(name, len(forecasts), len(test), flush=True)


if __name__ == '__main__':
    for name in ('oulad','uci697'):
        fit(Path(sys.argv[1]), name)
