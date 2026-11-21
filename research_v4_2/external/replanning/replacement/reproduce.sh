#!/usr/bin/env bash
set -eu
p=$(cd "$(dirname "$0")" && pwd)
net=${1:?pass development network}
out=${2:?pass output directory}
mkdir -p "$out"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
sed '/^int main(/,$d' "$p/../lazy/lazy.cpp" > "$work/lazy_engine.inc"
sed '/^int main(/,$d' "$p/../corridor/bench.cpp" > "$work/corridor_engine.inc"
ulimit -S -v 1048576
g++ -O3 -DNDEBUG -std=c++17 -I"$work" -I"$p/../lazy" "$p/bench.cpp" -o "$work/bench"
"$work/bench" "$net" "$out/latency.csv" "$work/witnesses" "$out/setup.csv"
ulimit -S -v unlimited 2>/dev/null || true
gzip -nc "$work/witnesses" > "$out/witnesses.txt.gz"
node --max-old-space-size=256 "$p/verify.mjs" "$net" "$out/witnesses.txt.gz" "$out/latency.csv" "$out/setup.csv" "$p/../inventory.json" > "$out/result.json"
