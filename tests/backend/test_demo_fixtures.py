# -*- coding: utf-8 -*-
"""Tests for Demonstration Fixtures Integrity and Absence of Fake Commercial Data."""
from __future__ import annotations

import pytest
from backend.services.demo_fixtures import verify_demo_fixtures_integrity
from backend.services.heritage_import import import_heritage_data


def test_demo_fixtures_integrity_and_honesty(db_session):
    """Verify demo fixtures load cleanly without fake customer accounts or fabricated revenue."""
    report, stats = import_heritage_data(db_session, dry_run=False)
    assert report.is_valid is True
    assert stats.places_inserted >= 23
    assert stats.creators_inserted >= 3
    assert stats.experiences_inserted >= 3
    assert stats.stories_inserted >= 3

    report = verify_demo_fixtures_integrity(db_session)
    assert report["status"] == "PASS"
    assert report["commercial_honesty"] == "ENFORCED"
    assert report["creators_verified"] >= 3
    assert report["experiences_verified"] >= 3
    assert report["stories_verified"] >= 3
