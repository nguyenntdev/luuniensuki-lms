"""Recompute the eight learner-cluster intervals from the released forecasts."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

root=Path(sys.argv[1])
receipt=json.loads((root/"result.json").read_text())
frame=pd.read_csv(root/"screen.csv.gz")
names=list(receipt["contrasts"])
full=names+["blend_joint"]
y=frame.y.to_numpy()[:,None]
p=np.clip(frame[full].to_numpy(),1e-7,1-1e-7)
loss=-np.where(y==1,np.log(p),np.log1p(-p))
uids,group=np.unique(frame.uid,return_inverse=True)
cluster=np.zeros((len(uids),len(names)))
for i in range(len(names)):
    cluster[:,i]=np.bincount(group,weights=loss[:,i]-loss[:,-1])
sizes=np.bincount(group)
rng=np.random.default_rng(732)
# Repeat the exact frozen multinomial generator; compute interval statistics per draw.
weights=rng.multinomial(len(sizes),np.full(len(sizes),1/len(sizes)),size=5000)
values=np.array([np.average(cluster/sizes[:,None],axis=0,weights=w*sizes) for w in weights])
limits=np.quantile(values,[.025/len(names),1-.025/len(names)],axis=0)
for i,n in enumerate(names):
    np.testing.assert_allclose(limits[:,i],receipt["contrasts"][n]["ci"],atol=1e-12)
print(f"Verified {len(names)} simultaneous paired intervals on {len(uids)} learner clusters.")
