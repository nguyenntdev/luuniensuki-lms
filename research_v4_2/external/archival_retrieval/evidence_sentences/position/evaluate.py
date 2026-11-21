"""Run the frozen SciFact position-prior development screen."""

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
from itertools import product
import json
from pathlib import Path
import re
import tarfile

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


STUDY = Path(__file__).resolve().parent
ARCHIVE_SHA256 = "11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be"
BM25_SETTINGS = tuple(product((0.6, 1.2, 1.8), (0.25, 0.75)))
MIXTURES = tuple(
    (bm / 4, word / 4, (4 - bm - word) / 4)
    for bm in range(4, -1, -1)
    for word in range(4 - bm, -1, -1)
)
LAMBDAS = (0, 0.05, 0.10, 0.20, 0.40, 0.80)
AUGMENTED = ("learned", "later_first", "earlier_first", "hash_order")
CONTROLS = ("lexical", "later_first", "earlier_first", "hash_order")
TOKENS = re.compile(r"\w+")


@dataclass(frozen=True)
class Pair:
    claim_id: int
    doc_id: int
    claim: str
    sentences: list[str]
    gold: tuple[int, ...]
    component: tuple[int, ...]


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load(archive):
    if sha256(archive) != ARCHIVE_SHA256:
        raise ValueError(f"SciFact archive checksum mismatch: {archive}")
    with tarfile.open(archive, "r:gz") as tar:
        with tar.extractfile("data/corpus.jsonl") as stream:
            corpus = {row["doc_id"]: row["abstract"] for row in map(json.loads, stream)}
        with tar.extractfile("data/claims_train.jsonl") as stream:
            claims = sorted(map(json.loads, stream), key=lambda row: row["id"])
    return corpus, claims


def source_components(claims):
    parents = {}

    def root(doc):
        parents.setdefault(doc, doc)
        while parents[doc] != doc:
            parents[doc] = parents[parents[doc]]
            doc = parents[doc]
        return doc

    for row in claims:
        sources = sorted(set(row["cited_doc_ids"]) | set(map(int, row["evidence"])))
        if sources:
            anchor = root(sources[0])
            for doc in sources[1:]:
                parents[root(doc)] = anchor

    grouped = defaultdict(list)
    for doc in sorted(parents):
        grouped[root(doc)].append(doc)
    return {doc: tuple(group) for group in grouped.values() for doc in group}


def partition(corpus, claims):
    components = source_components(claims)
    partitions = {"fit": [], "selection": [], "screen": []}
    for row in claims:
        for doc, annotations in sorted(row["evidence"].items(), key=lambda item: int(item[0])):
            gold = tuple(sorted({index for ann in annotations for index in ann["sentences"]}))
            if not gold:
                continue
            doc_id = int(doc)
            sentences = corpus[doc_id]
            if not 0 <= gold[0] <= gold[-1] < len(sentences):
                raise ValueError(f"Invalid evidence index for claim {row['id']}, document {doc}")
            component = components[doc_id]
            key = ",".join(map(str, component)).encode()
            bucket = int.from_bytes(hashlib.sha256(key).digest()[:8], "big") % 4
            split = ("fit", "fit", "selection", "screen")[bucket]
            partitions[split].append(
                Pair(row["id"], doc_id, row["claim"], sentences, gold, component)
            )
    checks = (
        {name: {pair.claim_id for pair in pairs} for name, pairs in partitions.items()},
        {name: {doc for pair in pairs for doc in pair.component} for name, pairs in partitions.items()},
    )
    for sets in checks:
        if any(not ids for ids in sets.values()) or sum(map(len, sets.values())) != len(
            set.union(*sets.values())
        ):
            raise ValueError("Empty partition or claim/source leakage")
    return partitions


def normalize(values):
    peak = values.max()
    return values / peak if peak > 0 else values


def cosine(pair, **settings):
    vectorizer = TfidfVectorizer(**settings)
    try:
        matrix = vectorizer.fit_transform(pair.sentences)
    except ValueError as exc:
        if "empty vocabulary" not in str(exc):
            raise
        return np.zeros(len(pair.sentences))
    values = (matrix @ vectorizer.transform([pair.claim]).T).toarray().ravel()
    return normalize(values)


