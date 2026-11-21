#!/usr/bin/env bash
set -euo pipefail
p=$(cd "$(dirname "$0")" && pwd)
net=${1:?pass the pinned MBTA development projection}
out=${2:?pass a fresh output directory}
mkdir -p "$out"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
export PYTHONDONTWRITEBYTECODE=1
python "$p/workloads.py" "$net" "$work"
# Reuse the engines without including their standalone benchmark entry points.
sed '/^int main(/,$d' "$p/../benchmark.cpp" > "$work/base_engine.inc"
sed -e '/^int main(/,$d' -e '/^#define main /d' -e '/^#undef main/d' \
    -e 's|^#include "../benchmark.cpp"$|#include "base_engine.inc"|' \
    "$p/../lazy/lazy.cpp" > "$work/lazy_engine.inc"
sed '/^int main(/,$d' "$p/../corridor/bench.cpp" > "$work/corridor_engine.inc"
g++ -O3 -DNDEBUG -std=c++17 -Wall -Wextra -Werror -I"$work" "$p/bench.cpp" -o "$work/bench"
for workload in original bursts; do
    mkdir -p "$out/$workload"
    "$work/bench" "$work/$workload.network" "$out/$workload/latency.csv" "$work/witnesses" "$out/$workload/setup.csv"
    gzip -nc "$work/witnesses" > "$out/$workload/witnesses.txt.gz"
done
python "$p/verify.py" "$net" "$out" > "$out/result.json"
