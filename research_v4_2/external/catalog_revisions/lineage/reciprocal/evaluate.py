"""Predict heading lineage on the frozen PEP and Sphinx development cohorts."""
import argparse
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from itertools import chain
import json
from math import log, sqrt
from pathlib import Path
import re
import subprocess
import sys

from scipy.optimize import linear_sum_assignment


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))
from lineage.evaluate import HEADING, RIGHTS  # noqa: E402


MIN_SCORE = 0.20
METHODS = {
    "text": ("text", False),
    "position": ("position", False),
    "locked": ("text", True),
    "anchored": ("position", True),
    "locked_content": ("content", True),
}


def read_sections(repo, blob, project):
    source = subprocess.check_output(
        ["git", "-C", repo, "cat-file", "blob", blob]
    ).decode("utf8", "replace")
    if project == "peps" and not RIGHTS.search(source):
        raise ValueError(f"No public-domain declaration in {blob}")
    matches = list(HEADING.finditer(source))
    ends = [m.start() for m in matches[1:]] + [len(source)]
    return [(m[1], m[2], m[3], source[m.end():end]) for m, end in zip(matches, ends)]


def masked_sections(old, new):
    labels = {label.casefold() for label, *_ in chain(old, new) if label}
    ordered = sorted(labels, key=lambda s: (-len(s), s))
    mask = re.compile("|".join(map(re.escape, ordered))) if ordered else None

    def clean(text):
        folded = text.casefold()
        return mask.sub(" ", folded) if mask else folded

    return [
        [(clean(title), style, re.findall(r"\w+", clean(body)))
         for _, title, style, body in sections]
        for sections in (old, new)
    ]


def context_tokens(sections):
    levels = list(dict.fromkeys(style for _, style, _ in sections))
    stack = []
    siblings = defaultdict(list)
    for index, (_, style, _) in enumerate(sections):
        level = levels.index(style)
        while stack and stack[-1][0] >= level:
            stack.pop()
        parent = stack[-1][1] if stack else None
        siblings[parent].append(index)
        stack.append((level, index))
    context = [set() for _ in sections]
    for parent, group in siblings.items():
        for pos, index in enumerate(group):
            neighbors = group[max(0, pos - 1):pos] + group[pos + 1:pos + 2]
            if parent is not None:
                neighbors.append(parent)
            context[index] = set(re.findall(r"\w+", " ".join(sections[i][0] for i in neighbors)))
    return context


def tfidf_vectors(sections):
    counts = [Counter(words) for _, _, words in sections]
    # Count each token once per section.
    df = Counter(word for count in counts for word in count)
    vectors = []
    for count in counts:
        vector = {
            word: (1 + log(frequency)) * (1 + log((1 + len(counts)) / (1 + df[word])))
            for word, frequency in count.items()
        }
        norm = sqrt(sum(weight * weight for weight in vector.values()))
        vectors.append({word: weight / norm for word, weight in vector.items()})
    return vectors


def jaccard(a, b):
    return len(a & b) / max(1, len(a | b))


def unchanged_anchors(old, new):
    old_titles, new_titles = ([title.strip() for title, _, _ in side] for side in (old, new))
    old_counts, new_counts = map(Counter, (old_titles, new_titles))
    destinations = {title: j for j, title in enumerate(new_titles)}
    return {
        i: destinations[title]
        for i, title in enumerate(old_titles)
        if title and old_counts[title] == new_counts[title] == 1
    }


def projected_position(source, anchors):
    """Project within flanking anchors, or by offset from the nearest one."""
    left = next((i for i in reversed(anchors) if i < source), None)
    right = next((i for i in anchors if i > source), None)
    if left is not None and right is not None:
        return anchors[left] + (source - left) * (anchors[right] - anchors[left]) / (right - left)
    neighbor = left if left is not None else right
    return None if neighbor is None else source + anchors[neighbor] - neighbor


