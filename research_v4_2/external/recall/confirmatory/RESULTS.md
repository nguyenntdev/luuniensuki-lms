# Results on the reserved Duolingo learners

The four-component ensemble had mean learner log loss 0.325446 across 4,596 learners and 526,770 item encounters. It cleared the 0.005-nat margin for 12 of 16 controls under one-sided Holm tests. Positive gains favor the ensemble.

| Control | Mean learner log loss | Paired gain in nats | Simultaneous 95% interval | Holm p at 0.005 | Clears margin |
|---|---:|---:|---:|---:|---|
| matched catboost | 0.325474 | 0.000028 | [-0.000023, 0.000080] | 1 | No |
| history logistic | 0.329239 | 0.003793 | [0.002764, 0.004821] | 1 | No |
| base catboost | 0.329939 | 0.004492 | [0.003400, 0.005585] | 1 | No |
| hist boost | 0.330004 | 0.004558 | [0.003472, 0.005643] | 1 | No |
| logistic | 0.331535 | 0.006089 | [0.004756, 0.007422] | 0.0395 | Yes |
| smoothed history | 0.334544 | 0.009098 | [0.007665, 0.010532] | 1.23e-16 | Yes |
| history hlr | 0.334625 | 0.009179 | [0.007719, 0.010640] | 1.23e-16 | Yes |
| leitner | 0.334958 | 0.009512 | [0.008003, 0.011021] | 5.31e-18 | Yes |
| author hlr | 0.335344 | 0.009898 | [0.008337, 0.011459] | 1.15e-19 | Yes |
| hlr no lexeme | 0.335394 | 0.009948 | [0.008385, 0.011510] | 6.05e-20 | Yes |
| author hlr ablated | 0.335460 | 0.010014 | [0.008442, 0.011586] | 3.72e-20 | Yes |
| hlr no lexeme no h | 0.335460 | 0.010014 | [0.008442, 0.011586] | 3.72e-20 | Yes |
| pimsleur | 0.335779 | 0.010333 | [0.008738, 0.011929] | 5.43e-22 | Yes |
| lr no lexeme | 0.335941 | 0.010495 | [0.008891, 0.012098] | 5.65e-23 | Yes |
| author lr | 0.335941 | 0.010495 | [0.008891, 0.012098] | 5.65e-23 | Yes |
| constant | 0.335941 | 0.010495 | [0.008891, 0.012098] | 5.65e-23 | Yes |

The original ten-comparator family cleared 6 of 10 margins. Both analyses condition on fixed fits and assume independent learners. [Original results](run/result.json) · [Expanded results](run/reference_result.json) · [Original protocol](protocol.md) · [Additional reference controls](reference_protocol.md)
