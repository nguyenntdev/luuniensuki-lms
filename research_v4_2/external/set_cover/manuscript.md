# What redundancy removal recovers in weighted alternative-provider planning

**Abstract.** When several activities cover the same requirement, a greedily built plan can retain an expensive activity that later selections render redundant. We measured this failure mode on all ten externally published OR-Library set 4 instances. Reverse deletion reduced the summed cost of greedy witnesses from 5,695 to 5,282. Integer programming certified a sum of optimal costs of 5,100. Redundancy removal closed 413 of the original 595 excess cost units, or 69.4%. Every pruned solution remained feasible, and every one retained a positive optimality gap. On 20 held-out instances under an equal five-second deadline, multicolumn repair saved 6.805% over the pruned starting solution but cost 1.704% more on average than the specialist CFT solver.

## Model

Let each column represent an available provider with positive cost and each row a requirement. A binary matrix specifies the requirements each provider covers. A plan must cover each row at least once. This is a special case of alternative-provider planning with no travel, precedence or time windows. Its advantage as a diagnostic is that feasibility and objective value can be checked directly from an externally supplied matrix.

The greedy baseline repeatedly maximizes newly covered rows per unit cost. This is Chvátal's established weighted set-cover rule. After the last row is covered, we visit selected columns in reverse insertion order and remove any column whose removal preserves coverage. Each deletion maintains feasibility by construction. Positive costs ensure that deletion lowers the objective. This argument gives no guarantee that the remaining cover is minimum cost. [Chvátal's algorithm](https://doi.org/10.1287/moor.4.3.233)

## External evaluation

We evaluated scp41 through scp410 without selecting instances by outcome. Each has 200 rows and 1,000 columns. A binary integer program minimized column cost subject to the same row constraints using SciPy's HiGHS interface. We retained the incumbent, dual bound and selected column IDs. The verifier checked every witness against the original matrix. On every instance the solver certified optimality. [OR-Library dataset](https://people.brunel.ac.uk/~mastjjb/jeb/orlib/scpinfo.html)

| Instance | Greedy | After deletion | Optimum |
|---|---:|---:|---:|
| scp41 | 463 | 434 | 429 |
| scp42 | 582 | 529 | 512 |
| scp43 | 598 | 537 | 516 |
| scp44 | 548 | 506 | 494 |
| scp45 | 577 | 518 | 512 |
| scp46 | 615 | 594 | 560 |
| scp47 | 476 | 447 | 430 |
| scp48 | 533 | 525 | 492 |
| scp49 | 747 | 664 | 641 |
| scp410 | 556 | 528 | 514 |

## Comparator and budget sensitivity

A [follow-up on 45 OR-Library instances across seven families](multifamily/README.md) tested a one-column drop-and-repair search against Zhu’s published SetCoverPy implementation. The repair improved the pruned greedy solution 41 times and tied four times. Against the median of three seeded comparator runs, repair won on 23 instances under the short budget and eight under the extended budget. The latter profile was added after observing the short runs. Different CPU costs and frequent iteration-limit warnings make these counts budget-specific. Integer feasibility checks cover 540 witnesses, and eleven instances have matching upper and lower bounds. [Verified certificates and instance results](multifamily/instances.csv)

## Held-out comparison at a common CPU deadline

We reserved 20 instances from four additional OR-Library families (NRE through NRH, five per family). Each solver received the same feasible starting cover and five seconds of single-thread process CPU time to report a cheaper feasible solution. The candidate drops and repairs multiple columns. A same-code ablation drops exactly one. For randomized solvers we used the median across seeds 11, 29 and 47 on each instance. Savings are measured relative to each comparator’s cost on that instance and then averaged over the 20 instances. A positive value favors the candidate. [Protocol](equal_budget/protocol.md) · [Implementations and timing](equal_budget/README.md)

| Comparator | Mean saving | 95% stratified bootstrap interval | Wins / ties / losses | Holm-adjusted one-sided p |
|---|---:|---:|---:|---:|
| Pruned greedy warm start | 6.805% | [5.626%, 8.020%] | 20 / 0 / 0 | 0.000006 |
| Deterministic one-column exchange | 3.850% | [2.817%, 4.880%] | 16 / 4 / 0 | 0.000046 |
| Randomized one-column ablation | 0.957% | [0.473%, 1.447%] | 9 / 10 / 1 | 0.007813 |
| Caprara–Fischetti–Toth (CFT) | −1.704% | [−2.584%, −0.763%] | 2 / 8 / 10 | 0.996582 |
| SetCoverPy | 6.805% | [5.626%, 8.020%] | 20 / 0 / 0 | 0.000006 |
| HiGHS | 6.805% | [5.626%, 8.020%] | 20 / 0 / 0 | 0.000006 |

CFT delivered lower median cost on ten instances and higher cost on two. Its advantage in mean relative cost held in each family. The one-column ablation also prevented an all-baseline win because the observed 0.957% saving fell below the prespecified 1% margin. SetCoverPy and HiGHS matched the starting cost at the median on all 20 instances. Their results characterize this incumbent-reporting deadline and implementation. Solver calls could return late, and only incumbents observed by the deadline received credit. Independent row-wise replay verified all 340 saved covers, costs and incumbent timestamps. Four of six comparisons passed the prespecified rule. [All six comparisons and per-instance medians](equal_budget/summary.json) · [Independent verifier](equal_budget/verify.mjs)

## Interpretation

A planner that returns only a valid cover can conceal two costs: retaining redundant choices and making earlier choices that deletion cannot repair. The certified comparator quantifies the second component. For example, scp43 moved from 598 to 537 but still exceeded its optimum by 21. Across the family, treating a pruned witness as optimal would hide 182 cost units. These descriptive sums concern one benchmark family. They establish neither runtime superiority nor the prevalence of redundant activities in a real curriculum. The contribution is a reproducible decomposition of excess cost with witnesses for each term.

[Protocol](protocol.md) · [Evaluator](evaluate.py) · [Witnesses and bounds](result.json)
