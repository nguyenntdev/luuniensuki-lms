"""Generate text, assignment, and prefix features on the two development releases."""
import argparse
from collections import Counter
from functools import lru_cache
from hashlib import sha256
import html
import math
from pathlib import Path
import re
import unicodedata

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process
from rapidfuzz.distance import JaroWinkler
from scipy.optimize import linear_sum_assignment

DATASETS = ("DBLP-ACM", "DBLP-GoogleScholar")


@lru_cache(maxsize=100000)
def fields(record):
    parts = re.split(r"\bCOL (?:title|authors|venue|year) VAL\b", record)
    assert len(parts) == 5 and not parts[0]
    result = []
    for value in parts[1:]:
        value = html.unescape(re.sub(r"&\s+([a-zA-Z]+)\s*;", r"&\1;", value))
        value = unicodedata.normalize("NFKD", value.casefold())
        value = "".join(char for char in value if not unicodedata.combining(char))
        result.append(tuple(re.findall(r"[^\W_]+", value)))
    return result


def character(a, b):
    if not a or not b:
        return [0.] * 4
    left, right = " ".join(a), " ".join(b)
    return [fuzz.ratio(left, right), fuzz.partial_ratio(left, right),
            fuzz.token_sort_ratio(left, right), fuzz.ratio("".join(a), "".join(b))]


def prefix_features(sim, left, right):
    # Anchored local alignment. Gaps may preserve order within a title.
    # Stopping at any paired prefix models suffix material appended by corruption.
    n, m = sim.shape
    if not n or not m:
        return [0.] * 5
    wl, wr = np.cumsum(left), np.cumsum(right)
    dp = np.zeros((n+1, m+1))
    for i in range(n):
        for j in range(m):
            hit = min(left[i], right[j]) * sim[i, j]
            dp[i+1,j+1] = max(dp[i,j+1], dp[i+1,j], dp[i,j]+hit)
    mass = dp[1:,1:]
    agreement = 2 * mass / (wl[:,None]+wr[None,:])
    # The saturating evidence weight discounts a one-token coincidence.
    support = agreement * (1 - np.exp(-mass/15.0))
    end = np.unravel_index(np.argmax(support), support.shape)
    return [support[end], agreement[end], np.log1p(mass[end]),
            mass[-1,-1] / wl[-1], mass[-1,-1] / wr[-1]]


def blocks(a, b, idf):
    lt = sum(a, ())
    rt = sum(b, ())
    char = character(lt, rt) + sum((character(u, v) for u,v in zip(a,b)), [])
    sim = process.cdist(lt, rt, scorer=JaroWinkler.normalized_similarity,
                        score_cutoff=.9, dtype=np.float64)
    lw = np.array([idf(x) for x in lt])
    rw = np.array([idf(x) for x in rt])
    weight = sim * np.minimum(lw[:,None], rw[None,:])
    rows, cols = linear_sum_assignment(weight, maximize=True)
    links = weight[rows,cols]
    flat = [links.sum()/max(1, lw.sum()), links.sum()/max(1, rw.sum()),
            np.log1p(links.sum())]
    # The exact same matching is used by the flattened and field-resolved variants.
    la = np.repeat(np.arange(4), [len(tokens) for tokens in a])
    rb = np.repeat(np.arange(4), [len(tokens) for tokens in b])
    mass = np.zeros((4,4))
    np.add.at(mass, (la[rows],rb[cols]), links)
    left_mass = np.bincount(la, weights=lw, minlength=4)
    right_mass = np.bincount(rb, weights=rw, minlength=4)
    assignment = [*(mass/np.maximum(1,left_mass[:,None])).ravel(),
                  *(mass/np.maximum(1,right_mass[None,:])).ravel()]
    n,m = len(a[0]),len(b[0])
    prefix = prefix_features(sim[:n,:m],lw[:n],rw[:m])
    return [*char, *flat, *assignment, *prefix]


def generate(raw, work, name):
    rows = []
    for split in ("train","valid"):
        path = raw / f"{name}-{split}.txt"
        for line in path.read_text().splitlines():
            a,b,label = line.split("\t")
            key = sha256((a+"\t"+b).encode()).hexdigest()
            role = "validation" if split=="valid" else "calibration" if int(key[:8],16)%5==0 else "fit"
            rows.append((role,a,b,int(label)))
    old = pd.read_csv(work / f"{name}.csv",header=None,usecols=[1,2,3,4])
    assert list(old[1]) == [r[0] for r in rows]
    assert list(old[2]) == [r[3] for r in rows]
    for index in (1,2):
        assert list(old[index+2]) == [sha256(r[index].encode()).hexdigest() for r in rows]
    docs = sorted({text for role,a,b,_ in rows if role=="fit" for text in (a,b)})
    freq = Counter(token for doc in docs for token in set(sum(fields(doc), ())))
    def idf(token):
        return 1 + math.log((1+len(docs))/(1+freq[token]))
    features = []
    with (work / f"{name}-second.tsv").open("w") as handle:
        for role,a,b,_ in rows:
            left,right = fields(a),fields(b)
            handle.write("\t".join((role," ".join(sum(left, ()))," ".join(sum(right, ()))))+"\n")
            features.append(blocks(left,right,idf))
    np.save(work / f"{name}-soft.npy", np.array(features))
    print(name, len(rows), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("work", type=Path)
    args = parser.parse_args()
    for dataset in DATASETS:
        generate(args.raw, args.work, dataset)
