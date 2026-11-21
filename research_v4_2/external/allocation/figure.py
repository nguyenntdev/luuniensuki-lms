"""Plot paired policy differences from the released aggregate counts."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MaxNLocator

folder = Path(__file__).resolve().parent
data = pd.read_csv(folder / "results.csv")
fig, axes = plt.subplots(2, 2, figsize=(8.2, 5.4), sharex=True, sharey=True)
for row, (dataset, label) in enumerate([("dropout", "University dropout"),
                                        ("mathematics", "Secondary mathematics")]):
    for col, model in enumerate(["logistic", "boosting"]):
        ax = axes[row, col]
        subset = data[(data.dataset == dataset) & (data.model == model)]
        recalls = subset.pivot(index="percent", columns="policy", values="worst_recall")
        ax.axhline(0, color="#555555", linewidth=0.9)
        for policy, name, color, marker in [("fair", "FA*IR", "#006e68", "o"),
                                             ("quota", "Proportional quota", "#9e4224", "s")]:
            diff = (recalls[policy] - recalls.risk) * 100
            ax.plot(diff.index, diff, marker=marker, label=name, color=color)
        ax.set_title(f"{label} · {model}", fontsize=11)
        ax.set_xticks([5, 10, 15], ["5%", "10%", "15%"])
        ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))
        ax.spines[["top", "right"]].set_visible(False)
fig.supylabel("Change in worst-group recall (percentage points)", fontsize=11)
fig.supxlabel("Pool review budget", fontsize=11, y=0.095)
fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="lower center", ncol=2, frameon=False)
fig.tight_layout(rect=(0.035, 0.12, 1, 1))
fig.savefig(folder / "recall_differences.png", dpi=180)
