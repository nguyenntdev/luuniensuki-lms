# Novelty Counterexample — P04

## Setting
Let a curriculum DAG have prerequisite relations $A_{u, v} > 0$ such that observed student feature activity accumulates upstream performance: $X = S (I - A)^{-1} + \epsilon$.
The true student outcome $y$ depends strictly on intrinsic competency innovations $S$, where $y \sim \text{Bernoulli}(\sigma(S w^*))$.

## Prior Art Limitations
1. **Standard ERM (C1)** learns $w_{ERM} = (X^T X)^{-1} X^T y$. Because $X$ accumulates variance along prerequisite chains, $w_{ERM}$ puts near-zero or negative weights on fundamental prerequisites and massive weight on terminal topics (shortcut learning).
2. **Domain CORAL (C2)** aligns second-order covariances $\text{Cov}(X_s)$ and $\text{Cov}(X_t)$. However, when the prerequisite structure changes (e.g., in S1 modular clusters $A_{S1}$ or S2 modular electives $A_{S2} = 0$), linear covariance matching cannot disentangle the underlying intrinsic innovations from the structural routing shift.

## Concrete Counterexample
Let $d=2$, with prerequisite $A = \begin{bmatrix} 0 & 0.8 \\ 0 & 0 \end{bmatrix}$.
Then $X_1 = S_1$, $X_2 = 0.8 S_1 + S_2$.
Suppose $y = S_1 + S_2$.
In terms of observed features, $y = 0.2 X_1 + X_2$.
ERM learns $w_1 = 0.2, w_2 = 1.0$.
Now consider shifted cohort S2 where prerequisite chaining is absent: $X_1' = S_1, X_2' = S_2$.
ERM predicts $\hat{y} = 0.2 S_1 + 1.0 S_2$, under-weighting skill 1 by 80%!
CORAL scales the covariance of $X'$, but cannot invert the triangular dependency.

## Proposed Resolution
OGD-Shift explicitly projects $X$ through $(I - A_{target})$, recovering $S_1$ and $S_2$ exactly. Hence, prediction on intrinsic skills is invariant to arbitrary curriculum rearrangements.
