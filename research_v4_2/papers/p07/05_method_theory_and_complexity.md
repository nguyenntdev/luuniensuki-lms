# P07 Method Theory and Complexity

## Mathematical Formulation
Let $T$ be a task with required affordance set $R(T) \subseteq \mathcal{A}$.
Let $D = (B, N, W, K, S)$ be the device constraints where:
- $B$: max payload capacity (KB)
- $N$: network streaming bandwidth ceiling (kbps)
- $W \in \{0, 1\}$: WebGL support
- $K \in \{0, 1\}$: Keyboard-only navigation
- $S \in \{0, 1\}$: Screen-reader support

Candidate objects $\mathcal{O} = \{o_1, \dots, o_n\}$. For each object $o_i$:
- $L(o_i) \in \mathcal{L}$: license status
- $P(o_i) \in \{0, 1\}$: cryptographic provenance certificate validity
- $c(o_i)$: payload size in KB
- $s(o_i) \in [0, 1]$: multimodal semantic relevance (e.g. from SigLIP2)
- $a(o_i, r) \in \{0, 1\}$: affordance indicator for $r \in \mathcal{A}$.

## Feasibility Space $\mathcal{F}$
An object $o_i \in \mathcal{F}$ iff:
1. $L(o_i) \in \mathcal{L}_{\text{allowed}} \land P(o_i) = 1$
2. $c(o_i) \le B$
3. $N \ge \text{Ceiling}(o_i.\text{modality})$
4. $(o_i.\text{modality} = \text{3D}) \implies W = 1$
5. $K = 1 \implies a(o_i, \text{keyboard}) = 1$
6. $S = 1 \implies a(o_i, \text{screen\_reader}) = 1$
7. $\forall r \in R(T), a(o_i, r) = 1$.

## Objective
If $\mathcal{F} \neq \emptyset$:
$$\arg\max_{o \in \mathcal{F}} \left[ s(o) - \lambda \frac{c(o)}{B} + \mu P(o) \right]$$
Else, emit typed abstention `abstain_missing_affordance` or `reject_rights_violation`.

## Complexity
- Feasibility check per candidate: $\mathcal{O}(|R(T)|)$.
- Optimization over $n$ candidates: $\mathcal{O}(n \cdot |R(T)|)$ time, $\mathcal{O}(1)$ additional memory.
