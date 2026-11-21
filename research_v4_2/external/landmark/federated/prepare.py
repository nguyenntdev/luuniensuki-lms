"""Build a deidentified development matrix from the pinned OULAD archive."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from evaluate import FEATURES, prepare

archive, output = map(Path, sys.argv[1:])
frame = prepare(archive)
future = frame.code_presentation.eq("2014J")
training = ~future & ~frame.id_student.isin(frame.loc[future, "id_student"])
rows = frame.loc[(training | future) & frame.eligible].copy()
rows["split"] = np.where(rows.code_presentation.eq("2014J"), "dev", "train")
clients = set(rows.loc[rows.split.eq("train"), "code_module"])
assert set(rows.loc[rows.split.eq("dev"), "code_module"]) <= clients
train_ids = rows.loc[rows.split.eq("train"), "id_student"]
assert not train_ids.isin(rows.loc[rows.split.eq("dev"), "id_student"]).any()
rows["learner"] = pd.factorize(rows.id_student, sort=True)[0]
rows["row"] = np.arange(len(rows))
rows["y"] = rows.outcome.astype(int)
rows[["row", "learner", "code_module", "code_presentation", "split", "y", *FEATURES]].to_csv(output, index=False)
