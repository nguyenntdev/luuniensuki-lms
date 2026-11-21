# Exact timetable repair after a simulated Boston rail trip cancellation

On the MBTA timetable for 20 November 2026, exact cached-path invalidation answered batches of 512 origin/time/destination requests in **0.112 ms at p95**. Repairing precomputed destination profiles took **0.154 ms**. Only 80 of 24,576 scenario–request pairs changed their optimal arrival after cancellation. Six became unreachable within the two-hour study horizon. Reusing valid paths was inexpensive under this workload. [Protocol](protocol.md) · [Results](result.json)

The study uses 418 scheduled trips, 4,931 timed ride legs and 124 stations across eight rail routes from 07:00 to 09:00. Each of 48 hypothetical scenarios removes one active trip. The four destination batches repeat across scenarios, giving the exact cache the same advance knowledge of requests as every other algorithm. These controlled deletions measure the response to a specified disruption. Their frequency and distribution in real operations remain unknown. The model permits instantaneous transfers within a parent station and omits walking, platform restrictions, uptake restrictions and real-time delays. The goal is earliest scheduled arrival on this precise projection. This study leaves the original heritage itinerary objective, generalization to other operators, and publication-level superiority open. [MBTA developer information and data terms](https://www.mbta.com/developers) · [GTFS feed archive](https://cdn.mbta.com/archive/archived_feeds.txt) · [Source inventory and projection digest](inventory.json)

| Exact algorithm | One-time solver setup, ms | Batch p95, ms | Batch geometric mean, ms | p95 amortizing setup over 48 updates, ms |
|---|---:|---:|---:|---:|
| Forward connection scan per request | <0.001 | 2.240 | 1.929 | 2.240 |
| Recompute four destination profiles | <0.001 | 0.456 | 0.398 | 0.456 |
| Cached paths with invalidation and forward scan | 2.214 | 0.112 | 0.031 | 0.158 |
| Repair profiles, enqueue every predecessor of a worsened value | 0.331 | 0.174 | 0.117 | 0.180 |
| Repair profiles, enqueue dependent predecessors only | 0.309 | 0.154 | 0.116 | 0.160 |

Forward connection scan reimplements the published timetable scan on the projected segment network. Station labels suffice in this model because each edge is independently boardable. Exact caching preserves a base optimum whenever its witness survives: deleting edges cannot improve an arrival, and the surviving path attains its old arrival. Both reverse-profile methods process event vertices in decreasing time. A vertex with an available optimal successor of unchanged value still attains its previous optimum. Removing the selected ride or worsening its selected successor triggers reevaluation. Equal-valued replacements change the witness without propagating the value. Each updated label is restored before the next cancellation. Dependency-directed maintenance has extensive prior work in dynamic shortest paths. This development result supports no algorithmic priority or all-baseline superiority claim. [Connection Scan Algorithm](https://arxiv.org/abs/1703.05997) · [Ramalingam and Reps, incremental shortest paths](https://doi.org/10.1006/jagm.1996.0046)

The benchmark used single-core C++ implementations on a Xeon E5-2696 v4. Each timed batch includes checking the cancelled trip, solver work, construction of the returned ride lists and restoration of mutable profiles. Common archive ingestion, event graph construction, validation, serialization and result disposal are outside the timer. One-time setup measures each solver's additional state. Method order is shuffled within five repetitions. The p95 is the nearest-rank quantile of the 48 per-scenario median latencies. A JavaScript oracle separately ran station-based time-dependent Dijkstra and checked every finite witness, including temporal order and the absence of the cancelled trip. It verified 122,880 decisions and 1,106,292 returned ride legs across five solvers. 9,462 scenario–query pairs were unreachable in the projected network. Positive leg duration ensures chronological scanning remains exact even for equal departure timestamps. [Raw timings](latency.csv) · [Setup timings](setup.csv) · [Returned journeys](witnesses.txt.gz) · [Independent scorer](verify.mjs)

The candidate gained 11.26% in p95 against the all-predecessor repair but only 1.21% in geometric mean. It lost both endpoints against path caching. Two of four controls passed the dual 10% development margin. The single service day and overlapping requests provide insufficient independent units for a confirmatory estimate. The independent operator and period remain unevaluated. Measurement noise also limits interpretation of the small amortized latency difference between the candidate and caching.

## Reproduction

From the repository root, run the commands below. The script checks the feed checksum before parsing. The data were supplied by the Massachusetts Bay Transportation Authority. The numbered witnesses derive their meaning from the pinned projection. Local execution used Python 3.12, GCC 13 and Node 24.

```bash
set -eu
p=research_v4_2/external/replanning
r=private_data/raw/replanning
out=$(mktemp -d)
mkdir -p "$r"
curl -fsSL https://cdn.mbtace.com/archive/20261112.zip -o "$r/mbta.zip"
python "$p/prepare.py" "$r/mbta.zip" "$out/network" > "$out/inventory.json"
cmp "$p/inventory.json" "$out/inventory.json"
node --check "$p/verify.mjs"
node "$p/verify.mjs" "$out/network" "$p/witnesses.txt.gz" "$p/latency.csv" "$p/setup.csv" "$p/inventory.json" > "$out/result.json"
cmp "$p/result.json" "$out/result.json"
g++ -std=c++17 -O3 -DNDEBUG -Wall -Wextra -Werror "$p/benchmark.cpp" -o "$out/bench"
taskset -c 28 "$out/bench" "$out/network" "$out/latency.csv" "$out/routes" "$out/setup.csv"
gzip -nc "$out/routes" > "$out/routes.gz"
node "$p/verify.mjs" "$out/network" "$out/routes.gz" "$out/latency.csv" "$out/setup.csv" "$p/inventory.json"
```

Fresh timings depend on processor state and contention. The frozen wire and latency tables allow exact verification of the reported results.
