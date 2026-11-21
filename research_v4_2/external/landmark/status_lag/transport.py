"""Replay two prespecified, training-free activity rankings in the three earlier terms."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from replay import prepare_landmark, select


def transport(archive):
    frame = prepare_landmark(archive)
    frame = frame[frame.code_presentation != "2014J"].copy()
    assert set(frame.code_presentation) == {"2013B", "2013J", "2014B"}
    frame["low_clicks"] = -frame.clicks
    frame["uniform"] = 0.
    results = []
    for (term, module), rows in frame.groupby(["code_presentation", "code_module"]):
        eligible = rows.eligible.to_numpy()
        cases = eligible & rows.outcome.to_numpy()
        seats = int(eligible.sum()//10)
        for lag in (0, 7, 30, None):
            available = np.ones(len(rows), bool) if lag is None else ~rows.date_unregistration.le(60-lag).to_numpy()
            for method in ("recency", "low_clicks", "uniform"):
                selection = select(rows.loc[available, method].to_numpy(), seats)
                assert np.isclose(selection.sum(), seats)
                results.append(dict(term=term, module=module, lag="all" if lag is None else str(lag),
                                    method=method, seats=seats, eligible=int(eligible.sum()),
                                    cases=int(cases.sum()), stale=selection[~eligible[available]].sum(),
                                    captures=selection[cases[available]].sum()))
    return pd.DataFrame(results)


if __name__ == "__main__":
    archive, out = map(Path, sys.argv[1:])
    results = transport(archive)
    out.mkdir(parents=True, exist_ok=True)
    results.to_csv(out/"transport_modules.csv", index=False, float_format="%.8f")
    pooled = results.groupby(["term","lag","method"], sort=False, as_index=False)[
        ["seats","eligible","cases","stale","captures"]].sum()
    pooled.to_csv(out/"transport_terms.csv", index=False, float_format="%.8f")
