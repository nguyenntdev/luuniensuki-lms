# P10 simulated target addition

Use every eligible ordered catalog triple in the parent protocol. Each independent episode starts with its first two targets and simulates adding its third. The transcript is empty. Compare an exact cached prefix frontier, full unpruned recomputation and a matched cold run with identical dominance pruning. Count attempted pairwise unions after the edit. Record the cost of building the initial frontier separately. No cache is shared across episodes. A subset dominates its supersets because union with any subsequent choice preserves containment. All three methods must return the same minimum and lexicographic tie break.

The endpoint is computational work after an append, excluding parsing, dominance tests and cache storage. It measures neither wall time nor human edits. These overlapping triples come from two tables in Oliver Nyland's public deposit (Zenodo 23313887). The parent verifier exhaustively checks the published reference minima against the original formulas.

From the repository root run the following with the source archive described in the parent README.

```sh
d=research_v4_2/external/curriculum_plan/incremental
taskset -c 0-15 python3 "$d/study.py"
taskset -c 0-15 python3 "$d/verify.py"
```
