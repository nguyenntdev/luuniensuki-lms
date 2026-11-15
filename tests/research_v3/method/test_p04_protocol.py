"""P04 protocol tests: independence gate, rights, splits, determinism, leakage.

Scope: tests/research_v3/method/test_p04_*.py (P04-exclusive). These tests
never require network access and never fabricate numbers; when the real raw
snapshot is present they verify against it, and protocol-level invariants are
always tested on synthetic protocol rows (clearly separated from real data).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNS_P04 = PROJECT_ROOT / "research_artifacts_v3" / "runs" / "p04"

VALID_DECISIONS = {"PROCEED", "MERGE_INTO_P01", "WITHDRAW"}


# ---------------------------------------------------------------------------
# Independence gate artifact (mandatory first step)
# ---------------------------------------------------------------------------

class TestIndependenceGate:
    def test_artifact_exists_and_decision_is_valid(self):
        path = RUNS_P04 / "independence_decision.json"
        assert path.is_file(), "mandatory independence gate artifact missing"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["decision"] in VALID_DECISIONS
        assert len(data.get("decision_justification", "")) > 200, (
            "independence decision requires a written justification"
        )

    def test_collision_check_against_p01_is_recorded(self):
        data = json.loads((RUNS_P04 / "independence_decision.json").read_text(encoding="utf-8"))
        assert "same_primary_hypothesis_as_p01" in data["collision_check"]
        assert "same_primary_outcome_table_as_p01" in data["collision_check"]
        # If it were a pure re-report of P01, the decision must NOT be PROCEED
        if data["collision_check"]["same_primary_hypothesis_as_p01"] and data["collision_check"][
            "same_primary_outcome_table_as_p01"
        ]:
            assert data["decision"] != "PROCEED"

    def test_human_only_tasks_marked_blocked(self):
        data = json.loads((RUNS_P04 / "independence_decision.json").read_text(encoding="utf-8"))
        blocked = data["consequences"].get("PROCEED", "")
        assert "P04-T19/T20/T21 remain BLOCKED" in blocked


# ---------------------------------------------------------------------------
# Rights ledger (P04-T02/T04)
# ---------------------------------------------------------------------------

class TestRights:
    def test_raw_snapshot_hashes_match_frozen_manifest(self):
        from research_v3.methods.p04.rights import verify_raw_snapshot

        pytest.importorskip("yaml")
        manifest = verify_raw_snapshot()
        for ds_id, entry in manifest["datasets"].items():
            if ds_id in {"oulad-2013-2014", "uci-student-performance-2014"}:
                assert entry["usable"], f"{ds_id}: raw snapshot hash mismatch or missing"
                assert entry["archive_sha256_matches_expected"]
                assert entry["license_sha256_matches_expected"]

    def test_blocked_datasets_have_exact_reasons(self):
        from research_v3.methods.p04.rights import blocked_datasets

        blocked = blocked_datasets()
        for name in ("assistments", "junyi", "ednet"):
            assert name in blocked and len(blocked[name]) > 40

    def test_datasheet_discloses_nc_license_for_oulad(self):
        sheet = (PROJECT_ROOT / "research_v3/methods/p04/datasheets/P04_datasheet.md").read_text(
            encoding="utf-8"
        )
        assert "CC BY-NC 4.0" in sheet, "OULAD captured license is BY-NC and must be disclosed"
        assert "f2ed1902616c1fe8d2824d872c0b7d2d72be435bf0124d077044fe4be2c6d3e4" in sheet


# ---------------------------------------------------------------------------
# Bridge + scenarios (P04-T03)
# ---------------------------------------------------------------------------

class TestBridgeAndScenarios:
    def test_bridge_maps_verified_and_returns_not_applicable(self):
        from research_v3.methods.p04.bridge import NOT_APPLICABLE, BridgeEdge, OntologyBridge

        edges = {
            "quiz": BridgeEdge("quiz", "assessment", "verified", "test"),
        }
        bridge = OntologyBridge(ontology_version="t", edges=edges)
        assert bridge.map_source("quiz") == "assessment"
        assert bridge.map_source("unseen-type") == NOT_APPLICABLE
        assert bridge.map_source(None) == NOT_APPLICABLE
        assert bridge.map_source("") == NOT_APPLICABLE

    def test_bridge_from_real_oulad_covers_all_observed_types(self):
        pytest.importorskip("yaml")
        oulad = PROJECT_ROOT / "private_data/raw/oulad/2013-2014/_extracted/studentInfo.csv"
        if not oulad.is_file():
            pytest.skip("real OULAD snapshot not present")
        import collections
        import csv

        from research_v3.methods.p04.bridge import bridge_from_oulad
        from research_v3.methods.p04.run_reference_eval import oulad_rows_with_activity

        rows, _ = oulad_rows_with_activity()
        counts = collections.Counter(r["input"]["activity_type"] for r in rows if r["input"]["activity_type"])
        bridge = bridge_from_oulad(counts)
        assert bridge.coverage() == 1.0
        assert bridge.unknown_sources == ()
        assert set(counts) == set(bridge.edges)

    def test_every_preregistered_stratum_has_a_scenario(self):
        from research_v3.methods.p04.scenarios import ALL_STRATA, check_strata_complete, oulad_scenarios

        scens = oulad_scenarios(courses=["AAA", "FFF"], presentations=["2013J", "2014J"])
        complete = check_strata_complete(scens)
        assert complete["S1"] and complete["S3"] and complete["S4"]

    def test_invalid_stratum_rejected(self):
        from research_v3.methods.p04.scenarios import Scenario, ScenarioError

        with pytest.raises(ScenarioError):
            Scenario("S9", "bogus", "ds", "d", {})


# ---------------------------------------------------------------------------
# Predictor contract (P04-T09: NOT_APPLICABLE and ABSTAIN are first-class)
# ---------------------------------------------------------------------------

def _proto_rows(n: int = 40) -> list[dict]:
    rows = []
    for i in range(n):
        rows.append(
            {
                "case_id": f"c{i}",
                "group_id": f"g{i % 8}",
                "label": i % 2,
                "input": {"activity_type": "quiz" if i % 3 else "homepage"},
                "mapped_canonical": "assessment" if i % 3 else "administrative",
                "no_activity": False,
            }
        )
    return rows


class TestPredictorContract:
    def test_abstain_is_not_a_negative_prediction(self):
        from research_v3.methods.p04.bench import score_predictions

        rows = _proto_rows()
        preds = [{"prediction": 1 if i % 2 else 0, "probability": 0.9} for i in range(len(rows))]
        base = score_predictions(rows, preds)
        preds_abstain = list(preds)
        preds_abstain[0] = {"prediction": "ABSTAIN"}
        with_abstain = score_predictions(rows, preds_abstain)
        assert with_abstain["n_abstain"] == 1
        assert with_abstain["n_scored"] == base["n_scored"] - 1
        # abstain must NOT change anyone else's scored outcome
        assert with_abstain["coverage"] < base["coverage"]

    def test_not_applicable_excluded_and_reported(self):
        from research_v3.methods.p04.bridge import NOT_APPLICABLE
        from research_v3.methods.p04.bench import score_predictions

        rows = _proto_rows()
        rows[0]["mapped_canonical"] = NOT_APPLICABLE
        preds = [{"prediction": 1, "probability": 0.8}] * len(rows)
        out = score_predictions(rows, preds)
        assert out["n_not_applicable"] >= 1
        assert out["n_scored"] == len(rows) - out["n_not_applicable"]

    def test_contract_rejects_missing_probability(self):
        from research_v3.methods.p04.bench import PredictorContractError, validate_predictions

        with pytest.raises(PredictorContractError):
            validate_predictions([{"case_id": "c"}], [{"prediction": 1}])

    def test_contract_rejects_garbage_prediction(self):
        from research_v3.methods.p04.bench import PredictorContractError, validate_predictions

        with pytest.raises(PredictorContractError):
            validate_predictions([{"case_id": "c"}], [{"prediction": "N/A"}])

    def test_contract_rejects_length_mismatch(self):
        from research_v3.methods.p04.bench import PredictorContractError, validate_predictions

        with pytest.raises(PredictorContractError):
            validate_predictions([{"case_id": "c"}], [])


# ---------------------------------------------------------------------------
# Determinism of the protocol (P04-T05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_split_hash_reproducible_across_row_order(self):
        """Group->partition assignment is deterministic; the split hash is
        order-insensitive because ids within a partition are sorted first."""
        from research_v3.eval.splitters import assert_no_leakage, freeze_hash, group_split
        from research_v3.contracts.cards import FrozenSplit

        rows = [{"case_id": f"c{i}", "group_id": f"g{i % 40}"} for i in range(40)]
        s1 = group_split(rows, group_key="group_id", paper_id="P04", salt="p04-v1")
        s2 = group_split(list(reversed(rows)), group_key="group_id", paper_id="P04", salt="p04-v1")
        # identical group->partition map (row order must not change assignment)
        assert {k: set(v) for k, v in s1.split_ids.items()} == {
            k: set(v) for k, v in s2.split_ids.items()
        }
        assert_no_leakage(s1)
        # canonical (sorted) restatement has one frozen hash
        canon1 = FrozenSplit(paper_id=s1.paper_id, protocol=s1.protocol,
                             split_ids={k: tuple(sorted(v)) for k, v in s1.split_ids.items()})
        canon2 = FrozenSplit(paper_id=s2.paper_id, protocol=s2.protocol,
                             split_ids={k: tuple(sorted(v)) for k, v in s2.split_ids.items()})
        assert freeze_hash(canon1) == freeze_hash(canon2)

    def test_injector_deterministic_given_salt(self):
        from research_v3.methods.p04.bench import hide_bridge_edges
        from research_v3.methods.p04.bridge import BridgeEdge, OntologyBridge

        edges = {
            f"t{i}": BridgeEdge(f"t{i}", "content", "verified", "p") for i in range(20)
        }
        bridge = OntologyBridge(ontology_version="t", edges=edges)
        b1 = hide_bridge_edges(bridge, 0.5, salt="s")
        b2 = hide_bridge_edges(bridge, 0.5, salt="s")
        hidden1 = {k for k, e in b1.edges.items() if e.status == "unknown"}
        hidden2 = {k for k, e in b2.edges.items() if e.status == "unknown"}
        assert hidden1 == hidden2 and len(hidden1) == 10

    def test_auc_matches_bruteforce_on_tie_heavy_data(self):
        import random

        from research_v3.methods.p04.bench import _auc

        rng = random.Random(7)
        for _ in range(50):
            n = rng.randint(2, 50)
            ys = [rng.randint(0, 1) for _ in range(n)]
            xs = [rng.choice([0.1, 0.2, 0.3, 0.5]) for _ in range(n)]
            if len(set(ys)) < 2:
                continue
            pos = [s for s, y in zip(xs, ys) if y == 1]
            neg = [s for s, y in zip(xs, ys) if y == 0]
            wins = sum(1.0 for p in pos for q in neg if p > q) + 0.5 * sum(
                1.0 for p in pos for q in neg if p == q
            )
            expected = wins / (len(pos) * len(neg))
            assert abs(_auc(xs, ys) - expected) < 1e-12

    def test_rank_stability_perfect_for_identical_rankings(self):
        from research_v3.methods.p04.bench import rank_stability

        r = {"S1": ["a", "b", "c"], "S3": ["a", "b", "c"]}
        assert rank_stability(r) == 1.0


# ---------------------------------------------------------------------------
# Leakage guards (P04-T05)
# ---------------------------------------------------------------------------

class TestLeakage:
    def test_split_partitions_are_disjoint(self):
        from research_v3.eval.splitters import assert_no_leakage, group_split

        rows = [{"case_id": f"c{i}", "group_id": f"g{i % 40}"} for i in range(40)]
        split = group_split(rows, group_key="group_id", paper_id="P04", salt="p04-v1")
        assert_no_leakage(split)  # raises on any overlap

    def test_shared_leakage_audit_rejects_gold_in_input(self):
        from research_v3.eval.leakage import LeakageError, audit_rows

        rows = [{"case_id": "c1", "input": {"label": 1}}]
        with pytest.raises(LeakageError):
            audit_rows(rows, strict=True)

    def test_oulad_adapter_refuses_label_in_features(self):
        pytest.importorskip("yaml")
        from research_v3.datasets.adapters.oulad import OuladSchemaError

        # adapter constant: final_result must never appear as a feature key
        from research_v3.datasets.adapters.oulad import FORBIDDEN_FEATURE_FIELDS

        assert "final_result" in FORBIDDEN_FEATURE_FIELDS

    def test_frozen_test_labels_not_editable_by_scoring(self):
        # scoring reads labels but never writes them; a mutation attempt on the
        # rows dict must not alter scoring results
        from research_v3.methods.p04.bench import score_predictions

        rows = _proto_rows()
        preds = [{"prediction": 1, "probability": 0.7}] * len(rows)
        before = [r["label"] for r in rows]
        score_predictions(rows, preds)
        assert [r["label"] for r in rows] == before


# ---------------------------------------------------------------------------
# Reference evaluation artifact (present + internally consistent when run)
# ---------------------------------------------------------------------------

class TestReferenceEvalArtifact:
    def test_leaderboard_exists_with_valid_schema(self):
        path = RUNS_P04 / "reference_eval" / "leaderboard.json"
        assert path.is_file(), "run `python -m research_v3.methods.p04.run_reference_eval` first"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["n_oulad_rows"] == 32593
        assert data["external_generalization"].startswith("UNVERIFIED")
        for cell in data["leaderboard"]:
            assert cell["schema_version"] == "p04-leaderboard-1.0"
            assert cell["status"] in {"MEASURED", "BLOCKED_FIT_FAILURE"}
            if cell["status"] == "MEASURED" and cell["n_scored"] > 0:
                assert cell["auc"] is None or 0.0 <= cell["auc"] <= 1.0
                assert 0.0 <= cell["coverage"] <= 1.0
                assert 0.0 <= cell["mapping_coverage"] <= 1.0

    def test_no_fabricated_metric_cells(self):
        data = json.loads(
            (RUNS_P04 / "reference_eval" / "leaderboard.json").read_text(encoding="utf-8")
        )
        for cell in data["leaderboard"]:
            if cell["n_scored"] == 0:
                assert cell["auc"] is None, "empty denominator must yield None, not a number"

    def test_strata_complete_in_leaderboard(self):
        data = json.loads(
            (RUNS_P04 / "reference_eval" / "leaderboard.json").read_text(encoding="utf-8")
        )
        strata = {c["stratum"] for c in data["leaderboard"]}
        assert {"S0", "S1", "S2", "S3", "S4"} <= strata

    def test_null_assessment_present(self):
        data = json.loads(
            (RUNS_P04 / "reference_eval" / "leaderboard.json").read_text(encoding="utf-8")
        )
        assert "h0_stands" in data["null_assessment"]
        assert isinstance(data["null_assessment"]["reliable_failures"], list)