def score_matrices(old, new, anchors):
    old_context, new_context = map(context_tokens, (old, new))
    old_early, new_early = ([set(words[:80]) for _, _, words in side] for side in (old, new))
    vectors = tfidf_vectors(old + new)
    scores = {metric: [] for metric in ("title", "content", "full_content", "context", "text", "position")}
    for i, (title, _, _) in enumerate(old):
        projected = projected_position(i, anchors)
        if projected is not None:
            projected = max(0, min(len(new) - 1, projected))
        for matrix in scores.values():
            matrix.append([])
        for j, (target, _, _) in enumerate(new):
            lexical = SequenceMatcher(None, title, target).ratio()
            early = jaccard(old_early[i], new_early[j])
            body = sum(weight * vectors[len(old) + j].get(word, 0.0)
                       for word, weight in vectors[i].items())
            context = jaccard(old_context[i], new_context[j])
            total = lexical + body + context
            position = (total + 1 / (1 + abs(projected - j))) / 4 if projected is not None else total / 3
            for metric, value in zip(scores, (lexical, early, body, context, total / 3, position)):
                scores[metric][-1].append(value)
    return scores


def match(matrix, locks):
    """Return independent and maximum-weight assignments on the same residual graph."""
    sources = [i for i in range(len(matrix)) if i not in locks]
    reserved = set(locks.values())
    destinations = [j for j in range(len(matrix[0])) if j not in reserved]
    independent = dict(locks)
    joint = dict(locks)
    if not sources:
        return independent, joint

    utilities = [
        [round(matrix[i][j] - MIN_SCORE, 10) for j in destinations] + [0.0] * len(sources)
        for i in sources
    ]
    for i, row in zip(sources, utilities):
        best = max(range(len(destinations)), key=row.__getitem__, default=None)
        independent[i] = destinations[best] if best is not None and row[best] > 0 else None
    rows, columns = linear_sum_assignment(utilities, maximize=True)
    for row, column in zip(rows, columns):
        joint[sources[row]] = destinations[column] if column < len(destinations) and utilities[row][column] > 0 else None
    return independent, joint


def collisions(predictions):
    counts = Counter(pred for pred in predictions if pred is not None)
    return {destination: count for destination, count in sorted(counts.items()) if count > 1}


def label_swap(old, new, rows):
    """Find a competing labeled pair whose gold can flip with identical features."""
    by_choice = defaultdict(list)
    for row in rows:
        by_choice[row["predictions"]["independent_full_content"]].append(row)
    for group in by_choice.values():
        if len(group) != 2:
            continue
        first, second = group
        i, k = first["source"], second["source"]
        j, l = first["target"], second["target"]
        if j == l or old[i][1] == new[l][1] or old[k][1] == new[j][1]:
            continue
        swapped = new.copy()
        swapped[j] = (new[l][0], *new[j][1:])
        swapped[l] = (new[j][0], *new[l][1:])
        if masked_sections(old, new) != masked_sections(old, swapped):
            raise ValueError("Swapping destination labels changed the masked input")
        return {"observed": [[i, j], [k, l]], "counterfactual": [[i, l], [k, j]]}
    return None


def joint_gold_gap(matrix, anchors, rows, joint):
    gold = {row["source"]: row["target"] for row in rows}
    forced = anchors | gold
    if any(forced[i] != j for i, j in anchors.items()) or len(forced) != len(set(forced.values())):
        return None

    def objective(mapping):
        return sum(round(matrix[i][j] - MIN_SCORE, 10) for i, j in mapping.items()
                   if i not in anchors and j is not None)

    _, solution = match(matrix, forced)
    return round(objective(joint) - objective(solution), 10)


