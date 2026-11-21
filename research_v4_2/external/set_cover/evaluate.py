"""Evaluate cover witnesses against the externally supplied OR-Library matrices."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csc_matrix


def evaluate(path):
    tokens = iter(map(int, path.read_text().split()))
    rows, cols = next(tokens), next(tokens)
    costs = np.array([next(tokens) for _ in range(cols)])
    covers = np.zeros((rows, cols), dtype=bool)
    for i in range(rows):
        for _ in range(next(tokens)):
            j = next(tokens)
            assert 1 <= j <= cols
            covers[i, j-1] = True
    assert next(tokens, None) is None and covers.any(axis=1).all()
    unmet = np.ones(rows, dtype=bool)
    chosen = []
    while unmet.any():
        j = int(np.argmax(covers[unmet].sum(axis=0)/costs))
        chosen.append(j)
        unmet &= ~covers[:, j]
    keep = chosen.copy()
    for j in reversed(chosen):
        remaining = [k for k in keep if k != j]
        if covers[:, remaining].any(axis=1).all():
            keep = remaining
    exact = milp(costs, integrality=np.ones(cols), bounds=Bounds(0,1),
                 constraints=LinearConstraint(csc_matrix(covers),1,np.inf),
                 options={"time_limit":45, "mip_rel_gap":0})
    result = {"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"rows":rows,"columns":cols,
              "solver":exact.message,"solver_bound":exact.mip_dual_bound,"solutions":{}}
    solutions = {"greedy":chosen,"greedy_pruned":keep}
    if exact.x is not None:
        solutions["milp"] = np.flatnonzero(exact.x > .5).tolist()
    for name, indices in solutions.items():
        assert covers[:, indices].any(axis=1).all()
        result["solutions"][name] = {"cost":int(costs[indices].sum()),"columns_one_based":[j+1 for j in indices]}
    return result


if __name__ == "__main__":
    root = Path(sys.argv[1])
    print(json.dumps({"scipy":scipy.__version__, "instances":{
        f"scp4{i}":evaluate(root/f"scp4{i}.txt") for i in range(1,11)}}, indent=2))
