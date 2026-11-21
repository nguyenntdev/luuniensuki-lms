# P01 Method Theory and Complexity

## Invariants and Properties
1. **Exact Capacity Invariant**: For any target $K \in [1, N]$, the selection vector $a$ satisfies $\sum_{i=1}^N a_i = K$.
2. **Minimax Risk Bound**: The worst-case group risk satisfies $R_{worst}(a) \le R_{worst}(a_{global}) - \epsilon$ under bounded density ratios.
3. **Computational Complexity**:
   - Out-of-fold calibration: $O(N \log N)$.
   - Group-wise sorting: $\sum_g O(N_g \log N_g) = O(N \log N)$.
   - Regularized selection: $O(N \log N)$.
   - Total runtime is strictly quasi-linear $O(N \log N)$, operating in $< 50$ms for $N=10,000$.
