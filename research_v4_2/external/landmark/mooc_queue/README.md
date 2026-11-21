# Does the review-queue reversal recur in a separate course platform?

We transferred two training-free OULAD rankings to the independently collected SNAP/JODIE MOOC stream. Longer inactivity and fewer logged actions both identified more future flagged learners than random review when first-flag status was current. With no status filter, only the inactivity ranking reversed. The difference identifies a limit on which aspect of the OULAD result traveled. [Original OULAD fixed rules](../status_lag/other_presentations.md) · [Independent MOOC event source](https://snap.stanford.edu/data/act-mooc.html)

At the prespecified midpoint, 5,763 learners had appeared, 3,755 had yet to receive a recorded flag and 1,256 of them received one later. With 375 review seats, inactivity ranking captured 196 future flags using current status and 51 with no filter. The unfiltered list spent 274 seats on previously flagged learners. Fractional captures for other rules reflect uniform selection within cutoff ties. Reversing each ranking direction is a control. All four are evaluated on both rosters. The simultaneous 95% intervals below cover the eight primary contrasts conditional on the observed course stream and budget. [Full results](result.json)

| Ranking | Additional future flags per 100 seats vs uniform, current status | Additional future flags per 100 seats vs uniform, no filter |
|---|---:|---:|
| Longer inactivity | +18.82 [11.88, 24.94] | −8.19 [−12.74, −3.31] |
| Fewer actions | +23.99 [17.77, 30.24] | +14.45 [7.68, 21.45] |
| More recent activity | −6.78 [−12.36, −0.10] | +4.07 [−2.51, 9.36] |
| More actions | −17.11 [−22.05, −11.95] | −6.19 [−10.87, −0.97] |

The quarter and three-quarter landmarks showed the same directions for both original rules, with no additional inference across times. No parameter was fitted to the MOOC outcomes. This release has 4,066 flagged learners. Each has exactly one flag, and none has activity at a later timestamp. This terminal-event structure makes elapsed time since activity especially sensitive to status filtering. A learner can first appear after actual enrollment. An absent event through the end of logging does not establish eventual course completion. The source covers about 30 days, with about 15 days of remaining observation at the primary landmark. OULAD measures formal withdrawal after enrollment. The MOOC measures a recorded transition after activity onset. These are different administrative and behavioral endpoints. The publisher defines the positive flag using the learner’s last action. Knowing at that instant that no later action will occur would require future information. Current status here is an oracle scenario, and the trace provides neither a live exit feed nor an identified second university. No real intervention or reporting delay was observed.

Download the pinned author CSV using the [action-study reproduction instructions](../interaction/README.md). From the repository root, run with NumPy and pandas. The evaluator verifies the raw SHA-256. The SQL verifier recomputes every expected case and stale-seat count from the raw stream.

```sh
set -eu
p=research_v4_2/external/landmark/mooc_queue
a=private_data/raw/act-mooc/author-mooc.csv
(cd "$p" && sha256sum -c protocol.sha256)
OPENBLAS_NUM_THREADS=1 python "$p/evaluate.py" "$a" | diff - "$p/result.json"
python "$p/verify.py" "$a"
```
