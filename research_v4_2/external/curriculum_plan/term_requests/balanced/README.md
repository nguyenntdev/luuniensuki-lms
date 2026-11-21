# Which requests preserve the original optimal peak?

All 14 development curricula had a certified minimum peak. With that peak fixed, 252 of the 448 requests were infeasible and 196 had verified timetables. The same requests under the administrative ceilings yielded 190 and 258, respectively. Precedence alone found 190 of the 252 infeasible requests. Interval capacity tests found another 39. Fractional assignment with either expected-term or cumulative precedence inequalities found zero further cases. The remaining 23 required integer search in this comparison. The fractional extension missed its five-percentage-point incremental target. [Protocol](design.md) · [All 448 decisions, peak-search attempts and schedules](results.json)

The operational target uses the peak-load objective from CSPLib. The procedure increases the peak from the rounded-up average until CP-SAT returns a valid schedule, requiring infeasibility at each smaller attempted peak. Every request then receives the same certified cap as its original curriculum. Both fractional tests enforce original credit and enrollment bounds. The cumulative version also requires the mass assigned to a dependent course up to each term to fit within the mass assigned to its prerequisite strictly earlier. Integer witnesses are validated directly against all constraints.

Use the same pinned data, Python and solver versions as the [administrative comparison](../README.md). The script reads the original requests and writes a new file.

```sh
d=research_v4_2/external/curriculum_plan/term_requests/balanced
out=$(mktemp)
python "$d/screen_balanced.py" private_data/raw/csplib-bacp/bacp.zip "$out" --workers 4
cmp "$d/results.json" "$out"
```
