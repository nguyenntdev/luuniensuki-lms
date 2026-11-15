"""LN-10 dataset loading, schema validation and case construction.

The inference-time feature schema for one case (the ``input`` subtree of the
T3 holdout fixtures):

    actor      : {owns_project: bool, role: str}           (who requests)
    project    : {version: int, state: str, goal: str, reflection_completed: bool, type: str}
    transition : {action: str, expected_version: int, rationale: str, new_goal?: str}
    learner    : profile metadata (never used by any policy)
    content    : heritage content metadata (never used by any policy)
    seed       : scenario generation seed (never used by policies)

Mandatory mandatory-case support: ``concurrent_edits`` may carry TWO OR MORE
offline edits targeting the same project version. Each edit is
``{editor: str, expected_version: int, action: str, rationale: str,
new_goal?: str}``. A single-edit list is the ordinary offline-edit case; two
edits with divergent payloads on the same ``expected_version`` are the
mandatory conflicting-offline-edits counterexample (LN-10-03.F case 1).

Any invalid row rejects the whole batch with its location - never a guessed
fallback value (LN-10-03.C step 6 / LN-10-04.C step 6).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = REPO_ROOT / "research_v2" / "data" / "ln10" / "t3_inputs.jsonl"
GOLD_PATH = REPO_ROOT / "research_v2" / "data" / "ln10" / "t3_gold.jsonl"
STUDY_ID = "LN-10"

#: Zimmerman cycle stages accepted by the finite state machine (monitoring is
#: the performance-phase stage every T3 scenario lives in).
KNOWN_PROJECT_STATES = frozenset(
    {"planning", "monitoring", "reflecting", "revising", "completed", "submitted"}
)

#: Transition actions accepted by the finite state machine.
KNOWN_ACTIONS = frozenset(
    {"revise_plan", "submit", "advance_stage", "update_goal", "record_reflection"}
)

#: Actions that legally move the project forward (performance -> reflection).
ACTIONABLE_ACTIONS = frozenset({"revise_plan", "submit", "advance_stage", "update_goal"})


class DatasetError(ValueError):
    """Raised when a dataset row violates the LN-10 input schema."""


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load a JSONL file; any malformed line fails with its location."""
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise DatasetError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return rows


@dataclass(frozen=True)
class Actor:
    role: str
    owns_project: bool

    @classmethod
    def from_dict(cls, raw: Any, *, location: str) -> "Actor":
        if not isinstance(raw, Mapping):
            raise DatasetError(f"{location}: actor must be a mapping, got {type(raw).__name__}")
        role = raw.get("role")
        owns = raw.get("owns_project")
        if not isinstance(role, str) or not role:
            raise DatasetError(f"{location}: actor.role must be a non-empty string")
        if not isinstance(owns, bool):
            raise DatasetError(f"{location}: actor.owns_project must be a boolean")
        return cls(role=role, owns_project=owns)


@dataclass(frozen=True)
class Project:
    version: int
    state: str
    goal: str
    reflection_completed: bool
    type: str = "heritage_city"

    @classmethod
    def from_dict(cls, raw: Any, *, location: str) -> "Project":
        if not isinstance(raw, Mapping):
            raise DatasetError(f"{location}: project must be a mapping, got {type(raw).__name__}")
        version = raw.get("version")
        if not isinstance(version, int) or isinstance(version, bool) or version < 0:
            raise DatasetError(f"{location}: project.version must be a non-negative integer")
        state = raw.get("state")
        if not isinstance(state, str) or not state:
            raise DatasetError(f"{location}: project.state must be a non-empty string")
        goal = raw.get("goal")
        if not isinstance(goal, str):
            raise DatasetError(f"{location}: project.goal must be a string")
        reflection = raw.get("reflection_completed")
        if not isinstance(reflection, bool):
            raise DatasetError(f"{location}: project.reflection_completed must be a boolean")
        ptype = raw.get("type", "heritage_city")
        if not isinstance(ptype, str):
            raise DatasetError(f"{location}: project.type must be a string")
        return cls(
            version=version,
            state=state,
            goal=goal,
            reflection_completed=reflection,
            type=ptype,
        )


