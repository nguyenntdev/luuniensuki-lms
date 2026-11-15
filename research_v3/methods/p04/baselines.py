"""Reference baselines for CurriculumShiftBench (P04-T07).

C0 (majority class prior, fitted on train only) and C1 (logistic regression on
leakage-safe features, fitted on train only) are the honest reference
population every stratum is scored against. Numbers are measured, never
illustrative; when a cell cannot be computed (e.g. single-class partition) the
value is None and disclosed as such.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from research_v3.methods.p04.bench import PredictorContractError


class MajorityBaseline:
    """C0: always predicts the train-set majority class with its prior."""

    def __init__(self) -> None:
        self.majority: int | None = None
        self.prior: float | None = None

    def fit(self, rows: Sequence[Mapping[str, Any]]) -> "MajorityBaseline":
        counts = Counter(int(r["label"]) for r in rows)
        self.majority = counts.most_common(1)[0][0]
        self.prior = counts[self.majority] / sum(counts.values())
        return self

    def predict(self, rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        if self.majority is None:
            raise PredictorContractError("MajorityBaseline used before fit")
        return [
            {"prediction": self.majority, "probability": round(self.prior, 6)} for _ in rows
        ]


class LogisticBaseline:
    """C1: L2 logistic regression on numeric leakage-safe features.

    Categorical features are one-hot encoded on a fixed train-derived
    vocabulary; unseen categories at inference map to all-zeros (no target
    encoding, no label statistics in features). Fit on train partitions only.
    """

    NUMERIC_KEYS = (
        "num_of_prev_attempts", "studied_credits", "early_click_total", "early_active_sites",
        # UCI student-performance numeric features (OULAD numerics absent there)
        "age", "Medu", "Fedu", "traveltime", "studytime", "failures",
        "famrel", "freetime", "goout", "Dalc", "Walc", "health", "absences",
    )
    CATEGORICAL_KEYS = (
        "gender", "highest_education", "imd_band", "age_band", "disability", "region",
        # UCI categorical features
        "subject", "school", "sex", "address", "famsize", "Pstatus",
        "schoolsup", "famsup", "paid", "activities", "nursery", "higher",
        "internet", "romantic",
    )

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.vocab: dict[str, dict[str, int]] = {}
        self.mean: list[float] = []
        self.std: list[float] = []
        self._model = None
        self.feature_names: list[str] = []

    def _vectorize(self, rows: Sequence[Mapping[str, Any]], fit: bool) -> list[list[float]]:
        if fit:
            # two passes: grow the vocabulary first so every row gets the same
            # vector width, then emit fixed-width rows
            self.vocab = {}
            for row in rows:
                inp = row["input"]
                for key in self.CATEGORICAL_KEYS:
                    value = str(inp.get(key, ""))
                    if value and value not in self.vocab.setdefault(key, {}):
                        self.vocab[key][value] = len(self.vocab[key])
        vectors: list[list[float]] = []
        for row in rows:
            inp = row["input"]
            vec: list[float] = []
            for key in self.NUMERIC_KEYS:
                try:
                    vec.append(float(inp.get(key, 0.0) or 0.0))
                except (TypeError, ValueError):
                    vec.append(0.0)
            for key in self.CATEGORICAL_KEYS:
                vocab = self.vocab.get(key, {})
                onehot = [0.0] * len(vocab)
                idx = vocab.get(str(inp.get(key, "")))
                if idx is not None:
                    onehot[idx] = 1.0
                vec.extend(onehot)
            vectors.append(vec)
        return vectors

    def fit(self, rows: Sequence[Mapping[str, Any]]) -> "LogisticBaseline":
        import numpy as np
        from sklearn.linear_model import LogisticRegression

        X = np.asarray(self._vectorize(rows, fit=True), dtype=float)
        y = np.asarray([int(r["label"]) for r in rows], dtype=int)
        if len(set(y.tolist())) < 2:
            raise PredictorContractError("C1 requires both classes in training data")
        self.mean = X.mean(axis=0).tolist()
        self.std = (X.std(axis=0) + 1e-9).tolist()
        Xs = (X - np.asarray(self.mean)) / np.asarray(self.std)
        self._model = LogisticRegression(max_iter=1000, random_state=self.seed)
        self._model.fit(Xs, y)
        return self

    def predict_proba_rows(self, rows: Sequence[Mapping[str, Any]]) -> list[float]:
        import numpy as np

        if self._model is None:
            raise PredictorContractError("LogisticBaseline used before fit")
        X = np.asarray(self._vectorize(rows, fit=False), dtype=float)
        Xs = (X - np.asarray(self.mean)) / np.asarray(self.std)
        return [round(float(p), 6) for p in self._model.predict_proba(Xs)[:, 1]]

    def predict(self, rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        return [
            {"prediction": 1 if p >= 0.5 else 0, "probability": p}
            for p in self.predict_proba_rows(rows)
        ]
