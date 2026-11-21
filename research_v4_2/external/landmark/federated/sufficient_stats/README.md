# P13 exact ridge follow-up

Seven simulated OULAD module clients converged in six rounds. Summed derivatives recovered the centralized optimum to 2.50e-16 maximum development probability difference. Each client exchanged 1,248 numerical payload bytes (8,736 total), versus the parent 3,240 per client. Counts include the convergence check and final broadcast and exclude transport overhead. This single-machine simulation measures neither network behavior nor privacy.

Equal-module development AUC was 0.61587, up 0.01958 over FedAvg and 0.01936 over FedProx, but down 0.00416 against local training, 0.00941 against adaptation and 0.01529 against weak ridge. Only GGG exceeded weak ridge. The point estimates already fail the conjunctive strong-gain gate, so no simultaneous interval was needed to reject advancement. Predictive equivalence against the stronger controls remains unestablished. The numerical parity claim applies to the matched centralized objective on this previously inspected development cohort.

From this directory, with the pinned OULAD zip and the parent preparation dependencies installed, run

```sh
sha256sum -c protocol.sha256
taskset -c 12-23 python ../prepare.py "$OULAD_ZIP" /tmp/suff-p13-input.csv
OPENBLAS_NUM_THREADS=1 taskset -c 12-23 python fit.py /tmp/suff-p13-input.csv > execution.json
sha256sum -c results.sha256
```

The archived AUC table includes every module and parent control. Stored predictions join to the parent archive by registration and learner identifiers.

A second implementation computes tie-corrected AUC influence values, clusters by learner across modules and applies a Bonferroni critical value across the eight archived comparisons. The equal-module gain versus weak ridge was −.01529 (simultaneous 95% interval −.05379 to .02320). Reproduce with the prepared matrix using `python study.py /tmp/suff-p13-input.csv` followed by `python score.py run`, both with one BLAS thread. [Paired uncertainty](run/summary.json)
