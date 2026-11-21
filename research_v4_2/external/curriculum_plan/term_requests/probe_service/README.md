# Can interval probing resolve more timetable requests within the solver budget?

On 448 requests in 14 even-numbered curricula, interval probing returned a verified answer to every request. A service that narrowed the search to the original prerequisite windows and screened interval capacity answered 447. Both services used one worker and the same per-request CP-SAT budget. On curriculum 18 the probing service found a valid timetable for the request on which both comparison services timed out. The archived high-budget verifier had already established feasibility for that request.

| Policy | CP-SAT calls | Feasible schedules returned | Infeasibilities proved | Unresolved |
|---|---:|---:|---:|---:|
| Prerequisite windows | 260 | 188 | 259 | 1 |
| Windows and interval capacity | 214 | 188 | 259 | 1 |
| Windows, interval capacity and probing | 203 | 189 | 259 | 0 |

Probing proved 11 additional infeasibilities before integer search. It passed its tighter windows to the fallback model. Across curricula its geometric mean service time was 7.33% higher than interval screening and 1.44% higher than windows alone. It was faster than interval screening on three of fourteen curricula. Timings include the probes, model cloning and exact fallback and exclude one-time common template construction and closure preparation. The latter is recorded per curriculum. The study meets the full-resolution criterion on this sample and misses the 10% speed target. The fixtures were previously inspected with other policies. Public CSPLib data supplies the course structures and simulated requests supply the workload. [Design](design.md) · [Per-request schedules and timing samples](results.json) · [Verification and paired timing intervals](verification.json)

## Reproduction

From the repository root use the parent OR-Tools 9.14.6206 environment. Provide a CPU set appropriate for the number of processes. The recorded run pinned fourteen workers to separate CPUs 40–53. Within each curriculum, each request was evaluated in three shuffled complete blocks. Timing varies by execution. The verifier checks each definite decision against the archived independent reference, directly evaluates every returned schedule, and recomputes the timing ratios. Its supplementary intervals resample the 14 curricula, condition on this timing run and use Bonferroni adjustment over the two comparisons.

```sh
set -eu
d=research_v4_2/external/curriculum_plan/term_requests/probe_service
a=private_data/raw/csplib-bacp/bacp.zip
(cd "$d" && sha256sum -c design.sha256)
python "$d/verify_results.py" "$a" "$d/results.json" | diff - "$d/verification.json"
out=$(mktemp)
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 taskset -c 40-53 python "$d/benchmark.py" "$a" "$out"
python "$d/verify_results.py" "$a" "$out"
```
