# Which rubric changes the selected tutor across sources?

**Actionability accounts for the MathDial-to-Bridge switch.** Every training objective that included Actionability selected Llama31405B. Every objective without it selected GPT4. Guidance alone gave GPT4 a two-case training lead over Llama31405B (113 vs. 111 out of 145). Requiring Actionability as well removed 40 of GPT4's guidance successes and 12 of Llama31405B's, leaving 73 vs. 99. Both choices were unique training maxima.

On Bridge, the switch raised the count on the common guidance criterion from **26/37 to 30/37**. Llama31405B recovered seven cases and lost three, a gain of 10.8 percentage points with a paired 95% interval of −8.1 to +25.9 points. On the parent study's secondary four-criterion endpoint the same switch raised the count from 6/37 to 19/37 (+35.1 points, 95% interval +11.1 to +51.9). The two endpoint calculations use the same archived responses and tutor choices. [Frozen parent protocol](../protocol.md) · [Frozen parent results](../result.json)

## All rubric subsets and training ties

Each row uses guidance plus the listed rubrics during training. The training objective counts a case only when every included label is `Yes`. The target count always uses the released `Providing_Guidance = Yes` label. I means Mistake Identification, L means Mistake Location, and A means Actionability.

| Added rubrics | MathDial training maxima / 145 | Bridge guidance / 37 | Bridge training maxima / 37 | MathDial guidance / 145 |
| --- | --- | --- | --- | --- |
| None | GPT4 (113) | 26 | Gemini (31) | 71 |
| I | GPT4 (113) | 26 | Gemini and Llama31405B (30 each) | 71 or 111 |
| L | GPT4 (111) | 26 | Gemini and Llama31405B (30 each) | 71 or 111 |
| A | Llama31405B (99) | 30 | Gemini (24) | 71 |
| I + L | GPT4 (111) | 26 | Gemini and Llama31405B (30 each) | 71 or 111 |
| I + A | Llama31405B (98) | 30 | Gemini (24) | 71 |
| L + A | Llama31405B (98) | 30 | Gemini (24) | 71 |
| I + L + A | Llama31405B (97) | 30 | Gemini (24) | 71 |

In Bridge-to-MathDial transfer, guidance alone and the full conjunction both select Gemini uniquely. Identification alone, Location alone, and their combination each tie Gemini with Llama31405B at 30/37. The frozen alphabetical rule selects Gemini in all three ties. Had an origin-only tie rule selected Llama31405B, its MathDial guidance score would have been 111/145 versus 71/145 for Gemini, with 52 cases recovered and 12 lost (+27.6 points, 95% interval +17.9 to +37.0). The training counts give no preference between the tied tutors. Actionability resolves those ties in favor of Gemini. [All six tutors' training counts and paired target outcomes](result.json)

## Data and evaluation

- The pinned MRBench V3 development release contains 300 conversations and six eligible tutors per conversation. All 7,200 labels for the four rubrics were `Yes`, `No`, or `To some extent`. Only `Yes` counts as a success.
- Join V3 to V2 provenance on conversation ID and lowercased, whitespace-collapsed full history. V2 has 200 records with 195 unique keys. The five repeated keys agree on their source. The join yields 145 MathDial cases and 37 Bridge cases, leaving 118 unlinked cases outside both transfer splits.
- Split by source and remove origin cases whose normalized opening occurs in the target. The opening is the lowercased, whitespace-collapsed prefix before the first `Student:` marker, with the frozen evaluator's allowance for whitespace before the colon. MathDial has 119 opening groups and Bridge has 27. The two sources share zero opening groups and zero conversation IDs, so the filter removes zero cases in either direction. Text normalization leaves possible paraphrased problems across the split.
- Score the same six tutors for each of the eight training objectives in each direction. Retain every exact training maximum, with the parent's alphabetical rule as the fixed decision. Evaluate each maximizer on the same target cases, primarily on guidance and secondarily on the four-label conjunction. Use the guidance-only choice as the paired reference for both endpoints.
- Use the frozen bootstrap of 10,000 paired opening-group resamples with seed 42 and percentile limits. The intervals are pointwise, preserve case weighting within each resample, and condition on the selected tutors.

This is a post hoc attribution of the selector's behavior on the source splits already studied in MRBench. Actionability explains which archived tutor the rule chooses on MathDial. The Bridge guidance interval includes zero, and the reverse-direction advantage depends on which training maximizer is chosen. The audit uses the same archived outputs and released annotations throughout. It adds no human validation and establishes no improvement in the tutors themselves or in student learning.

## Reproduce

From the repository root, use Python 3.12 with NumPy 2.4.4. Use an existing verified source cache or download the two files into a temporary directory outside the repository. The evaluator verifies both SHA-256 hashes and emits only aggregate counts and intervals. The command below uses CPU cores 24–31, as in the reproduced run.

```bash
set -euo pipefail
study=research_v4_2/external/tutoring/multiple_rubrics
inputs=$(mktemp -d)
trap 'rm -rf "$inputs"' EXIT
data=https://raw.githubusercontent.com/kaushal0494/UnifyingAITutorEvaluation/bbef521ddb875f2cc8a5ee798f4066965a7cfd8a
curl -fLsS "$data/BEA_Shared_Task_2025_Datasets/mrbench_v3_devset.json" -o "$inputs/mrbench_v3_devset.json"
curl -fLsS "$data/MRBench/MRBench_V2.json" -o "$inputs/MRBench_V2.json"
taskset -c 24-31 python "$study/evaluate.py" "$inputs" | diff -u "$study/result.json" -
taskset -c 24-31 python "$study/attribution/evaluate.py" "$inputs" | diff -u "$study/attribution/result.json" -
```

[Pinned MRBench release and licence](https://github.com/kaushal0494/UnifyingAITutorEvaluation/tree/bbef521ddb875f2cc8a5ee798f4066965a7cfd8a)
