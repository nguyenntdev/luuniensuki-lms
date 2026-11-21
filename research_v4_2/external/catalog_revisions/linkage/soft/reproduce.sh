#!/usr/bin/env bash
# Run from the repository root with JDK 17 (javac and java) on PATH.
set -euo pipefail
study=research_v4_2/external/catalog_revisions/linkage
raw=private_data/raw/ditto-bibliography
source_id=44d67bb2c8af8e03c963717ce4c799ab051583ca
work=${1:?supply an empty temporary working directory}
mkdir -p "$work/classes" "$raw/tools"
sha256sum -c "$study/inputs.sha256"
if [[ ! -f "$raw/tools/secondstring.tar.gz" ]]; then
  curl -fsSL --retry 3 "https://codeload.github.com/TeamCohen/secondstring/tar.gz/$source_id" -o "$raw/tools/secondstring.tar.gz"
fi
echo "d861006d1073d22597f024e9bdf9df926d23508427501bf26fe93a345f1faf93  $raw/tools/secondstring.tar.gz" | sha256sum -c -
tar -xzf "$raw/tools/secondstring.tar.gz" -C "$work"
src="$work/secondstring-$source_id"
cp_lib="$src/lib/log4j-1.2.8.jar"
node "$study/features.mjs" "$raw" "$work"
OPENBLAS_NUM_THREADS=1 python "$study/soft/extract.py" "$raw" "$work"
javac -d "$work/classes" -sourcepath "$src/src" -cp "$cp_lib" "$study/soft/PublishedMatcher.java"
for d in DBLP-ACM DBLP-GoogleScholar; do
  java -Xmx768m -cp "$work/classes:$cp_lib" PublishedMatcher "$work/$d-second.tsv" "$work/$d-published.csv"
done
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=3 python "$study/soft/evaluate.py" "$work" "$work/run"
node "$study/soft/verify.mjs" "$raw" "$work/run"
diff -r "$study/soft/run" "$work/run"
