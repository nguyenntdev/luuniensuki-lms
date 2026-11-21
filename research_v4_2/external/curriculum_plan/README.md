# Can alternative prerequisites reduce the number of direct course additions?

A three-course bundle can allow two courses to share a prerequisite. Choosing the cheapest repair for each course separately can miss that option. We evaluated every eligible triple in Oliver Nyland's two public catalog tables, using the released Boolean conditions verbatim to check eligibility. Nyland's dissertation deposit already represents nested prerequisites; the empirical question here concerns the size of the shared repair. Exhaustive evaluation certifies the minimum on these tables. [Versioned data and author](https://doi.org/10.5281/zenodo.23313887) · [CC BY 4.0 terms](https://creativecommons.org/licenses/by/4.0/) · [Study design](protocol.md)

| Table | Eligible bundles | Independent repairs, mean additions | Sequential overlap rule | Exact joint repair | Bundles improved over independent |
|---|---:|---:|---:|---:|---:|
| Computing | 1,367 | 3.509 | 3.458 | 3.399 | 150 |
| Mathematics | 547 | 3.786 | 3.786 | 3.786 | 0 |

The exact algorithm carries forward alternative sets of course additions and drops a set when a proper subset already satisfies the same processed targets. Subsequent unions preserve containment, so pruning preserves the optimum. Keeping all sets returns the same minimum on all 1,914 triples. The mean reduction fell below the one-course development margin on both tables. The verifier uses an independent postfix evaluator and tests every smaller subset for infeasibility. [All repairs](run/repairs.csv) · [Summary](run/result.json) · [Verification](run/verification.json)

The 58 source rows contain 41 eligible Boolean course rules. Nine empty rules and eight rules containing placement or credit conditions were excluded. Their target names are recorded in the summary. The transcript is empty by design. The reference includes direct prerequisites of the target courses. Study planning with recursive requirements, completed courses, semester offerings, or credit prerequisites changes the optimization problem. There were no recorded teacher edits or editing times, so the result addresses only the direct-repair component of P10. The overlapping bundles do not provide 1,914 independent curricula.

## Reproduction

From the repository root, use Python 3.12. Keep the source ZIP under the ignored data directory. The evaluator verifies its SHA-256 before reading the tables.

```bash
set -eu
d=research_v4_2/external/curriculum_plan
r=private_data/raw/otago-prereqs
mkdir -p "$r"
curl -fLsS --retry 3 'https://zenodo.org/api/records/23313887/files/olivergn/comp490-course-prereqs-v1.0.0.zip/content' -o "$r/release.zip"
(cd "$d" && sha256sum -c protocol.sha256)
out=$(mktemp -d)
python "$d/screen.py" "$r/release.zip" "$out"
python "$d/verify.py" "$r/release.zip" "$out" > "$out/verification.json"
diff -r "$out" "$d/run"
```
