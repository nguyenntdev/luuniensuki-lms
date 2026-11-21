# Exact suffix repair for repeated timetable queries

Query-directed repair answered 512 Boston timetable requests in **31.58 μs at p95** across 48 separately simulated trip cancellations. Indexed path caching with a forward rescan took 74.55 μs. Removing the lower-bound check from the same suffix solver raised p95 to 33.64 μs and geometric mean from 18.63 to 18.71 μs. Those differences missed the 10% development criterion. Setup amortized over 48 cancellations also made the candidate slower in geometric mean than indexed caching. Five of seven controls met all four latency margins. The independent station-based oracle checked 196,608 arrivals and 1,770,915 ride legs. [Protocol](protocol.md) · [All timings and gate decisions](result.json) · [Published timetable, network and problem definition](../README.md)

For each of four destinations, reverse dynamic programming selects an optimal base suffix at every station-time vertex. Each vertex stores the union of a successor's trip bitset and its selected edge's trip. A query whose selected path survives a single-trip removal retains the original optimum because deletion cannot lower arrival time. The inverted trip-to-query list identifies all queries requiring repair. The recursive solver returns an unchanged label when the banned trip is absent from its suffix. Otherwise it minimizes over surviving edges in the time-ordered graph and caches each repaired label for the current cancellation. The old successor time is a lower bound on its updated time. Once a feasible surviving suffix attains that bound or better, the solver can skip that branch. Reconstruction follows a mixture of memoized and surviving original edges and copies the entire ride sequence into the response. [C++ implementation](lazy.cpp)

Every solver had advance access to the same requests. The additional indexed CSA control gets the same base routes from the four optimal profiles, the same inverted index and the same output-copy loop. It avoids suffix bitsets and recomputes only invalid routes by connection scan. For this short sequence of disruptions, its setup cost was 0.513 ms against 1.109 ms for the candidate. After allocating setup across updates its geometric mean was 35.57 μs against 42.03 μs. Setup is a single construction measurement per method; per-scenario run times use medians from five randomized execution orders. These are timings on one public schedule under modeled cancellations. The external operator and period remain reserved. [Frozen timing samples](latency.csv) · [Setup measurements](setup.csv) · [Published prior work and scope](../README.md)

## Reproduction

Use the parent instructions to generate the source-checked network. The JavaScript implementation checks the projection hash, optimal time, ride endpoints, temporal order, cancellation exclusion, scenario membership and complete output cardinality. Run the following from the repository root using Bash, Node 24 and GCC 13. The original benchmark is included directly for the five unchanged control implementations. GCC may warn about the renamed original benchmark entry point, which the follow-up harness never invokes.

```bash
set -eu
p=research_v4_2/external/replanning/lazy
n=private_data/raw/replanning/network.txt
w=$(mktemp -d)
node --check "$p/verify.mjs"
node "$p/verify.mjs" "$n" "$p/witnesses.txt.gz" "$p/latency.csv" "$p/setup.csv" "$p/../inventory.json" | diff - "$p/result.json"
g++ -std=c++17 -O3 -DNDEBUG "$p/lazy.cpp" -o "$w/bench"
taskset -c 28 "$w/bench" "$n" "$w/latency.csv" "$w/witnesses" "$w/setup.csv"
gzip -nc "$w/witnesses" > "$w/witnesses.gz"
node "$p/verify.mjs" "$n" "$w/witnesses.gz" "$w/latency.csv" "$w/setup.csv" "$p/../inventory.json"
```
