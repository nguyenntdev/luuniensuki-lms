# Detecting changes in assessment counts across OULAD offerings

The Open University release describes the assessment types, learning resources and online interactions of 22 offerings across seven modules. Of 15 consecutive within-module transitions, two changed the number of exams, tutor-marked assignments or computer-marked assignments. Those transitions were BBB from 2014B to 2014J and DDD from 2013B to 2013J. The assessment table supplied the labels; separate click and resource tables supplied the detector inputs. The source describes the whole resource inventory for each offering, so it is a retrospective comparator. Only activity detectors observe the first 56 days. [OULAD release](https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset) · [Endpoint and operating threshold](protocol.md)

The weekly quiz-interaction detector obtained average precision .500. Tracking the full activity distribution achieved .833 with or without week alignment. The resource inventory ranked both positives first (AP 1.000). With thresholds selected on the six other modules under a 10% false-discovery limit, the inventory detected one positive without a false alert. The weekly quiz detector selected zero transitions. A stable ranking between disjoint learner halves (Spearman .986 for the quiz detector) coexisted with weak recovery of the structural changes. The two halves share assessments and resources.

A total of 25,361 learners contributed early activity. The effective sample for the comparison is seven modules, with positive examples in only two. The reference detects count changes and omits content, skill mappings, weights and changes in instructional quality. A transition can change curriculum while preserving all three counts. This screen provides direct evidence for one structural proxy in P04. Detecting validated curriculum failure strata under shift remains open. [All 120 alerts](run/edges.csv) · [Scores for eight methods](run/result.json) · [Independent source and metric checks](run/verification.json)

## Reproduction

Use the pinned OULAD archive and analysis dependencies from the portfolio. The registration keys remain local; the output contains module-transition scores. [Source and environment](../../README.md#reproducing-the-primary-analyses)

```bash
set -eu
d=research_v4_2/external/curriculum_shift/assessment
r=private_data/raw/oulad/2013-2014/oulad.zip
out=$(mktemp -d)
(cd "$d" && sha256sum -c protocol.sha256)
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python "$d/screen.py" "$r" "$out"
python "$d/verify.py" "$r" "$out" > "$out/verification.json"
diff -r "$out" "$d/run"
```
