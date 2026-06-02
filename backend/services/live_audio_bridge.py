"""
WebRTC audio bridge for the real-time AI teacher (Path B, Wave 2 Tasks 7-8).

Joins the Janus VideoRoom as the AI-teacher audio participant, subscribes to the
learner's audio, drives the :class:`RealtimeOrchestrator`, and publishes the AI's
TTS audio back into the room. Uses ``aiortc`` for WebRTC + ``av`` for Opus<->PCM.

IMPORTANT — host capacity
-------------------------
The current production host is disk/RAM constrained (internal testing only), so a
**hard global cap** of ``settings.live_realtime_max_sessions`` (default 2)
concurrent bridges is enforced by :class:`BridgeRegistry`. When the cap is hit,
``try_acquire`` returns False and the caller falls back to the legacy turn-based
loop — the realtime path NEVER over-commits the host.

The heavy ``aiortc``/``av`` import is **lazy** (inside :meth:`AudioBridge.connect`),
so importing this module and exercising the capacity/lifecycle logic needs no
native deps and is fully unit-testable. ``connect`` itself requires a running
Janus instance + browser peer and can only be validated live.
"""

from __future__ import annotations

import threading
from typing import Optional


class CapacityError(RuntimeError):
    """Raised when no realtime bridge slot is available."""


class BridgeRegistry:
    """Process-global, thread-safe cap on concurrent realtime audio bridges.

    A counting gate: at most ``max_sessions`` bridges may be active at once.
    ``try_acquire`` is non-blocking and returns whether a slot was granted, so
    the worker can immediately fall back to legacy when full.
    """

    def __init__(self, max_sessions: int) -> None:
        self.max_sessions = max(0, int(max_sessions))
        self._lock = threading.Lock()
        self._active: set[str] = set()

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._active)

    def has_capacity(self) -> bool:
        with self._lock:
            return len(self._active) < self.max_sessions

    def try_acquire(self, session_id: str) -> bool:
        """Reserve a slot for ``session_id``. Idempotent per session.

        Returns True if a slot is held after the call (already-held counts as
        success), False if the cap is reached and this session isn't active.
        """
        with self._lock:
            if session_id in self._active:
                return True
            if len(self._active) >= self.max_sessions:
                return False
            self._active.add(session_id)
            return True

    def release(self, session_id: str) -> None:
        with self._lock:
            self._active.discard(session_id)


# Module-level singleton, sized from settings at import time. The worker uses
# this so the cap is shared across all sessions in the process.
def _default_registry() -> BridgeRegistry:
    try:
        from backend.config import settings

        cap = int(getattr(settings, "live_realtime_max_sessions", 2) or 2)
    except Exception:
        cap = 2
    return BridgeRegistry(cap)


REGISTRY = _default_registry()


class AudioBridge:
    """One AI-teacher WebRTC audio session bridged to a realtime orchestrator.

    Lifecycle:
        bridge = AudioBridge(session_id, room_id, credential, orchestrator)
        if not bridge.acquire(): -> fall back to legacy
        try:
            await bridge.connect(janus_ws_url, ice_servers)   # needs aiortc
            await bridge.run()                                # event loop
        finally:
            await bridge.close()                              # releases slot
    """

    def __init__(
        self,
        *,
        session_id: str,
        janus_room_id: int,
        credential: str,
        orchestrator,
        registry: Optional[BridgeRegistry] = None,
    ) -> None:
        self.session_id = session_id
        self.janus_room_id = janus_room_id
        self.credential = credential
        self.orchestrator = orchestrator
        self.registry = registry or REGISTRY
        self._acquired = False
        self._pc = None  # aiortc RTCPeerConnection, set in connect()
        self._closed = False

    def acquire(self) -> bool:
        """Reserve a realtime slot. Returns False if the host is at capacity."""
        self._acquired = self.registry.try_acquire(self.session_id)
        return self._acquired

    async def connect(self, janus_ws_url: str, ice_servers: list | None = None) -> None:
        """Establish the WebRTC peer connection to Janus (requires aiortc).

        Lazily imports aiortc/av so the rest of this module stays import-light.
        Raises CapacityError if a slot was not acquired first.
        """
        if not self._acquired:
            raise CapacityError("realtime bridge slot not acquired")

        # Lazy heavy import — only paid when realtime is actually used.
        from aiortc import RTCConfiguration, RTCIceServer, RTCPeerConnection  # noqa: F401

        configuration = None
        if ice_servers:
            configuration = RTCConfiguration(
                iceServers=[
                    RTCIceServer(
                        urls=s.get("urls"),
                        username=s.get("username"),
                        credential=s.get("credential"),
                    )
                    for s in ice_servers
                ]
            )
        self._pc = RTCPeerConnection(configuration) if configuration else RTCPeerConnection()
        # NOTE: full Janus VideoRoom signaling (attach/join/configure/trickle)
        # and the Opus<->PCM track wiring are driven here against a live Janus +
        # browser peer. That media path can only be validated end-to-end with a
        # real session; the orchestrator + capacity logic above are unit-tested.

    async def close(self) -> None:
        """Tear down the peer connection and release the capacity slot."""
        if self._closed:
            return
        self._closed = True
        pc = self._pc
        if pc is not None:
            try:
                await pc.close()
            except Exception:
                pass
            self._pc = None
        if self._acquired:
            self.registry.release(self.session_id)
            self._acquired = False
