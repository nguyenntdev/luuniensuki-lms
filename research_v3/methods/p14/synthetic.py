"""Deterministic synthetic learning-object manifest for P14.

External rights-cleared media could not be obtained in this environment:
- Smithsonian Open Access API: HTTP 403 without an API key (key required;
  https://www.si.edu/openaccess/devtools).
- Europeana API: HTTP 401 without an API key (key required;
  https://pro.europeana.eu/page/apis).
- hue-heritage-corpus: BLOCKED (no written permission; unlicensed).

Per the study rules, the fallback is a *documented synthetic media manifest*
that is clearly labelled "synthetic, no third-party rights". No real Huế (or
any third-party) imagery is embedded or described as usable. Every object
carries origin "synthetic:..." and rights "Synthetic - no third-party rights".
The study is therefore marked PARTIAL for external media.

Deterministic: seeded mutation generator; identical input -> identical bytes.
"""
from __future__ import annotations

import hashlib
from typing import Any

from research_v3.methods.p14.schema import LearningObject, MediaAsset, SchemaError

SYNTHETIC_MANIFEST_VERSION = "p14-synthetic-manifest-1.0.0"
SYNTHETIC_RIGHTS = "Synthetic - no third-party rights (generated for P14, not real imagery)"
SYNTHETIC_ORIGIN_PREFIX = "synthetic:"

# ---------------------------------------------------------------- base objects


def _asset(asset_id: str, media_type: str, **kw: Any) -> MediaAsset:
    return MediaAsset(asset_id=asset_id, media_type=media_type, rights=SYNTHETIC_RIGHTS, **kw)