def evaluate_revision(repo, project, references):
    first = references[0]
    old, new = [read_sections(repo, blob, project) for blob in first["blobs"]]
    masked_old, masked_new = masked_sections(old, new)
    anchors = unchanged_anchors(masked_old, masked_new)
    scores = score_matrices(masked_old, masked_new, anchors)
    predictions = {}
    for name, (metric, lock) in METHODS.items():
        independent, joint = match(scores[metric], anchors if lock else {})
        predictions[f"independent_{name}"] = independent
        predictions[f"global_{name}"] = joint
        assigned = [j for j in joint.values() if j is not None]
        if len(set(assigned)) != len(assigned):
            raise ValueError(f"Non-injective assignment for {name}")

    residual = {i: j for i, j in predictions["independent_anchored"].items() if i not in anchors}
    body = scores["full_content"]
    rows = []
    for ref in references:
        i, j = ref["source"], ref["target"]
        label = ref["label"]
        if not (ref["blobs"] == first["blobs"] and ref["candidates"] == len(new)
                and old[i][0] == new[j][0] == label
                and [old[i][1], new[j][1]] == ref["titles"]
                and all(sum(section[0] == label for section in side) == 1 for side in (old, new))):
            raise ValueError(f"Frozen label does not match the Git blobs: {ref}")
        content = max(range(len(new)), key=scores["content"][i].__getitem__)
        if content != ref["predictions"]["content"]:
            raise ValueError(f"Published content prediction failed reproduction: {ref}")
        best_body = max(range(len(new)), key=body[i].__getitem__)
        body_ties = sum(abs(value - body[i][best_body]) <= 1e-10 for value in body[i])
        rows.append({
            **{key: ref[key] for key in ("source", "target", "hard")},
            "predictions": {
                **{f"published_{k}": v for k, v in ref["predictions"].items()},
                "independent_full_content": best_body,
                **{name: mapping[i] for name, mapping in predictions.items()},
            },
            "source_locked_to": anchors.get(i),
            "target_locked_from": next((k for k, v in anchors.items() if v == j), None),
            "body_top_ties": body_ties,
            "body_score_at_target": round(body[i][j], 6),
            "body_score_at_top": round(body[i][best_body], 6),
        })
    result = {
        **{key: first[key] for key in ("path", "commit", "blobs")},
        "source_headings": len(old),
        "destination_headings": len(new),
        "anchors": len(anchors),
        "residual_collisions": collisions(residual.values()),
        "labeled_collisions": {
            name: collisions(row["predictions"][name] for row in rows)
            for name in ("published_content", "published_combined", "independent_full_content", "independent_anchored")
        },
        "rows": rows,
    }
    if len(rows) > 1:
        result["forced_gold_objective_gap"] = joint_gold_gap(
            scores["position"], anchors, rows, predictions["global_anchored"]
        )
        witness = label_swap(old, new, rows)
        if witness:
            result["label_swap_witness"] = witness
    return result


def evaluate(repo, project, frozen):
    by_revision = defaultdict(list)
    for row in frozen["rows"]:
        by_revision[row["commit"], row["path"]].append(row)
    revisions = [evaluate_revision(repo, project, refs) for refs in by_revision.values()]
    by_file = defaultdict(list)
    for revision in revisions:
        by_file[revision["path"]].extend(revision["rows"])
    rows = list(chain.from_iterable(by_file.values()))
    metrics = {}
    for method in rows[0]["predictions"]:
        def hits(group):
            return sum(row["predictions"][method] == row["target"] for row in group)
        metrics[method] = {
            "correct": hits(rows),
            "equal_file_accuracy": round(sum(hits(g) / len(g) for g in by_file.values()) / len(by_file), 6),
            "hard_correct": hits([row for row in rows if row["hard"]]),
        }

    return {
        "cohort": "development",
        "start": frozen["start"],
        "end": frozen["end"],
        "resolved": len(rows),
        "hard": frozen["hard"],
        "censored": len(frozen["censored"]),
        "revisions": len(revisions),
        "files": len(by_file),
        "multi_label_revisions": sum(len(rev["rows"]) > 1 for rev in revisions),
        "residual_collision_revisions": sum(bool(rev["residual_collisions"]) for rev in revisions),
        "anchored_assignment_changes": sum(
            row["predictions"]["global_anchored"] != row["predictions"]["independent_anchored"]
            for row in rows
        ),
        "metrics": metrics,
        "predictions": revisions,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("peps_repo", type=Path)
    parser.add_argument("sphinx_repo", type=Path)
    args = parser.parse_args()
    results = {
        project: evaluate(repo, project, json.loads((ROOT / "transfer" / f"{project}.json").read_text()))
        for project, repo in (("peps", args.peps_repo), ("sphinx", args.sphinx_repo))
    }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
