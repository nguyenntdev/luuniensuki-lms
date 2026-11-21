"""Re-score the archived P01 policies at their observed review capacity."""
import argparse
import json
from pathlib import Path

import pandas as pd


def evaluate(root):
    results = {}
    for split in ["G","T"]:
        path = root / split
        dfs = [pd.read_json(path/f,lines=True).set_index("case_id").sort_index() for f in
               ["sealed_gold.jsonl","predictions_proposed_rc_stg.jsonl","predictions_C1_regularized_logistic.jsonl"]]
        gold, gate, base = dfs
        assert gold.index.is_unique and gold.index.equals(gate.index) and gold.index.equals(base.index)
        eligible = gate.decision != "ABSTAIN"
        # Deterministic ties by sorted case ID. Evaluation uses aggregate budgets only.
        course = gold.index.str.split("-").str[1]
        order = base.sort_values("score",ascending=False,kind="stable")
        top = order.index[:eligible.sum()]
        stratified = []
        for group in sorted(set(course)):
            ids = gold.index[course==group]
            n = int(eligible.loc[ids].sum())
            stratified.extend(order.index[order.index.isin(ids)][:n])
        runs = {"gate":gate.loc[eligible],"full_logit":base,"same_cases_logit":base.loc[eligible],
                "global_confidence":base.loc[top],"course_confidence":base.loc[stratified]}
        metrics = {}
        for name, table in runs.items():
            correct = table.decision == gold.loc[table.index,"label"]
            metrics[name] = dict(accepted=len(table),correct=int(correct.sum()),accuracy=correct.mean())
        results[split] = dict(total=len(gold), coverage=eligible.mean(),policies=metrics,
                              disagreements_on_accepted=int((gate.loc[eligible,"decision"]!=base.loc[eligible,"decision"]).sum()))
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root",type=Path)
    print(json.dumps(evaluate(parser.parse_args().root),indent=2))
