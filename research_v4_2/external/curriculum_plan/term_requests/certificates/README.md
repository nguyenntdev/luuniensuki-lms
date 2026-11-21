# Joint credit and enrollment certificates on development requests

The joint cut added 0 rejections across 448 requests at the saved balanced peaks. The existing precedence and interval screen rejected 229. Of the remaining 219 requests, matched CP-SAT controls proved 23 infeasible and returned witnesses for 196. The additional cut therefore saved zero solver calls. These are the original 14 odd-numbered development curricula and their previously evaluated requests.

For each contiguous interval, courses whose windows lie inside contribute their full credits. Courses with overlapping windows may contribute a fraction between zero and one. Enrollment limits inside and outside the interval bound the number of optional courses needed and the room available. Taking the cheapest needed courses gives a lower credit bound. Taking the most expensive courses that fit gives an upper bound. These extrema also bound fractional allocations because moving mass toward a cheaper or more expensive course improves the corresponding objective until a bound is tight. Credit limits inside and outside give a second required credit range. Disjoint ranges or inconsistent enrollment bounds certify infeasibility using integer arithmetic. Passing all cuts gives no feasibility guarantee.

The runner replays every baseline decision and uses the balanced study's saved exact status for the identical instance, peak and request. It skips the added cut on baseline rejections. The JSON records each matched decision. Reproduce from the repository root using the parent study's pinned archive and OR-Tools environment.

```sh
d=research_v4_2/external/curriculum_plan/term_requests/certificates
out=$(mktemp)
taskset -c 12-23 python "$d/compare.py" private_data/raw/csplib-bacp/bacp.zip > "$out"
cmp "$d/results.json" "$out"
```
