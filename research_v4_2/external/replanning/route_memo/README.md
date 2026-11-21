# Memoizing exact ride suffixes after a timetable cancellation

Memoized ride reconstruction missed the P02 development threshold on both request workloads. The candidate retained the one-word signature solver's exact witnesses and improved some batch latencies before setup. After charging setup across 48 cancellations, its geometric mean was slower than the unmodified signature solver on both workloads in both runs. [Protocol](protocol.md) · [Initial results](result.json) · [Repeat results](repeat/result.json)

The existing signature solver shares repaired arrival labels across all affected requests, but reconstructs each owned witness by following every event edge. The candidate memoizes the first ride of each reconstructed suffix by destination and event for the current cancellation. This collapses waiting chains. After emitting a ride, it resumes from the ride's arrival event. Exactness follows from retaining the repaired event labels and deleting only waiting edges from the emitted sequence. An unmemoized label reached through the selected repair path has a clear signature bit and can use its base ride index. A signature collision still triggers exact label repair. The matched control shares the same base ride index and output allocation heuristic and traverses repaired event edges without memoizing their first rides. Both indexed variants return full, independently owned leg vectors. [Implementation](bench.cpp)

## Development workload and results

Both workloads use the same pinned MBTA timetable, four destinations and 48 cancellations. The original workload had 504 distinct destination–start events across 512 requests. The burst workload uses eight nearby departure times for each of 64 requests, producing 66 distinct destination–start events. Optimal arrival worsened for 80 request–cancellation pairs per workload. Those pairs covered 79 distinct starts summed over cancellations in the original workload and 10 in bursts. Worsened arrival is a lower bound on the count of repairs because a replacement can keep the same arrival time. [Source inventory](../inventory.json) · [Workload generator](workloads.py)

Initial timings use logical CPU 15 on an Intel Xeon E5-2696 v4. Batch statistics summarize the medians of 15 repetitions per cancellation. Setup is the median of seven builds. Amortized columns add setup divided by 48 to each batch median before summarizing. The suite also ran during the initial benchmark with affinity covering CPU 15. The repeat ran after the suite finished.

| Workload | Solver | Setup (ms) | Batch p95 (µs) | Batch geometric mean (µs) | Amortized p95 (µs) | Amortized geometric mean (µs) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Original | Indexed CSA | 0.498 | 92.67 | 24.81 | 103.04 | 36.40 |
| Original | Signature-only | 0.701 | 32.66 | 20.45 | 47.25 | 35.23 |
| Original | Signature with base ride index | 0.855 | 30.21 | 18.99 | 48.02 | 36.98 |
| Original | Memoized rides | 0.880 | 31.42 | 18.45 | 49.75 | 36.97 |
| Bursts | Indexed CSA | 0.439 | 111.18 | 18.62 | 120.32 | 28.71 |
| Bursts | Signature-only | 0.638 | 23.68 | 17.39 | 36.97 | 30.75 |
| Bursts | Signature with base ride index | 0.849 | 21.76 | 15.12 | 39.45 | 32.92 |
| Bursts | Memoized rides | 0.819 | 21.61 | 14.85 | 38.67 | 32.04 |

Against the matched control, the candidate's initial batch p95 was 4.0% slower on the original workload and 0.7% faster on bursts. In the repeat it was 8.7% faster on the original and 0.5% slower on bursts. The repeat also found 19.2% and 26.9% lower batch p95 against the unmodified signature solver, but the amortized geometric mean was 3.2% and 6.5% slower, respectively. No run cleared the required 10% improvement across all four summaries and all controls. The shared base ride index adds 72,864 bytes of integer payload. Memoization adds a further 145,728 bytes of ride heads and epoch tags across 18,216 destination–event states. These figures exclude vector headers and allocator overhead. Neither run opens the reserved network. [Initial original timings](original/latency.csv) · [Initial burst timings](bursts/latency.csv) · [Repeat results](repeat/result.json)

An independent station-based Dijkstra oracle verified 196,608 arrivals and 1,800,063 returned ride legs across the two workloads. All three signature implementations returned identical itineraries, including exact agreement with the archived corridor signature control on the original workload. Every timing repetition matched its method's warmup witness. Both runs produced identical witness archives. Saved artifacts contain benchmark measurements and derived witnesses keyed by leg ID. [Verifier](verify.py) · [Original witnesses](original/witnesses.txt.gz) · [Burst witnesses](bursts/witnesses.txt.gz)

## Reproduction

Generate the pinned projection with the [parent instructions](../README.md). Run from the repository root with Python 3.12 and GCC 13. Verification reads both sets of saved measurements. The repeat deliberately reuses the byte-identical witness archives.

```bash
set -eu
p=research_v4_2/external/replanning/route_memo
net=private_data/raw/replanning/network.txt
export PYTHONDONTWRITEBYTECODE=1
taskset -c 15 python "$p/verify.py" "$net" "$p" | diff - "$p/result.json"
taskset -c 15 python "$p/verify.py" "$net" "$p/repeat" --witness-evidence "$p" | diff - "$p/repeat/result.json"
out=$(mktemp -d)
taskset -c 15 bash "$p/reproduce.sh" "$net" "$out"
for workload in original bursts; do
    cmp "$p/$workload/witnesses.txt.gz" "$out/$workload/witnesses.txt.gz"
done
```
