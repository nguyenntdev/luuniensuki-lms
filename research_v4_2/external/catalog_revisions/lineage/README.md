# Relocating heading citations across PEP revisions

Across 31 edited Python Enhancement Proposals, 92 old section headings had unique explicit reStructuredText labels. At the later revision 80 had a unique matching label. All three methods recovered all 80. Only one recoverable title changed, and its normalized heading still matched. There is no evidence of a context advantage. The remaining 12 rows lack a unique reference at follow-up. Their predictions are retained and cannot establish accuracy.

The study uses the two pinned python/peps Git commits in evaluate.py and requires an explicit public-domain declaration in both texts. It includes changed single-file PEPs at the same path and recognizes four heading underline characters. Explicit labels immediately preceding headings supply reference identities, independently of heading text. Persistent label reuse is possible. The experiment models a title-derived locator using lowercase ASCII alphanumeric runs joined with hyphens. It does not verify rendered Sphinx fragments or measure explicit-label URL resolution. Candidates are all parsed headings in the destination document. Text matching scores title sequence similarity. Context adds Jaccard overlap of the first 80 body words. Ties resolve to the earliest candidate. Results store zero-based parsed heading indices, including unresolved references. This is a development comparison with no held-out estimate.

From this directory, using Python 3 and Git:

```sh
taskset -c 31-45 git clone https://github.com/python/peps /tmp/peps-lineage-repro
taskset -c 31-45 python evaluate.py /tmp/peps-lineage-repro > /tmp/peps-lineage-results.json
cmp results.json /tmp/peps-lineage-results.json
```
