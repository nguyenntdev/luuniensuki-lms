"""Draw actionable precision for fixed queues and two frozen status conditions."""
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parent
main = pd.read_csv(root/"run/summary.csv").query("percent == 10")
earlier = pd.read_csv(root/"transport_run/transport_terms.csv")
fig, (left, right) = plt.subplots(1, 2, figsize=(10, 3.7), layout="constrained")
labels = ["0","1","7","14","30","all"]
for model, name, color, marker in [("catboost_all","CatBoost","#135b89","o"),
                                   ("logit_all","Logistic","#b45517","s"),
                                   ("uniform","Uniform","#4e6253","^")]:
    ordered = main[main.model.eq(model)].set_index("lag").loc[labels]
    left.plot(range(6), 100*ordered.actionable_precision, marker=marker, color=color, label=name)
left.set(xticks=range(6), xticklabels=["0","1","7","14","30","Unfiltered"],
         ylabel="Actionable cases per 100 review slots", xlabel="Delay in withdrawal status (days)",
         title="Day-60 review in 2014J")
left.legend(frameon=False, fontsize=8)
for i, lag in enumerate(["0","all"]):
    scores = earlier[earlier.lag.eq(lag)].pivot(index="term", columns="method", values="captures")
    budgets = earlier.groupby("term").seats.first()
    diff = (scores.recency-scores.uniform)/budgets*100
    right.bar(np.arange(len(diff))+(i-.5)*.36, diff, width=.34,
              label=["Current", "Unfiltered"][i], color=["#135b89","#b45517"][i])
right.axhline(0,color="#444444",linewidth=.7)
right.set(xticks=np.arange(len(diff)), xticklabels=diff.index,
          xlabel="Earlier presentation", ylabel="Additional actionable cases per 100 slots",
          title="Inactivity ranking versus uniform review")
right.legend(frameon=False, fontsize=8)
for ax in (left,right):
    ax.spines[["top","right"]].set_visible(False)
fig.savefig(root/"queues.png", dpi=200)
