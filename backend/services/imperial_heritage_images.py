import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_CORPUS_FILE = Path(__file__).resolve().parents[2] / "data" / "imperial" / "heritage_images.json"

_CACHED_CORPUS: Optional[Dict[str, Any]] = None


def _load_corpus() -> Dict[str, Any]:
    global _CACHED_CORPUS
    if _CACHED_CORPUS is None:
        if not _CORPUS_FILE.exists():
            return {"content_scope": "STTT_IMPERIAL_CITY", "images": []}
        with open(_CORPUS_FILE, mode="r", encoding="utf-8") as f:
            _CACHED_CORPUS = json.load(f)
    return _CACHED_CORPUS


def list_heritage_images(
    site_slug: Optional[str] = None,
    category: Optional[str] = None,
    image_type: Optional[str] = None,
    featured_only: bool = False,
) -> List[Dict[str, Any]]:
    """List verified heritage images with optional filters according to Spec Patch V2.2."""
    corpus = _load_corpus()
    images = corpus.get("images", [])

    results = []
    for item in images:
        if site_slug and item.get("site_slug") != site_slug:
            continue
        if category and item.get("category") != category:
            continue
        if image_type and item.get("image_type") != image_type:
            continue
        if featured_only and not item.get("featured", False):
            continue
        results.append(item)

    return sorted(results, key=lambda x: x.get("sort_order", 999))


def get_image_by_id(image_id: str) -> Optional[Dict[str, Any]]:
    """Get a single verified heritage image by its unique ID."""
    corpus = _load_corpus()
    for item in corpus.get("images", []):
        if item.get("id") == image_id:
            return item
    return None


def get_primary_image_for_site(site_slug: str) -> Optional[Dict[str, Any]]:
    """Get the primary (featured) image for a monument site, or first available."""
    images = list_heritage_images(site_slug=site_slug)
    if not images:
        return None
    for img in images:
        if img.get("featured"):
            return img
    return images[0]
