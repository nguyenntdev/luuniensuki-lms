# Foundations labels and merged paths

All 77 merged PRs in the frozen catalog have a pinned Git merge-result commit. Comparing its tree with its first parent measures the net landed change. Renames count both path endpoints. counts.txt retains counts and a SHA-256 of Git's NUL-delimited path list per PR. merges.tsv pairs each PR with the merge_commit_sha from the original REST extract. SHA256SUMS pins the labels, commit mapping and derived output.

A path under foundations/ agreed with 21 positive labels and all 54 negative labels. Both discrepancies were in the original training partition. PR 31371 updated the labeler configuration and workflow under .github. PR 31411 changed lesson authoring guidance, Markdown linting and templates. Neither landed a Foundations file. Both published positives are retained. The label assignment history is unverified.

At the final pinned PR commit, .github/labeler.yml maps the Foundations label to foundations/**/* and .github/workflows/labeler.yml runs actions/labeler on PR opening. Later edits can change the paths before merge. The workflow documents a direct mechanism for agreement but cannot identify who applied each label.

The original holdout has 13 matching positives and 13 matching negatives. Perfect holdout agreement measures reconstruction of the published label using landed paths. Counting it as a predictive win would reward access to the label-generation input. The title-only predictions and split were kept frozen. This audit covers only merged PRs already carrying a Content label.

From this directory, reproduce with a full-history clone:

```sh
git clone --bare https://github.com/TheOdinProject/curriculum /tmp/odin-curriculum.git
python audit.py /tmp/odin-curriculum.git | diff - counts.txt
sha256sum -c SHA256SUMS
```
