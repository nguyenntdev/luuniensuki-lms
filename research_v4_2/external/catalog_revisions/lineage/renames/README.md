# P12 longitudinal PEP heading renames

The development census spans the last first-parent revision before 2016 UTC (exclusive) through the pinned November 2026 endpoint (inclusive). Both hashes are in evaluate.py and results.json. We enumerate every first-parent diff, including merges against their first parent, and every modified same-path numbered PEP reStructuredText file at repository root or under peps/. No random subsampling occurs. Of 5,662 file transitions, 21 heading transitions have a changed literal title, the same unique explicit target immediately above each heading (one blank line), and the public-domain declaration recognized in both versions. The reference uses label continuity as a proxy for identity. Repeated edits to one document can contribute multiple observations. Moves, deletions, missing labels and other heading syntax fall outside this conditional population.

Nineteen cases are hard by the prespecified structural criterion of a changed ASCII-normalized title anchor. Across all 21, exact anchor recovered 2, title similarity 17, body overlap 17, parent/sibling context 16, and their equal-weight sum 19. Removing title, body or context gives 18, 19 and 19 respectively. These development results establish no unique benefit for the full combination.

All parsed destination headings compete. Before scoring, case-folded literal label strings from both heading lists are removed throughout titles and body text, including titles used for neighbors. This conservative masking can erase ordinary words. Title uses sequence similarity, content uses Jaccard overlap of the first 80 body tokens, and context uses title-token Jaccard over the parent and immediate preceding/following siblings. Hierarchy follows underline styles in first-appearance order. Ties favor the earliest heading. Exact match abstains on misses. Each row retains both blobs, indices, label, titles and every prediction.

From this directory with Python 3 and Git:

```sh
taskset -c 31-45 git clone https://github.com/python/peps /tmp/p12-peps
taskset -c 31-45 python evaluate.py /tmp/p12-peps > /tmp/p12-renames.json
taskset -c 31-45 cmp results.json /tmp/p12-renames.json
```
