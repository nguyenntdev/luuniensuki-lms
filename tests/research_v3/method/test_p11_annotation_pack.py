"""P11 annotation-pack completeness tests: templates empty, no fabricated content."""
from __future__ import annotations

import csv
import json
from pathlib import Path

PACK = Path("research_v3/annotations/tasks/p11_annotation_pack")

TEMPLATE_HEADERS = {
    "assignment_template.csv": {"unit_id", "rater_id", "block", "order_index", "assigned_at", "completed_at"},
    "ratings_template.csv": {"unit_id", "rater_id", "criterion", "rating", "uncertain", "seconds_elapsed", "batch_id", "codebook_version", "rated_at"},
    "adjudication_log_template.csv": {"unit_id", "criterion", "rating_1", "rating_2", "adjudicated", "rationale", "adjudicator_pseudonym", "decided_at", "trigger"},
}


def test_templates_have_headers_and_zero_data_rows():
    for fname, expected_headers in TEMPLATE_HEADERS.items():
        path = PACK / fname
        assert path.exists(), f"missing {fname}"
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            rows = list(reader)
        assert set(header or ()) == expected_headers, f"{fname} header drift"
        assert rows == [], f"{fname} must contain ZERO data rows (no fabricated ratings)"


def test_no_fabricated_annotator_ids_anywhere():
    """Pseudonyms may appear only as template placeholders like 'rater_A' in docs, never
    as filled rating rows or agreement values."""
    for csv_name in TEMPLATE_HEADERS:
        text = (PACK / csv_name).read_text(encoding="utf-8")
        # no data row may contain a pseudonym
        for line in text.splitlines()[1:]:
            line = line.strip()
            assert line == "", f"{csv_name} contains a data row: {line!r}"


def test_annotation_card_release_decision_is_blocked():
    text = (PACK / "ANNOTATION_CARD.md").read_text(encoding="utf-8")
    assert "BLOCKED until authentic annotation + approval available" in text
    assert "REQUIRED-BEFORE-RATING" in text


def test_codebook_covers_all_criteria_and_levels():
    text = (PACK / "CODEBOOK.md").read_text(encoding="utf-8")
    for crit in ("S1", "S2", "S3", "S4"):
        assert crit in text
    for mark in ("NOT_APPLICABLE", "ABSTAIN"):
        assert mark in text
    assert "never create synthetic 'experts'" in text or "No synthetic raters" in text


def test_constructed_cases_labeled_not_human():
    case_dir = PACK / "constructed_cases"
    expected = [f"CC0{i}_*.json" for i in range(1, 7)]
    found = sorted(p.name for p in case_dir.glob("CC*.json"))
    assert len(found) == 6, f"expected 6 constructed cases, found {found}"
    for p in case_dir.glob("CC*.json"):
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data["label"] == "CONSTRUCTED_NOT_HUMAN", p.name
        assert "scorer_output" in data
    rows = list(csv.DictReader((case_dir / "expected_levels.csv").open(encoding="utf-8")))
    assert len(rows) == 6
    assert all(r["note"] == "constructed_not_human" for r in rows)
    # expected list referenced by name for the completeness assertion
    assert all(any(p.match(pat) for p in case_dir.glob("CC*.json")) for pat in expected)


def test_expected_levels_csv_has_no_agreement_statistics():
    rows = list(csv.DictReader((PACK / "constructed_cases" / "expected_levels.csv").open(encoding="utf-8")))
    for row in rows:
        for key, value in row.items():
            assert "alpha" not in key.lower() and "kappa" not in key.lower()
            if key not in ("case_id", "note"):
                assert value in {"0", "1", "2", "3"}, f"{row['case_id']}/{key}={value!r}"


def test_adjudication_protocol_preserves_first_ratings():
    text = (PACK / "adjudication_protocol.md").read_text(encoding="utf-8")
    assert "immutable" in text.lower() or "never overwrites" in text.lower()
    assert "pre-adjudication" in text.lower()


def test_readme_unblocking_steps_present():
    text = (PACK / "README.md").read_text(encoding="utf-8")
    assert "BLOCKED_AWAITING_HUMAN_RATERS" in text
    assert "ethics approval" in text.lower()
