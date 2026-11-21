# Count-preserving assessment revisions

The [Software Carpentry Python lesson release archive](https://api.github.com/repos/swcarpentry/python-novice-inflammation/releases?per_page=100) returned six tagged releases. Four had empty release notes. Tags alone do not identify structural edits, and the archive supplies no matched learner activity by release. To repeat the bounded source check, fetch that JSON and inspect each tag_name and body. This candidate yielded no scored transitions.

For a narrower retrospective screen we used [OULAD](https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset). Within each assessment type we compared the sorted multiset of published weights between consecutive offerings, retaining only edges with equal counts by type. This detects a change in grading structure even if the number of assignments stays fixed. It misses content changes and permutations of the same weights. No grades or learner outcomes enter the label.

One of 13 eligible transitions changed weights, DDD 2014B to 2014J. Using all eight frozen scores from the adjacent assessment study on exactly these edges, the weekly quiz detector ranked it ninth (AP .111). Weekly and pooled full activity and raw clicks each ranked it first. Full-offering resource inventory ranked it second. A single positive module cannot support a general superiority claim. These observations reuse the same learners and scores as the count study and provide no direct test of prerequisite graphs or learner failure strata.

From the repository root reproduce the saved output with the portfolio Python environment:

```bash
d=research_v4_2/external/curriculum_shift/revisions
taskset -c 12-23 python "$d/check.py" private_data/raw/oulad/2013-2014/oulad.zip | diff - "$d/result.txt"
curl -fsSL 'https://api.github.com/repos/swcarpentry/python-novice-inflammation/releases?per_page=100' | python -c 'import json,sys; print([(r["tag_name"], bool(r["body"])) for r in json.load(sys.stdin)])'
```
