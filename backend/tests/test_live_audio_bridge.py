"""Capacity/lifecycle tests for the realtime audio bridge (no aiortc needed)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.live_audio_bridge import AudioBridge, BridgeRegistry, CapacityError


def test_registry_caps_at_max():
    reg = BridgeRegistry(max_sessions=2)
    assert reg.try_acquire("s1") is True
    assert reg.try_acquire("s2") is True
    # Third distinct session is refused.
    assert reg.try_acquire("s3") is False
    assert reg.active_count == 2
    assert reg.has_capacity() is False


def test_registry_acquire_is_idempotent_per_session():
    reg = BridgeRegistry(max_sessions=1)
    assert reg.try_acquire("s1") is True
    # Re-acquiring the same session does not consume a second slot.
    assert reg.try_acquire("s1") is True
    assert reg.active_count == 1


def test_registry_release_frees_slot():
    reg = BridgeRegistry(max_sessions=1)
    assert reg.try_acquire("s1") is True
    assert reg.try_acquire("s2") is False
    reg.release("s1")
    assert reg.has_capacity() is True
    assert reg.try_acquire("s2") is True


def test_registry_zero_capacity_refuses_all():
    reg = BridgeRegistry(max_sessions=0)
    assert reg.try_acquire("s1") is False
    assert reg.active_count == 0


def test_bridge_acquire_reflects_registry():
    reg = BridgeRegistry(max_sessions=1)
    b1 = AudioBridge(session_id="a", janus_room_id=1, credential="c", orchestrator=None, registry=reg)
    b2 = AudioBridge(session_id="b", janus_room_id=2, credential="c", orchestrator=None, registry=reg)
    assert b1.acquire() is True
    assert b2.acquire() is False  # at capacity → caller falls back to legacy


async def _connect_without_acquire():
    b = AudioBridge(session_id="x", janus_room_id=1, credential="c", orchestrator=None,
                    registry=BridgeRegistry(max_sessions=1))
    await b.connect("ws://janus", [])


def test_connect_without_slot_raises():
    import asyncio

    try:
        asyncio.run(_connect_without_acquire())
        assert False, "expected CapacityError"
    except CapacityError:
        pass


def test_close_releases_slot():
    import asyncio

    reg = BridgeRegistry(max_sessions=1)
    b = AudioBridge(session_id="a", janus_room_id=1, credential="c", orchestrator=None, registry=reg)
    assert b.acquire() is True
    assert reg.active_count == 1
    asyncio.run(b.close())
    assert reg.active_count == 0
    # Slot is now free for another session.
    assert reg.try_acquire("b") is True