@dataclass(frozen=True)
class Transition:
    action: str
    expected_version: int | None
    rationale: str
    new_goal: str | None = None

    @classmethod
    def from_dict(cls, raw: Any, *, location: str) -> "Transition":
        if not isinstance(raw, Mapping):
            raise DatasetError(f"{location}: transition must be a mapping, got {type(raw).__name__}")
        action = raw.get("action")
        if not isinstance(action, str) or not action:
            raise DatasetError(f"{location}: transition.action must be a non-empty string")
        expected = raw.get("expected_version")
        if expected is not None and (not isinstance(expected, int) or isinstance(expected, bool)):
            raise DatasetError(f"{location}: transition.expected_version must be an integer or null")
        rationale = raw.get("rationale")
        if rationale is not None and not isinstance(rationale, str):
            raise DatasetError(f"{location}: transition.rationale must be a string or null")
        new_goal = raw.get("new_goal")
        if new_goal is not None and not isinstance(new_goal, str):
            raise DatasetError(f"{location}: transition.new_goal must be a string or null")
        return cls(
            action=action,
            expected_version=expected,
            rationale=rationale or "",
            new_goal=new_goal,
        )


@dataclass(frozen=True)
class OfflineEdit:
    """One offline edit targeting the project (mandatory-case carrier)."""

    editor: str
    expected_version: int | None
    action: str
    rationale: str
    new_goal: str | None = None

    @classmethod
    def from_dict(cls, raw: Any, *, location: str) -> "OfflineEdit":
        if not isinstance(raw, Mapping):
            raise DatasetError(f"{location}: offline edit must be a mapping, got {type(raw).__name__}")
        editor = raw.get("editor")
        if not isinstance(editor, str) or not editor:
            raise DatasetError(f"{location}: offline edit editor must be a non-empty string")
        action = raw.get("action")
        if not isinstance(action, str) or not action:
            raise DatasetError(f"{location}: offline edit action must be a non-empty string")
        expected = raw.get("expected_version")
        if expected is not None and (not isinstance(expected, int) or isinstance(expected, bool)):
            raise DatasetError(f"{location}: offline edit expected_version must be an integer or null")
        rationale = raw.get("rationale")
        if rationale is not None and not isinstance(rationale, str):
            raise DatasetError(f"{location}: offline edit rationale must be a string or null")
        new_goal = raw.get("new_goal")
        if new_goal is not None and not isinstance(new_goal, str):
            raise DatasetError(f"{location}: offline edit new_goal must be a string or null")
        return cls(
            editor=editor,
            expected_version=expected,
            action=action,
            rationale=rationale or "",
            new_goal=new_goal,
        )


@dataclass(frozen=True)
class SRLCase:
    """Validated, oracle-free view of one LN-10 case."""

    case_id: str
    actor: Actor
    project: Project
    transition: Transition
    concurrent_edits: tuple[OfflineEdit, ...] = ()
    event_log: tuple[Mapping[str, Any], ...] = field(default=())

    @classmethod
    def from_features(cls, features: Mapping[str, Any], *, case_id: str) -> "SRLCase":
        location = f"case {case_id!r}"
        if not isinstance(features, Mapping):
            raise DatasetError(f"{location}: features must be a mapping")
        actor = Actor.from_dict(features.get("actor"), location=f"{location} actor")
        project = Project.from_dict(features.get("project"), location=f"{location} project")
        transition = Transition.from_dict(
            features.get("transition"), location=f"{location} transition"
        )

        edits_raw = features.get("concurrent_edits", [])
        if not isinstance(edits_raw, list):
            raise DatasetError(f"{location}: concurrent_edits must be a list")
        edits = tuple(
            OfflineEdit.from_dict(e, location=f"{location} concurrent_edits[{i}]")
            for i, e in enumerate(edits_raw)
        )

        log_raw = features.get("event_log", [])
        if not isinstance(log_raw, list):
            raise DatasetError(f"{location}: event_log must be a list")
        for i, ev in enumerate(log_raw):
            if not isinstance(ev, Mapping):
                raise DatasetError(f"{location}: event_log[{i}] must be a mapping")
            if not isinstance(ev.get("event_id"), str) or not ev["event_id"]:
                raise DatasetError(f"{location}: event_log[{i}].event_id must be a non-empty string")
        event_log = tuple(log_raw)

        return cls(
            case_id=case_id,
            actor=actor,
            project=project,
            transition=transition,
            concurrent_edits=edits,
            event_log=event_log,
        )


def parse_case(case_id: str, features: Mapping[str, Any]) -> SRLCase:
    """Parse and validate features into an SRLCase (typed failure, no default)."""
    return SRLCase.from_features(features, case_id=case_id)