def lexical_signals(pair, bm25_settings):
    word = cosine(pair, stop_words="english", ngram_range=(1, 2))
    char = cosine(pair, analyzer="char_wb", ngram_range=(3, 5))
    counts = [Counter(TOKENS.findall(sentence.lower())) for sentence in pair.sentences]
    lengths = np.array([sum(counter.values()) for counter in counts])
    query_words = sorted(set(TOKENS.findall(pair.claim.lower())))
    frequencies = np.array([[counter[term] for counter in counts] for term in query_words])
    bm25 = {}
    for k, b in bm25_settings:
        values = np.zeros(len(counts))
        if query_words and lengths.any():
            df = np.count_nonzero(frequencies, axis=1)
            idf = np.log1p((len(counts) - df + 0.5) / (df + 0.5))
            normalizer = k * (1 - b + b * lengths / lengths.mean())
            values = (idf[:, None] * (k + 1) * frequencies / (frequencies + normalizer)).sum(axis=0)
        bm25[k, b] = normalize(values)
    return word, char, bm25


def bins(n):
    return 5 * (2 * np.arange(n) + 1) // (2 * n)


def fit_prior(pairs):
    total = np.zeros(5, dtype=int)
    gold = np.zeros(5, dtype=int)
    for pair in pairs:
        positions = bins(len(pair.sentences))
        total += np.bincount(positions, minlength=5)
        gold += np.bincount(positions[list(pair.gold)], minlength=5)
    other = total - gold
    logits = np.log((gold + 1) / (other + 1))
    return logits, {"gold": gold.tolist(), "non_gold": other.tolist(), "log_odds": logits.tolist()}


def position_scores(pair, logits):
    n = len(pair.sentences)
    learned = logits[bins(n)]
    learned = learned - learned.mean()
    later_first = np.sort(learned)
    hash_indices = sorted(
        range(n),
        key=lambda i: (hashlib.sha256(f"position-control:{pair.doc_id}:{i}".encode()).digest(), i),
    )
    hash_order = np.empty_like(learned)
    hash_order[hash_indices] = later_first
    return {
        "learned": learned,
        "later_first": later_first,
        "earlier_first": later_first[::-1],
        "hash_order": hash_order,
    }


def order(scores):
    return np.argsort(-scores, kind="stable")


def outcomes(pair, ranking):
    hits = np.flatnonzero(np.isin(ranking, pair.gold))
    return 1 / (1 + int(hits[0])), np.count_nonzero(hits < 3) / len(pair.gold)


def mean_mrr(pairs, scores):
    return float(np.mean([outcomes(pair, order(s))[0] for pair, s in zip(pairs, scores, strict=True)]))


def combine(word, char, bm25, mixture):
    return mixture[0] * bm25 + mixture[1] * word + mixture[2] * char


def select(pairs, logits):
    signals = [lexical_signals(pair, BM25_SETTINGS) for pair in pairs]
    bm25_mrr = {
        settings: mean_mrr(pairs, (bm25[settings] for _, _, bm25 in signals))
        for settings in BM25_SETTINGS
    }
    best_bm25 = max(bm25_mrr, key=bm25_mrr.get)
    mixture_mrr = {
        mixture: mean_mrr(
            pairs, (combine(word, char, bm25[best_bm25], mixture) for word, char, bm25 in signals)
        )
        for mixture in MIXTURES
    }
    best_mix = max(mixture_mrr, key=mixture_mrr.get)
    lexical = [combine(word, char, bm25[best_bm25], best_mix) for word, char, bm25 in signals]
    positions = [position_scores(pair, logits) for pair in pairs]
    augmented_mrr = {
        method: {
            weight: mean_mrr(
                pairs, (s + weight * p[method] for s, p in zip(lexical, positions, strict=True))
            )
            for weight in LAMBDAS
        }
        for method in AUGMENTED
    }
    best_weights = {method: max(grid, key=grid.get) for method, grid in augmented_mrr.items()}
    selection = {
        "bm25": {"selected_k1_b": best_bm25, "mrr": [[*key, value] for key, value in bm25_mrr.items()]},
        "lexical": {
            "selected_bm25_word_char": best_mix,
            "mrr": [[*key, value] for key, value in mixture_mrr.items()],
        },
        "augmentation": {
            method: {"selected_lambda": best_weights[method], "mrr": list(grid.items())}
            for method, grid in augmented_mrr.items()
        },
    }
    return best_bm25, best_mix, best_weights, selection


