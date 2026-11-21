"""Compare version-drift alarms at artifact, record, and cited-field granularity."""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd


def compare(old,new):
    frames = []
    hashes = []
    for p in [old,new]:
        hashes.append(hashlib.sha256(p.read_bytes()).hexdigest())
        frame = pd.read_csv(p,dtype=str,keep_default_na=False).set_index("id",verify_integrity=True)
        frames.append(frame)
    a,b = frames
    common = a.index.intersection(b.index)
    assert a.columns.equals(b.columns)
    diff = a.loc[common] != b.loc[common]
    record = diff.any(axis=1)
    scope = ["title","artist","dateText","medium"]
    # Each reference is a potential citation to one documented metadata value.
    # Exclude empty values on the cited (old) version.
    observed = a.loc[common,scope] != ""
    changed = int((diff[scope]&observed).sum().sum())
    return dict(source_sha=hashes,common=len(common),added=len(b.index.difference(common)),
                removed=len(a.index.difference(common)),record_changes=int(record.sum()),
                by_field=diff.sum().astype(int).to_dict(),citation_opportunities=int(observed.sum().sum()),
                changed_citations=changed,alerts_file=int(observed.sum().sum()) if hashes[0]!=hashes[1] else 0,
                alerts_record=int(observed.loc[record].sum().sum()),alerts_field=changed)


if __name__ == "__main__":
    print(json.dumps(compare(Path(sys.argv[1]),Path(sys.argv[2])),indent=2))
