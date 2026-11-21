"""Two-group fixed-capacity policies. All inputs are available before the outcome."""
import numpy as np
from scipy.stats import binom


def prefix_table(k, p):
    ranks = np.arange(1, k + 1)
    low, high = 0., .1
    for _ in range(32):
        alpha = (low + high) / 2
        table = binom.ppf(alpha, ranks, p).astype(int)
        mass = np.ones(1)
        for minimum in table:
            mass = np.convolve(mass, [1-p, p])
            mass[:minimum] = 0
        if 1 - mass.sum() <= .1:
            low = alpha
        else:
            high = alpha
    return binom.ppf(low, ranks, p).astype(int)


def fair_rank(female, other, table):
    # Inputs are queues of shared score-order positions, smaller is better.
    i = j = 0
    ranking = []
    for minimum in table:
        if i < len(female) and (i < minimum or j == len(other) or female[i] < other[j]):
            ranking.append(female[i])
            i += 1
        else:
            ranking.append(other[j])
            j += 1
    return np.array(ranking)


def discounted_dp(values, female, other, table):
    # State (r, f) records the best utility with f female recipients after r places.
    # Monotone discounts make within-group score order optimal by exchange.
    k = len(table)
    last = np.full(k + 1, -np.inf)
    last[0] = 0
    chose_female = np.zeros((k + 1, k + 1), dtype=bool)
    for rank, minimum in enumerate(table, start=1):
        current = np.full_like(last, -np.inf)
        for f in range(max(minimum, rank-len(other)), min(rank, len(female)) + 1):
            m = rank - f
            discount = np.log2(rank + 1)
            left = last[f-1] + values[female[f-1]] / discount if f else -np.inf
            right = last[f] + values[other[m-1]] / discount if m else -np.inf
            chose_female[rank, f] = left >= right
            current[f] = max(left, right)
        last = current
    f = int(np.argmax(last))
    result = []
    for rank in range(k, 0, -1):
        if chose_female[rank, f]:
            result.append(female[f-1])
            f -= 1
        else:
            result.append(other[rank-f-1])
    return np.array(result[::-1])


def allocate(scores, protected, k):
    # Caller breaks point-score ties by lexical ID. Indices here are global rank.
    assert np.all(np.diff(scores[0]) <= 0)
    female, other = np.flatnonzero(protected), np.flatnonzero(~protected)
    assert len(female) and len(other)
    table = prefix_table(k, protected.mean())
    choices = np.arange(max(table[-1], k-len(other)), min(k, len(female)) + 1)

    def capture(indices, counts):
        sums = np.pad(scores[:, indices].cumsum(axis=1), ((0, 0), (1, 0)))
        return sums[:, counts], sums[:, -1:]

    f_capture, f_total = capture(female, choices)
    m_capture, m_total = capture(other, k-choices)
    expected = (f_capture + m_capture)[0]
    recall = np.minimum(f_capture/f_total, m_capture/m_total)
    feasible = np.flatnonzero(expected >= expected.max() - .01*k)

    def threshold(objective):
        best = max(feasible, key=lambda i: (objective[i], expected[i], -choices[i]))
        return ranked_split(choices[best])

    def ranked_split(f):
        return fair_rank(female[:f], other[:k-f], table)

    quota = (2*k*len(female) + len(protected)) // (2*len(protected))
    rankings = {
        "unrestricted": np.arange(k),
        "fair": fair_rank(female, other, table),
        "quota": ranked_split(quota),
        "threshold": threshold(recall[0]),
        "discount_dp": discounted_dp(scores[0], female, other, table),
        "robust": threshold(np.quantile(recall[1:], .10, axis=0)),
    }
    for name, ids in rankings.items():
        assert len(set(ids)) == k and np.all((0 <= ids) & (ids < len(protected)))
        if name != "unrestricted":
            assert np.all(np.cumsum(protected[ids]) >= table)
        assert scores[0, ids].sum() <= scores[0, :k].sum() + 1e-9
    assert np.isclose(scores[0, rankings["fair"]].sum(), expected.max())
    discounts = 1 / np.log2(np.arange(2, k+2))
    assert all(scores[0, rankings["discount_dp"]] @ discounts + 1e-9 >= scores[0, ids] @ discounts
               for name, ids in rankings.items() if name != "unrestricted")
    return rankings, table
