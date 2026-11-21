# Recombining CFT incumbents on weighted set cover

On 20 previously evaluated OR-Library matrices, the CFT-pool solver produced the same median cost as five-second CFT on 11 matrices and a higher cost on nine. Its mean cost was 1.086% higher when each matrix's difference was divided by its CFT comparator cost and the 20 ratios were averaged. This development result does not support a superiority claim. [Protocol](protocol.md) · [Audited results by matrix and seed](summary.json)

| Comparator | Lower / equal / higher candidate cost across 20 instance medians | Mean relative saving | Lower / equal / higher across 60 paired seeds |
| --- | --- | ---: | --- |
| Five-second CFT | 0 / 11 / 9 | −1.086% | 1 / 34 / 25 |
| Best two-second prefix witness | 1 / 19 / 0 | +0.028% | 3 / 57 / 0 |
| Same-size random pool plus incumbent, then HiGHS | 1 / 19 / 0 | +0.028% | 3 / 56 / 1 |
| All columns plus incumbent, then HiGHS | 1 / 19 / 0 | +0.028% | 3 / 57 / 0 |

All three prefix improvements came from scpnrg1. The median prefix cost was 179, the recombined cost was 178, and continued CFT achieved 176. On seed 29 alone, recombination reached 176 against 177 for continued CFT. Across the 60 runs, the prefix produced one to nine distinct observed CFT witnesses and the restricted models contained 14 to 173 columns. HiGHS reported optimality within the deadline for 35 of the 60 candidate models. These are optima within their particular column pools.

## Timing and verification

Each branch receives the same measured CFT prefix, including native construction, search and the Python work of launching the subprocess, checking its output and selecting witnesses. The native runner tests the cutoff at outer-refinement boundaries. An inner phase can continue after the two-second witness cutoff. The recorded prefix time exceeded the entire five-second allowance twice, so those branches retained the prefix incumbent. HiGHS can also return control after the deadline. The maximum observed return was 6.72 CPU seconds for the candidate, 9.56 for the CFT comparator, and 45.19 for the unrestricted HiGHS control. Costs measure eligible incumbents at the deadline. The experiment does not establish a hard five-second return guarantee.

The independent JavaScript verifier read the archived matrix hashes and the original OR-Library row lists. It checked 515 witness records for row coverage, unique valid column indices and integer cost. These comprised 20 warm covers, 110 baseline updates, 205 prefix observations and 180 final branch witnesses. It also reconstructed the elite pool, checked random-control pool size and incumbent inclusion, checked the timing fields and recomputed the paired summaries. Optimality counts use HiGHS's reported termination status. All experiments used previously seen matrices. No external registration or generalization test was performed.

## Replay

Run the following commands from the repository root. Use the matrices, pinned CFT/fmt checkouts and Python environment from the [equal-budget replay instructions](../equal_budget/README.md). Choose an empty output directory for a fresh run. The recorded environment used Python 3.12.3, highspy 1.12.0, NumPy 2.4.4, SciPy 1.17.1, GCC 13.3.0 and Node 24.22.3 on a Xeon E5-2696 v4. The build recreates the existing CFT comparator unchanged and compiles a second observer that retains three-phase local incumbents.

```bash
study=research_v4_2/external/set_cover/cft_pool
data=private_data/raw/orlib/equal_budget
work=$(mktemp -d)
(cd "$study" && sha256sum -c protocol.sha256 && sha256sum -c evidence.sha256)
python "$study/build.py" "$data/cft" "$data/fmt" "$work/build"
python "$study/run.py" "$data/instances" "$work/build" "$work/runs" --jobs 16
node "$study/verify.mjs" "$data/instances" "$work/runs" "$work/replay.json"
```

To audit the saved measurements without installing either solver, run the commands below. The final comparison must reproduce the archived summary byte-for-byte. Fresh time-limited runs can vary with machine speed and contention.

```bash
node "$study/verify.mjs" "$data/instances" "$study/run" "$work/audit.json"
cmp "$study/summary.json" "$work/audit.json"
```
