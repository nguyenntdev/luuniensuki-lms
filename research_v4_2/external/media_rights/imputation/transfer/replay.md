# Reproduce the training-only source audit

Run from the repository root with Python 3.12 and Node 24. The two immutable release archives contain the public metadata published by the Minneapolis Institute of Art. Each command uses a single local CPU. Both implementations skip development and reserved object IDs before parsing their documents. They also exclude previewed IDs 1 and 17, invalid JSON or empty files, internal and file ID mismatches, and records filed under an inconsistent bucket directory. The counts describe valid numeric object paths only. The Node reader verifies the original SHA-256 digests and independently recomputes the eligibility and outcome-transition counts. [2024 release](https://github.com/artsmia/collection/tree/e51eafbfab4a59f5d864fd81d5ef899d0fd502e7) · [2026 release](https://github.com/artsmia/collection/tree/790eb625934680f2eeccb262391618d2ca948486)

```bash
set -eu
d=research_v4_2/external/media_rights/imputation/transfer
r=private_data/raw/mia
mkdir -p "$r"
for rev in e51eafbfab4a59f5d864fd81d5ef899d0fd502e7 790eb625934680f2eeccb262391618d2ca948486; do
  curl --retry 2 -fLsS "https://codeload.github.com/artsmia/collection/tar.gz/$rev" -o "$r/$rev.tar.gz"
done
out=$(mktemp)
taskset -c 0 python "$d/feasibility.py" "$r" > "$out"
cmp "$out" "$d/feasibility.json"
taskset -c 0 node --check "$d/verify.mjs"
pending=$(mktemp)
aliases=$(mktemp)
taskset -c 0 python "$d/pending.py" "$r" > "$pending"
cmp "$pending" "$d/pending.json"
UV_THREADPOOL_SIZE=1 taskset -c 0 node --v8-pool-size=1 "$d/verify.mjs" "$r" "$out" "$pending" "$aliases"
cmp "$aliases" "$d/aliases.json"
```
