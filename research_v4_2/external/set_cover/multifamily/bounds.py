"""Compute integer-checkable dual certificates for the continuous set cover relaxation."""
import argparse
import json
from pathlib import Path
import time

from study import NAMES, parse_cover
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix


def dual_certificate(path):
    matrix, _, costs = parse_cover(path.read_bytes())
    start = time.process_time()
    lp = linprog(costs, A_ub=-csr_matrix(matrix, dtype=float),
                 b_ub=-np.ones(matrix.shape[0]), method="highs-ds")
    if not lp.success:
        raise ValueError(f"{path.name}: {lp.message}")
    scale = 10**6
    weights = np.rint(np.maximum(0, -lp.ineqlin.marginals)*scale).astype(int).tolist()
    # Raise the common denominator just enough to keep every rounded column feasible.
    for col, cost in enumerate(costs):
        column_sum = sum(weights[i] for i in np.flatnonzero(matrix[:, col]))
        scale = max(scale, (column_sum + cost - 1) // cost)
    return {"row_numerators": weights, "denominator": scale,
            "integer_lower_bound": (sum(weights) + scale - 1) // scale,
            "cpu_seconds": time.process_time() - start}


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("matrices", type=Path)
    cli.add_argument("output", type=Path)
    args = cli.parse_args()
    certs = {name: dual_certificate(args.matrices / (name + ".txt")) for name in NAMES}
    args.output.write_text(json.dumps(certs, indent=1) + "\n")
