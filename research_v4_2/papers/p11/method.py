"""P11: Reliability-aware historical reasoning rubric with evidence-path decision anchors and active arbitration.

Winning Candidate Method for V4.2.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import math
import numpy as np


class InferenceType(str, Enum):
    DIRECT_OBSERVATION = "direct_observation"
    CAUSAL = "causal"
    CONTEXTUAL = "contextual"


@dataclass
class EvidenceSpan:
    span_id: str
    text: str
    source_id: str
    locator: str  # e.g., "Châu bản triều Nguyễn, Minh Mạng tập 12, tr. 45"
    verified: bool
    confidence: float = 1.0


@dataclass
class HistoricalClaim:
    claim_id: str
    statement: str
    inference_type: InferenceType
    spans: List[EvidenceSpan] = field(default_factory=list)


@dataclass
class StudentArgument:
    response_id: str
    student_id: str
    prompt_id: str
    text: str
    claims: List[HistoricalClaim] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


FACETS = [
    "authenticity",
    "temporal_placement",
    "corroboration",
    "counterevidence_handling",
]

DECISION_ANCHORS: Dict[str, Dict[int, str]] = {
    "authenticity": {
        0: "No authentic artifacts or sources identified; claims ungrounded.",
        1: "Mentions authentic relics/documents but with superficial or partially inaccurate attributes.",
        2: "Accurately references authentic primary artifacts (e.g. Cửu Đỉnh motifs, Châu bản records).",
        3: "Exemplary identification of primary artifacts with rigorous provenance and physical/epigraphic detail.",
    },
    "temporal_placement": {
        0: "Anachronistic assertions; conflates eras or reigns without awareness.",
        1: "Basic chronological placement with occasional misattribution of reign dates.",
        2: "Accurate placement within correct reign/dynastic period (e.g., Minh Mạng 1835-1837 for Cửu Đỉnh).",
        3: "Nuanced understanding of temporal trajectory, promulgation context, and administrative timing.",
    },
    "corroboration": {
        0: "Isolated assertion with zero cross-referencing.",
        1: "Cites single source or secondary summary without cross-verification.",
        2: "Cross-references at least two distinct sources (e.g. bronze relief rubbing + Châu bản imperial edict).",
        3: "Synthesizes multi-modal archival and material records, addressing concordance and nuance.",
    },
    "counterevidence_handling": {
        0: "Ignores conflicting evidence or historiographical uncertainty.",
        1: "Acknowledges uncertainty or alternative claim only when explicitly prompted.",
        2: "Explicitly evaluates competing interpretations, unconfirmed motifs, or lacunae in archival records.",
        3: "Critically evaluates provenance limits, historiographical controversies, and biases in official annals.",
    },
}


@dataclass
class RaterAssessment:
    rater_id: str
    response_id: str
    scores: Dict[str, int]
    anchors_cited: Dict[str, str] = field(default_factory=dict)
    caps_applied: List[str] = field(default_factory=list)
    flagged_fabrication: bool = False
    scoring_time_sec: float = 0.0


@dataclass
class ConsensusVerdict:
    response_id: str
    final_scores: Dict[str, int]
    overall_score: float
    arbitrated: bool
    arbitrated_facets: List[str]
    caps_applied: List[str]
    discrepancy_score: float
    rater_count: int


def compute_krippendorff_alpha(ratings: np.ndarray, level_of_measurement: str = "ordinal") -> float:
    """Compute Krippendorff's alpha for rater reliability.
    
    ratings: 2D array of shape (n_raters, n_items). NaN represents missing ratings.
    """
    ratings = np.asarray(ratings, dtype=float)
    n_raters, n_items = ratings.shape

    # Find unique values across all valid entries
    valid_mask = ~np.isnan(ratings)
    unique_vals = np.unique(ratings[valid_mask])
    if len(unique_vals) <= 1:
        return 1.0

    # Build coincidence matrix
    val_to_idx = {v: i for i, v in enumerate(unique_vals)}
    n_vals = len(unique_vals)
    coincidence = np.zeros((n_vals, n_vals), dtype=float)

    for col in range(n_items):
        col_vals = ratings[:, col]
        valid_col = col_vals[~np.isnan(col_vals)]
        m_u = len(valid_col)
        if m_u <= 1:
            continue
        weight = 1.0 / (m_u - 1)
        for i in range(m_u):
            for j in range(m_u):
                if i != j:
                    idx_i = val_to_idx[valid_col[i]]
                    idx_j = val_to_idx[valid_col[j]]
                    coincidence[idx_i, idx_j] += weight

    n_pairs = np.sum(coincidence)
    if n_pairs == 0:
        return 0.0

    # Marginal totals
    marginals = np.sum(coincidence, axis=1)

    # Difference metric matrix
    delta = np.zeros((n_vals, n_vals), dtype=float)
    if level_of_measurement == "ordinal":
        # Ordinal distance
        for i in range(n_vals):
            for j in range(n_vals):
                if i < j:
                    # sum of marginals between i and j
                    mid_sum = np.sum(marginals[i : j + 1]) - (marginals[i] + marginals[j]) / 2.0
                    delta[i, j] = mid_sum ** 2
                    delta[j, i] = delta[i, j]
    else:  # interval
        for i in range(n_vals):
            for j in range(n_vals):
                delta[i, j] = (unique_vals[i] - unique_vals[j]) ** 2

    # Observed and expected disagreement
    d_obs = np.sum(coincidence * delta) / n_pairs
    d_exp = 0.0
    for i in range(n_vals):
        for j in range(n_vals):
            d_exp += marginals[i] * marginals[j] * delta[i, j]
    d_exp /= (n_pairs * (n_pairs - 1)) if n_pairs > 1 else 1.0

    if d_exp == 0.0:
        return 1.0
    alpha = 1.0 - (d_obs / d_exp)
    return float(alpha)


class EvidenceAnchoredAdjudicationRubric:
    """Proposed candidate winning scoring method (P11 V4.2).
    
    Combines:
    1. Structured decision-anchored grading per facet (0-3 scale).
    2. Span verification and fabrication penalty caps (CC01, CC05).
    3. Uncertainty / discrepancy-triggered active arbitration on divergent facets only.
    """

    def __init__(self, discrepancy_threshold: float = 1.0):
        self.discrepancy_threshold = discrepancy_threshold

    def score_single_rater(
        self,
        argument: StudentArgument,
        rater_id: str,
        rater_bias: float = 0.0,
        noise_level: float = 0.1,
        seed: Optional[int] = None,
    ) -> RaterAssessment:
        """Scores an argument using explicit evidence-anchored criteria."""
        rng = np.random.default_rng(seed)

        # 1. Evidence analysis
        total_claims = len(argument.claims)
        total_spans = sum(len(c.spans) for c in argument.claims)
        verified_spans = sum(sum(1 for s in c.spans if s.verified) for c in argument.claims)
        fabricated_spans = total_spans - verified_spans

        caps = []
        is_fabricated = fabricated_spans > 0

        # Calculate base ground-truth competence from argument structure
        scores: Dict[str, int] = {}
        anchors: Dict[str, str] = {}

        # Authenticity
        if total_spans == 0:
            auth_score = 0
            caps.append("CAP_ZERO_EVIDENCE_AUTH")
        elif is_fabricated:
            auth_score = min(1, 1 if total_claims > 0 else 0)
            caps.append("CAP_FABRICATION_AUTH")
        else:
            auth_score = 3 if verified_spans >= 3 else (2 if verified_spans >= 2 else 1)

        # Temporal placement
        has_temporal = any(
            any("183" in s.locator or "Minh Mạng" in s.locator or "18" in s.locator for s in c.spans)
            for c in argument.claims
        )
        if total_spans == 0:
            temp_score = 0
            caps.append("CAP_ZERO_EVIDENCE_TEMP")
        else:
            temp_score = 3 if (has_temporal and verified_spans >= 2) else (2 if has_temporal else 1)

        # Corroboration
        distinct_sources = len({s.source_id for c in argument.claims for s in c.spans if s.verified})
        if distinct_sources >= 2 and not is_fabricated:
            corrob_score = 3 if distinct_sources >= 3 else 2
        elif distinct_sources == 1 and not is_fabricated:
            corrob_score = 1
        else:
            corrob_score = 0
            if is_fabricated:
                caps.append("CAP_FABRICATION_CORROB")

        # Counterevidence handling
        has_counter = any(
            c.inference_type == InferenceType.CONTEXTUAL or "unconfirmed" in c.statement.lower() or "tranh cãi" in c.statement.lower() or "dị bản" in c.statement.lower()
            for c in argument.claims
        )
        if has_counter and verified_spans >= 2:
            counter_score = 3 if distinct_sources >= 2 else 2
        elif has_counter:
            counter_score = 1
        else:
            counter_score = 0

        raw_scores = {
            "authenticity": auth_score,
            "temporal_placement": temp_score,
            "corroboration": corrob_score,
            "counterevidence_handling": counter_score,
        }

        # Apply slight rater subjectivity / noise anchored around criteria
        for facet, base_val in raw_scores.items():
            perturbed = base_val + rater_bias + rng.normal(0, noise_level)
            clamped = int(round(np.clip(perturbed, 0, 3)))
            # Enforce hard caps strictly
            if "CAP_ZERO_EVIDENCE_AUTH" in caps and facet == "authenticity":
                clamped = 0
            if "CAP_FABRICATION_AUTH" in caps and facet == "authenticity":
                clamped = min(clamped, 1)
            if "CAP_FABRICATION_CORROB" in caps and facet == "corroboration":
                clamped = min(clamped, 1)
            scores[facet] = clamped
            anchors[facet] = DECISION_ANCHORS[facet][clamped]

        # Simulated scoring time: anchored rubric is faster because criteria are explicit
        time_spent = 45.0 + rng.uniform(-5.0, 5.0)

        return RaterAssessment(
            rater_id=rater_id,
            response_id=argument.response_id,
            scores=scores,
            anchors_cited=anchors,
            caps_applied=caps,
            flagged_fabrication=is_fabricated,
            scoring_time_sec=time_spent,
        )

    def arbitrate_assessments(
        self,
        argument: StudentArgument,
        assessments: List[RaterAssessment],
    ) -> ConsensusVerdict:
        """Active arbitration of low-agreement facets."""
        if not assessments:
            raise ValueError("Assessments list cannot be empty")

        response_id = argument.response_id
        final_scores: Dict[str, int] = {}
        arbitrated_facets: List[str] = []
        all_caps = sorted(list({cap for a in assessments for cap in a.caps_applied}))

        max_discrepancy = 0.0

        for facet in FACETS:
            facet_vals = [a.scores[facet] for a in assessments]
            diff = max(facet_vals) - min(facet_vals)
            if diff > max_discrepancy:
                max_discrepancy = float(diff)

            if diff >= self.discrepancy_threshold:
                # Active arbitration required on this facet
                arbitrated_facets.append(facet)
                # Adjudication resolves by consulting the authoritative evidence anchors
                auth_assessment = self.score_single_rater(argument, rater_id="adjudicator", noise_level=0.0)
                final_scores[facet] = auth_assessment.scores[facet]
            else:
                # Raters in agreement; take consensus median/rounded mean
                final_scores[facet] = int(round(float(np.median(facet_vals))))

        overall = float(np.mean(list(final_scores.values())))
        return ConsensusVerdict(
            response_id=response_id,
            final_scores=final_scores,
            overall_score=overall,
            arbitrated=len(arbitrated_facets) > 0,
            arbitrated_facets=arbitrated_facets,
            caps_applied=all_caps,
            discrepancy_score=max_discrepancy,
            rater_count=len(assessments),
        )
