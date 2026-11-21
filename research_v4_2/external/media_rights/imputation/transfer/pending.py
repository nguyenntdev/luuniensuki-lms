"""Report training-only transitions from an explicit pending museum declaration."""
import argparse
from collections import Counter
import json
from pathlib import Path
from feasibility import NEW, OLD, snapshot

PENDING = {"Copyright Not Evaluated", "Copyright Undetermined"}


def audit(old, new):
    observed_family = Counter(family for label, family, _, _ in old.values()
                              if family and label and label not in PENDING)
    outcome = Counter()
    raw_labels = Counter()
    groups = set()
    support = Counter()
    for oid, (label, family, _, _) in old.items():
        if label not in PENDING:
            continue
        if oid not in new:
            outcome["no_valid_later_record"] += 1
            continue
        later = new[oid][0]
        if not later or later in PENDING:
            outcome["still_pending" if later else "blank"] += 1
            continue
        raw_labels[later] += 1
        outcome["public_domain" if later == "Public Domain" else "other_substantive"] += 1
        groups.add(("family", family) if family else ("object", oid))
        support["available" if observed_family[family] else "unavailable"] += 1
    return dict(outcomes=dict(sorted(outcome.items())), final_declarations=dict(sorted(raw_labels.items())),
                distinct_resolved_groups=len(groups), earlier_sibling_support=dict(support))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    before, _, _ = snapshot(args.raw, OLD)
    after, _, _ = snapshot(args.raw, NEW)
    print(json.dumps(audit(before, after), indent=2, ensure_ascii=False))
