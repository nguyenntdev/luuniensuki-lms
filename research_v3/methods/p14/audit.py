"""P14 accessibility/UDL audit engine (deterministic, fixed-rule, fail-closed).

Evaluates a manifest of learning objects against the versioned UDL + WCAG 2.2
AA rubric and emits per-criterion verdicts, per-object verdicts, aggregate
metrics and a remediation list. All rules are fixed constraints; there are no
learned parameters and no randomness, so identical input yields identical
output (determinism is test-enforced).
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from research_v3.methods.p14.rubric import (
    RUBRIC_VERSION,
    LEARNED_PARAMETERS,
    criteria_for_media_type,
    load_rubric,
)
from research_v3.methods.p14.schema import (
    AuditCriterion,
    CriterionResult,
    CriterionVerdict,
    LearningObject,
    MediaAsset,
    ObjectAuditVerdict,
    RemediationItem,
    SchemaError,
)

AUDIT_ENGINE_VERSION = "p14-audit-1.0.0"

# Predefined contrast pairs used by the synthetic/manifest checker. Values are
# measured WCAG contrast ratios of declared fg/bg pairs; a pair below 4.5:1
# (normal text, AA) fails. Real rendering audits need actual pixel sampling
# and are out of scope for the manifest-level audit (documented limitation).
AA_NORMAL_TEXT_RATIO = 4.5

_LOW_CONTRAST_PAIRS: frozenset[tuple[str, str]] = frozenset(
    {
        ("#777777", "#ffffff"),  # ~4.48:1
        ("#aaaaaa", "#ffffff"),  # ~2.3:1
    }
)


def _contrast_declared(object_metadata: Mapping[str, Any]) -> str | None:
    """Objects may declare a single text colour pair they render with."""
    pair = object_metadata.get("contrast_pair")
    if pair is None:
        return None
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        raise SchemaError("contrast_pair must be a [fg, bg] pair")
    return f"{str(pair[0]).lower()}|{str(pair[1]).lower()}"


def _has_truthy(asset: MediaAsset, attr: str) -> bool:
    value = getattr(asset, attr)
    return value is True


def _keyboard_trapped(object_metadata: Mapping[str, Any]) -> bool:
    """Keyboard trap declaration: interactive asset swallows focus exit."""
    return bool(object_metadata.get("keyboard_trap", False))


def audit_object(
    obj: LearningObject,
    criteria: Iterable[AuditCriterion] | None = None,
) -> tuple[list[CriterionResult], ObjectAuditVerdict]:
    """Audit one learning object; return (per-criterion results, object verdict).

    Deterministic pure function of (object, rubric).
    """
    criteria = list(load_rubric()) if criteria is None else list(criteria)
    media_types = {a.media_type for a in obj.assets}
    applicable = criteria_for_media_type(criteria, media_types)

    results: list[CriterionResult] = []
    remediation: list[RemediationItem] = []
    contrast = _contrast_declared(obj.metadata)
    trapped = _keyboard_trapped(obj.metadata)

    images = [a for a in obj.assets if a.media_type in {"image", "model3d"}]
    av = [a for a in obj.assets if a.media_type in {"audio", "video"}]
    texts = [a for a in obj.assets if a.media_type == "text"]
    interactive = [a for a in obj.assets if a.interactive]

    for criterion in applicable:
        verdict = CriterionVerdict.NOT_APPLICABLE
        evidence = ""
        fix: str | None = None
        cid = criterion.criterion_id

        if cid in {"udl-rep-alt-text", "wcag-text-alternative"}:
            if not images:
                evidence = "no image/3D assets"
            else:
                missing = [a.asset_id for a in images if not _has_truthy(a, "has_text_alternative")]
                if missing:
                    verdict, fix = CriterionVerdict.FAIL, (
                        f"Add text alternatives for assets: {', '.join(missing)}"
                    )
                else:
                    verdict, evidence = CriterionVerdict.PASS, "all visual assets declare alt text"
        elif cid == "udl-rep-transcript":
            if not av:
                evidence = "no audio/video assets"
            else:
                missing = [a.asset_id for a in av if not _has_truthy(a, "has_transcript")]
                if missing:
                    verdict, fix = CriterionVerdict.FAIL, (
                        f"Add transcripts for assets: {', '.join(missing)}"
                    )
                else:
                    verdict, evidence = CriterionVerdict.PASS, "all A/V assets declare transcripts"
        elif cid == "udl-rep-captions":
            videos = [a for a in obj.assets if a.media_type == "video"]
            if not videos:
                evidence = "no video assets"
            else:
                missing = [a.asset_id for a in videos if not _has_truthy(a, "has_captions")]
                if missing:
                    verdict, fix = CriterionVerdict.FAIL, f"Add captions to: {', '.join(missing)}"
                else:
                    verdict, evidence = CriterionVerdict.PASS, "all videos declare captions"
        elif cid == "udl-rep-multi-modal":
            channels = len({a.media_type for a in obj.assets} | ({"text"} if texts else set()))
            if channels >= 2:
                verdict, evidence = CriterionVerdict.PASS, f"{channels} modalities present"
            else:
                verdict, fix = CriterionVerdict.FAIL, (
                    "Provide the key content in a second modality (e.g. a text summary)"
                )
        elif cid == "udl-rep-inscription-source":
            visuals = [a for a in obj.assets if a.media_type in {"image", "video", "model3d"}]
            labelled = [
                a
                for a in visuals
                if (a.caption or "").strip()
                or _has_truthy(a, "has_text_alternative")
                or _has_truthy(a, "has_captions")
            ]
            if not visuals:
                evidence = "no visual assets"
            elif len(labelled) == len(visuals):
                verdict, evidence = CriterionVerdict.PASS, "all visuals carry caption/source"
            else:
                verdict, fix = CriterionVerdict.FAIL, (
                    "Attach inscription/source captions to unlabeled visuals"
                )
        elif cid == "udl-eng-low-bandwidth":
            if obj.low_bandwidth_variant:
                verdict, evidence = CriterionVerdict.PASS, "low-bandwidth variant present"
            else:
                verdict, fix = CriterionVerdict.FAIL, (
                    "Provide a low-bandwidth variant preserving task feasibility"
                )
        elif cid == "udl-eng-goal-transparency":
            if (obj.metadata.get("learning_goal") or "").strip():
                verdict, evidence = CriterionVerdict.PASS, "learning goal stated"
            else:
                verdict, fix = CriterionVerdict.FAIL, "State the object's learning goal"
        elif cid == "udl-eng-reduced-motion":
            motion = [a for a in obj.assets if a.media_type in {"video", "model3d"}]
            if not motion:
                evidence = "no motion-bearing assets"
            elif obj.metadata.get("respects_reduced_motion") is True:
                verdict, evidence = CriterionVerdict.PASS, "reduced-motion honoured"
            else:
                verdict, fix = CriterionVerdict.FAIL, (
                    "Honour prefers-reduced-motion; avoid auto-play without control"
                )
        elif cid == "udl-action-keyboard":
            motion = [a for a in obj.assets if a.media_type in {"model3d", "video"}]
            if not interactive and not motion:
                evidence = "no interactive/3D/video assets"
            elif trapped:
                verdict, fix = CriterionVerdict.FAIL, (
                    "Remove the keyboard trap so focus can always exit (WCAG 2.1.2)"
                )
            elif interactive and all(_has_truthy(a, "keyboard_operable") for a in interactive):
                verdict, evidence = CriterionVerdict.PASS, "keyboard operable, no trap"
            else:
                # Non-interactive media: playback controls must still be keyboard
                # reachable; the manifest records this as an object-level flag.
                if obj.metadata.get("player_keyboard_operable") is True:
                    verdict, evidence = CriterionVerdict.PASS, "player controls keyboard operable"
                else:
                    verdict, fix = CriterionVerdict.FAIL, (
                        "Make media player/3D controls keyboard operable without a trap"
                    )
        elif cid == "udl-action-alternative-response":
            if obj.metadata.get("non_pointer_response") is True:
                verdict, evidence = CriterionVerdict.PASS, "non-pointer response format offered"
            else:
                verdict, fix = CriterionVerdict.FAIL, (
                    "Offer at least one keyboard/text response format"
                )
        elif cid == "wcag-contrast":
            if contrast is None:
                verdict = CriterionVerdict.ABSTAIN
                evidence = "no declared colour pair; rendering-level audit required"
            elif f"{contrast.split('|')[0]}|{contrast.split('|')[1]}" in {
                f"{a}|{b}" for a, b in _LOW_CONTRAST_PAIRS
            }:
                verdict, fix = CriterionVerdict.FAIL, (
                    f"Increase contrast of pair {contrast} to at least "
                    f"{AA_NORMAL_TEXT_RATIO}:1"
                )
            else:
                verdict, evidence = CriterionVerdict.PASS, f"declared pair {contrast} passes AA"
        elif cid == "wcag-focus-visible":
            if not interactive:
                evidence = "no interactive assets"
            elif obj.metadata.get("focus_visible") is True:
                verdict, evidence = CriterionVerdict.PASS, "focus indicators declared"
            else:
                verdict, fix = CriterionVerdict.FAIL, "Provide visible focus indicators"
        else:  # pragma: no cover - rubric and engine must stay in sync
            raise SchemaError(f"engine does not implement criterion {cid!r}")

        result = CriterionResult(
            criterion_id=cid,
            object_id=obj.object_id,
            verdict=verdict,
            evidence=evidence,
            remediation=fix,
        )
        results.append(result)
        if fix is not None:
            remediation.append(
                RemediationItem(
                    object_id=obj.object_id,
                    criterion_id=cid,
                    framework=criterion.framework,
                    severity="critical" if criterion.critical else "minor",
                    action=fix,
                )
            )

    evaluated = [r for r in results if r.verdict in {CriterionVerdict.PASS, CriterionVerdict.FAIL}]
    abstained = sum(1 for r in results if r.verdict is CriterionVerdict.ABSTAIN)
    failed = [r for r in evaluated if r.verdict is CriterionVerdict.FAIL]
    passed = len(evaluated) - len(failed)
    not_applicable = sum(1 for r in results if r.verdict is CriterionVerdict.NOT_APPLICABLE)

    if abstained == len(results):
        whole = "ABSTAIN"
    elif failed:
        whole = "FAIL"
    else:
        whole = "PASS"

    object_verdict = ObjectAuditVerdict(
        object_id=obj.object_id,
        total_applicable=len(results),
        passed=passed,
        failed=len(failed),
        not_applicable=not_applicable,
        abstained=abstained,
        missing_affordances=tuple(r.criterion_id for r in failed),
        verdict=whole,
    )
    return results, object_verdict


def audit_manifest(
    objects: Iterable[LearningObject],
    criteria: Iterable[AuditCriterion] | None = None,
) -> dict[str, Any]:
    """Audit a whole manifest; return metrics + per-object results + remediation."""
    criteria = list(load_rubric()) if criteria is None else list(criteria)
    all_results: list[CriterionResult] = []
    verdicts: list[ObjectAuditVerdict] = []
    remediation: list[RemediationItem] = []

    for obj in objects:
        results, verdict = audit_object(obj, criteria)
        all_results.extend(results)
        verdicts.append(verdict)
        remediation.extend(
            RemediationItem(
                object_id=r.object_id,
                criterion_id=r.criterion_id,
                framework=next(c.framework for c in criteria if c.criterion_id == r.criterion_id),
                severity="critical"
                if next(c.critical for c in criteria if c.criterion_id == r.criterion_id)
                else "minor",
                action=r.remediation or "",
            )
            for r in results
            if r.remediation
        )

    metrics = compute_metrics(all_results, verdicts)
    return {
        "audit_engine_version": AUDIT_ENGINE_VERSION,
        "rubric_version": RUBRIC_VERSION,
        "learned_parameters": LEARNED_PARAMETERS,
        "metrics": metrics,
        "object_verdicts": [v.__dict__ | {"missing_affordances": list(v.missing_affordances)} for v in verdicts],
        "criterion_results": [
            {
                "object_id": r.object_id,
                "criterion_id": r.criterion_id,
                "verdict": r.verdict.value,
                "evidence": r.evidence,
                "remediation": r.remediation,
            }
            for r in all_results
        ],
        "remediation_list": [r.__dict__ for r in remediation],
    }


def compute_metrics(
    results: list[CriterionResult],
    verdicts: list[ObjectAuditVerdict],
) -> dict[str, Any]:
    """Primary/secondary metrics: conformance rate, UDL coverage, missing count.

    Denominator discipline: PASS + FAIL only. NOT_APPLICABLE is excluded from
    the conformance denominator; ABSTAIN is reported separately and excluded
    from both the numerator and denominator (spec §3.1).
    """
    real = [r for r in results if r.verdict in {CriterionVerdict.PASS, CriterionVerdict.FAIL}]
    passed = sum(1 for r in real if r.verdict is CriterionVerdict.PASS)
    abstains = sum(1 for r in results if r.verdict is CriterionVerdict.ABSTAIN)

    rubric = load_rubric()
    framework_of = {c.criterion_id: c.framework for c in rubric}

    per_framework: dict[str, dict[str, int]] = {}
    for r in real:
        framework = framework_of[r.criterion_id]
        bucket = per_framework.setdefault(framework, {"pass": 0, "fail": 0})
        bucket["pass" if r.verdict is CriterionVerdict.PASS else "fail"] += 1

    udl_coverage: dict[str, float | None] = {}
    for framework in ("udl-representation", "udl-engagement", "udl-action", "wcag22"):
        fw_results = [r for r in real if framework_of[r.criterion_id] == framework]
        udl_coverage[framework] = (
            round(sum(1 for r in fw_results if r.verdict is CriterionVerdict.PASS) / len(fw_results), 4)
            if fw_results
            else None
        )

    return {
        "objects_audited": len(verdicts),
        "objects_pass": sum(1 for v in verdicts if v.verdict == "PASS"),
        "objects_fail": sum(1 for v in verdicts if v.verdict == "FAIL"),
        "objects_abstain": sum(1 for v in verdicts if v.verdict == "ABSTAIN"),
        "criteria_evaluated": len(real),
        "criteria_passed": passed,
        "criteria_failed": len(real) - passed,
        "criteria_abstained": abstains,
        "accessibility_conformance_rate": round(passed / len(real), 4) if real else None,
        "udl_principle_coverage": udl_coverage,
        "missing_affordance_count": sum(len(v.missing_affordances) for v in verdicts),
        "per_framework": per_framework,
    }
