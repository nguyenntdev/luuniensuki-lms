"""Score new and historical models on the same registrations using the previous AUC scorer."""
import json
from pathlib import Path
import subprocess
import sys
import gzip
import shutil
import pandas as pd

here=Path(__file__).resolve().parent
run=Path(sys.argv[1])
earlier=here.parent/"run"
pred=pd.read_csv(run/"predictions.csv.gz",float_precision="round_trip")
old=pd.read_csv(earlier/"predictions.csv.gz",float_precision="round_trip")
keys=["row","learner","code_module","code_presentation","y"]
pd.testing.assert_frame_equal(pred[keys],old[keys])
for method in old.columns[5:]:
    pred["previous_"+method]=old[method]
with gzip.GzipFile(str(run/"predictions.csv.gz"),"wb",mtime=0) as f:pred.to_csv(f,index=False)
shutil.copyfile(earlier/"counts.csv",run/"counts.csv")
subprocess.run([sys.executable,str(here.parent/"score.py"),str(run)],check=True)
scores=pd.read_csv(run/"scores.csv").query('course!="pooled"')
local=scores.query('method=="mixed_local"').set_index("course").auc
rows=[]
for method,group in scores.groupby("method"):
    values=group.set_index("course").auc
    diffs=values-local
    rows.append(dict(method=method,macro=values.mean(),p10=values.quantile(.1),minimum=values.min(),
                     courses_losing_to_local=int((diffs < -1e-12).sum()),courses_improving_on_local=int((diffs>1e-12).sum()),
                     macro_log_loss=group.log_loss.mean()))
pd.DataFrame(rows).to_csv(run/"client_metrics.csv",index=False)
