# Reproduce the fixed-budget replay

Run from the repository root with Python 3.12.3. The scoring code imports the existing university benchmark in `research_v4_2/diagnostics/course_allocation.py` and checks its 10% outputs against the companion JSON. The replay reads published archives directly. Outputs include cohort counts, score-model comparisons and prefix thresholds. No individual scores, labels or student identifiers are exported.

## Sources

| Input | Source and license | SHA-256 of archive |
|---|---|---|
| University data.csv, semicolon-delimited | [UCI 697, Realinho et al., CC BY 4.0](https://archive.ics.uci.edu/dataset/697/predict+students+dropout+and+academic+success) | `e90e55fd65ec462ae283ebeb2cca409319e3460ed898d8754f62fb35cc83a65d` |
| Mathematics student-mat.csv inside nested student.zip | [UCI 320, Cortez and Silva, CC BY 4.0](https://archive.ics.uci.edu/dataset/320/student+performance) | `82ae9d66437b9808df42e8c89d2bb179c46e9cfbcf06f38abc1d20b3b747e177` |
| fairsearchcore 1.0.4 sdist, Apache 2.0 | [PyPI release](https://pypi.org/project/fairsearchcore/1.0.4/) · [Author test fixtures at pinned revision](https://github.com/fair-search/fairsearchcore-python/blob/a92a3d6a94e8050a1216d7f5d1157d4882d4d584/tests/test_fair.py) | `ca15304579a0c9b3135246a1ad41a23367d963e144269553f6200ad608ac44d6` |

## Download and execute

On a fresh checkout, place the exact archives under the gitignored raw directory. The runner verifies all three hashes and temporarily unpacks the algorithm there. The environment below installs only the scoring, figure and upstream test dependencies.

```bash
python3.12 -m venv /tmp/allocation-venv
source /tmp/allocation-venv/bin/activate
python -m pip install numpy==2.4.4 pandas==3.0.2 scipy==1.17.1 scikit-learn==1.8.0 threadpoolctl==3.6.0 matplotlib==3.10.8 pytest==9.1.1
raw=private_data/raw
mkdir -p "$raw/uci/dropout-697" "$raw/uci/student-performance-2014" "$raw/allocation"
curl -fLsS https://archive.ics.uci.edu/static/public/697/predict+students+dropout+and+academic+success.zip -o "$raw/uci/dropout-697/source.zip"
curl -fLsS https://archive.ics.uci.edu/static/public/320/student+performance.zip -o "$raw/uci/student-performance-2014/student.zip"
curl -fLsS https://files.pythonhosted.org/packages/5a/10/493100010291cc8f69fa8c3c9ff59a29d54f6149ba46c188fa50bee368e6/fairsearchcore-1.0.4.tar.gz -o "$raw/allocation/fairsearchcore-1.0.4.tar.gz"
OPENBLAS_NUM_THREADS=1 python -m research_v4_2.external.allocation.run
python research_v4_2/external/allocation/figure.py
```

## Verify fidelity and output

The 2019 package's memoization key can return a NumPy integer on this stack, which raises a TypeError in Python. A wrapper converts its existing hash value to int for both execution and tests. The study loads the algorithm directly from the verified sdist. Its per-prefix quantile, adjustment search and greedy ranking routines run as distributed. For the upstream test suite on a fresh checkout, run the following after the replay.

```bash
raw=private_data/raw/allocation
tar -xzf "$raw/fairsearchcore-1.0.4.tar.gz" -C "$raw"
git clone https://github.com/fair-search/fairsearchcore-python.git "$raw/upstream"
git -C "$raw/upstream" checkout --detach a92a3d6a94e8050a1216d7f5d1157d4882d4d584
PYTHONPATH="$PWD/$raw/fairsearchcore-1.0.4" python -c 'from research_v4_2.external.allocation.run import enable_python_hash_compatibility; enable_python_hash_compatibility(); import pytest; raise SystemExit(pytest.main(["-q", "private_data/raw/allocation/upstream/tests/test_fair.py"]))'
```

All 19 tests passed. The replay separately checks all 114 empirical ranked lists against their quantiles and independent greedy selection. Two full executions reproduced the following bytes.

| Output | SHA-256 |
|---|---|
| [36 pooled policy results](results.csv) | `c12eca0212c9e39b3a1bda18b27f1a802976adad382a0e1cbb39d4a6fc6f9ebf` |
| [342 within-pool breakdowns](pool_counts.csv) | `ab0810cef4b53425776ff679aa8909786e2553294261d951f784d7cd86267880` |
| [57 prefix tables](thresholds.json) | `6599069987d281690eff32370a4614beac612c4ba3de6c0f3f0a12272e1cc312` |

In both CSVs, k is the number of review places. The female and case-count columns give population denominators, and the seat and capture columns give policy numerators. The quota's prefix violations refer to ordering its selected set by the shared risk ordering. In the threshold file, m lists the minimum protected count at ranks 1 through k. Crossing is the exact probability of violating at least one of those bounds under independent Bernoulli(p) draws.
