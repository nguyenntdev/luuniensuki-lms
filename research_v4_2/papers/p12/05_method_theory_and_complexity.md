# P12 Method Theory & Computational Complexity

## Formal Invariant: Cryptographic Tamper Evident Chain
Each block $B_i$ contains:
$$H_i = \text{SHA256}(i \parallel t_i \parallel \text{claim\_id} \parallel \text{verdict} \parallel D_{\text{loc}} \parallel H_{\text{page}} \parallel H_{i-1})$$

Theorem: Under standard cryptographic hash collision resistance (SHA-256), any mutation of past block data $B_k$ ($k < n$) results in $H_n \ne \text{compute\_hash}(B_n)$ with probability $1 - 2^{-256}$.

## Complexity
- Locator resolution & verification: $\mathcal{O}(|Page\_Length|)$.
- Block verification: $\mathcal{O}(1)$ per block, $\mathcal{O}(N)$ for whole chain audit.
