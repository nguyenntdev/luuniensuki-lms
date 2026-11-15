"""P11 reliability harness: Krippendorff's alpha, weighted Cohen's kappa, ICC(A,1), Cronbach's alpha.

Operates on annotation matrices: rows = units (responses), columns = raters,
cells = ordinal levels 0-3, or NaN/None for missing ratings (any number of raters).

HARD RULE (ethics + spec): results computed here may only be reported from REAL human
annotation matrices. Synthetic toy matrices are permitted ONLY inside tests and the
clearly-labeled harness smoke run (this file's CLI), never in manuscript results.

No fabrication guarantee: every function raises EmptyMatrixError on empty/all-missing
input instead of returning a plausible number. No annotator IDs or agreement values are
invented anywhere in this module.

Agreement math implemented locally: research_v3/scripts/annotations.py does not exist
(verified 2026-11-15); per task instruction the math lives here. Formulations follow
Krippendorff (2004) coincidence-matrix alpha, Cohen (1968) weighted kappa with
quadratic weights, and Shrout & Fleiss (1979) ICC case 2A (absolute agreement).

Python deps: numpy + scipy only (both pinned project-wide); no external agreement lib.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

try:  # scipy is available in the project env; degrade with a clear error if not
    from scipy import stats as _stats
except ImportError as _e:  # pragma: no cover
    _stats = None  # type: ignore[assignment]
    _scipy_import_error = _e


class ReliabilityError(ValueError):
    """Raised on malformed annotation matrices — fail closed, never guess."""


class EmptyMatrixError(ReliabilityError):
    """Raised when no ratable unit exists; a number here would be fabrication."""


#: sentinel accepted in annotation matrices for "not rated by this rater"
MISSING = None


def _to_matrix(ratings: Sequence[Sequence[float | int | None]]) -> np.ndarray:
    m = np.asarray(
        [[np.nan if v is None else float(v) for v in row] for row in ratings],
        dtype=float,
    )
    if m.ndim != 2:
        raise ReliabilityError("ratings must be a 2-D matrix (units x raters)")
    if m.shape[1] < 2:
        raise ReliabilityError("need >= 2 raters for agreement")
    valid = m[~np.isnan(m)]
    if valid.size == 0:
        raise EmptyMatrixError("no rated units — refusing to produce a number")
    return m


# ---------------------------------------------------------------------------
# Krippendorff's alpha (coincidence-matrix formulation, general missing data)
# ---------------------------------------------------------------------------


def _alpha_general(
    ratings: Sequence[Sequence[float | int | None]],
    distance: str,
) -> float | None:
    """Krippendorff (2004, 2011) coincidence-matrix alpha with general missing data.

    D_o = (1/n) * sum_{u!=v} c_uv * delta(u,v)
    D_e = 1/(n(n-1)) * sum_{u!=v} n_u * n_v * delta(u,v)
    alpha = 1 - D_o / D_e
    where c_uv is the coincidence matrix, n_u its marginals, n the number of
    pairable values. Ordinal distance uses cumulative coincidence marginals
    (Krippendorff 2011, ordinal metric).
    """
    m = _to_matrix(ratings)

    values = np.unique(m[~np.isnan(m)])
    k = len(values)
    value_index = {v: i for i, v in enumerate(values)}
    c = np.zeros((k, k), dtype=float)

    for row in m:
        obs = row[~np.isnan(row)]
        mu = len(obs)
        if mu < 2:
            continue  # unpairable unit
        for a in range(mu):
            for b in range(mu):
                if a == b:
                    continue
                c[value_index[obs[a]], value_index[obs[b]]] += 1.0 / (mu - 1)

    n = float(c.sum())  # total pairable values (= sum of coincidence marginals)
    if n < 2:
        raise EmptyMatrixError("fewer than 2 pairable observations — alpha undefined")

    marginals = c.sum(axis=1)

    if distance == "nominal":
        def delta(x: float, y: float) -> float:
            return 0.0 if x == y else 1.0
    elif distance in ("interval", "quadratic"):
        def delta(x: float, y: float) -> float:
            return (x - y) ** 2
    elif distance == "ordinal":
        # Krippendorff (2011) ordinal metric:
        # delta(x, y) = ( sum_{g=rank_min..rank_max} n_g - (n_rank_min + n_rank_max)/2 )^2
        # where ranks are over the sorted observed value domain and n_g are the
        # coincidence marginals.
        def delta(x: float, y: float) -> float:
            ix, iy = value_index[x], value_index[y]
            if ix == iy:
                return 0.0
            lo_i, hi_i = (ix, iy) if ix < iy else (iy, ix)
            span = float(marginals[lo_i : hi_i + 1].sum())
            half = (float(marginals[lo_i]) + float(marginals[hi_i])) / 2.0
            return (span - half) ** 2
    else:
        raise ReliabilityError(f"unknown distance {distance!r}")

    do = 0.0
    de = 0.0
    for i in range(k):
        for j in range(k):
            if i == j:
                continue
            d = delta(float(values[i]), float(values[j]))
            do += c[i, j] * d
            de += marginals[i] * marginals[j] * d
    do /= n
    de /= n * (n - 1.0)

    if do == 0.0 and de == 0.0:
        return 1.0  # perfect agreement
    if de == 0.0:
        raise ReliabilityError("degenerate expected disagreement — alpha undefined")
    return float(1.0 - do / de)


def krippendorff_alpha(
    ratings: Sequence[Sequence[float | int | None]],
    *,
    level_of_measurement: str = "ordinal",
) -> float | None:
    """Krippendorff's alpha over a units x raters matrix with missing data support.

    level_of_measurement: nominal | ordinal | interval | quadratic.
    Returns None only if the matrix is too sparse (EmptyMatrixError otherwise).
    """
    if level_of_measurement not in {"nominal", "ordinal", "interval", "quadratic"}:
        raise ReliabilityError(f"unknown level_of_measurement {level_of_measurement!r}")
    return _alpha_general(ratings, level_of_measurement)


# ---------------------------------------------------------------------------
# Weighted Cohen's kappa (quadratic weights, two raters, no missing pairs)
# ---------------------------------------------------------------------------


def cohen_kappa_weighted(
    rater_a: Sequence[float | int | None],
    rater_b: Sequence[float | int | None],
    *,
    weights: str = "quadratic",
    n_levels: int = 4,
) -> float | None:
    """Quadratic-weighted Cohen's kappa for two complete raters on an ordinal scale.

    Pairs where either rater is missing are excluded (listwise); if fewer than 2
    complete pairs remain, raises EmptyMatrixError rather than inventing a value.
    """
    if len(rater_a) != len(rater_b):
        raise ReliabilityError("rater vectors must align")
    pairs = [
        (float(a), float(b))
        for a, b in zip(rater_a, rater_b)
        if a is not None and b is not None
    ]
    if len(pairs) < 2:
        raise EmptyMatrixError("fewer than 2 complete rating pairs — kappa undefined")

    lo = 0.0
    hi = float(n_levels - 1)
    o = np.zeros((n_levels, n_levels), dtype=float)
    for a, b in pairs:
        ia, ib = int(round(a - lo)), int(round(b - lo))
        if not (0 <= ia < n_levels and 0 <= ib < n_levels):
            raise ReliabilityError(f"rating outside 0..{n_levels - 1}: ({a}, {b})")
        o[ia, ib] += 1.0

    n = o.sum()
    if n == 0:
        raise EmptyMatrixError("empty confusion matrix")

    w = np.zeros((n_levels, n_levels), dtype=float)
    if weights == "quadratic":
        for i in range(n_levels):
            for j in range(n_levels):
                w[i, j] = float((i - j) ** 2)
    elif weights == "linear":
        for i in range(n_levels):
            for j in range(n_levels):
                w[i, j] = float(abs(i - j))
    elif weights == "unweighted":
        for i in range(n_levels):
            for j in range(n_levels):
                w[i, j] = 0.0 if i == j else 1.0
    else:
        raise ReliabilityError(f"unknown weights {weights!r}")

    ra = o.sum(axis=1) / n
    rb = o.sum(axis=0) / n
    p_o = float((o * w).sum() / n)
    p_e = float((np.outer(ra, rb) * w).sum())
    if n > 0 and float(o.trace()) == n and float((np.outer(ra, rb) * w).sum()) == 0.0:
        return 1.0  # all pairs agree and expected weighted disagreement is 0
    if p_e == 1.0:
        raise EmptyMatrixError("degenerate marginals — kappa undefined")
    return float(1.0 - p_o / p_e)


def cohen_kappa_unweighted(
    rater_a: Sequence[float | int | None],
    rater_b: Sequence[float | int | None],
) -> float | None:
    return cohen_kappa_weighted(rater_a, rater_b, weights="unweighted")


# ---------------------------------------------------------------------------
# ICC(A,1): two-way random effects, absolute agreement, single rater
# ---------------------------------------------------------------------------


def icc_a1(ratings: Sequence[Sequence[float | int | None]]) -> float | None:
    """ICC(A,1) — Shrout & Fleiss (1979) case 2: absolute agreement, single rater.

    Complete-case: units with any missing rating are excluded (consistent with the
    two-way ANOVA identity); requires >= 2 complete units and >= 2 raters.
    """
    m = _to_matrix(ratings)
    complete = m[~np.isnan(m).any(axis=1)]
    if complete.shape[0] < 2:
        raise EmptyMatrixError("need >= 2 complete units for ICC")
    n, k = complete.shape

    grand = complete.mean()
    row_means = complete.mean(axis=1)
    col_means = complete.mean(axis=0)

    ss_total = ((complete - grand) ** 2).sum()
    ss_rows = k * ((row_means - grand) ** 2).sum()
    ss_cols = n * ((col_means - grand) ** 2).sum()
    ss_err = ss_total - ss_rows - ss_cols

    ms_r = ss_rows / (n - 1)
    ms_c = ss_cols / (k - 1)
    ms_e = ss_err / ((n - 1) * (k - 1))

    denom = ms_r + (k - 1) * ms_e + k * (ms_c - ms_e) / n
    if denom == 0:
        return None
    return float((ms_r - ms_e) / denom)


# ---------------------------------------------------------------------------
# Internal consistency (Cronbach's alpha over the 4 criteria — NOT inter-rater)
# ---------------------------------------------------------------------------


def cronbach_alpha(items: Sequence[Sequence[float | int | None]]) -> float | None:
    """Cronbach's alpha across items (columns) for internal-consistency reporting.

    Here columns are the S1-S4 criteria scored by ONE rater; it says nothing about
    inter-rater reliability and must be labeled as instrument internal consistency.
    Listwise deletion of rows with missing values.
    """
    m = _to_matrix(items)
    complete = m[~np.isnan(m).any(axis=1)]
    if complete.shape[0] < 2:
        raise EmptyMatrixError("need >= 2 complete rows for Cronbach alpha")
    k = complete.shape[1]
    if k < 2:
        raise ReliabilityError("need >= 2 items (columns)")
    variances = complete.var(axis=0, ddof=1)
    total_var = complete.sum(axis=1).var(ddof=1)
    if total_var == 0:
        return None
    return float((k / (k - 1)) * (1.0 - variances.sum() / total_var))


# ---------------------------------------------------------------------------
# Harness entry point
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReliabilityReport:
    source: str
    is_synthetic_toy: bool
    n_units: int
    n_raters: int
    n_complete_pairs: int
    alpha_nominal: float | None
    alpha_ordinal: float | None
    alpha_interval: float | None
    kappa_weighted: float | None
    kappa_unweighted: float | None
    icc: float | None
    provenance_note: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "is_synthetic_toy": self.is_synthetic_toy,
            "n_units": self.n_units,
            "n_raters": self.n_raters,
            "n_complete_pairs": self.n_complete_pairs,
            "alpha_nominal": self.alpha_nominal,
            "alpha_ordinal": ReliabilityReport._r3(self.alpha_ordinal),
            "alpha_interval": ReliabilityReport._r3(self.alpha_interval),
            "kappa_weighted": ReliabilityReport._r3(self.kappa_weighted),
            "kappa_unweighted": ReliabilityReport._r3(self.kappa_unweighted),
            "icc": ReliabilityReport._r3(self.icc),
            "provenance_note": self.provenance_note,
        }

    @staticmethod
    def _r3(x: float | None) -> float | None:
        return round(x, 3) if isinstance(x, float) else None


def compute_reliability(
    ratings: Sequence[Sequence[float | int | None]],
    *,
    source: str = "unlabeled",
    is_synthetic_toy: bool = False,
    n_levels: int = 4,
) -> ReliabilityReport:
    """Full reliability report for one annotation matrix.

    `is_synthetic_toy=True` marks the input as toy; the harness CLI refuses to write
    toy-derived numbers into results paths (tests + smoke run only).
    """
    m = _to_matrix(ratings)
    n_units, n_raters = m.shape
    complete_pairs = int(
        sum(
            1
            for row in ratings
            if len(row) >= 2 and row[0] is not None and row[1] is not None
        )
    )
    try:
        icc_value: float | None = icc_a1(ratings)
    except EmptyMatrixError:
        icc_value = None  # too few complete units; ICC unestimable, never guessed
    return ReliabilityReport(
        source=source,
        is_synthetic_toy=is_synthetic_toy,
        n_units=n_units,
        n_raters=n_raters,
        n_complete_pairs=complete_pairs,
        alpha_nominal=krippendorff_alpha(ratings, level_of_measurement="nominal"),
        alpha_ordinal=krippendorff_alpha(ratings, level_of_measurement="ordinal"),
        alpha_interval=krippendorff_alpha(ratings, level_of_measurement="interval"),
        kappa_weighted=cohen_kappa_weighted(
            [r[0] for r in ratings], [r[1] for r in ratings], n_levels=n_levels
        ),
        kappa_unweighted=cohen_kappa_unweighted(
            [r[0] for r in ratings], [r[1] for r in ratings]
        ),
        icc=icc_value,
        provenance_note=(
            "SYNTHETIC TOY — not a result"
            if is_synthetic_toy
            else "REAL annotation matrix; must carry annotation_batch card reference"
        ),
    )


# ---------------------------------------------------------------------------
# CSV ingestion (annotation CSV contract, see annotation pack README)
# ---------------------------------------------------------------------------


def load_ratings_csv(path: str, *, value_columns: tuple[str, ...] | None = None) -> tuple[list[str], list[list[float | None]]]:
    """Load a units x raters matrix from CSV with explicit column selection.

    CSV contract (annotation pack): one row per unit; rater columns are
    pseudonymous (rater_A, rater_B, ...); missing = empty cell; values = 0-3 or
    NOT_APPLICABLE/ABSTAIN (both mapped to None so NA/ABSTAIN never enter agreement math).
    NOT_APPLICABLE/ABSTAIN mapping is a PREREGISTERED rule: excluded, never imputed.
    """
    import csv

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ReliabilityError("CSV has no header")
        cols = list(value_columns or ())
        if not cols:
            cols = [c for c in reader.fieldnames if c not in ("unit_id", "response_id", "criterion", "notes")]
        rows: list[list[float | None]] = []
        ids: list[str] = []
        for rec in reader:
            ids.append(rec.get("unit_id", rec.get("response_id", "")))
            row: list[float | None] = []
            for c in cols:
                raw = (rec.get(c) or "").strip()
                if raw in {"", "NA", "NOT_APPLICABLE", "ABSTAIN"}:
                    row.append(None)
                else:
                    try:
                        v = float(raw)
                    except ValueError as e:
                        raise ReliabilityError(f"non-numeric rating {raw!r} in column {c}") from e
                    if not 0.0 <= v <= 3.0:
                        raise ReliabilityError(f"rating {v} outside 0-3 in column {c}")
                    row.append(v)
            rows.append(row)
    if not rows:
        raise EmptyMatrixError("CSV contains no rating rows")
    return ids, rows


# ---------------------------------------------------------------------------
# CLI smoke run (TOY data only — output is labeled and never a result)
# ---------------------------------------------------------------------------


def _toy() -> tuple[list[list[float | None]], list[list[float | None]], list[list[float | None]]]:
    """Deterministic toy matrices for smoke + tests. SYNTHETIC, never results."""
    # perfect agreement, 2 raters, 6 units
    perfect = [[2, 2], [3, 3], [1, 1], [0, 0], [3, 3], [2, 2]]
    # systematic near-disagreement: rater B always one level below rater A
    systematic = [[3, 2], [3, 2], [2, 1], [3, 2], [2, 1], [3, 3]]
    # sparse: 3 raters with missing cells
    sparse = [[2, 2, None], [3, None, 3], [None, 1, 1], [0, 0, None], [3, 3, 3], [1, None, 2]]
    return perfect, systematic, sparse


def smoke_toy() -> dict[str, object]:
    """Run the harness on deterministic toy matrices; every number is labeled SYNTHETIC TOY."""
    perfect, systematic, sparse = _toy()
    out: dict[str, object] = {
        "warning": "SYNTHETIC TOY DATA — NOT A RESULT. Real reliability requires human annotation matrices (P11-T19 BLOCKED).",
        "perfect_agreement": compute_reliability(perfect, source="toy_perfect", is_synthetic_toy=True).to_dict(),
        "systematic_disagreement": compute_reliability(
            systematic, source="toy_systematic", is_synthetic_toy=True
        ).to_dict(),
        "sparse_missing": compute_reliability(sparse, source="toy_sparse", is_synthetic_toy=True).to_dict(),
    }
    return out


if __name__ == "__main__":
    import json

    print(json.dumps(smoke_toy(), indent=2))
