"""P11: Baseline models for historical reasoning rubric evaluation.

C0: Keyword / Heuristic baseline.
C1: Standard Analytic Rubric without span anchors or targeted arbitration.
B*: Standard Analytic Rubric with random sample adjudication.
"""
from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np

from research_v4_2.papers.p11.method import (
    FACETS,
    RaterAssessment,
    StudentArgument,
    ConsensusVerdict,
)


class C0KeywordBaseline:
    """C0: Word count & superficial keyword presence heuristic."""

    def __init__(self):
        self.keywords = [
            "cửu đỉnh",
            "châu bản",
            "minh mạng",
            "triều nguyễn",
            "khắc",
            "đồng",
            "thực lục",
            "nghiên cứu",
        ]

    def score_single_rater(
        self,
        argument: StudentArgument,
        rater_id: str = "c0",
        noise_level: float = 0.3,
        seed: Optional[int] = None,
    ) -> RaterAssessment:
        rng = np.random.default_rng(seed)
        text_lower = argument.text.lower()
        kw_hits = sum(1 for kw in self.keywords if kw in text_lower)
        word_count = len(text_lower.split())

        base_score = min(3, int(kw_hits // 2) + int(word_count > 40))
        scores = {}
        for facet in FACETS:
            perturbed = base_score + rng.normal(0, noise_level)
            scores[facet] = int(round(np.clip(perturbed, 0, 3)))

        return RaterAssessment(
            rater_id=rater_id,
            response_id=argument.response_id,
            scores=scores,
            anchors_cited={},
            caps_applied=[],
            flagged_fabrication=False,
            scoring_time_sec=15.0,
        )


class C1StandardAnalyticRubric:
    """C1: Standard generic analytic rubric without evidence-span anchors or caps."""

    def __init__(self, rater_subjectivity_sigma: float = 0.55):
        self.sigma = rater_subjectivity_sigma

    def score_single_rater(
        self,
        argument: StudentArgument,
        rater_id: str,
        rater_bias: float = 0.0,
        seed: Optional[int] = None,
    ) -> RaterAssessment:
        rng = np.random.default_rng(seed)

        # Baseline raters estimate quality without verifying span provenance
        # They are vulnerable to fabricated citations appearing impressive
        total_spans = sum(len(c.spans) for c in argument.claims)
        has_citations = total_spans > 0

        # Impressionistic scoring
        scores = {}
        for facet in FACETS:
            # Rater subjective impression
            latent = 1.0 + (1.0 if has_citations else 0.0) + (0.5 if len(argument.claims) >= 2 else 0.0)
            score_val = latent + rater_bias + rng.normal(0, self.sigma)
            scores[facet] = int(round(np.clip(score_val, 0, 3)))

        return RaterAssessment(
            rater_id=rater_id,
            response_id=argument.response_id,
            scores=scores,
            anchors_cited={},
            caps_applied=[],
            flagged_fabrication=False,
            scoring_time_sec=60.0 + rng.uniform(-10.0, 10.0),
        )


class BaselineChampionBStar:
    """B*: Standard analytic rubric with random 20% sample adjudication."""

    def __init__(self, sample_adjudication_rate: float = 0.20, rater_subjectivity_sigma: float = 0.55):
        self.c1 = C1StandardAnalyticRubric(rater_subjectivity_sigma=rater_subjectivity_sigma)
        self.sample_rate = sample_adjudication_rate

    def score_single_rater(
        self,
        argument: StudentArgument,
        rater_id: str,
        rater_bias: float = 0.0,
        seed: Optional[int] = None,
    ) -> RaterAssessment:
        return self.c1.score_single_rater(argument, rater_id, rater_bias, seed)

    def evaluate_cohort(
        self,
        arguments: List[StudentArgument],
        raters: List[str],
        seed: int = 42,
    ) -> List[ConsensusVerdict]:
        rng = np.random.default_rng(seed)
        results = []

        for arg in arguments:
            assessments = [
                self.score_single_rater(arg, rater_id=r, rater_bias=rng.uniform(-0.2, 0.2), seed=seed + i)
                for i, r in enumerate(raters)
            ]

            # In B*, 20% random sample is sent to adjudication regardless of disagreement
            is_adjudicated = rng.random() < self.sample_rate
            final_scores = {}
            for facet in FACETS:
                vals = [a.scores[facet] for a in assessments]
                if is_adjudicated:
                    # Adjudication provides median of raters (no evidence-grounded anchors)
                    final_scores[facet] = int(round(float(np.median(vals))))
                else:
                    final_scores[facet] = int(round(float(np.mean(vals))))

            overall = float(np.mean(list(final_scores.values())))
            results.append(
                ConsensusVerdict(
                    response_id=arg.response_id,
                    final_scores=final_scores,
                    overall_score=overall,
                    arbitrated=is_adjudicated,
                    arbitrated_facets=FACETS if is_adjudicated else [],
                    caps_applied=[],
                    discrepancy_score=float(max(vals) - min(vals)),
                    rater_count=len(raters),
                )
            )

        return results