def score(pairs, logits, bm25_settings, mixture, weights):
    rows = []
    for pair in pairs:
        word, char, bm25_grid = lexical_signals(pair, (bm25_settings,))
        bm25 = bm25_grid[bm25_settings]
        lexical = combine(word, char, bm25, mixture)
        position = position_scores(pair, logits)
        indices = np.arange(len(pair.sentences))
        scores = {
            "word_tfidf": word,
            "char_tfidf": char,
            "bm25": bm25,
            "lexical": lexical,
            **{method: lexical + weights[method] * position[method] for method in AUGMENTED},
            "learned_only": position["learned"],
            "earlier_first_only": -indices,
            "later_first_only": indices,
        }
        rankings = {method: order(values) for method, values in scores.items()}
        rows.append({
            "claim_id": pair.claim_id,
            "doc_id": pair.doc_id,
            "component": pair.component,
            "rankings": {method: ranking.tolist() for method, ranking in rankings.items()},
            "outcomes": {method: outcomes(pair, ranking) for method, ranking in rankings.items()},
        })
    return rows


def summarize(rows):
    methods = list(rows[0]["outcomes"])
    observed = np.array([[row["outcomes"][method] for method in methods] for row in rows])
    means = observed.mean(axis=0)
    deltas = observed[:, [methods.index("learned")], :] - observed[:, [methods.index(c) for c in CONTROLS], :]
    grouped = defaultdict(list)
    for row, delta in zip(rows, deltas, strict=True):
        grouped[row["component"]].append(delta)
    clusters = [grouped[key] for key in sorted(grouped)]
    cluster_sums = np.array([np.sum(cluster, axis=0) for cluster in clusters])
    counts = np.array([len(cluster) for cluster in clusters])
    rng = np.random.default_rng(20261121)
    draws = rng.integers(len(counts), size=(10000, len(counts)))
    boot = cluster_sums[draws].sum(axis=1) / counts[draws].sum(axis=1)[:, None, None]
    primary = np.quantile(boot[:, :, 0], [0.025 / len(CONTROLS), 1 - 0.025 / len(CONTROLS)], axis=0)
    secondary = np.quantile(boot[:, :, 1], [0.025, 0.975], axis=0)
    gain = deltas.mean(axis=0)
    return {
        "metrics": {
            method: {"mrr": mrr, "recall_at_3": recall}
            for method, (mrr, recall) in zip(methods, means.tolist(), strict=True)
        },
        "learned_minus_control": {
            control: {
                "mrr_difference": gain[i, 0],
                "mrr_familywise_95_ci": primary[:, i].tolist(),
                "recall_at_3_difference": gain[i, 1],
                "recall_at_3_95_ci": secondary[:, i].tolist(),
            }
            for i, control in enumerate(CONTROLS)
        },
        "passed_screen": bool((primary[0] > 0).all()),
    }


def run(archive, out):
    protocol = sha256(STUDY / "protocol.md")
    if protocol != (STUDY / "protocol.sha256").read_text().split()[0]:
        raise ValueError("Protocol checksum mismatch")

    splits = partition(*load(archive))
    fit_logits, fit_counts = fit_prior(splits["fit"])
    bm25, mixture, weights, selection = select(splits["selection"], fit_logits)
    final_logits, final_counts = fit_prior(splits["fit"] + splits["selection"])
    rows = score(splits["screen"], final_logits, bm25, mixture, weights)
    result = {
        "archive_sha256": ARCHIVE_SHA256,
        "protocol_sha256": protocol,
        "partitions": {
            name: {
                "pairs": len(pairs),
                "claims": len({pair.claim_id for pair in pairs}),
                "evidence_documents": len({pair.doc_id for pair in pairs}),
                "source_components": len({pair.component for pair in pairs}),
            }
            for name, pairs in splits.items()
        },
        "prior_counts": {"fit": fit_counts, "fit_plus_selection": final_counts},
        "selection": selection,
        **summarize(rows),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    with (out / "predictions.jsonl").open("w") as stream:
        for row in rows:
            stream.write(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path("private_data/raw/scifact/data.tar.gz"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.archive, args.out)


if __name__ == "__main__":
    main()
