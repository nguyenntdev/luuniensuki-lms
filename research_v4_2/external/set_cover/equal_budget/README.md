# Weighted set cover under a five-second incumbent deadline

The [protocol](protocol.md) defines the 20 previously unused instance IDs, six controls, three seed values and all-comparators decision rule. Its local checksum was recorded before test runs. The native implementation and Python driver were hashed after a smoke run on the earlier development instance scp41 and before launching the held-out comparisons. This is a local freeze without an external registration timestamp. [Frozen hashes](protocol.sha256)

## Methods

For each instance all runs start with the same reverse-deletion greedy witness. The adaptive candidate destroys between one and one third of the current columns, in random order. Repair visits uncovered rows in a shuffled order. It takes the incident column with largest gain per cost after multiplying by a uniform factor in [0.85, 1.15]. A pass through the most expensive selected columns first deletes redundancies. Cheaper and equally costly moves are accepted. A more expensive move of at most one mean selected-column cost is accepted with probability 0.1. Each iteration restarts from the best witness with probability 0.05. The one-column control runs the identical compiled search with destruction size fixed at one. The exchange comparator separately runs the earlier deterministic best one-column drop and global greedy refill. It can return the best explicitly feasible trial evaluated before the deadline.

The CFT implementation uses its default search with the common warm start. The build adapter records witnesses during the three-phase routine and maps them back across both levels of column fixing. It adds a CPU deadline check at the outer refinement boundary. It compiles observer headers outside the source checkout. The driver supplies SetCoverPy's original default iteration limits and counts each completed feasible greedy incumbent. In its dense constructor the driver removes columns covering zero rows. This preparation is timed. HiGHS receives the binary covering formulation, the warm solution, one thread, a seed and its default presolve and search. Its improving MIP solution callback supplies eligible incumbents. Each public solver starts with the same fallback warm objective even if it does not immediately return an improved witness. [CFT source](https://github.com/c4v4/cft/tree/6cb63d0036223b8be9c4d01f95b296d641209f95) · [SetCoverPy source](https://github.com/guangtunbenzhu/SetCoverPy/tree/a1ff3c5cec45cc1b16541999a4adb593fa652363)

Each worker is pinned to one logical CPU. Matrix parsing, library import and construction of the identical warm cover precede timing. Method-specific preparation, model construction, search and in-process instrumentation consume the five-second process-CPU allowance. Methods can return earlier through convergence. A native solver call or uninterruptible optimization phase can return control late. The timestamp filter rejects late incumbents and records both the time of the last accepted improvement and the CPU time observed when control returned. Consequently the comparison is about the cost of a witness available by a common deadline. The actual CPU consumed can exceed it. Solver settings were frozen before test evaluation and the historical shorter iteration profiles remain in the original multifamily study.

## Replay

The recorded machine used Python 3.12.3, NumPy 2.4.4, SciPy 1.17.1, highspy 1.12.0, GCC 13.3.0 and Node 24.22.3 on an Intel Xeon E5-2696 v4. Run from repository root. The matrices are held in the ignored external data directory. The Bash commands below download the original Brunel text files and verify the archived SHA-256 values. [Publisher's catalog and file layout](https://people.brunel.ac.uk/~mastjjb/jeb/orlib/scpinfo.html)

```bash
study=research_v4_2/external/set_cover/equal_budget
data=private_data/raw/orlib/equal_budget
work=$(mktemp -d)
mkdir -p "$data/instances"
for family in e f g h; do
  for i in 1 2 3 4 5; do
    name="scpnr${family}${i}.txt"
    curl -fsSL --retry 3 "https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/$name" -o "$data/instances/$name"
  done
done
sha256sum -c "$study/matrices.sha256"
(cd "$study" && sha256sum -c protocol.sha256)

git clone https://github.com/c4v4/cft "$work/cft"
git -C "$work/cft" checkout 6cb63d0036223b8be9c4d01f95b296d641209f95
git clone https://github.com/fmtlib/fmt "$work/fmt"
git -C "$work/fmt" checkout 40626af88bd7df9a5fb80be7b25ac85b122d6c21
git clone https://github.com/guangtunbenzhu/SetCoverPy "$work/zhu"
git -C "$work/zhu" checkout a1ff3c5cec45cc1b16541999a4adb593fa652363
python3.12 -m venv "$work/env"
"$work/env/bin/pip" install numpy==2.4.4 scipy==1.17.1 highspy==1.12.0
"$work/env/bin/python" "$study/build.py" "$work/cft" "$work/fmt" "$work/build"
"$work/env/bin/python" "$study/challenge.py" "$data/instances" "$work/build/solve" "$work/zhu" "$work/runs" --jobs 10
node "$study/verify.mjs" "$data/instances" "$work/runs" "$work/replay-summary.json"
```

For deterministic verification without any solver installation, use the same downloaded matrices and run the following. The independent Node parser evaluates every selected column against the original row lists. It also recomputes the statistics from the seed-level costs. Fresh time-limited solver runs can differ with machine speed or contention.

```bash
node "$study/verify.mjs" "$data/instances" "$study/run" "$work/verified.json"
cmp "$study/summary.json" "$work/verified.json"
```
