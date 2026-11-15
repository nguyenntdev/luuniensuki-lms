"""V3-G08: blind-adjudication annotation schema + agreement helpers.

Pure functions, tested with toy data. Provides:

- :class:`AnnotationItem` / :class:`AnnotatorDecision`: the blind-adjudication
  schema. Annotator ids are opaque tokens supplied by the caller — this module
  NEVER fabricates annotator ids, and decisions record the blindness contract
  (whether the annotator saw any condition label).
- :func:`cohen_kappa` — chance-corrected agreement for 2 annotators.
- :func:`krippendorff_alpha` — nominal/ordinal/interval data, >=2 annotators,
  with the standard coincidence-matrix formulation.
- :func:`blind_adjudication_report` — agreement + ALL disagreement rows
  (adjudication candidates), with gold access controls left to the caller.

Values in [0, 1] convention: kappa/alpha < 0 possible for chance-worse
agreement and are reported verbatim (never clamped).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence


class AnnotationError(ValueError):
    """Raised when annotation records violate the blind-adjudication schema."""


@dataclass(frozen=True)
class AnnotationItem:
    item_id: str
    task_id: str
    blind: bool = True
    condition_label: str | None = None  # revealed only after adjudication


@dataclass(frozen=True)
class AnnotatorDecision:
    item_id: str
    annotator_token: str  # opaque caller-supplied token; never generated here
    label: str
    blind: bool = True
    notes: str = ""


@dataclass(frozen=True)
class AdjudicationReport:
    n_items: int
    n_annotators: int
    labels: tuple[str, ...]
    kappa: float | None
    alpha: float | None
    agreement_rate: float | None
    disagreements: tuple[dict[str, Any], ...] = field(default_factory=tuple)


def validate_decisions(decisions: Sequence[AnnotatorDecision]) -> None:
    if not decisions:
        raise AnnotationError("no annotator decisions provided")
    for d in decisions:
        if not d.annotator_token:
            raise AnnotationError(f"item {d.item_id}: empty annotator token (never fabricate ids)")
        if not d.label:
            raise AnnotationError(f"item {d.item_id}: empty label from {d.annotator_token!r}")
        if not d.blind:
            raise AnnotationError(
                f"item {d.item_id}: non-blind decision rejected — the blind-adjudication "
                "schema requires blind=True; reveal conditions only after adjudication"
            )


def cohen_kappa(labels_a: Sequence[str], labels_b: Sequence[str]) -> float | None:
    """Cohen's kappa for two aligned raters. None when undefined (degenerate)."""
    if len(labels_a) != len(labels_b):
        raise AnnotationError("aligned raters must have equal length")
    n = len(labels_a)
    if n == 0:
        return None
    categories = sorted(set(labels_a) | set(labels_b))
    if len(categories) < 2:
        return None
    po = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n
    pe = sum(
        (labels_a.count(c) / n) * (labels_b.count(c) / n) for c in categories
    )
    if pe == 1.0:
        return None  # completely degenerate marginals
    return (po - pe) / (1 - pe)


def krippendorff_alpha(
    units: Sequence[Mapping[str, str]],
    *,
    level: str = "nominal",
) -> float | None:
    """Krippendorff's alpha via the coincidence formulation.

    ``units`` is a sequence of mappings annotator_token -> label (missing keys
    = unrated by that annotator). Supports nominal, ordinal and interval
    distances. Returns None when there is not enough data (fewer than 2 rated
    units). Values below 0.0 (chance-worse agreement) are reported verbatim.
    """
    if level not in {"nominal", "ordinal", "interval"}:
        raise AnnotationError(f"unknown level {level!r}")
    rated = [dict(u) for u in units if len(u) >= 2]
    if len(rated) < 2:
        return None

    def distance(a, b) -> float:
        if level == "nominal":
            return 0.0 if a == b else 1.0
        x, y = float(a), float(b)
        if level == "ordinal":
            return abs(x - y)
        return (x - y) ** 2

    # pairable values
    n_v = sum(len(u) for u in rated)
    if n_v < 3:
        return None

    do = 0.0
    n_pairs = 0
    for u in rated:
        items = list(u.items())
        m_u = len(items)
        for i in range(m_u):
            for j in range(i + 1, m_u):
                do += distance(items[i][1], items[j][1])
                n_pairs += 1
    if n_pairs == 0:
        return None
    do /= n_pairs

    # expected disagreement from the pooled distribution of all values
    all_values = [v for u in rated for v in u.values()]
    de_sum = 0.0
    de_pairs = 0
    for i in range(len(all_values)):
        for j in range(i + 1, len(all_values)):
            de_sum += distance(all_values[i], all_values[j])
            de_pairs += 1
    if de_pairs == 0:
        return None
    de = de_sum / de_pairs
    if de == 0.0:
        # every pair identical -> perfect agreement
        return 1.0
    return 1.0 - do / de


def blind_adjudication_report(
    decisions: Sequence[AnnotatorDecision],
    items: Mapping[str, AnnotationItem],
    *,
    level: str = "nominal",
) -> AdjudicationReport:
    """Agreement + all disagreements for a blind adjudication round."""
    validate_decisions(decisions)
    by_item: dict[str, dict[str, str]] = {}
    for d in decisions:
        if d.item_id not in items:
            raise AnnotationError(f"decision for unknown item {d.item_id!r}")
        if d.blind != items[d.item_id].blind:
            raise AnnotationError(
                f"item {d.item_id}: decision blindness {d.blind} != item blindness "
                f"{items[d.item_id].blind} — the blind contract must match"
            )
        by_item.setdefault(d.item_id, {})[d.annotator_token] = d.label

    tokens = sorted({d.annotator_token for d in decisions})
    labels_seen = sorted({d.label for d in decisions})

    # kappa on the two lowest-token annotators over jointly-rated items
    kappa: float | None = None
    if len(tokens) >= 2:
        a, b = tokens[0], tokens[1]
        joint = sorted(set(by_item) & {i for i, m in by_item.items() if a in m and b in m})
        la = [by_item[i][a] for i in joint]
        lb = [by_item[i][b] for i in joint]
        kappa = cohen_kappa(la, lb)

    alpha = krippendorff_alpha(list(by_item.values()), level=level)

    disagreements: list[dict[str, Any]] = []
    for item_id in sorted(by_item):
        votes = by_item[item_id]
        if len(set(votes.values())) > 1:
            disagreements.append({"item_id": item_id, "votes": dict(sorted(votes.items()))})

    agreement_rate: float | None = None
    if by_item:
        unanimous = sum(1 for v in by_item.values() if len(set(v.values())) == 1)
        agreement_rate = unanimous / len(by_item)

    return AdjudicationReport(
        n_items=len(by_item),
        n_annotators=len(tokens),
        labels=tuple(labels_seen),
        kappa=kappa,
        alpha=alpha,
        agreement_rate=agreement_rate,
        disagreements=tuple(disagreements),
    )
