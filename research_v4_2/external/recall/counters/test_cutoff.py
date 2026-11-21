"""Perturbing an entire timestamp can only change later counter-history predictors."""
import numpy as np
import pandas as pd
from prepare import ABILITY, DELTA, PREVIOUS, enrich

data=pd.DataFrame({
    "user_id":["a"]*6,"lexeme":["x","y","x","x","y","x"],"timestamp":[1,1,2,2,2,3],
    "session_seen":[1,1,2,1,1,1],"session_correct":[1,0,1,0,1,1],
    "history_seen":[3,1,5,5,2,8],"history_correct":[2,0,4,4,0,5],
    "delta":[1,1,1,1,1,1],"pos":["n"]*6,"item_difficulty":[.8]*6})
data["gold"]=data.session_correct/data.session_seen
before=enrich(data)
perturbed=data.copy()
mask=data.timestamp.eq(2)
perturbed.loc[mask,"session_seen"]=10
perturbed.loc[mask,"session_correct"]=9
perturbed.loc[mask,"gold"]=.9
after=enrich(perturbed)
pd.testing.assert_frame_equal(before.loc[data.timestamp<=2,PREVIOUS+ABILITY+DELTA],
                              after.loc[data.timestamp<=2,PREVIOUS+ABILITY+DELTA])
last=before.iloc[-1]
assert last.prev_session==3 and last.prev_success==1 and last.excess_seen==0 and last.excess_correct==0
assert before.iloc[2].excess_seen==1 and before.iloc[2].excess_correct==1
assert after.iloc[-1].excess_seen == -17
assert before.iloc[0][PREVIOUS+DELTA].isna().all()
shuffled=enrich(data.sample(frac=1,random_state=9).reset_index()).set_index("index").sort_index()
pd.testing.assert_frame_equal(before[PREVIOUS+ABILITY+DELTA],shuffled[PREVIOUS+ABILITY+DELTA],check_names=False)
print("Verified tied-timestamp perturbation, grouping, arrival-order invariance and signed differences.")
