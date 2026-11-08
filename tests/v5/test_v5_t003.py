"""
Tests for W00-A03 (V5-T003): Production Mock Call-Site Registry.
Verifies that all mock call-sites, fake-success handlers, and placeholder routes
are cataloged in W00_A03_mock_callsite_registry.json and flagged for elimination.
"""

import json
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT_DIR / "artifacts/implementation/W00/W00_A03_mock_callsite_registry.json"


def test_registry_artifact_exists_and_valid():
    """Verify registry JSON artifact exists, has valid structure, and correct baseline SHA."""
    assert REGISTRY_PATH.exists(), f"Missing mock registry artifact at {REGISTRY_PATH}"
    
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["version"] == "v6.0-w00"
    assert data["baseline_source_sha"] == "54da2beb71f3df70e1f00b215ae0fb1a850eb263"
    assert "summary" in data
    assert data["summary"]["total_callsites"] >= 20
    assert data["summary"]["p0_count"] >= 5


def test_registry_covers_critical_p0_gaps():
    """Verify all P0 gaps from V5_03_MOCK_AUDIT.md are present in registry."""
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    gap_ids = {item["gap_id"] for item in data["registry"]}
    p0_gaps = {"GAP-001", "GAP-002", "GAP-003", "GAP-004", "GAP-005", "GAP-006", "GAP-007"}
    
    missing = p0_gaps - gap_ids
    assert not missing, f"Missing P0 gaps in registry: {missing}"


def test_mobile_placeholders_registered():
    """Verify Flutter mobile placeholder widgets and mock providers are registered."""
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    mobile_items = [
        item for item in data["registry"]
        if item["file_path"].startswith("mobile/")
    ]
    
    assert len(mobile_items) >= 10, f"Expected at least 10 mobile items, got {len(mobile_items)}"
    
    terms = {item["target_term"] for item in mobile_items}
    assert "QuestsPlaceholder" in terms
    assert "MockQuizData.mockQuestions" in terms
    assert "MockNotifications.items" in terms
    assert "addMockFriends" in terms


def test_every_registry_entry_has_target_endpoint():
    """Ensure every flagged mock call-site has a target backend endpoint or replacement spec."""
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for item in data["registry"]:
        assert item["target_backend_endpoint"], f"Entry {item['gap_id']} in {item['file_path']} lacks target endpoint"
        assert item["status"] == "FLAGGED_FOR_ELIMINATION"
        assert len(item["line_numbers"]) > 0
