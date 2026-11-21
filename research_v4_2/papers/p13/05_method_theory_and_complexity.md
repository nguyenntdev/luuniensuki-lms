# P13 Method Theory & Computational Complexity

## Formulation
Let $t \le T_{\text{cutoff}}$ be discrete days.
Scheduled course exposure is given by $E(t) \in [0, 1]$.
Normalized activity rate:
$$r_{\text{norm}}(t) = \frac{\sum_{s=t-7}^t w_s}{\sum_{s=t-7}^t E(s) + \epsilon}$$
Risk hazard model:
$$P(\text{dropout} \mid X_{\le T_{\text{cutoff}}}) = \sigma\left(\sum_j w_j X_j + b\right)$$
Calibrated via isotonic scaling $f(z) = \sigma(a z + b)$.

## Invariant
Temporal Barrier: For all feature extractors $\Phi$,
$$\frac{\partial \Phi(x)}{\partial \text{event}(t)} = 0 \quad \forall t > T_{\text{cutoff}}$$
