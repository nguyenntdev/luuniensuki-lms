# When an accessibility checker returns “passed” on an inapplicable example

## Abstract

Can an automated accessibility checker detect every labeled failure in a benchmark and still give a misleading impression of what it checked? We ran axe-core 4.11.0 on published Accessibility Conformance Testing (ACT) examples for five rules. It flagged all 30 expected failures and passed all 35 expected passes. Of 18 examples labeled inapplicable, 11 received the same label, three passed, one required review, and three fell outside the HTML harness. A separate comparison of published axe-core and Siteimprove Alfa reports on 85 shared testcase IDs found that both flagged the same 30 expected failures, yet their exact outcome labels differed on 13 cases. For learning-platform audits, preserving applicability and manual-review states tells maintainers more than reporting violation recall alone.

## Question and design

ACT authors supply examples of elements that satisfy a rule, violate it, or fall outside its scope. We asked how often an implementation reproduced those three labels at the **example** level. This exact-label measure is intentionally stricter than ACT implementation consistency. For example, the ACT mapping guidance permits a checker to return a pass on an inapplicable example when its procedure has broader scope. [ACT implementation mapping guidance](https://github.com/act-rules/act-rules.github.io/blob/50d2bede1ee705be6840d06f356a6ae2fd94cb2c/pages/implementations/mapping.md)

The local evaluation covered every numbered passed, failed and inapplicable example in five selected rule files. For each example with one HTML block, the harness opened a fresh Chrome page, served the markup and available local assets, and ran exactly the axe procedures declaring that ACT ID. It reduced their document-wide findings in this order of precedence: violation, incomplete, pass, inapplicable. It retained examples outside the HTML parser's scope as unexecuted. We counted matches among executed examples and separately among all enumerated examples. [Pinned ACT source](https://github.com/act-rules/act-rules.github.io/tree/50d2bede1ee705be6840d06f356a6ae2fd94cb2c/_rules) · [Deque axe-core 4.11.0](https://github.com/dequelabs/axe-core/tree/v4.11.0) · [Local harness](evaluate.cjs)

## Local results

| ACT rule | Enumerated | Executed | Exact matches | Labeled failures flagged |
|---|---:|---:|---:|---:|
| Image accessible name (23a2a8) | 17 | 17 | 17 | 5/5 |
| Button accessible name (97a4e1) | 17 | 17 | 15 | 5/5 |
| Form field accessible name (e086e5) | 21 | 21 | 20 | 9/9 |
| ARIA state or property value (6a7281) | 21 | 20 | 19 | 7/7 |
| HTML page language (b5c3f8) | 7 | 5 | 5 | 4/4 |
| **Total** | **83** | **80** | **76** | **30/30** |

Exact agreement was 76/80 (95.0%) among executed fixtures. With skipped examples retained in the denominator, 76/83 (91.6%) had a demonstrated match. All four executed discrepancies arose on expected-inapplicable cases. A button with link semantics, a disabled button with presentational semantics, and a disabled select with presentational semantics yielded passes. An empty-valued ARIA live-region attribute yielded an incomplete result. XML and SVG fixtures account for all three skips. The language rule therefore has no executed inapplicable control in this run. A dashboard counting only flagged violations would conceal all seven distinctions. [Case-level outputs](result.json)

## Published comparator on shared examples

We independently compared the published reports for axe-core 4.14.1 and fully automated Siteimprove Alfa 0.118.0. Both reports provide procedure outcomes and expected labels for exactly the same 85 rule/testcase ID pairs across the five rules. We verified the identities and expected labels before pairing. For each implementation we reduced mapped procedure outcomes in the same priority order, treating the report's `cantTell` as a review state. Both reports classify each of these five rule mappings as complete under their implementation reporting criteria. [W3C axe-core report](https://github.com/w3c/wcag-act-rules/blob/4ce3d61b6f7b04cbf2df0082a3446e97248b9124/_data/wcag-act-rules/implementations/axe-core.json) · [W3C Alfa report](https://github.com/w3c/wcag-act-rules/blob/4ce3d61b6f7b04cbf2df0082a3446e97248b9124/_data/wcag-act-rules/implementations/alfa.json)

| Published examples | Cases | axe-core exact | Alfa exact |
|---|---:|---:|---:|
| Image accessible name | 18 | 18 | 14 |
| Button accessible name | 17 | 13 | 17 |
| Form field accessible name | 22 | 20 | 22 |
| ARIA state or property value | 21 | 20 | 20 |
| HTML page language | 7 | 7 | 6 |
| **Total** | **85** | **78** | **79** |

The one-case difference in aggregate masks variation by rule. Only axe-core matched four image examples where Alfa reported inapplicable on an expected pass. Only Alfa matched four button cases and two form-field cases. Across all five rules, both matched 72 cases, only axe-core matched six and only Alfa matched seven. All 30 expected failures matched in both reports. The published comparison has one additional image example and one additional form-field example relative to the local corpus. The reports come from different tool releases and reporting dates. These conditions permit a paired descriptive comparison within the reports and preclude attributing local-to-published differences to software upgrades. [Paired rows](published_comparison.csv)

## Does the result transfer beyond the five selected rules?

The W3C archive also permits a paired test across four publicly documented engines. We selected axe-core, Alfa, IBM Equal Access and QualWeb, retained approved ACT rules and approved examples, and joined every example present in at least one of those four implementation reports. The union contains 527 examples for 35 rules. The intersection where every tool reported an outcome other than untested contains 455 examples for 31 rules. A request for manual inspection counts as an exercised procedure with no exact match to the expected label. An absent result contributes zero detected failures in the union. The numbers below come from the pinned publisher reports. We did not execute these four versions on live websites. [W3C source reports](https://github.com/w3c/wcag-act-rules/tree/4ce3d61b6f7b04cbf2df0082a3446e97248b9124/_data/wcag-act-rules/implementations)

| Tool | Exercised in union | Exact in union / 527 | True failure flags / 170 | Other failure flags | Exact on shared / 455 | Shared failures flagged / 150 |
|---|---:|---:|---:|---:|---:|---:|
| axe-core | 501 | 412 | 150 | 1 | 374 | 140 |
| Alfa | 527 | 494 | 162 | 8 | 437 | 148 |
| IBM Equal Access | 467 | 282 | 130 | 6 | 274 | 130 |
| QualWeb | 496 | 473 | 161 | 0 | 439 | 149 |

**The denominator reverses the order of the two leading tools.** Alfa had 21 more exact outcomes than QualWeb across the union. QualWeb had two more on the shared cases. The same reversal occurs for expected failures, with Alfa detecting one more in the union and QualWeb one more in the intersection. Thus a comparison restricted to fixtures both tools exercise can give a different answer from an operator's question about coverage of a fixed inventory. Both numbers matter, especially given the small differences on the matched cases.

Combining Alfa and QualWeb with an “either flags” rule detects 164 of 170 expected failures in the union and raises eight other alerts. Relative to QualWeb alone this adds three true flags and eight other flags. On their common four-tool denominator the combined policy detects exactly the same 149 failures as QualWeb while adding seven other flags. This distinguishes gains due to broader test coverage from gains available when both engines already have an outcome. The labels describe example-level ACT expectations, and the union excludes fixtures missing from all four reports. [Four-tool evaluator](rule_coverage.py) · [All denominators and six engine pairs](rule_coverage.json)

## Interpretation, limitations and fit

A team auditing a heritage learning object can use these fixtures to test whether its reporting layer distinguishes a detected failure, a pass, a target outside a rule's scope, and a check needing review. An image can have a nonempty name while that name fails to convey the historical information a learner needs. The fixture result answers the structural question only. Evaluating description quality requires material selected for that purpose and judgments about meaning in context. [ACT image rule and accessibility requirements](https://github.com/act-rules/act-rules.github.io/blob/50d2bede1ee705be6840d06f356a6ae2fd94cb2c/_rules/image-non-empty-accessible-name-23a2a8.md)

The five rules were selected and the authored examples cluster within rules. They have no sampling design for estimating defect prevalence or accuracy across sites. The local experiment used one browser and a page-level reduction that discards element-level explanations. The comparator reanalyses published tool outputs, with no independent Alfa execution. No learner tasks, assistive-technology sessions, heritage pages, or semantic judgments entered the dataset. The evidence fits an accessibility-testing methods or reproducibility report. The project's P14 hypothesis about semantic accessibility recall on heritage learning objects remains open.

## Reproduction

Run the following from the LMS repository root with Python 3, Node.js, npm, curl, tar and Chrome available. The local run used Node.js 24.22.3, Playwright 1.57.0, axe-core 4.11.0 and Chrome 158.0.8127.36 on Linux. A different browser version changes the output metadata and may change outcomes. The frontend lockfile supplies both JavaScript packages.

```bash
set -eu
study=research_v4_2/external/accessibility
work=$(mktemp -d)
act_revision=50d2bede1ee705be6840d06f356a6ae2fd94cb2c
report_revision=4ce3d61b6f7b04cbf2df0082a3446e97248b9124
npm ci --prefix frontend
curl -fsSL "https://codeload.github.com/act-rules/act-rules.github.io/tar.gz/$act_revision" -o "$work/act.tgz"
tar -xzf "$work/act.tgz" -C "$work"
CHROME_BIN="${CHROME_BIN:-/opt/google/chrome/chrome}" node "$study/evaluate.cjs" \
  "$work/act-rules.github.io-$act_revision" > "$work/local.json"
cmp "$study/result.json" "$work/local.json"

for tool in axe-core alfa; do
  curl -fsSL "https://raw.githubusercontent.com/w3c/wcag-act-rules/$report_revision/_data/wcag-act-rules/implementations/$tool.json" \
    -o "$work/$tool.json"
done
python3 "$study/compare_reports.py" "$work" > "$work/published.csv"
cmp "$study/published_comparison.csv" "$work/published.csv"
```

The comparison script verifies both source report SHA-256 digests before producing the paired CSV. The local run uses only the rules and test assets in the ACT source archive. [Report comparison script](compare_reports.py)

The four-tool expansion can also be reproduced from the repository root. The fetcher verifies the W3C report hashes before analysis.

```bash
python research_v4_2/external/fetch.py private_data/raw --study accessibility
python research_v4_2/external/accessibility/rule_coverage.py private_data/raw/act-reports | diff - research_v4_2/external/accessibility/rule_coverage.json
```

## Prediction on previously unscored rules

After removing 13 overlapping test cases, the held-out comparison included 605 examples across 50 proposed ACT rules. A logistic model combining published engine outputs classified 430 examples correctly and detected 130 of 206 expected failures with 19 false alerts. Equal-rule accuracy was 67.03% versus 64.86% for the confusion-matrix naive Bayes baseline. Fusion won on seven rules, tied on 39 and lost on four. The Holm-adjusted sign-test p-value was 0.5488. The advantage in the point estimate did not establish superiority over every comparator. [Protocol](confirmatory/protocol.md) · [Paired results](confirmatory/result.json) · [Fixture predictions](confirmatory/predictions.csv)

Pairwise engine interactions reduced equal-rule exact accuracy from 67.03% to 59.11% on the 605 previously evaluated W3C examples. The fitted main effects also changed, which affected fixtures where a pair term could never fire. [Paired evaluation and matched additive control](conditional_rules/README.md)
