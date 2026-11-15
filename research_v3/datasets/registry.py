"""Dataset registry and license gating for Research V3.

The cardinal rule from the spec: a public URL is NOT a license. A dataset is
usable for a primary claim only when its card is APPROVED with a captured
license-text hash and a verified file hash. Everything else stays BLOCKED.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research_v3.contracts.cards import ContractError, DatasetCard

REGISTRY_PATH = Path(__file__).resolve().parent / "registry.yaml"


class LicenseGateError(ContractError):
    """Raised when a study tries to use a dataset that is not APPROVED."""


def load_registry(path: Path | None = None) -> list[DatasetCard]:
    """Load dataset cards from the YAML registry (a JSON-compatible subset)."""
    try:
        import yaml
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("PyYAML is required to read the dataset registry") from exc

    target = Path(path or REGISTRY_PATH)
    if not target.is_file():
        return []
    raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    cards: list[DatasetCard] = []
    for entry in raw.get("datasets", []):
        payload = dict(entry)
        for key in ("allowed_uses", "group_keys"):
            if key in payload and payload[key] is not None:
                payload[key] = tuple(payload[key])
        cards.append(DatasetCard(**payload))
    return cards


def approve(registry: list[DatasetCard], dataset_id: str) -> DatasetCard:
    for card in registry:
        if card.dataset_id == dataset_id:
            return card
    raise LicenseGateError(f"dataset {dataset_id!r} not registered")


def require_approved(registry: list[DatasetCard], dataset_ids: list[str], *, paper_id: str) -> list[DatasetCard]:
    """Fail-closed: every dataset needed for a primary claim must be APPROVED."""
    approved: list[DatasetCard] = []
    problems: list[str] = []
    for ident in dataset_ids:
        card = next((c for c in registry if c.dataset_id == ident), None)
        if card is None:
            problems.append(f"{ident}: not registered")
            continue
        if card.status != "APPROVED":
            problems.append(f"{ident}: status={card.status} ({card.blocked_reason or 'no reason'})")
            continue
        approved.append(card)
    if problems:
        raise LicenseGateError(
            f"{paper_id}: cannot run a primary claim on non-approved datasets: {problems}"
        )
    return approved


def write_registry(cards: list[DatasetCard], path: Path | None = None) -> None:
    import yaml

    target = Path(path or REGISTRY_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "v3",
        "note": (
            "A public URL is not a license. Only APPROVED cards with a captured "
            "license-text hash and verified file hash may back a primary claim."
        ),
        "datasets": [c.to_dict() for c in cards],
    }
    target.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def summary(cards: list[DatasetCard]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for card in cards:
        counts[card.status] = counts.get(card.status, 0) + 1
    return {"total": len(cards), "by_status": counts}
