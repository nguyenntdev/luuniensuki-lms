"""Fixed cohorts and training inputs. Individual records stay in memory."""
import csv
import hashlib
import io
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ARCHIVES = {
    "oulad": ("oulad/2013-2014/oulad.zip", "f2ed1902616c1fe8d2824d872c0b7d2d72be435bf0124d077044fe4be2c6d3e4"),
    "uci856": ("uci856.zip", "bbf757cd90b8312e9bfadb9192b05413f939a7c20e5f880a0d7e97064fecf557"),
}
KEYS = ["code_module", "code_presentation", "id_student"]


def verified_archive(dataset, raw):
    name, digest = ARCHIVES[dataset]
    path = Path(raw) / name
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
            raise ValueError(f"Unexpected data version: {path}")
    return ZipFile(path)


def cohort(dataset, archive):
    if dataset == "oulad":
        categorical = ["code_module", "gender", "age_band", "highest_education"]
        numeric = ["date_registration", "studied_credits", "num_of_prev_attempts"]
        info = pd.read_csv(archive.open("studentInfo.csv"), usecols=list(set(
            KEYS + categorical + numeric[1:])))
        reg = pd.read_csv(archive.open("studentRegistration.csv"), na_values=["?"])
        active = reg.date_registration.le(0) & (
            reg.date_unregistration.isna() | reg.date_unregistration.gt(0))
        data = info.merge(reg.loc[active, KEYS + ["date_registration"]],
                          on=KEYS, validate="one_to_one")
        data["sid"] = data.id_student.astype(str)
        data["key"] = data[KEYS].astype(str).agg("/".join, axis=1)
        data["female"] = data.gender.eq("F")
        data["pool"] = data.code_module
        data = data.sort_values(["code_presentation", "code_module", "sid"])
        test = data[data.code_presentation.eq("2014J")].drop_duplicates("sid")
        train = data[data.code_presentation.str.startswith("2013") &
                     ~data.sid.isin(test.sid)].drop_duplicates("sid")
    else:
        categorical = ["1", "2", "3", "4", "COURSE ID"]
        numeric = []
        data = pd.read_csv(archive.open("DATA (1).csv"), usecols=["STUDENT ID", *categorical])
        data["key"] = data["sid"] = data["STUDENT ID"]
        data["female"] = data["2"].eq(1)
        data["pool"] = "campus"
        ids = np.random.default_rng(42).permutation(sorted(data.sid))
        train_ids = ids[:int(.60 * len(ids))]
        train, test = data[data.sid.isin(train_ids)], data[~data.sid.isin(train_ids)]
    assert train.sid.is_unique and test.sid.is_unique and set(train.sid).isdisjoint(test.sid)
    return train.reset_index(drop=True), test.sort_values("sid").reset_index(drop=True), categorical, numeric


def outcomes(archive, dataset, requested):
    # Access the outcome field only after testing membership in the requested set.
    name = "studentInfo.csv" if dataset == "oulad" else "DATA (1).csv"
    labels = {}
    with io.TextIOWrapper(archive.open(name), encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            key = "/".join(row[k] for k in KEYS) if dataset == "oulad" else row["STUDENT ID"]
            if key in requested:
                labels[key] = (row["final_result"] == "Withdrawn" if dataset == "oulad"
                               else int(row["GRADE"]) <= 2)
    assert set(labels) == requested
    return labels


def predict(train, test, categorical, numeric, labels):
    y = train.key.map(labels).to_numpy(dtype=int)
    design = [("category", OneHotEncoder(handle_unknown="ignore"), categorical)]
    if numeric:
        design.append(("numeric", StandardScaler(), numeric))
    model = make_pipeline(ColumnTransformer(design), LogisticRegression(C=1, max_iter=1000))
    samples = [np.arange(len(train))]
    rng = np.random.default_rng(314)
    samples.extend(rng.integers(len(train), size=len(train)) for _ in range(40))
    probabilities = []
    for sample in samples:
        model.fit(train.iloc[sample], y[sample])
        probabilities.append(model.predict_proba(test)[:, 1])
    return np.array(probabilities)
