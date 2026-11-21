"""Flag all cited fields on a record when any one of those fields changes."""
import json
import sys

import pandas as pd

fields = ["title", "artist", "dateText", "medium"]
older, newer = [
    pd.read_csv(path, usecols=["id", *fields], dtype=str, keep_default_na=False).set_index("id")
    for path in sys.argv[1:]
]
assert older.index.is_unique and newer.index.is_unique
ids = older.index.intersection(newer.index)
cited = older.loc[ids, fields]
changed_group = cited.ne(newer.loc[ids, fields]).any(axis=1)
print(json.dumps({
    "records_with_group_change": int(changed_group.sum()),
    "alerts": int(cited.loc[changed_group].ne("").sum().sum()),
}, indent=2))
