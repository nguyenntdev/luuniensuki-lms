# Which citations need review after a museum catalogue changes?

## Abstract

A changed catalogue file can invalidate a checksum while leaving the particular value cited by a reader intact. We measured how many potential single-field citations would receive a review alert at file, record, field-group and single-field granularity in Tate’s published catalogue. Between June and October 2014, 4,285 of 270,420 eligible values changed. A file-level check flagged all 270,420. A record-level check flagged 16,503, of which 12,218 still contained the cited value verbatim. Repeating the comparison on the preceding revision interval produced 37,789 such record-level alerts. These counts quantify the value of retaining the cited column and object identifier for exact-text review.

## Question and design

Rauber and colleagues describe how timestamped queries and versioned data can recover a cited subset of a changing dataset. Their objective is persistent identification. We ask a narrower operational question after the subset has been identified. If an editor cites one catalogue value, how often would checking the containing record or file prompt review when that value is unchanged? Our baselines represent two ordinary checksum or comparison policies. The experiment measures alert volume and does not benchmark the authors’ implementation. [Rauber et al., *Precisely and Persistently Identifying and Citing Arbitrary Subsets of Dynamic Data*](https://doi.org/10.1162/99608f92.be565013)

We compared three successive published versions of Tate’s artwork CSV, aligned by its unique string-valued object ID. The unit is an object–column pair whose older value was nonempty, restricted to title, artist, dateText and medium on IDs present in both versions. Each pair gets equal weight. We compare parsed strings exactly, preserving empty strings. A changed file hash flags every eligible pair. A record rule flags every eligible pair on any record with a difference among its 19 non-ID columns. A more targeted comparator watches the four descriptive columns as a group. Any difference within that group flags all eligible pairs on the object. A field rule flags the pair if its own string changed. Newly added records have no prior citation in this design. [Tate collection and field definitions](https://github.com/tategallery/collection)

## Results

| Revision interval in 2014 | Common IDs | Added / removed IDs | Changed records | File alerts | Record alerts | Changed eligible values | Unchanged values flagged by record rule |
|---|---:|---:|---:|---:|---:|---:|---:|
| June 12 to October 27 | 69,201 | 0 / 0 | 4,243 | 270,420 | 16,503 | 4,285 | 12,218 |
| January 8 to June 12 | 69,075 | 126 / 0 | 10,681 | 269,915 | 42,587 | 4,798 | 37,789 |

In the June–October interval, 25.96% of record-level alerts pointed to a changed cited value. The corresponding share in January–June was 11.27%. Ancillary columns can change on objects whose descriptive text remains stable. For instance, the earlier interval included 3,895 changes to thumbnail copyright strings and 2,893 changes to object URLs. Those counts can overlap on the same object and cannot be added to attribute the excess alerts. Changes to a copyright string are used here only to trigger the record comparator. The separate media-rights audit assesses what a rights declaration covers. [June–October field counts](result.json) · [January–June field counts](january_june.json)

Watching the four descriptive columns as a group produced 11,629 alerts in June–October and 19,061 in January–June. Relative to checking the entire record, this spared 4,874 and 23,526 alerts, respectively. The group rule still flagged 7,344 and 14,263 unchanged values because a neighbouring descriptive field changed. This comparison isolates the cost of grouping even when every monitored column belongs to the citation scope. [June–October group counts](june_october_group.json) · [January–June group counts](january_june_group.json)

## Observed links in English Wikipedia

A frozen MediaWiki external-link query returned 443 rows on 328 distinct pages. The response contained a continuation token, so this is a partial contemporary sampling frame. Of those pages, 266 had a retrievable revision at the June 2014 cutoff. Those revisions yielded 280 distinct page–artwork-path pairs. Exact matching to a unique June catalogue URL retained 185 pairs from 142 pages referring to 181 artworks. The other 95 pairs contribute to the exclusion count. Selecting pages through surviving external links can underrepresent paths that subsequently disappeared. [Frame](references/frame.json) · [Revision IDs](references/revisions.json) · [MediaWiki query semantics](https://www.mediawiki.org/wiki/API:Exturlusage)

Across those 185 pairs the October catalogue preserved every URL path. Record comparison flagged five pairs, three after thumbnail copyright edits and two after dimension edits. The external-link label matched the June title verbatim in 44 pairs. None of those titles changed. An always-silent comparator also made zero path errors on this sample. Sensitivity to genuine path changes and the semantic validity of the citing statements remain unknown. The paths were compared as catalogue strings. The study did not test HTTP redirects. [Edge-level comparisons](references/edges.json) · [Counts](references/results.json)

To replay, run the following from the repository root. The collector requests the historical revision IDs from English Wikipedia. Each revision can be attributed through its permanent history link, for example [revision 612334022](https://en.wikipedia.org/wiki/Special:PermanentLink/612334022). The saved path records contain label hashes. [Wikimedia terms](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use)

```bash
set -eu
paper=research_v4_2/external/catalog_revisions/references
cache=private_data/raw/tate/wiki
out=$(mktemp -d)
python "$paper/benchmark.py" collect --cache "$cache" --out "$out"
cmp "$paper/paths.json" "$out/paths.json"
python "$paper/benchmark.py" evaluate --inputs "$out" --cache "$cache" --out "$out"
cmp "$paper/results.json" "$out/results.json"
cmp "$paper/edges.json" "$out/edges.json"
```

## Interpretation and limits

Exact field matching recovers every exact field change by construction. The empirical finding is the magnitude and variation of the excess review queue under coarser comparisons. An editor who quotes a title may care about punctuation that an editor paraphrasing the same title would ignore. Conversely, a correction to an artist identifier or an attribution role can alter the meaning of an unchanged artist string. A reviewer handling that claim would need to retain those dependencies. The catalogue-wide calculation weights possible citations equally. The Wikipedia follow-up measures a selected distribution of links. Human assessments of significance and measured review times are unavailable. Both intervals share a publisher and a boundary snapshot. They provide a temporal sensitivity check within one archive.

## Reproduction

From the repository root, run the following in Bash with curl, Python 3.12 and pandas 3.0.2. All four diffs should be empty. The JSON includes both input SHA-256 digests, record turnover, per-column changes and policy totals.

```bash
set -euo pipefail
work=$(mktemp -d)
paper=research_v4_2/external/catalog_revisions
base=https://raw.githubusercontent.com/tategallery/collection
curl -fsSL "$base/4498068b7be0dec49d35c30ec5e5e3cd0529ffac/artwork_data.csv" -o "$work/jan.csv"
curl -fsSL "$base/b628039a8759f5f27f3edd542d959859a5882039/artwork_data.csv" -o "$work/jun.csv"
curl -fsSL "$base/e7936a63d954d5b17628c59990531d723d2da010/artwork_data.csv" -o "$work/oct.csv"
python "$paper/evaluate.py" "$work/jun.csv" "$work/oct.csv" | diff - "$paper/result.json"
python "$paper/evaluate.py" "$work/jan.csv" "$work/jun.csv" | diff - "$paper/january_june.json"
python "$paper/field_group.py" "$work/jun.csv" "$work/oct.csv" | diff - "$paper/june_october_group.json"
python "$paper/field_group.py" "$work/jan.csv" "$work/jun.csv" | diff - "$paper/january_june_group.json"
```
