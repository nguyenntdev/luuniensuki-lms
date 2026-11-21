# Forced-path contraction for exact trip-cancellation queries

Removing a scheduled trip can invalidate many event labels even when relatively few passenger routes change. For a fixed destination, every successful journey from an event with exactly one reachable outgoing edge must follow that edge. This development experiment contracted chains of such edges and tested whether bypassing the chain during repair repaid its construction cost. Across the MBTA rail workload, contraction increased p95 batch latency by 17.0% compared with the same algorithm operating on individual events. Only 80 of 24,576 query–cancellation pairs had a later optimal arrival after removing a trip. The external operator and period remain reserved. [Development protocol](protocol.md) · [Timetable and prior routing work](../README.md)

| Solver | Batch p95, µs | Geometric mean, µs | Setup, ms | Amortized geometric mean, µs |
|---|---:|---:|---:|---:|
| Indexed CSA | 71.14 | 24.83 | 0.520 | 36.64 |
| Exact-bitset lazy repair without pruning | 32.71 | 19.56 | 1.058 | 41.85 |
| Exact-bitset lazy repair with pruning | 37.83 | 19.58 | 1.093 | 42.61 |
| One-word trip signature | 29.84 | 18.62 | 0.745 | 34.34 |
| One-word signature plus forced-path contraction | 34.91 | 18.56 | 0.910 | 37.78 |

The matched method without contraction had the lowest p95 and amortized geometric mean. Two techniques account for this comparison. First, a single word represents trips along the unmodified optimal suffix, assigning trip ID modulo 64 to a bit. A clear bit certifies that a suffix survives. A set bit triggers exact repair, including for collisions. Second, the contraction variant precomputes the endpoint of each maximal forced chain and its own trip signature. A possible cancellation in the chain triggers an exact leg scan. An intact chain inherits the optimum of its endpoint. Any trip deleted from the unique feasible chain makes travel from that event impossible. Reconstruction expands the stored original edges so every returned journey includes its full leg sequence. Time strictly increases along all edges, making this recursion finite. [Implementation](bench.cpp)

The measured p95 gain over the earlier pruned solver was 7.7%, and the geometric-mean gain was 5.2%. Both missed the 10% development threshold. Only five of nine comparisons passed all four latency thresholds. Single-run setup costs are included in the amortized figures. The independent station-based oracle verified 245,760 arrivals across ten solvers and 2,214,003 witness legs. Timings are five shuffled executions per method and cancellation on logical CPU 9. Supplemental paired bootstrap bounds resample 48 cancellations, with a simultaneous one-sided 95% adjustment across 36 contrasts. The estimates for p95 depend on a few tail scenarios, and these conditional intervals do not capture setup variation or generalization across operators. [Measured results](result.json) · [Simultaneous bounds](intervals.json)

The relative performance of the compact signature warrants further work on small-memory exact routing. Comparing signature widths, measuring false-positive repair calls, and testing independently sampled query loads within development would identify whether reduced setup and memory offset collision costs. The present timings support neither a general superiority claim nor releasing a reserved operator for confirmation.

## Reproduction

From the repository root, generate the development projection using the [parent instructions](../README.md). GCC may warn about the unused legacy entry point included for unchanged baseline code. Reproduce the exact saved assessment, then time a fresh run into a separate directory.

```bash
set -eu
p=research_v4_2/external/replanning/corridor
net=private_data/raw/replanning/network.txt
taskset -c 9 node --check "$p/verify.mjs"
taskset -c 9 node --check "$p/uncertainty.mjs"
taskset -c 9 node "$p/verify.mjs" "$net" "$p/witnesses.txt.gz" "$p/latency.csv" "$p/setup.csv" "$p/../inventory.json" | diff - "$p/result.json"
taskset -c 9 node "$p/uncertainty.mjs" "$p/latency.csv" "$p/setup.csv" | diff - "$p/intervals.json"
w=$(mktemp -d)
taskset -c 9 bash "$p/reproduce.sh" "$net" "$w"
cmp "$p/witnesses.txt.gz" "$w/witnesses.txt.gz"
```
