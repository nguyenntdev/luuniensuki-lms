"""Prepare anonymous covariates and training labels with an order commitment."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from screen import cohort_data


def key_digest(keys):
    return hashlib.sha256('\n'.join(keys).encode()).hexdigest()


def export(raw, folder):
    folder.mkdir(parents=True,exist_ok=True)
    for name in ('oulad','uci697'):
        train, test, cat, num, known, _, _ = cohort_data(name,raw)
        meta = dict(cat=cat,num=num,ordered_keys=key_digest(test.key))
        (folder/f'{name}.json').write_text(json.dumps(meta))
        train[cat+num].assign(y=train.key.map(known).astype(int)).to_csv(folder/f'{name}_train.csv.gz',index=False)
        test[cat+num].to_csv(folder/f'{name}_test.csv.gz',index=False)


if __name__ == '__main__':
    export(Path(sys.argv[1]),Path(sys.argv[2]))
