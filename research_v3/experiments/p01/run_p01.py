#!/usr/bin/env python3
"""P01 evaluation CLI: run the preregistered matrix on real OULAD data.

Usage:
    python -m research_v3.experiments.p01.run_p01 [--out DIR] [--seed N]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from research_v3.methods.p01.pipeline import main as run_main


def cli() -> int:
    parser = argparse.ArgumentParser(description="P01 preregistered evaluation")
    parser.add_argument("--out", default="research_artifacts_v3/runs/p01")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    summary = run_main(out_root=args.out, seeds=(args.seed,))
    print(json.dumps({
        "rows_used": summary["rows_used"],
        "protocols": {
            k: {
                "sizes": v["sizes"],
                "null_result_is_null": v["null_result"]["is_null_or_negative"],
            }
            for k, v in summary["protocols"].items()
        },
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
