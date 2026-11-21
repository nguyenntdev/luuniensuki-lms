# P11 Method Theory & Computational Complexity

## Formulation
Let $A = (c_1, \dots, c_m)$ be an argument with claims $c_i$ and cited evidence spans $s_{ij} \in \mathcal{S}$.
Each span has verification status $v(s_{ij}) \in \{0, 1\}$.
Facets $\mathcal{F} = \{\text{authenticity}, \text{temporal\_placement}, \text{corroboration}, \text{counterevidence}\}$.

Hard Invariant Caps:
$$\text{Score}(\text{authenticity}) \le 1 \quad \text{if } \exists s_{ij}: v(s_{ij}) = 0$$
$$\text{Score}(\text{authenticity}) = 0 \quad \text{if } |\mathcal{S}| = 0$$

Targeted Active Arbitration:
$$\Delta_f = \max_{r} S_{r,f} - \min_{r} S_{r,f}$$
Arbitration is invoked iff $\exists f \in \mathcal{F}: \Delta_f \ge \tau$, where $\tau = 1.0$.

## Complexity
- Single rater evaluation: $\mathcal{O}(|Claims| \times |Spans|)$.
- Active arbitration: $\mathcal{O}(|Facets|_{discordant})$, where $|Facets|_{discordant} \ll |\mathcal{F}|$.
- Alpha calculation: $\mathcal{O}(N \cdot K^2)$ where $N$ is items and $K$ is score levels.
