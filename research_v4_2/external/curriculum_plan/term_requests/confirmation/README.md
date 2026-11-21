# Load-preserving term requests on fourteen reserved curricula

The interval-capacity filter avoided 234 of 448 integer searches. Against the unfiltered solver it reduced mean service time by 17.77% across curricula. Against the solver given precedence-narrowed domains the gain was 0.90%, with a simultaneous interval from −3.91% to +7.55%. The registered 10% speed improvement against every comparator was missed. All six services agreed on 188 feasible and 259 infeasible requests and exhausted the per-query deterministic budget on the same remaining request. The full-service parity requirement therefore also missed. A second encoding with a larger budget subsequently found a feasible timetable for that request on instance 18. This witness is preserved separately from the timed outcomes. [Locked design](design.md) · [Raw timings and witnesses](results.json) · [Verification](verification.json)

| Comparator | Integer solver calls | Relative time saved by the interval service | Simultaneous interval |
|---|---:|---:|---:|
| Unfiltered integer template | 448 | 17.77% | 7.02% to 31.87% |
| Precedence filter | 260 | 7.89% | 1.89% to 17.53% |
| Singleton capacity filter | 219 | 1.88% | −0.15% to 6.49% |
| Interval filter plus cumulative assignment LP | 214 | 42.10% | 29.28% to 53.91% |
| Integer model with narrowed precedence domains | 260 | 0.90% | −3.91% to 7.55% |

The interval service made 214 solver calls. Percentages use the geometric mean of within-instance ratios. Each instance had one fixed CPU core for all six methods and all three repetitions. Fourteen distinct cores ran in parallel. The shared peak certificate and model template were built outside the timer for all services. These requests are simulated, the curricula come from one CSPLib benchmark family, and the recorded time excludes teacher decisions. The LP arm used a floating-point solver. Every declared infeasibility was corroborated by a second integer encoding.

Use the data and OR-Tools installation from the [development study](../README.md). Keep the same OR-Tools version for deterministic budgets. Timing varies with the host. The verifier also rechecks each saved feasible timetable against the source constraints.

```sh
set -eu
d=research_v4_2/external/curriculum_plan/term_requests/confirmation
r=private_data/raw/csplib-bacp/bacp.zip
(cd "$d" && sha256sum -c protocol.sha256)
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python "$d/evaluate.py" "$r" "$(mktemp)" --cores 24,25,26,27,28,29,30,31,32,33,34,35,36,37
python "$d/verify.py" "$r" --workers 4 | diff - "$d/verification.json"
```
