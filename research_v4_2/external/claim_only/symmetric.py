"""Calculate a model-independent accuracy ceiling under claim-only input."""
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

raw = Path(sys.argv[1]).read_bytes()
assert hashlib.sha256(raw).hexdigest() == "b2ff560615bd3337c858bc5b09256d04f39aaa034aaae2351bb2d6345c110f83"
counts = defaultdict(Counter)
for line in raw.splitlines():
    row = json.loads(line)
    counts[row["claim"]][row["label"]] += 1
n = sum(sum(labels.values()) for labels in counts.values())
correct = sum(max(labels.values()) for labels in counts.values())
print(json.dumps(dict(n=n,strings=len(counts),ambiguous_strings=sum(len(labels)>1 for labels in counts.values()),
                      correct_ceiling=correct,accuracy_ceiling=correct/n),indent=2))
