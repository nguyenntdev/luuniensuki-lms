# Predicting one MultiNLI vote from the other four

**The candidate failed the prespecified superiority criterion.** The six-component empirical Bayes mixture improved Brier loss over six baselines, including development-fitted Dirichlet shrinkage and a three-class latent model. The development-fitted conditional histogram had marginally lower loss. Its interval includes improvements in either direction. The data do not establish equivalence.

| Predictor | Test Brier ↓ | Baseline minus candidate | Simultaneous 95% interval |
|---|---:|---:|---:|
| Six-component candidate | .239941 | — | — |
| Empirical frequencies | .248750 | .008809 | [.007643, .009936] |
| Majority with uniform ties | .278900 | .038959 | [.034722, .043282] |
| Jeffreys add-half | .260099 | .020158 | [.018763, .021486] |
| Laplace add-one | .301143 | .061202 | [.058982, .063464] |
| Fitted Dirichlet | .244057 | .004116 | [.003056, .005154] |
| Three-class latent model | .248122 | .008181 | [.006083, .010324] |
| Fitted conditional histogram | **.239927** | **−.000014** | **[−.000201, .000172]** |

## Design and interpretation

The forecaster sees counts of entailment, neutral and contradiction among four votes. For each five-vote item we scored each held position once and averaged the five multiclass Brier losses. Matched development provided 10,000 fitting pairs in 3,334 prompt/premise groups. The sole evaluation used 10,000 mismatched development pairs in 3,326 disjoint groups across five held-out genres. All rows qualified. No prompt IDs or normalized premises crossed the split. Grouped five-fold development validation selected a conditional-table backoff of 25 held-vote counts. Each of the 15 possible four-vote histograms has a saved forecast from every model. Intervals use 10,000 paired group bootstrap draws with Bonferroni adjustment over seven comparisons.

The latent-class baseline adapts Dawid and Skene's EM model to the available inputs by sharing error rates across anonymous voters. The saturated conditional table directly estimates the target distribution for each possible model input. ChaosNLI is related work on human NLI response distributions using additional judgments and text-based predictors. Its published text-model scores cannot be transferred to this four-vote experiment. We make no literature-wide best-model claim. [Dawid and Skene](https://doi.org/10.2307/2346806) · [Nie, Zhou and Bansal](https://aclanthology.org/2020.emnlp-main.734/)

MultiNLI combines the elicited construction label with four validation labels per item. The endpoint refers to a uniformly sampled recorded position. It does not establish performance for a new independent reviewer, agreement with historical truth, or LMS classroom raters. The intervals condition on the fitted models and these genres. The corpus paper details source-specific permissions, including OANC and fiction licenses. The outputs contain identifiers, counts and forecasts. [Williams, Nangia and Bowman](https://aclanthology.org/N18-1101/) · [Author release](https://cims.nyu.edu/~sbowman/multinli/)

## Freeze and replay

The local protocol and implementation were hashed before first test access. The first execution wrote all fitted forecasts before opening the holdout, then halted on a duplicate released pair ID before computing any test scores. A metadata check found 27 repeated IDs, all attached to distinct sentence pairs. The only implementation correction added the archive line number to each output ID and removed the uniqueness assertion on bare pair IDs. All eligible rows and the prespecified group rule were retained. The original pre-evaluation forecast SHA-256 was b555f79fbb23ce4b36fc8f672b270bd77feaef8eb9c11d0a28813ebab33f912f. The corrected run produced byte-identical forecasts. The protocol hash documents a local freeze without an external timestamp.

Run from this directory with Python 3.12.3, NumPy 2.4.4 and SciPy 1.17.1. The output directory must be new. The archive is verified inside the evaluator.

```sh
curl -fL https://cims.nyu.edu/~sbowman/multinli/multinli_1.0.zip -o /tmp/multinli_1.0.zip
sha256sum -c protocol.sha256
sha256sum -c manifest.sha256
OPENBLAS_NUM_THREADS=1 python run.py /tmp/multinli_1.0.zip /tmp/multinli_vote_replay
diff -r frozen /tmp/multinli_vote_replay
```

The frozen directory contains the development-only probability tables and tuning scores, item-level holdout counts and group keys, and all test scores and intervals. Each row key combines the released pair ID and its one-based archive line. The separate preflight implementation digest records the original version that stopped before scoring.

The [100-vote panel follow-up](../panel/README.md) measures prediction of remaining new votes conditional on earlier judgments in two ChaosNLI cohorts.
