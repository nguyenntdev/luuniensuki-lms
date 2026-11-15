"""Fetch a dataset from its official source and capture immutable provenance.

Never invents a license. The fetcher records the URL, the HTTP status, the file
SHA-256 and byte size, and stores the raw file OUTSIDE Git (``private_data/raw``)
so restricted data is never committed. License text is fetched separately and
hashed; a reviewer still has to set the card to APPROVED.
"""
from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RAW_ROOT = Path(__file__).resolve().parents[3] / "private_data" / "raw"
USER_AGENT = "luunien-research-v3/1.0 (academic use; contact maintainer)"
TIMEOUT_SECONDS = 120


class FetchError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(
    *,
    provider: str,
    version: str,
    filename: str,
    urls: list[str],
    license_url: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Download the first URL that works and return a provenance record."""
    target_dir = RAW_ROOT / provider / version
    target = target_dir / filename
    record: dict[str, Any] = {
        "provider": provider,
        "version": version,
        "filename": filename,
        "requested_urls": urls,
        "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "FAILED",
    }

    if dry_run:
        record["status"] = "DRY_RUN"
        return record

    target_dir.mkdir(parents=True, exist_ok=True)
    last_error: str | None = None
    for url in urls:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
                if response.status != 200:
                    last_error = f"HTTP {response.status} from {url}"
                    continue
                payload = response.read()
            target.write_bytes(payload)
            record.update(
                {
                    "used_url": url,
                    "http_status": 200,
                    "byte_size": len(payload),
                    "sha256": _sha256(target),
                    "status": "DOWNLOADED",
                    "path": str(target),
                }
            )
            break
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    else:
        record["error"] = last_error
        return record

    if license_url:
        try:
            request = urllib.request.Request(license_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
                license_bytes = response.read()
            license_path = target_dir / "LICENSE.txt"
            license_path.write_bytes(license_bytes)
            record["license_url"] = license_url
            record["license_text_sha256"] = hashlib.sha256(license_bytes).hexdigest()
            record["license_path"] = str(license_path)
        except Exception as exc:  # pragma: no cover - network dependent
            record["license_error"] = f"{type(exc).__name__}: {exc}"

    manifest = target_dir / "provenance.json"
    manifest.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record
