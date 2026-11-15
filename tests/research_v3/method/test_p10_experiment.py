"""P10 experiment/report tests (P10-T12/T14/T15): metrics, CIs, fail-closed run."""
from __future__ import annotations

from research_v3.eval.statistics import proportion_ci
from research_v3.methods.p10.experiment import run_matrix


class TestRunMatrix:
    def test_primary_metric_structure(self):
        payload = run_matrix(seed=42)
        m1 = payload["metrics"]["M1_sequence_validity_rate"]
        assert m1["n"] == 3  # C0, C1, proposed
        assert 0 <= m1["successes"] <= m1["n"]
        lo, hi = m1["wilson_ci_95"]
        assert 0.0 <= lo <= hi <= 1.0

    def test_anchor_counts_present_and_honest(self):
        payload = run_matrix(seed=42)
        reg = payload["anchor_registry"]
        assert reg["documented"] == 3
        assert reg["needs_expert_review"] == 27
        assert reg["total_anchors"] == 30

    def test_h0_and_blocked_tasks_declared(self):
        payload = run_matrix(seed=42)
        assert "BLOCKED" in payload["hypothesis_h0"]
        honesty = " ".join(payload["honesty_notes"])
        assert "NOT pedagogical endorsement" in honesty
        assert "needs_expert_review" in honesty

    def test_designs_include_all_five_families(self):
        payload = run_matrix(seed=42)
        ids = [d["design_id"] for d in payload["designs"]]
        assert any(i.startswith("C0") for i in ids)
        assert any(i.startswith("C1") for i in ids)
        assert any(i.startswith("proposed") for i in ids)
        assert any(i.startswith("A1") for i in ids)
        assert any(i.startswith("A4") for i in ids)

    def test_provenance_embedded_in_payload(self):
        payload = run_matrix(seed=42)
        assert payload["provenance"]["paper_id"] == "P10"
        assert payload["provenance"]["manifest_sha256"]

    def test_no_expert_scores_fabricated(self):
        """Fail-closed honesty: no fabricated expert-rating VALUE may exist in
        the machine payload. Numeric CVI/kappa/rubric-score fields would be
        fabrications; the payload must carry only design-gate metrics."""
        import json

        payload = run_matrix(seed=42)

        def walk(node, path=""):
            if isinstance(node, dict):
                for k, v in node.items():
                    kl = str(k).lower()
                    assert not any(
                        tok in kl for tok in ("cvi", "kappa", "krippendorff", "rubric_score", "expert_rating")
                    ), f"fabricated expert metric at {path}/{k}"
                    walk(v, f"{path}/{k}")
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk(v, f"{path}[{i}]")

        walk(payload)

    def test_ablation_a3_notes_record_invented_anchor_acceptance(self):
        payload = run_matrix(seed=42)
        assert payload["ablation_notes"]["A3"]["invented_anchor_accepted"] is True


class TestStatisticsReuse:
    def test_proportion_ci_zero_successes_never_degenerate(self):
        ci = proportion_ci(0, 10)
        lo_w, hi_w = ci["wilson_ci_95"]
        lo_c, hi_c = ci["clopper_pearson_ci_95"]
        assert lo_w == 0.0 and hi_w > 0.0  # Wilson upper bound is positive
        assert hi_c > 0.0

    def test_proportion_ci_perfect_score_never_reaches_one(self):
        ci = proportion_ci(10, 10)
        _, hi_w = ci["wilson_ci_95"]
        _, hi_c = ci["clopper_pearson_ci_95"]
        assert hi_w < 1.0
        assert hi_c == 1.0  # Clopper-Pearson is exact; Wilson is not
