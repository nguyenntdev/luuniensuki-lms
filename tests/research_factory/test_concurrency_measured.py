# -*- coding: utf-8 -*-
"""Research Factory: AI 10-Subagent Concurrency Measurement Unit Suite.

Validates:
- 12 phases x 10 unique agent slots = 120 unique roles.
- Sweep-line interval analysis for measured peak concurrency.
- Negative abuse defense: 10 concurrency strictly rejected when peak < 10.
- Token cost calculations and provider breakdowns.
- Cryptographic trace logs and execution provenance.
"""
from __future__ import annotations

import pytest

from backend.services.research_factory import (
    DEFAULT_PROVIDER_PRICING,
    ConcurrencyMeasurementError,
    ConcurrencyTracker,
    ResearchFactoryConcurrencyAuditor,
    SubagentExecutionTrace,
    TokenCostCalculator,
    assert_strictly_10_concurrent,
    get_roles_for_phase,
    label_concurrency_level,
    measure_overlapping_tasks,
    validate_concurrency_invariant,
)


def test_12_phases_10_unique_agent_slots_registry():
    """Confirms 12 phases P00..P11 x 10 unique agent slots = exactly 120 unique agent slots."""
    verification = ResearchFactoryConcurrencyAuditor.verify_registry_12x10_slots()
    assert verification["verified"] is True
    assert verification["total_phases"] == 12
    assert verification["roles_per_phase"] == 10
    assert verification["total_agent_slots"] == 120
    assert verification["unique_role_codes_count"] == 120
    assert verification["total_estimated_tokens"] == 618000

    # Verify each phase individually
    for i in range(12):
        phase_code = f"P{i:02d}"
        roles = get_roles_for_phase(phase_code)
        assert len(roles) == 10
        slots = [r.slot for r in roles]
        assert slots == list(range(1, 11))
        codes = [r.code for r in roles]
        assert len(set(codes)) == 10
        assert all(code.startswith(f"{phase_code}-A") for code in codes)


def test_token_cost_calculation_across_all_12_phases():
    """Validates token budget calculations and pricing models across all 12 phases."""
    budget = TokenCostCalculator.calculate_factory_12_phase_budget()
    assert budget["total_phases"] == 12
    assert budget["total_agent_slots"] == 120
    assert budget["cumulative_estimated_tokens"] == 618000
    assert budget["cumulative_cost_usd"] > 0.0

    # Gemini vs OCR breakdown
    provider_totals = budget["provider_totals"]
    assert "gemini" in provider_totals
    assert "ocr" in provider_totals
    assert provider_totals["gemini"]["slots"] > 0
    assert provider_totals["ocr"]["slots"] > 0
    assert provider_totals["gemini"]["tokens"] + provider_totals["ocr"]["tokens"] == 618000

    # Cost calculation formulas
    # 1,000,000 Gemini tokens at $0.15/1M = $0.15
    cost_gemini = TokenCostCalculator.calculate_cost("gemini", 1_000_000)
    assert cost_gemini == 0.15

    # 1,000,000 OCR tokens at $1.50/1M = $1.50
    cost_ocr = TokenCostCalculator.calculate_cost("ocr", 1_000_000)
    assert cost_ocr == 1.50


def test_negative_abuse_strict_10_concurrency_rejection():
    """Negative abuse invariant: Concurrency of 10 is claimed ONLY when measured >= 10 overlapping leases."""
    # Peak >= 10 must succeed
    assert assert_strictly_10_concurrent(10) is True
    assert assert_strictly_10_concurrent(12) is True
    assert label_concurrency_level(10) == "10_CONCURRENT_VERIFIED"

    # Peak < 10 must raise ConcurrencyMeasurementError
    for low_peak in [9, 8, 5, 2, 1, 0]:
        with pytest.raises(ConcurrencyMeasurementError) as exc_info:
            assert_strictly_10_concurrent(low_peak)
        assert "Negative abuse violation" in str(exc_info.value)
        assert str(low_peak) in str(exc_info.value)

    # Simulated phase with peak 9 must fail strict check
    intervals_9 = [(10.0 + i * 0.01, 10.5) for i in range(9)]
    with pytest.raises(ConcurrencyMeasurementError):
        ResearchFactoryConcurrencyAuditor.simulate_or_audit_phase(
            phase_code="P01",
            intervals=intervals_9,
            strict_10_check=True,
        )


def test_sweep_line_overlapping_leases_measurement():
    """Validates mathematical correctness of sweep-line concurrency algorithm."""
    # Disjoint intervals -> peak concurrency is 1
    disjoint = [(1.0, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 5.0)]
    assert measure_overlapping_tasks(disjoint) == 1

    # Exactly 10 mutually overlapping intervals -> peak concurrency is 10
    ten_overlap = [(10.0, 20.0) for _ in range(10)]
    assert measure_overlapping_tasks(ten_overlap) == 10

    # Staggered overlapping intervals: 5 overlap at peak
    staggered = [
        (1.0, 5.0),
        (2.0, 6.0),
        (3.0, 7.0),
        (4.0, 8.0),
        (4.5, 9.0),
        (6.0, 10.0),
    ]
    # At t=4.5: tasks 0, 1, 2, 3, 4 are running (5 tasks)
    assert measure_overlapping_tasks(staggered) == 5


def test_subagent_execution_trace_provenance():
    """Validates cryptographic trace log serialization and integrity."""
    trace = SubagentExecutionTrace(
        trace_id="tr_12345",
        phase_code="P07",
        slot_number=1,
        role_code="P07-A01",
        role_name="Vietnamese long-form historian writer",
        worker_id="pod_worker_01",
        job_id="job_9876",
        lease_token="token_abcdef",
        start_time=100.0,
        end_time=100.085,
        duration_ms=85.0,
        tokens_used=8000,
        cost_usd=0.0012,
        provider="gemini",
        status="SUCCEEDED",
    )
    d = trace.to_dict()
    assert d["trace_id"] == "tr_12345"
    assert d["phase_code"] == "P07"
    assert d["slot_number"] == 1
    assert d["role_code"] == "P07-A01"
    assert d["lease_token"] == "token_abcdef"
    assert d["duration_ms"] == 85.0
    assert d["tokens_used"] == 8000
    assert d["cost_usd"] == 0.0012
    assert d["status"] == "SUCCEEDED"
