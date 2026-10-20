"""Automated pedagogical validation tests for STTT Imperial City materials.
Scope: Master Spec §7, §9, §10, and D-03/D-04 compliance.

Validates:
1. Lesson plan (45-minute timing, 4 activities, duration sum == 45).
2. Rubric S1-S4 complete with scale levels 0-3.
3. Fieldwork worksheet 4-column structure (Trạm quan sát / Hiện trạng mắt thấy / Tư liệu đối chiếu / Em kết luận gì).
4. Zero forbidden legacy terms in any pedagogical material.
5. Historical competency alignment (GDPT 2018).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.imperial.audit_no_legacy_content import (
    FORBIDDEN_TERMS,
    scan_file_for_violations,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LESSON_PLAN_PATH = REPO_ROOT / "data" / "imperial" / "lesson_plan_45m.json"
WORKSHEET_PATH = REPO_ROOT / "data" / "imperial" / "fieldwork_worksheet.json"


@pytest.fixture(scope="module")
def lesson_plan_data() -> dict[str, Any]:
    assert LESSON_PLAN_PATH.exists(), f"Missing {LESSON_PLAN_PATH}"
    content = LESSON_PLAN_PATH.read_text(encoding="utf-8")
    return json.loads(content)


@pytest.fixture(scope="module")
def worksheet_data() -> dict[str, Any]:
    assert WORKSHEET_PATH.exists(), f"Missing {WORKSHEET_PATH}"
    content = WORKSHEET_PATH.read_text(encoding="utf-8")
    return json.loads(content)


class TestLessonPlanPedagogy:
    """Validate formal 45-minute lesson plan for high school heritage education."""

    def test_lesson_plan_scope_and_duration(self, lesson_plan_data: dict[str, Any]):
        assert lesson_plan_data.get("content_scope") == "STTT_IMPERIAL_CITY"
        assert lesson_plan_data.get("document_type") == "lesson_plan_45m"
        assert lesson_plan_data.get("duration_minutes") == 45

    def test_lesson_plan_activities_count_and_timing(self, lesson_plan_data: dict[str, Any]):
        activities = lesson_plan_data.get("activities", [])
        assert len(activities) == 4, f"Expected exactly 4 activities, found {len(activities)}"

        # Check durations: 5p + 15p + 15p + 10p = 45p
        expected_durations = [5, 15, 15, 10]
        actual_durations = [act.get("duration_minutes") for act in activities]
        assert actual_durations == expected_durations, (
            f"Expected activity durations {expected_durations}, got {actual_durations}"
        )
        assert sum(actual_durations) == 45, "Sum of activity durations must equal 45 minutes"

        # Check sequential numbering and key titles
        for idx, act in enumerate(activities, start=1):
            assert act.get("activity_number") == idx
            assert act.get("name_vi") and len(act["name_vi"].strip()) > 5
            assert act.get("objective_vi")
            assert isinstance(act.get("teacher_actions"), list) and len(act["teacher_actions"]) > 0
            assert isinstance(act.get("student_actions"), list) and len(act["student_actions"]) > 0
            assert act.get("deliverables_vi")
            assert act.get("assessment_criteria_vi")

        # Specific activity themes
        assert "khởi động" in activities[0]["name_vi"].lower()
        assert "khám phá" in activities[1]["name_vi"].lower()
        assert "truy chứng" in activities[2]["name_vi"].lower() or "sử liệu" in activities[2]["name_vi"].lower()
        assert "tổng kết" in activities[3]["name_vi"].lower() or "exit ticket" in activities[3]["name_vi"].lower()

    def test_lesson_plan_rubrics_s1_s4(self, lesson_plan_data: dict[str, Any]):
        rubrics = lesson_plan_data.get("rubrics", {})
        assert isinstance(rubrics, dict)

        criteria = rubrics.get("criteria", [])
        assert len(criteria) == 4, f"Expected 4 criteria (S1-S4), got {len(criteria)}"

        criteria_ids = {c.get("id") for c in criteria}
        assert criteria_ids == {"S1", "S2", "S3", "S4"}

        # Each rubric criterion must define descriptors for scale 0, 1, 2, 3
        for c in criteria:
            cid = c.get("id")
            descriptors = c.get("descriptors", {})
            assert isinstance(descriptors, dict), f"Criterion {cid} descriptors must be an object"
            for level in ("0", "1", "2", "3"):
                assert level in descriptors, f"Criterion {cid} missing descriptor for level {level}"
                assert len(descriptors[level].strip()) > 10, f"Descriptor {cid}:{level} too brief"

    def test_lesson_plan_competencies_and_qualities(self, lesson_plan_data: dict[str, Any]):
        objectives = lesson_plan_data.get("objectives", {})
        competencies = objectives.get("historical_competencies", [])
        assert len(competencies) == 4
        comp_codes = {c.get("code") for c in competencies}
        assert comp_codes == {"S1_SPATIAL", "S2_TEMPORAL", "S3_EVIDENCE", "S4_ARGUMENT"}

        qualities = objectives.get("qualities", [])
        assert len(qualities) >= 2


class TestFieldworkWorksheetPedagogy:
    """Validate 4-column fieldwork worksheet and offline exploration tools."""

    def test_worksheet_scope_and_metadata(self, worksheet_data: dict[str, Any]):
        assert worksheet_data.get("content_scope") == "STTT_IMPERIAL_CITY"
        assert worksheet_data.get("document_type") == "fieldwork_worksheet"
        assert worksheet_data.get("title_vi")

    def test_worksheet_four_columns_structure(self, worksheet_data: dict[str, Any]):
        columns = worksheet_data.get("columns", [])
        assert len(columns) == 4, f"Expected exactly 4 columns, got {len(columns)}"

        col_titles = [col.get("title_vi", "").lower() for col in columns]
        # Column 1: Trạm quan sát
        assert any("trạm" in t or "quan sát" in t for t in [col_titles[0]])
        # Column 2: Hiện trạng mắt thấy
        assert any("hiện trạng" in t or "mắt thấy" in t for t in [col_titles[1]])
        # Column 3: Tư liệu đối chiếu
        assert any("tư liệu" in t or "đối chiếu" in t for t in [col_titles[2]])
        # Column 4: Em kết luận gì
        assert any("kết luận" in t for t in [col_titles[3]])

    def test_worksheet_stations_content_integrity(self, worksheet_data: dict[str, Any]):
        stations = worksheet_data.get("stations", [])
        assert len(stations) >= 4, f"Expected at least 4 observation stations, got {len(stations)}"

        expected_slugs = {"ngo-mon", "dien-thai-hoa", "hien-lam-cac", "cung-dien-tho"}
        actual_slugs = {s.get("monument_slug") for s in stations}
        assert expected_slugs.issubset(actual_slugs), f"Missing core stations: {expected_slugs - actual_slugs}"

        for station in stations:
            slug = station.get("monument_slug")
            assert station.get("monument_name_vi"), f"Station {slug} missing name_vi"
            assert station.get("zone_name_vi"), f"Station {slug} missing zone_name_vi"
            assert station.get("observation_prompt_vi"), f"Station {slug} missing observation_prompt_vi"
            assert station.get("evidence_prompt_vi"), f"Station {slug} missing evidence_prompt_vi"
            assert station.get("conclusion_guide_vi"), f"Station {slug} missing conclusion_guide_vi"

            # Check guiding source citation
            guiding_src = station.get("guiding_source", {})
            assert guiding_src.get("source_title"), f"Station {slug} missing source_title"
            assert guiding_src.get("volume"), f"Station {slug} missing volume"

    def test_worksheet_exit_ticket_and_export_helper(self, worksheet_data: dict[str, Any]):
        exit_ticket = worksheet_data.get("exit_ticket", {})
        assert exit_ticket.get("title_vi")
        questions = exit_ticket.get("questions", [])
        assert len(questions) >= 2

        export_helper = worksheet_data.get("export_helper", {})
        assert export_helper.get("printable_css_page_setup")
        assert export_helper.get("target_dpi") == 300


class TestPedagogyForbiddenContentAudit:
    """Ensure strictly 0 forbidden legacy terms appear in pedagogical files."""

    def test_lesson_plan_zero_forbidden_terms(self):
        violations = scan_file_for_violations(LESSON_PLAN_PATH, FORBIDDEN_TERMS)
        assert violations == [], (
            f"Forbidden legacy term(s) found in {LESSON_PLAN_PATH}:\n"
            + "\n".join(f"  Line {v.line_number}: '{v.matched_term}' -> {v.line_snippet}" for v in violations)
        )

    def test_fieldwork_worksheet_zero_forbidden_terms(self):
        violations = scan_file_for_violations(WORKSHEET_PATH, FORBIDDEN_TERMS)
        assert violations == [], (
            f"Forbidden legacy term(s) found in {WORKSHEET_PATH}:\n"
            + "\n".join(f"  Line {v.line_number}: '{v.matched_term}' -> {v.line_snippet}" for v in violations)
        )