def synthetic_manifest() -> list[LearningObject]:
    """Twelve deterministic objects covering pass/fail/abstain families."""
    objs: list[LearningObject] = []

    # Fully compliant object: alt, transcript, captions, keyboard, contrast, LBW.
    objs.append(
        LearningObject(
            object_id="syn-obj-01-compliant",
            title="Compliant bilingual motif card",
            origin=f"{SYNTHETIC_ORIGIN_PREFIX}compliant-card",
            source_url=None,
            rights=SYNTHETIC_RIGHTS,
            assets=(
                _asset("a-img", "image", has_text_alternative=True, caption="Motif A, rubbing, synthetic"),
                _asset("a-txt", "text"),
                _asset("a-audio", "audio", has_transcript=True),
            ),
            low_bandwidth_variant=(_asset("lb-txt", "text"),),
            metadata={
                "learning_goal": "Read one motif and its inscription context",
                "non_pointer_response": True,
                "contrast_pair": ["#1a1a1a", "#ffffff"],
            },
        )
    )

    # Missing alt text.
    objs.append(
        LearningObject(
            object_id="syn-obj-02-no-alt",
            title="Image without text alternative",
            origin=f"{SYNTHETIC_ORIGIN_PREFIX}mutation-no-alt",
            source_url=None,
            rights=SYNTHETIC_RIGHTS,
            assets=(
                _asset("b-img", "image", has_text_alternative=False),
                _asset("b-txt", "text"),
            ),
            low_bandwidth_variant=(_asset("lb-txt", "text"),),
            metadata={"learning_goal": "g", "non_pointer_response": True, "contrast_pair": ["#000000", "#ffffff"]},
        )
    )

    # Missing transcript.
    objs.append(
        LearningObject(
            object_id="syn-obj-03-no-transcript",
            title="Audio narration without transcript",
            origin=f"{SYNTHETIC_ORIGIN_PREFIX}mutation-no-transcript",
            source_url=None,
            rights=SYNTHETIC_RIGHTS,
            assets=(
                _asset("c-audio", "audio", has_transcript=False),
                _asset("c-txt", "text"),
            ),
            low_bandwidth_variant=(_asset("lb-txt", "text"),),
            metadata={"learning_goal": "g", "non_pointer_response": True, "contrast_pair": ["#000000", "#ffffff"]},
        )
    )

    # Keyboard trap on an interactive 3D viewer.
    objs.append(
        LearningObject(
            object_id="syn-obj-04-keyboard-trap",
            title="3D viewer that traps keyboard focus",
            origin=f"{SYNTHETIC_ORIGIN_PREFIX}mutation-trap",
            source_url=None,
            rights=SYNTHETIC_RIGHTS,
            assets=(
                _asset(
                    "d-3d", "model3d", interactive=True, keyboard_operable=True,
                    has_text_alternative=True,
                ),
                _asset("d-txt", "text"),
            ),
            low_bandwidth_variant=(_asset("lb-txt", "text"),),
            metadata={
                "learning_goal": "g", "non_pointer_response": True,
                "contrast_pair": ["#000000", "#ffffff"],
                "keyboard_trap": True, "respects_reduced_motion": True, "focus_visible": True,
            },
        )
    )

    # Low-bandwidth variant WITH transcript passes (a/v + text + LBW).
    objs.append(
        LearningObject(
            object_id="syn-obj-05-lbw-with-transcript",
            title="Low-bandwidth variant with transcript",
            origin=f"{SYNTHETIC_ORIGIN_PREFIX}compliant-lbw",
            source_url=None,
            rights=SYNTHETIC_RIGHTS,
            assets=(
                _asset("e-video", "video", has_transcript=True, has_captions=True),
                _asset("e-txt", "text"),
            ),
            low_bandwidth_variant=(_asset("lb-transcript", "text"),),
            metadata={
                "learning_goal": "g", "non_pointer_response": True,
                "contrast_pair": ["#000000", "#ffffff"], "respects_reduced_motion": True,
                "player_keyboard_operable": True,
            },
        )
    )

    # Video without captions.
    objs.append(
        LearningObject(
            object_id="syn-obj-06-video-no-captions",
            title="Video without captions",
            origin=f"{SYNTHETIC_ORIGIN_PREFIX}mutation-no-captions",
            source_url=None,
            rights=SYNTHETIC_RIGHTS,
            assets=(
                _asset("f-video", "video", has_transcript=True, has_captions=False),
                _asset("f-txt", "text"),
            ),
            low_bandwidth_variant=(_asset("lb-txt", "text"),),
            metadata={"learning_goal": "g", "non_pointer_response": True, "contrast_pair": ["#000000", "#ffffff"], "respects_reduced_motion": True},
        )
    )

    # Low contrast declared pair.
    objs.append(
        LearningObject(
            object_id="syn-obj-07-low-contrast",
            title="Low-contrast text pair",
            origin=f"{SYNTHETIC_ORIGIN_PREFIX}mutation-contrast",
            source_url=None,
            rights=SYNTHETIC_RIGHTS,
            assets=(_asset("g-txt", "text"),),
            low_bandwidth_variant=(_asset("lb-txt", "text"),),
            metadata={"learning_goal": "g", "non_pointer_response": True, "contrast_pair": ["#aaaaaa", "#ffffff"]},
        )
    )

    # No low-bandwidth variant.
    objs.append(
        LearningObject(
            object_id="syn-obj-08-no-lbw",
            title="No low-bandwidth variant",
            origin=f"{SYNTHETIC_ORIGIN_PREFIX}mutation-no-lbw",
            source_url=None,
            rights=SYNTHETIC_RIGHTS,
            assets=(
                _asset("h-img", "image", has_text_alternative=True),
                _asset("h-txt", "text"),
            ),
            low_bandwidth_variant=None,
            metadata={"learning_goal": "g", "non_pointer_response": True, "contrast_pair": ["#000000", "#ffffff"]},
        )
    )

    # Single-modality image-only object.
    objs.append(
        LearningObject(
            object_id="syn-obj-09-image-only",
            title="Image only, no second modality",
            origin=f"{SYNTHETIC_ORIGIN_PREFIX}mutation-single-modality",
            source_url=None,
            rights=SYNTHETIC_RIGHTS,
            assets=(_asset("i-img", "image", has_text_alternative=True),),
            low_bandwidth_variant=(_asset("lb-txt", "text"),),
            metadata={"learning_goal": "g", "non_pointer_response": True, "contrast_pair": ["#000000", "#ffffff"]},
        )
    )

    # 3D not keyboard operable.
    objs.append(
        LearningObject(
            object_id="syn-obj-10-3d-no-keyboard",
            title="3D asset not keyboard operable",
            origin=f"{SYNTHETIC_ORIGIN_PREFIX}mutation-no-keyboard",
            source_url=None,
            rights=SYNTHETIC_RIGHTS,
            assets=(
                _asset("j-3d", "model3d", interactive=True, keyboard_operable=False, has_text_alternative=True),
                _asset("j-txt", "text"),
            ),
            low_bandwidth_variant=(_asset("lb-txt", "text"),),
            metadata={"learning_goal": "g", "non_pointer_response": True, "contrast_pair": ["#000000", "#ffffff"], "respects_reduced_motion": True, "focus_visible": True},
        )
    )

    # No declared contrast pair -> wcag-contrast ABSTAINs.
    objs.append(
        LearningObject(
            object_id="syn-obj-11-contrast-unknown",
            title="Contrast not declared (auditor abstains)",
            origin=f"{SYNTHETIC_ORIGIN_PREFIX}mutation-contrast-unknown",
            source_url=None,
            rights=SYNTHETIC_RIGHTS,
            assets=(
                _asset("k-img", "image", has_text_alternative=True),
                _asset("k-txt", "text"),
            ),
            low_bandwidth_variant=(_asset("lb-txt", "text"),),
            metadata={"learning_goal": "g", "non_pointer_response": True},
        )
    )

    # Missing learning goal + no non-pointer response (engagement/action fails).
    objs.append(
        LearningObject(
            object_id="syn-obj-12-no-goal",
            title="Missing learning goal and pointer-only response",
            origin=f"{SYNTHETIC_ORIGIN_PREFIX}mutation-no-goal",
            source_url=None,
            rights=SYNTHETIC_RIGHTS,
            assets=(
                _asset("l-img", "image", has_text_alternative=True),
                _asset("l-txt", "text"),
            ),
            low_bandwidth_variant=(_asset("lb-txt", "text"),),
            metadata={"contrast_pair": ["#000000", "#ffffff"]},
        )
    )

    # Fully compliant interactive 3D object (needed so the remove_keyboard
    # mutation has a pre-mutation PASS to flip: mutation-reveals-mechanism).
    objs.append(
        LearningObject(
            object_id="syn-obj-13-compliant-interactive",
            title="Compliant interactive 3D object",
            origin=f"{SYNTHETIC_ORIGIN_PREFIX}compliant-interactive",
            source_url=None,
            rights=SYNTHETIC_RIGHTS,
            assets=(
                _asset(
                    "m-3d", "model3d", interactive=True, keyboard_operable=True,
                    has_text_alternative=True, caption="Urn relief, synthetic mesh",
                ),
                _asset("m-txt", "text"),
            ),
            low_bandwidth_variant=(_asset("lb-txt", "text"),),
            metadata={
                "learning_goal": "g", "non_pointer_response": True,
                "contrast_pair": ["#000000", "#ffffff"],
                "respects_reduced_motion": True, "focus_visible": True,
            },
        )
    )

    return objs


