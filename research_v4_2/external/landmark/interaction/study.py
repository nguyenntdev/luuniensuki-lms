"""Forecast the published SNAP MOOC state label with history available at each action."""
import argparse
import copy
import hashlib
import json
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from torch import nn

SEED = 731
NUMERIC = ["TIMESTAMP", "FEATURE0", "FEATURE1", "FEATURE2", "FEATURE3",
           "actions", "gap", "elapsed", "repetitions"]
CATEGORIES = ["TARGETID", "previous"]


def history(source, author_csv):
    if hashlib.sha256(source.read_bytes()).hexdigest() != "6829e169e12eaef2d3abcabeb545e8aef6f639ab13a6f28911d41859f2709922":
        raise ValueError("Unknown SNAP archive")
    with tarfile.open(source) as archive:
        def table(name):
            return pd.read_csv(archive.extractfile("act-mooc/" + name + ".tsv"), sep="\t").set_index("ACTIONID", verify_integrity=True)
        data = table("mooc_actions")
        for name in ["mooc_action_features"]:
            extra = table(name)
            assert data.index.equals(extra.index)
            data = data.join(extra)
    if hashlib.sha256(author_csv.read_bytes()).hexdigest() != "5e29679063c6e416c2ae741d94a8f2b8e996f21e7cbf278488687fb6cb1df15a":
        raise ValueError("Unknown JODIE release")
    fields = ["USERID", "TARGETID", "TIMESTAMP", "LABEL", "FEATURE0", "FEATURE1", "FEATURE2", "FEATURE3"]
    author = pd.read_csv(author_csv, skiprows=1, names=fields)
    assert len(author) == len(data) and author.LABEL.isin([0, 1]).all()
    for col in data:
        np.testing.assert_allclose(data[col], author[col], rtol=0, atol=1e-12 if col.startswith("FEATURE") else 0)
    data["LABEL"] = author.LABEL.to_numpy()
    assert np.array_equal(data.index, np.arange(len(data))) and data.TIMESTAMP.is_monotonic_increasing
    person = data.groupby("USERID", sort=False)
    data["actions"] = person.cumcount()
    data["previous"] = person.TARGETID.shift().fillna(-1).astype(int)
    data["gap"] = person.TIMESTAMP.diff().fillna(0)
    data["elapsed"] = data.TIMESTAMP - person.TIMESTAMP.transform("first")
    data["repetitions"] = data.groupby(["USERID", "TARGETID"]).cumcount()
    # Index zero is a masked left-padding token. All nonzero indices refer to observed actions.
    event = (data.index.to_series() + 1).groupby(data.USERID)
    window = np.column_stack([event.shift(s).fillna(0).astype(int) for s in reversed(range(8))])
    return data, window


class SequenceForecast(nn.Module):
    def __init__(self, vocab):
        super().__init__()
        self.item = nn.Embedding(vocab, 8, padding_idx=0)
        self.gru = nn.GRUCell(len(NUMERIC) + 16, 32)
        self.classifier = nn.Linear(32, 1)

    def forward(self, windows, numbers, activities):
        x = torch.cat([numbers[windows], self.item(activities[windows]).flatten(2)], dim=2)
        state = x.new_zeros((len(x), 32))
        for step in range(windows.shape[1]):
            updated = self.gru(x[:, step], state)
            state = torch.where(windows[:, step, None] != 0, updated, state)
        return self.classifier(state).flatten()


