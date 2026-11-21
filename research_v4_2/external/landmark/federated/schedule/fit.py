"""Run on CUDA with the parent train.py importable."""
import sys
import numpy as np
import pandas as pd
import torch
from train import FEATURES, adapt, federate, tensor

frame = pd.read_csv(sys.argv[1])
calendar = pd.read_csv(sys.argv[2], na_values="?")
keys = ["code_module", "code_presentation"]
count = calendar[calendar.date.between(0, 60)].groupby(keys).size()
frame = frame.join(count.rename("due"), on=keys)
dev = frame[frame.split == "dev"].copy()
for method in ("matched", "adapted"):
    def matrix(group):
        x = np.log1p(group[FEATURES].to_numpy()) / 4
        if method == "adapted":
            x = np.column_stack([x, x * group.due.fillna(0).to_numpy()[:, None] / 5])
        return tensor(np.column_stack([np.ones(len(x)), x]))

    clients = {c: (matrix(g), tensor(g.y.values))
               for c, g in frame[frame.split == "train"].groupby("code_module")}
    width = next(iter(clients.values()))[0].shape[1]
    w = federate(clients, tensor(np.zeros(width)), 0.)
    for c, g in dev.groupby("code_module"):
        local = adapt(*clients[c], w, [.005] + [.02] * (width - 1))
        dev.loc[g.index, method] = (matrix(g) @ local).sigmoid().cpu().numpy()
print(torch.cuda.get_device_name())
dev[["row", "learner", *keys, "y", "matched", "adapted"]].to_csv(sys.argv[3], index=False)
