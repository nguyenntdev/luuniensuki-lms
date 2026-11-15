"""Shared path resolution for Research V3 scripts.

Every script resolves the repository root the same way so artifacts always land
in the same place regardless of the caller's working directory.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

RESEARCH_V3_ROOT = REPO_ROOT / "research_v3"
RESEARCH_V2_ROOT = REPO_ROOT / "research_v2"
ARTIFACTS_V3_ROOT = REPO_ROOT / "research_artifacts_v3"
ARTIFACTS_V2_ROOT = REPO_ROOT / "research_artifacts_v2"

DATA_FROZEN_DIR = RESEARCH_V3_ROOT / "data_frozen"
GOVERNANCE_DIR = RESEARCH_V3_ROOT / "governance"
CONFIG_DIR = RESEARCH_V3_ROOT / "config"

CLAIMS_DIR = GOVERNANCE_DIR / "claims"
ETHICS_DIR = GOVERNANCE_DIR / "ethics"
AUDIT_LOG_DIR = GOVERNANCE_DIR / "audit_log"

RELEASE_DIR = ARTIFACTS_V3_ROOT / "release"
FIGURES_DIR = ARTIFACTS_V3_ROOT / "figures"
RUNS_DIR = ARTIFACTS_V3_ROOT / "runs"

SANITIZED_DIR = RESEARCH_V3_ROOT / "datasets" / "sanitized"
SPLIT_PROTOCOL_DIR = CONFIG_DIR / "split_protocols"
PAPER_CONFIG_DIR = CONFIG_DIR / "papers"

V2_RUNS_DIR = ARTIFACTS_V2_ROOT / "runs"
V2_RELEASE_DIR = ARTIFACTS_V2_ROOT / "release"

HISTORIC_G0_AUDIT = RESEARCH_V2_ROOT / "reports" / "G0_repo_audit.json"
