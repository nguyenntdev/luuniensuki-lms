# Station-indexed exact replacement search

The corridor baseline already indexes each base journey by the distinct trips it uses. An intact witness certifies the old optimum because deletion can only remove feasible journeys. This experiment keeps that incidence index and compares station-local departure scans with the global chronological scan for invalidated queries. The candidate settles reachable stations in earliest-arrival order and stops at the destination. Waiting is allowed, so an earlier station label dominates a later one. Each timed call returns owned copies of full journeys. The candidate copies the base batch before replacing invalidated entries, which adds copy work for those entries. No solver learns replacement journeys from earlier timing repetitions.

| Method | Setup ms | Batch p95 µs | Geometric mean µs | Amortized geometric mean µs |
| --- | ---: | ---: | ---: | ---: |
| Indexed chronological scan | 0.485 | 81.23 | 24.45 | 35.57 |
| Single-word signature repair | 0.725 | 34.89 | 19.49 | 34.82 |
| Station-indexed search | 0.546 | 127.92 | 24.92 | 37.95 |

The station index stores 4,931 additional integer leg IDs (19,724 bytes of payload), plus 124 vector headers, spare capacity and a per-query priority queue. Peak memory per solver was not measured. All eleven methods share one benchmark process under a 1 GiB address-space ceiling. Setup includes each method's private index and excludes shared network parsing. Amortization charges setup over 48 distinct cancellation batches. Five shuffled repetitions estimate each batch median on CPU 54. A single setup observation and one development timetable limit timing generalization.

The independent station oracle and journey validator checked 270,336 answers including full itinerary feasibility. The station implementation shares the oracle's algorithmic family and also agrees with chronological scan. The candidate missed the inherited 10% threshold against all controls. The reserved operator was not opened.

Reproduce from the repository root with a separate output directory.

```bash
p=research_v4_2/external/replanning/replacement
taskset -c 54 bash "$p/reproduce.sh" private_data/raw/replanning/network.txt "$(mktemp -d)"
```
