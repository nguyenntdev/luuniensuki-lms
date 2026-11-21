"""Check source memberships, item priors, and grid forecasts independently."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import norm

cache, study = map(Path, sys.argv[1:3])
original = pd.read_pickle(cache/"rows.pkl").reset_index(drop=True)
features = pd.read_csv(cache/"item_ability.csv.gz", dtype={"part":str,"skill":str})
assert original[["uid","start","row","y"]].equals(features[["uid","start","row","y"]])
est = pd.read_csv(study/"run/estimates.csv.gz")
source = original[original.bucket.between(70,79)]
assert source[["uid","start","row","y"]].reset_index(drop=True).equals(est[["uid","start","row","y"]])
fit_all = original[original.bucket < 60]
counts = fit_all.question.value_counts()
assert np.array_equal(source.question.map(counts).fillna(0),est.question_support)
assert set(source.uid).isdisjoint(fit_all.uid)

with np.load(cache/"simplekt.npz") as z:
    history_items,skills,answers = z["items"], z["skills"], z["responses"]

grid = np.linspace(-3, 3, 25)
checked = 0
for phase in [-1,0,1,2,3,4]:
    population = original[original.bucket >= 60] if phase == -1 else original[(original.bucket<60) & (original.bucket%5==phase)]
    sample = population.sample(n=50, random_state=51)
    allowed = fit_all if phase == -1 else fit_all[fit_all.bucket%5 != phase]
    assert set(allowed.uid).isdisjoint(sample.uid)
    by_skill = allowed.groupby("skill").y.agg(["size","sum"]).to_dict("index")
    by_question = allowed.groupby("question").y.agg(["size","sum"]).to_dict("index")
    rate = allowed.y.mean()
    def shifted(qid, skill):
        p = by_skill.get(str(skill),{"size":0, "sum":0})
        prior = (p["sum"] + 30*rate)/(p["size"] + 30)
        it = by_question.get(qid,{"size":0, "sum":0})
        level = (it["sum"]+6*prior)/(it["size"]+6)
        return level, expit(grid + np.log(level/(1-level)))
    for idx,row in sample.iterrows():
        posterior = norm.pdf(grid)
        for j,tag in enumerate(skills[idx]):
            if tag == -2: continue
            _, curve = shifted("q"+str(history_items[idx,j]), tag)
            posterior *= curve if answers[idx,j] else 1-curve
        level, curve = shifted(row.question,row.skill)
        estimate = float(np.average(curve,weights=posterior))
        np.testing.assert_allclose([level,estimate],features.loc[idx,["item_probability","rasch"]].astype(float),atol=1e-12,rtol=0)
        checked+=1
print(json.dumps(dict(development_rows=len(est),audited_posterior_updates=checked,overlap_learners=0,
    development_questions=source.question.nunique(),unseen_events=int((est.question_support==0).sum()))))