def recurrent(data, window, a, b, y):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(SEED)
    rng = np.random.default_rng(SEED)
    nums = StandardScaler().fit(data[NUMERIC][:a]).transform(data[NUMERIC])
    vocab = {int(item): i + 2 for i, item in enumerate(sorted(data.TARGETID[:a].unique()))}
    ids = data[CATEGORIES].apply(lambda col: col.map(vocab).fillna(1)).to_numpy(dtype=int)
    def tensor(v, dtype):
        return torch.as_tensor(v, device=device, dtype=dtype)
    numbers = tensor(np.pad(nums, ((1, 0), (0, 0))), torch.float32)
    activities = tensor(np.pad(ids, ((1, 0), (0, 0))), torch.long)
    windows = tensor(window, torch.long)
    target = tensor(y[:a], torch.float32)
    model = SequenceForecast(len(vocab) + 2).to(device)
    loss = nn.BCEWithLogitsLoss(pos_weight=tensor(np.sqrt((a - y[:a].sum()) / y[:a].sum()), torch.float32))
    optimizer = torch.optim.Adam(model.parameters(), lr=.001)
    @torch.no_grad()
    def forecast(lo, hi):
        model.eval()
        return torch.cat([model(windows[i:min(i+1024, hi)], numbers, activities).sigmoid()
                          for i in range(lo, hi, 1024)]).cpu().numpy()
    best, best_state = -1, None
    scores = []
    for epoch in range(8):
        model.train()
        indices = rng.permutation(a)
        for offset in range(0, a, 512):
            batch = tensor(indices[offset:offset+512], torch.long)
            optimizer.zero_grad()
            loss(model(windows[batch], numbers, activities), target[batch]).backward()
            optimizer.step()
        value = roc_auc_score(y[a:b], forecast(a, b))
        scores.append(float(value))
        if value > best:
            best, best_state = value, copy.deepcopy(model.state_dict())
    model.load_state_dict(best_state)
    return forecast(a, len(data)), scores, str(device)


def trees(data, y, a, b, numeric, categorical):
    # Training-only dictionaries also map previously unseen activities to missing at inference.
    X = data[numeric + categorical].copy()
    for col in categorical:
        X[col] = pd.Categorical(X[col], categories=sorted(X[col][:a].unique()))
    best, prediction, validation = -1, None, {}
    for leaves in (15, 31):
        model = HistGradientBoostingClassifier(max_leaf_nodes=leaves, max_iter=200, early_stopping=False,
                                               categorical_features="from_dtype", random_state=SEED)
        model.fit(X[:a], y[:a])
        p = model.predict_proba(X[a:])[:, 1]
        score = roc_auc_score(y[a:b], p[:b-a])
        validation[leaves] = float(score)
        if score > best:
            best, prediction = score, p
    return prediction, validation


def run(source, author_csv, out):
    out.mkdir(parents=True, exist_ok=True)
    data, window = history(source, author_csv)
    a, b = int(len(data)*.8), int(len(data)*.9)
    y = data.LABEL.to_numpy()
    p, tuning = {}, {}
    p["history_tree"], tuning["history_tree"] = trees(data, y, a, b, NUMERIC, CATEGORIES)
    p["current_tree"], tuning["current_tree"] = trees(data, y, a, b, NUMERIC[:5], CATEGORIES[:1])
    preprocess = ColumnTransformer([("num", StandardScaler(), NUMERIC),
                                   ("id", OneHotEncoder(handle_unknown="ignore"), CATEGORIES)])
    logistic = make_pipeline(preprocess, LogisticRegression(max_iter=1000))
    logistic.fit(data[:a], y[:a])
    p["logistic"] = logistic.predict_proba(data[a:])[:, 1]
    p["gru"], tuning["gru"], device = recurrent(data, window, a, b, y)
    weights = np.arange(5)/4
    blend = lambda w: w * p["gru"] + (1-w) * p["history_tree"]
    scores = [roc_auc_score(y[a:b], blend(w)[:b-a]) for w in weights]
    w = float(weights[np.argmax(scores)])
    p["blend"] = blend(w)
    frame = data[["USERID","LABEL"]].iloc[b:].copy()
    for name, values in p.items():
        frame[name] = values[b-a:]
    frame.to_csv(out/"predictions.csv.gz", compression={"method":"gzip","mtime":0})
    (out/"fit.json").write_text(json.dumps(dict(split=[a,b,len(data)], positive=[int(s.sum()) for s in (y[:a],y[a:b],y[b:])],
        validation=tuning, blend_grid=scores, gru_weight=w, device=device, torch=str(torch.__version__)), indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("author_csv", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    run(args.source, args.author_csv, args.out)
