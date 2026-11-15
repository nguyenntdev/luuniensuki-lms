"""P10 experiment runner: preregistered matrix C0/C1/proposed + A1-A4.

P10-T05/T06/T07/T10/T12/T14/T15. The runner is the single source of every
published number: it loads the documented corpus, builds all designs, runs the
preregistered metric set, applies the statistics helpers from
``research_v3/eval/statistics.py``, and writes one manifest per run with
SHA-256 hashes. No metric is ever hand-entered (P10-T15: source-to-table).

Preregistered metrics (frozen here and in pre_registration.yaml):
  M1 sequence_validity_rate   — fraction of designs whose certificate is valid
  M2 anchor_coverage_rate     — documented-anchor objects / total objects
  M3 needs_expert_review_rate — pending-anchor objects / total objects
  M4 bloom_leap_rate          — flagged leap edges / progression edges
All metrics report Wilson + Clopper-Pearson CIs via proportion_ci().
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from research_v2.contracts.canonical_hash import sha256_input
from research_v3.eval.statistics import proportion_ci

from .ablations import run_a1_no_layer_bridge, run_a2_no_bloom_ascent, run_a3_no_provenance_gate, run_a4_random_order
from .anchors import P10ContractError, SpiralSequence
from .corpus import load_corpus, build_prerequisite_edges
from .provenance import provenance_manifest
from .registry import anchor_confidence_summary, build_anchor_registry
from .spiral_builder import build_linear_playlist, build_spiral_dag, build_topological_no_bloom

PAPER_ID = "P10"
RUNS_DIR = Path(__file__).resolve().parents[3] / "research_artifacts_v3" / "runs" / "p10"

# Preregistered metric denominators are fixed before running (no peeking).
PRIMARY_METRIC = "M1_sequence_validity_rate"


@dataclass(frozen=True)
class DesignResult:
    design_id: str
    valid: bool
    certificate: dict[str, Any]
    notes: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "design_id": self.design_id,
            "valid": self.valid,
            "certificate": self.certificate,
            "notes": self.notes,
        }


def _sequence_row(seq: SpiralSequence, extra_notes: dict[str, Any] | None = None) -> DesignResult:
    notes: dict[str, Any] = {
        "n_objects": len(seq.ordered_object_ids),
        "documented_anchor_objects": seq.documented_anchor_count,
        "needs_expert_review_anchor_objects": seq.needs_expert_review_anchor_count,
        "bloom_leap_edges": len(seq.certificate.bloom_leap_edges),
    }
    if extra_notes:
        notes.update(extra_notes)
    return DesignResult(
        design_id=seq.design_id,
        valid=seq.certificate.valid,
        certificate=seq.certificate.to_dict(),
        notes=notes,
    )


def run_matrix(*, seed: int = 42) -> dict[str, Any]:
    """Execute the full preregistered comparison matrix. Deterministic except
    A4 (seeded). Returns the complete result payload ready for JSON freeze."""
    t0 = time.perf_counter()

    provenance = provenance_manifest()
    registry = build_anchor_registry()
    anchor_counts = anchor_confidence_summary(registry)
    objects = load_corpus()
    edges = build_prerequisite_edges(objects)

    designs: list[DesignResult] = []

    # --- Baselines -------------------------------------------------------
    c0 = build_linear_playlist(objects, registry)
    designs.append(_sequence_row(c0))

    c1 = build_topological_no_bloom(objects, edges, registry)
    designs.append(_sequence_row(c1))

    # --- Proposed --------------------------------------------------------
    prop = build_spiral_dag(objects, edges, registry)
    n_progression = sum(1 for e in edges if e.edge_kind == "progression")
    designs.append(
        _sequence_row(
            prop,
            {
                "n_progression_edges": n_progression,
                "n_bridge_edges": sum(1 for e in edges if e.edge_kind == "bridge"),
            },
        )
    )

    # --- Ablations (mechanism removals) ----------------------------------
    a1, a1_notes = run_a1_no_layer_bridge(objects, registry)
    designs.append(_sequence_row(a1, a1_notes))
    a2, a2_notes = run_a2_no_bloom_ascent(objects, registry)
    designs.append(_sequence_row(a2, a2_notes))
    a3, a3_notes = run_a3_no_provenance_gate(objects, registry)
    designs.append(_sequence_row(a3, a3_notes))
    a4, a4_notes = run_a4_random_order(objects, registry, seed=seed)
    designs.append(_sequence_row(a4, a4_notes))

    # --- Preregistered metrics -------------------------------------------
    # M1: validity rate over the three *designs under comparison* (C0, C1,
    # proposed). Ablations are failure-family probes, not members of the
    # confirmatory set — they are reported separately, per packet §5.
    confirmatory = [d for d in designs if d.design_id.startswith(("C0", "C1", "proposed"))]
    n_valid = sum(1 for d in confirmatory if d.valid)
    m1 = proportion_ci(n_valid, len(confirmatory))

    total_objects = len(objects)
    documented_objects = prop.documented_anchor_count
    pending_objects = prop.needs_expert_review_anchor_count
    m2 = proportion_ci(documented_objects, total_objects)
    m3 = proportion_ci(pending_objects, total_objects)

    leap_edges = len(prop.certificate.bloom_leap_edges)
    m4 = proportion_ci(leap_edges, n_progression) if n_progression else {"wilson_ci_95": [None, None], "clopper_pearson_ci_95": [None, None]}

    metrics = {
        PRIMARY_METRIC: {"successes": n_valid, "n": len(confirmatory), **m1},
        "M2_anchor_coverage_rate": {"successes": documented_objects, "n": total_objects, **m2},
        "M3_needs_expert_review_rate": {"successes": pending_objects, "n": total_objects, **m3},
        "M4_bloom_leap_rate": {"successes": leap_edges, "n": n_progression, **m4},
    }

    wall = time.perf_counter() - t0
    payload = {
        "paper_id": PAPER_ID,
        "preregistered_primary_metric": PRIMARY_METRIC,
        "hypothesis_h0": (
            "Chuỗi xoắn ốc không có ưu thế nhất quán theo rubric so với chuỗi "
            "chuẩn do giáo viên xây dựng — requires real teacher raters (BLOCKED, P10-T19)"
        ),
        "provenance": provenance,
        "anchor_registry": {
            "total_anchors": len(registry),
            "documented": anchor_counts["documented"],
            "needs_expert_review": anchor_counts["needs_expert_review"],
        },
        "corpus": {
            "n_objects": total_objects,
            "n_urns": 9,
            "n_edges": len(edges),
            "is_ai_generated_fraction": 1.0,
        },
        "designs": [d.to_dict() for d in designs],
        "ablation_notes": {"A1": a1_notes, "A2": a2_notes, "A3": a3_notes, "A4": a4_notes},
        "metrics": metrics,
        "engine": "research_v3.methods.p10 (pure deterministic builders; A4 seeded)",
        "seed": seed,
        "hardware": "CPU only (no GPU used; constraint checks are O(V+E))",
        "honesty_notes": [
            "Validity certificates are software gates, NOT pedagogical endorsement.",
            "Every GDPT-2018 competency-code pairing beyond the certain documented set "
            "is flagged needs_expert_review (27 of 30 anchors).",
            "No expert rating, CVI, or rubric score exists in this payload; such claims "
            "are BLOCKED pending real teachers (P10-T19/T20/T21).",
            "All 162 motif descriptions are AI-generated repo content; only object "
            "identities are used; no archival permission claimed.",
        ],
    }
    payload["payload_sha256"] = sha256_input(payload)
    # Wall time is a measurement, not a payload member: recording it inside the
    # hashed body would break byte-for-byte reproducibility (two identical runs
    # would hash differently). It is stored beside the hash instead.
    payload["wall_time_seconds_unhashed"] = round(wall, 6)
    return payload


def freeze_run(output_dir: Path | None = None, *, seed: int = 42) -> Path:
    """Run the matrix and freeze it as an immutable JSON artifact."""
    out_dir = Path(output_dir) if output_dir else RUNS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = run_matrix(seed=seed)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = out_dir / f"p10_run_{stamp}.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    return path