# ------------------------------------------------- mutation/stress generators


def mutate(
    obj: LearningObject, mutation: str, rng_seed: int = 0
) -> LearningObject:
    """Named-mechanism mutations for ablation/mutation tests (A1-A4 family).

    Deterministic: the seed only feeds the id hash, never the mutation body.
    """
    from dataclasses import replace

    tag = hashlib.sha256(f"{obj.object_id}:{mutation}:{rng_seed}".encode()).hexdigest()[:8]
    base_id = f"{obj.object_id}-mut-{mutation}-{tag}"
    if mutation == "remove_alt_text":
        assets = tuple(
            replace(a, has_text_alternative=False) if a.media_type in {"image", "model3d"} else a
            for a in obj.assets
        )
        return LearningObject(
            object_id=base_id, title=obj.title, origin=f"{SYNTHETIC_ORIGIN_PREFIX}mutation-remove-alt",
            source_url=None, rights=SYNTHETIC_RIGHTS, assets=assets,
            low_bandwidth_variant=obj.low_bandwidth_variant, metadata=dict(obj.metadata),
        )
    if mutation == "remove_transcript":
        assets = tuple(
            replace(a, has_transcript=False) if a.media_type in {"audio", "video"} else a
            for a in obj.assets
        )
        return LearningObject(
            object_id=base_id, title=obj.title, origin=f"{SYNTHETIC_ORIGIN_PREFIX}mutation-remove-transcript",
            source_url=None, rights=SYNTHETIC_RIGHTS, assets=assets,
            low_bandwidth_variant=obj.low_bandwidth_variant, metadata=dict(obj.metadata),
        )
    if mutation == "remove_keyboard":
        assets = tuple(
            replace(a, keyboard_operable=False) if a.interactive else a for a in obj.assets
        )
        return LearningObject(
            object_id=base_id, title=obj.title, origin=f"{SYNTHETIC_ORIGIN_PREFIX}mutation-remove-keyboard",
            source_url=None, rights=SYNTHETIC_RIGHTS, assets=assets,
            low_bandwidth_variant=obj.low_bandwidth_variant, metadata=dict(obj.metadata),
        )
    if mutation == "remove_lbw":
        return LearningObject(
            object_id=base_id, title=obj.title, origin=f"{SYNTHETIC_ORIGIN_PREFIX}mutation-remove-lbw",
            source_url=None, rights=SYNTHETIC_RIGHTS, assets=obj.assets,
            low_bandwidth_variant=None, metadata=dict(obj.metadata),
        )
    raise SchemaError(f"unknown mutation {mutation!r}")


def manifest_sha256(objects: list[LearningObject]) -> str:
    """Deterministic hash of the manifest content."""
    from research_v2.contracts.canonical_hash import sha256_input

    return sha256_input([o.to_dict() for o in objects])
