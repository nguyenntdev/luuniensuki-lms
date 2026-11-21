"""Plot fixed-queue comparisons in their respective endpoint units."""
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
with (HERE.parent / "status_bounds/results.csv").open() as stream:
    bounds = [r for r in csv.DictReader(stream) if r["features"]=="Assessment"
              and r["model"]=="Logistic regression"]
mooc = json.loads((HERE/"result.json").read_text())["landmarks"]["0.5"]["vs_uniform"]
fig, (ax, bx) = plt.subplots(1,2,figsize=(10.5,4.2),layout="constrained")
y = np.arange(len(bounds))
lo = [float(r["capture_lower"]) for r in bounds]
hi = [float(r["capture_upper"]) for r in bounds]
random = [float(r["uniform_expected"]) for r in bounds]
ax.hlines(y,lo,hi,color="#25667f",lw=3,label="Feasible capture interval")
ax.plot(lo,y,"|",color="#25667f",ms=9)
ax.plot(hi,y,"|",color="#25667f",ms=9)
ax.scatter(random,y,marker="D",color="#ad5d16",s=24,label="Uniform expectation",zorder=3)
ax.set_yticks(y,["Current","1 day","7 days","14 days","30 days","No filter"])
ax.invert_yaxis()
ax.set(xlim=(-9,309),xlabel="Eligible withdrawal labels captured in 857 seats",
       title="OULAD · published day-84 logistic scores")
ax.legend(loc="lower center",bbox_to_anchor=(.50,-.34),frameon=False,fontsize=9)
names=["inactivity","few_actions","recent_activity","many_actions"]
for lag,offset,color,marker,label in [("0",-.13,"#25667f","o","Current flag (oracle)"),
                                    ("all",.13,"#ad5d16","s","No flag filter")]:
    values = {r["method"]:r for r in mooc if r["lag"]==lag}
    vals = np.array([values[n]["gain"] for n in names])*100
    ci = np.array([values[n]["simultaneous_ci95"] for n in names]).T*100
    bx.errorbar(vals,np.arange(4)+offset,xerr=[vals-ci[0],ci[1]-vals],fmt=marker,ms=5,capsize=3,
                color=color,label=label)
bx.axvline(0,ls="--",lw=.85,color="#555555")
bx.set_yticks(range(4),["Longer inactivity","Fewer actions","Recent activity","More actions"])
bx.invert_yaxis()
bx.set(xlabel="Additional first flags per 100 seats vs uniform",
       title="Independent MOOC stream · midpoint")
bx.legend(loc="lower center",bbox_to_anchor=(.50,-.34),frameon=False,fontsize=9)
for panel in (ax,bx):
    panel.spines[["top","right"]].set_visible(False)
fig.savefig(HERE/"external_queues.png",dpi=180,bbox_inches="tight")
