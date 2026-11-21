# P01 Novelty Counterexample and Mathematical Differentiation

## Failure of Unconstrained and Global Conformal Deferral (CRC2026)
Standard conformal prediction and cost-aware deferral rank items solely by global non-conformity scores:
$$s(x, y) = 1 - P(y \mid x)$$
Under severe course-level covariate shift $P_g(x) \ne P(x)$ and finite human-review capacity $K$:
1. Global thresholding disproportionately selects items from low-variance, easy courses, saturating the review budget with students who need it least.
2. High-risk minority courses (e.g., Course 3 and Course 4 with complex historiographical rubrics) are allocated insufficient review slots, driving worst-course selective accuracy down to uncalibrated failure rates.

## Candidate Differentiator: Capacity-Coupled Minimax Group Quota
The proposed `CapacityCoupledRiskController` solves:
$$\min_{a \in \{0, 1\}^N} \sum_{i=1}^N w(x_i) e_i a_i + \lambda \max_{g \in \mathcal{G}} R_g(a) \quad \text{s.t.} \quad \sum_{i=1}^N a_i = K$$
Where:
- $w(x)$ is the density ratio estimation bounding temporal term shift.
- $\lambda > 0$ strictly penalizes worst-group risk disparity.
- Exact capacity $K$ is guaranteed through regularized non-conformity scaling across group priority queues.
