# Checking requested course periods before rescheduling

On 14 development curricula, prerequisite propagation alone identified all 190 infeasible requests among 448 simulated pairs. CP-SAT returned a valid timetable for each of the other 258. Adding both credit and enrollment tests on contiguous periods rejected zero additional requests. All three filters would avoid 42.4% of full solver calls under this workload. The sample includes two equally weighted request generators whose difficulty differed considerably.

| Uniform sampler | Requests | Infeasible by exact solver | Found by prerequisite bounds | Also checking singleton capacities | Also checking all intervals |
|---|---:|---:|---:|---:|---:|
| All course periods | 224 | 182 | 182 | 182 | 182 |
| Each course's original prerequisite window | 224 | 8 | 8 | 8 | 8 |

The source contains 28 CSPLib MiniZinc instances. Each development instance has 50 courses and ten periods. The administrative ceiling of 100 credits is loose compared with the balanced loads the published formulation minimizes. Results here condition on administrative feasibility and two simulated placements. They measure neither minimum peak load nor correction time. Transitive lower and upper bounds are sufficient for the precedence-only subproblem on these directed acyclic graphs. The full model also enforces lower and upper limits on credits and enrollment in every period. Each saved assignment was checked against these limits, both requests and every prerequisite. Course indices in the output are zero-based. Periods are one-based. [Development design](design.md) · [Decisions and witnesses](results.json)

## Reproduction

Use Python 3.12 and OR-Tools 9.14.6206. The runner checks the ZIP digest, scores odd-numbered instances, and uses one solver worker per concurrent request. The original optimization formulation and credits are available from CSPLib. Related scheduling work studies richer curricula and load balance. [Published problem](https://www.csplib.org/Problems/prob030/) · [Pinned benchmark](https://github.com/csplib/csplib/tree/c098b38a1598259aac69348468966db362f93844/Problems/prob030) · [Chiarandini et al., Journal of Heuristics](https://doi.org/10.1007/s10732-011-9158-2)

```sh
set -eu
d=research_v4_2/external/curriculum_plan/term_requests
r=private_data/raw/csplib-bacp/bacp.zip
mkdir -p "$(dirname "$r")"
curl -fsSL https://raw.githubusercontent.com/csplib/csplib/c098b38a1598259aac69348468966db362f93844/Problems/prob030/data/bacp_MiniZinc_Benchmarks.zip -o "$r"
out=$(mktemp)
python "$d/screen.py" "$r" "$out" --workers 4
cmp "$d/results.json" "$out"
```
