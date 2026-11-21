# /// script
# dependencies = ["matplotlib==3.10.8"]
# ///
"""Plot pointwise paired risk differences from the saved bootstrap results."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent
results = json.loads((root / "secondary_run/results.json").read_text())
fig, axes = plt.subplots(1, 2, figsize=(8, 3.6), sharey=True, layout="constrained")
for ax, name, title in zip(axes, ["oulad", "uci"], ["OULAD 2014J", "UCI Portugal"], strict=True):
    curve = results[name]["risk_curve"]
    x = [100 * point["coverage"] for point in curve]
    y = [100 * (point["reroute_risk"] - point["argmax_risk"]) for point in curve]
    low, high = zip(*(point["risk_difference_interval95"] for point in curve))
    ax.axhline(0, color="0.5", lw=1)
    ax.errorbar(x, y, yerr=[[v - 100*l for v, l in zip(y, low)],
                            [100*h - v for v, h in zip(y, high)]],
                fmt="o-", color="#185a76", capsize=3)
    ax.set_title(title)
    ax.set_xticks([10, 25, 50, 75, 100])
    ax.set_xlabel("Registrations accepted (%)")
axes[0].set_ylabel("Reroute minus argmax error\n(percentage points)")
fig.savefig(root / "risk_difference.png", dpi=180)
