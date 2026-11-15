"""Canonical hashing standard for all Research V2 records.

Standard: sha256 of ``json.dumps(obj, sort_keys=True, separators=(",", ":"),
ensure_ascii=False).encode("utf-8")``. This single standard is used for input
digests, dataset fingerprints and manifests so that any byte change is
detectable and hashes are stable across machines.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

STANDARD_NAME = "sha256(sort_keys,compact,utf8)"


def canonical_json(obj: Any) -> bytes:
    """Serialize an object into canonical UTF-8 JSON bytes.

    ``allow_nan=False`` guarantees strict-JSON compliance: Infinity/NaN raise.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_input(obj: Any) -> str:
    """Canonical digest of an arbitrary JSON-serializable object."""
    return sha256_bytes(canonical_json(obj))


def sha256_file(path) -> str:
    from pathlib import Path

    return sha256_bytes(Path(path).read_bytes())


def verify_input_hash(record: Mapping[str, Any], *, input_key: str = "input", hash_key: str = "input_hash") -> None:
    """Assert that a record's stored input hash matches its input.

    Raises ``ValueError`` with a precise message when the digest is stale.
    """
    if input_key not in record:
        raise ValueError(f"record missing {input_key!r}")
    if hash_key not in record:
        raise ValueError(f"record missing {hash_key!r}")
    expected = sha256_input(record[input_key])
    actual = record[hash_key]
    if actual != expected:
        raise ValueError(
            f"stale {hash_key}: stored={actual!r} expected={expected!r} "
            f"(standard {STANDARD_NAME})"
        )
