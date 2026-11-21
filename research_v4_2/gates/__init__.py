"""Automated Science and Engineering Release Gates for Research V4.2."""

from research_v4_2.gates.test_exit import validate_test_exit
from research_v4_2.gates.preregister import validate_preregistration
from research_v4_2.gates.novelty import validate_novelty
from research_v4_2.gates.baseline_parity import validate_baseline_parity
from research_v4_2.gates.statistical_claims import validate_statistical_claims
from research_v4_2.gates.integrity import validate_integrity
from research_v4_2.gates.license_ethics import validate_license_ethics
from research_v4_2.gates.cross_paper import validate_cross_paper_independence

__all__ = [
    "validate_test_exit",
    "validate_preregistration",
    "validate_novelty",
    "validate_baseline_parity",
    "validate_statistical_claims",
    "validate_integrity",
    "validate_license_ethics",
    "validate_cross_paper_independence",
]
