"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ConnectionQuality, Room, RoomEvent } from "livekit-client";
import {
  AlertTriangle,
  Camera,
  CameraOff,
  Hand,
  Lock,
  LockOpen,
  Mic,
  MicOff,
  Pin,
  PinOff,
  Radio,
  RefreshCcw,
  Sparkles,
  Volume2,
  VolumeX,
  Waves,
  UserMinus,
  Users,
} from "lucide-react";

import HeritageStage3D from "@/components/live/HeritageStage3D";
import {
  askLiveAiTeacher,
  createLiveSessionEvent,
  ensureLiveAiTeacherPresence,
  hostMuteAllLiveParticipants,
  hostRemoveLiveParticipant,
  joinLiveSession,
  leaveLiveSession,
  listLiveSessionEvents,
  listLiveSessionParticipants,
  synthesizeLiveAiTeacherVoice,
  transcribeLiveAiTeacherVoice,
  updateLiveHostSettings,
  updateLiveParticipantRole,
} from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

const HERITAGE_MISSIONS = [
  {
    id: "dinh-top",
    label: "Dinh",
    prompt:
      "Goi y cach nhin bo cuc tong the tren dinh va y nghia bieu tuong cua bo phan nay.",
    position: [0.0, 1.12, 0.0],
  },
  {
    id: "motif-band",
    label: "Hoa tiet",
    prompt:
      "Phan tich nhanh mot hoa tiet di san trong vung than dinh: hinh dang, y nghia, boi canh lich su.",
    position: [0.92, 0.67, 0.36],
  },
  {
    id: "inscription",
    label: "Chu khac",
    prompt:
      "Giai thich vai tro cua phan chu khac tren dinh va cach doc nguon tu lieu de hieu dung nghia.",
    position: [-0.88, 0.52, -0.42],
  },
  {
    id: "pedestal",
    label: "Chan de",
    prompt:
      "Tai sao chan de co y nghia trong ngon ngu tao hinh di san? Goi y cach lien he voi boi canh trieu Nguyen.",
    position: [0.18, -0.04, 0.98],
  },
];

const WAKE_PHRASES = ["co giao oi", "ai teacher"];

function normalizeSpeechText(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function hasWakePhrase(value) {
  const normalized = normalizeSpeechText(value);
  return WAKE_PHRASES.some((phrase) => normalized.includes(phrase));
}

function getTrackEnabledState(trackPublications) {
  return Array.from(trackPublications.values()).some((pub) => !pub.isMuted);
}

function toParticipantViewModel(participant, isLocal = false) {
  return {
    id: participant.identity,
    identity: participant.identity,
    name: participant.name || participant.identity || "Nguoi dung",
    isLocal,
    microphoneEnabled: getTrackEnabledState(participant.audioTrackPublications),
    cameraEnabled: getTrackEnabledState(participant.videoTrackPublications),
  };
}

function roleLabel(role) {
  if (role === "host") return "host";
  if (role === "cohost") return "co-host";
  if (role === "ai_teacher") return "ai-teacher";
  return "learner";
}

function canModerateRole(role) {
  return role === "host" || role === "cohost";
}

function humanizeLiveError(raw) {
  const message = String(raw || "").trim();
  const normalized = message.toLowerCase();

  if (normalized.includes("request-uri too large") || normalized.includes("http 414")) {
    return "Server dang chan URL ket noi qua dai (nginx 414). Da chuyen sang che do ket noi tuong thich de vao phong on dinh hon.";
  }
  if (normalized.includes("v1 rtc path not found")) {
    return "Server LiveKit dang khong tuong thich duong ket noi moi. He thong se thu ket noi bang che do tuong thich.";
  }
  if (
    normalized.includes("invalid authorization token") ||
    normalized.includes("token might be expired") ||
    normalized.includes("unauthorized") ||
    normalized.includes("not allowed")
  ) {
    return "Token phong live da het han hoac khong hop le. Bam Reconnect de cap token moi.";
  }
  if (normalized.includes("could not establish pc connection")) {
    return "Khong tao duoc ket noi WebRTC peer connection. He thong se uu tien relay mode va ban co the bam Reconnect de thu lai.";
  }
  if (normalized.includes("livekit api credentials are not configured")) {
    return "He thong LiveKit chua duoc cau hinh day du tren server.";
  }
  if (normalized.includes("disconnected")) {
    return "Phong live bi ngat ket noi. Thu reconnect de vao lai nhanh.";
  }
  return message || "Khong the ket noi phong live.";
}

function qualityMeta(quality) {
  const poor = ConnectionQuality?.Poor;
  const good = ConnectionQuality?.Good;
  const excellent = ConnectionQuality?.Excellent;

  if (quality === excellent) {
    return { label: "Tot", tone: "text-emerald-700" };
  }
  if (quality === good) {
    return { label: "On", tone: "text-amber-700" };
  }
  if (quality === poor) {
    return { label: "Kem", tone: "text-red-700" };
  }
  return { label: "Chua ro", tone: "text-zinc-500" };
}

function readHostSettings(metadata) {
  const source = metadata && typeof metadata === "object" ? metadata : {};
  return {
    lockRoom: Boolean(source.lock_room),
    aiEnabled: source.ai_enabled !== false,
  };
}

function normalizeAiSuggestedActions(raw) {
  if (!Array.isArray(raw)) return [];
  const result = [];
  for (const item of raw) {
    if (!item || typeof item !== "object") continue;
    const label = String(item.label || "").trim();
    const prompt = String(item.prompt || "").trim();
    if (!prompt) continue;
    result.push({
      label: label || "Hoc tiep",
      prompt,
    });
  }
  return result.slice(0, 3);
}

function normalizeAiReferences(raw) {
  if (!Array.isArray(raw)) return [];
  const result = [];
  for (const item of raw) {
    if (!item || typeof item !== "object") continue;
    const title = String(item.title || "").trim();
    if (!title) continue;
    result.push({
      title,
      sourceType: String(item.source_type || item.sourceType || "context"),
      snippet: String(item.snippet || "").trim(),
    });
  }
  return result.slice(0, 3);
}

function EventBadge({ eventType }) {
  if (eventType === "raise_hand") {
    return <span className="rounded bg-amber-100 px-2 py-0.5 text-[10px] text-amber-700">hand</span>;
  }
  if (eventType === "participant_joined") {
    return <span className="rounded bg-emerald-100 px-2 py-0.5 text-[10px] text-emerald-700">join</span>;
  }
  if (eventType === "participant_left") {
    return <span className="rounded bg-zinc-200 px-2 py-0.5 text-[10px] text-zinc-700">left</span>;
  }
  return <span className="rounded bg-zinc-200 px-2 py-0.5 text-[10px] text-zinc-700">{eventType}</span>;
}

function VideoTile({ tile, pinned, handRaised, onTogglePin }) {
  const videoRef = useRef(null);

  useEffect(() => {
    const videoElement = videoRef.current;
    if (!videoElement || !tile.track) return;
    tile.track.attach(videoElement);
    return () => {
      tile.track.detach(videoElement);
    };
  }, [tile.track]);

  return (
    <article
      className={[
        "relative overflow-hidden rounded-xl border bg-zinc-950",
        pinned ? "border-amber-300 ring-1 ring-amber-300" : "border-zinc-800",
      ].join(" ")}
    >
      {tile.track ? (
        <video
          ref={videoRef}
          autoPlay
          muted={tile.isLocal}
          playsInline
          className="aspect-video w-full bg-zinc-950 object-cover"
        />
      ) : (
        <div className="flex aspect-video w-full items-center justify-center bg-zinc-900">
          <div className="rounded-full bg-zinc-700/80 px-4 py-3 text-sm text-zinc-100">
            {tile.name}
          </div>
        </div>
      )}

      <div className="absolute inset-x-0 bottom-0 flex items-center justify-between bg-gradient-to-t from-zinc-950/90 to-transparent p-2 text-xs text-zinc-100">
        <div className="flex items-center gap-2">
          <span className="truncate">{tile.name}{tile.isLocal ? " (ban)" : ""}</span>
          {handRaised ? <Hand className="h-3.5 w-3.5 text-amber-300" /> : null}
        </div>
        <button
          type="button"
          onClick={() => onTogglePin(tile.identity)}
          className="rounded border border-zinc-600 bg-zinc-900/70 p-1 hover:border-zinc-400"
          aria-label={pinned ? "Bo pin participant" : "Pin participant"}
        >
          {pinned ? <PinOff className="h-3.5 w-3.5" /> : <Pin className="h-3.5 w-3.5" />}
        </button>
      </div>
    </article>
  );
}

export default function LiveSessionPage() {
  const params = useParams();
  const sessionId = String(params?.sessionId || "");
  const authStatus = useAuthStore((s) => s.status);
  const currentUser = useAuthStore((s) => s.user);

  const roomRef = useRef(null);
  const audioContainerRef = useRef(null);
  const audioTracksRef = useRef(new Map());
  const connectingRef = useRef(false);
  const leavingRef = useRef(false);

  const [connecting, setConnecting] = useState(false);
  const [connected, setConnected] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const [error, setError] = useState("");
  const [session, setSession] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [videoTiles, setVideoTiles] = useState([]);
  const [backendParticipants, setBackendParticipants] = useState([]);
  const [sessionEvents, setSessionEvents] = useState([]);
  const [localRole, setLocalRole] = useState("learner");
  const [hostSettings, setHostSettings] = useState({
    lockRoom: false,
    aiEnabled: true,
  });
  const [settingsBusy, setSettingsBusy] = useState(false);
  const [networkStatus, setNetworkStatus] = useState("disconnected");
  const [connectionQuality, setConnectionQuality] = useState(null);
  const [reconnectCount, setReconnectCount] = useState(0);
  const [lastReconnectedAt, setLastReconnectedAt] = useState(null);
  const [microphoneEnabled, setMicrophoneEnabled] = useState(false);
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [pinnedIdentity, setPinnedIdentity] = useState(null);
  const [sideTab, setSideTab] = useState("chat");
  const [selectedMissionId, setSelectedMissionId] = useState(HERITAGE_MISSIONS[0].id);

  const [moderationLoading, setModerationLoading] = useState(false);
  const [participantActionBusy, setParticipantActionBusy] = useState({});
  const [notice, setNotice] = useState("");

  const [aiMode, setAiMode] = useState("hint-first");
  const [aiInput, setAiInput] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiMessages, setAiMessages] = useState([
    {
      id: "seed-1",
      role: "assistant",
      content:
        "AI giao vien da san sang. Mac dinh la hint-first: toi se goi y truoc roi moi dua dap an day du.",
      meta: "system",
    },
  ]);
  const aiScrollRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const mediaChunksRef = useRef([]);
  const recognitionRef = useRef(null);
  const voiceTranscriptBufferRef = useRef("");
  const voiceInterimBufferRef = useRef("");
  const speechSynthesisRef = useRef(null);
  const voiceTimeoutRef = useRef(null);
  const activeTtsAudioRef = useRef(null);
  const activeTtsUrlRef = useRef("");
  const activeTtsAbortRef = useRef(null);
  const ttsRequestSeqRef = useRef(0);
  const processedVoiceEventIdsRef = useRef(new Set());
  const pendingAiRequestsRef = useRef(new Map());
  const completedAiRequestIdsRef = useRef(new Set());

  const [voiceSupported, setVoiceSupported] = useState(false);
  const [voiceBackendAvailable, setVoiceBackendAvailable] = useState(true);
  const [voiceListening, setVoiceListening] = useState(false);
  const [voiceWakePhraseRequired, setVoiceWakePhraseRequired] = useState(true);
  const [voiceAutoSpeakEnabled, setVoiceAutoSpeakEnabled] = useState(true);
  const [voiceInterimText, setVoiceInterimText] = useState("");
  const [voiceLastFinalText, setVoiceLastFinalText] = useState("");
  const [voiceTranscriptFeed, setVoiceTranscriptFeed] = useState([]);

  useEffect(() => {
    connectingRef.current = connecting;
  }, [connecting]);

  useEffect(() => {
    leavingRef.current = leaving;
  }, [leaving]);

  const localIdentity = useMemo(
    () => (currentUser?.id ? `user-${currentUser.id}` : null),
    [currentUser?.id],
  );

  const quality = useMemo(() => qualityMeta(connectionQuality), [connectionQuality]);
  const missionById = useMemo(
    () => new Map(HERITAGE_MISSIONS.map((mission) => [mission.id, mission])),
    [],
  );

  const aiHistoryPayload = useMemo(() => {
    return aiMessages
      .filter((msg) => msg.role === "user" || msg.role === "assistant")
      .slice(-8)
      .map((msg) => ({ role: msg.role, content: msg.content }));
  }, [aiMessages]);

  const clearPendingAiRequest = useCallback((requestId) => {
    const normalized = String(requestId || "").trim();
    if (!normalized) return;
    const timeoutId = pendingAiRequestsRef.current.get(normalized);
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    pendingAiRequestsRef.current.delete(normalized);
    setAiLoading(pendingAiRequestsRef.current.size > 0);
  }, []);

  const freezePendingAiFallback = useCallback((requestId) => {
    const normalized = String(requestId || "").trim();
    if (!normalized) return;
    const timeoutId = pendingAiRequestsRef.current.get(normalized);
    if (timeoutId) {
      clearTimeout(timeoutId);
      pendingAiRequestsRef.current.set(normalized, 0);
      setAiLoading(pendingAiRequestsRef.current.size > 0);
    }
  }, []);

  const markAiRequestCompleted = useCallback(
    (requestId) => {
      const normalized = String(requestId || "").trim();
      if (!normalized) {
        setAiLoading(pendingAiRequestsRef.current.size > 0);
        return;
      }
      completedAiRequestIdsRef.current.add(normalized);
      clearPendingAiRequest(normalized);
    },
    [clearPendingAiRequest],
  );

  const pushVoiceFeed = useCallback((item) => {
    if (!item?.text) return;
    setVoiceTranscriptFeed((prev) => {
      const next = [
        {
          id:
            item.id ||
            `${item.speaker || "unknown"}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          speaker: item.speaker || "user",
          text: String(item.text),
          source: item.source || "local",
          createdAt: item.createdAt || new Date().toISOString(),
        },
        ...prev,
      ];
      return next.slice(0, 60);
    });
  }, []);

  const isVoiceBackendCapabilityError = useCallback((raw) => {
    const message = String(raw || "").toLowerCase();
    return (
      message.includes("invalid token") ||
      message.includes("not available in group") ||
      (message.includes("model") && message.includes("not available"))
    );
  }, []);

  const publishDataChannelTranscript = useCallback(
    async (payload) => {
      const room = roomRef.current;
      if (!room || room.state !== "connected" || !room.localParticipant) return;
      try {
        const encoded = new TextEncoder().encode(JSON.stringify(payload));
        await room.localParticipant.publishData(encoded, {
          reliable: true,
          topic: "live-transcript",
        });
      } catch {
        // Data channel failures should not break main AI flow.
      }
    },
    [],
  );

  const stopCurrentSpeech = useCallback(() => {
    const pendingTtsAbort = activeTtsAbortRef.current;
    if (pendingTtsAbort) {
      pendingTtsAbort.abort();
      activeTtsAbortRef.current = null;
    }
    const activeAudio = activeTtsAudioRef.current;
    if (activeAudio) {
      activeAudio.pause();
      activeAudio.currentTime = 0;
      activeTtsAudioRef.current = null;
    }
    if (activeTtsUrlRef.current) {
      URL.revokeObjectURL(activeTtsUrlRef.current);
      activeTtsUrlRef.current = "";
    }
    const synth = speechSynthesisRef.current;
    if (synth) {
      try {
        synth.cancel();
      } catch {
        // no-op
      }
    }
  }, []);

  const clearRemoteAudio = useCallback(() => {
    for (const { track, el } of audioTracksRef.current.values()) {
      track.detach(el);
      el.remove();
    }
    audioTracksRef.current.clear();
  }, []);

  const attachRemoteAudioTrack = useCallback((track) => {
    if (!audioContainerRef.current) return;
    if (audioTracksRef.current.has(track.sid)) return;

    const mediaElement = track.attach();
    mediaElement.autoplay = true;
    mediaElement.playsInline = true;
    mediaElement.style.display = "none";
    audioContainerRef.current.appendChild(mediaElement);
    audioTracksRef.current.set(track.sid, { track, el: mediaElement });
  }, []);

  const detachRemoteAudioTrack = useCallback((track) => {
    const found = audioTracksRef.current.get(track.sid);
    if (!found) return;
    found.track.detach(found.el);
    found.el.remove();
    audioTracksRef.current.delete(track.sid);
  }, []);

  const syncParticipants = useCallback(() => {
    const room = roomRef.current;
    if (!room) return;

    const nextParticipants = [];
    const nextVideoTiles = [];

    if (room.localParticipant) {
      const localParticipant = room.localParticipant;
      nextParticipants.push(toParticipantViewModel(localParticipant, true));
      const localVideoPub = Array.from(localParticipant.videoTrackPublications.values()).find(
        (pub) => Boolean(pub.track),
      );
      nextVideoTiles.push({
        identity: localParticipant.identity,
        name: localParticipant.name || localParticipant.identity || "Ban",
        isLocal: true,
        track: localVideoPub?.track || null,
      });
    }

    for (const remote of room.remoteParticipants.values()) {
      nextParticipants.push(toParticipantViewModel(remote, false));
      const firstVideoPub = Array.from(remote.videoTrackPublications.values()).find(
        (pub) => Boolean(pub.track),
      );
      nextVideoTiles.push({
        identity: remote.identity,
        name: remote.name || remote.identity || "Nguoi dung",
        isLocal: false,
        track: firstVideoPub?.track || null,
      });
    }

    setParticipants(nextParticipants);
    setVideoTiles(nextVideoTiles);
  }, []);

  const refreshBackendParticipants = useCallback(async () => {
    if (!sessionId) return;
    const roster = await listLiveSessionParticipants({
      sessionId,
      includeInactive: false,
    });
    setBackendParticipants(Array.isArray(roster) ? roster : []);
  }, [sessionId]);

  const refreshSessionEvents = useCallback(async () => {
    if (!sessionId) return;
    const events = await listLiveSessionEvents({
      sessionId,
      limit: 120,
    });
    setSessionEvents(Array.isArray(events) ? events : []);
  }, [sessionId]);

  useEffect(() => {
    if (!currentUser?.id) return;
    const participant = backendParticipants.find(
      (item) => item.participant_identity === `user-${currentUser.id}`,
    );
    if (participant?.role) {
      setLocalRole(participant.role);
    }
  }, [backendParticipants, currentUser?.id]);

  useEffect(() => {
    const hasPinned = videoTiles.some((tile) => tile.identity === pinnedIdentity);
    if (!hasPinned) {
      setPinnedIdentity(null);
    }
  }, [pinnedIdentity, videoTiles]);

  useEffect(() => {
    if (!connected) return;
    let cancelled = false;

    async function pollSessionData() {
      try {
        await Promise.all([refreshBackendParticipants(), refreshSessionEvents()]);
      } catch {
        if (!cancelled) {
          // Polling failures should not break live room experience.
        }
      }
    }

    void pollSessionData();
    const interval = setInterval(() => {
      void pollSessionData();
    }, 5000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [connected, refreshBackendParticipants, refreshSessionEvents]);

  useEffect(() => {
    if (!sessionId) return;
    if (authStatus === "checking") return;
    if (authStatus !== "authed") {
      setError("Ban can dang nhap de vao phong live.");
      return;
    }

    let cancelled = false;
    const room = new Room({
      adaptiveStream: true,
      dynacast: true,
      // Force legacy /rtc path to avoid oversized join_request URL issues on some nginx setups.
      singlePeerConnection: false,
    });
    roomRef.current = room;
    let autoReconnectAttempts = 0;
    let autoReconnectTimer = null;

    const clearAutoReconnectTimer = () => {
      if (autoReconnectTimer) {
        clearTimeout(autoReconnectTimer);
        autoReconnectTimer = null;
      }
    };

    const syncRoomState = () => {
      if (cancelled) return;
      const isConnected = room.state === "connected";
      setConnected(isConnected);
      setMicrophoneEnabled(room.localParticipant?.isMicrophoneEnabled || false);
      setCameraEnabled(room.localParticipant?.isCameraEnabled || false);
      setNetworkStatus(
        room.state === "reconnecting"
          ? "reconnecting"
          : isConnected
            ? "connected"
            : "disconnected",
      );
      syncParticipants();
    };

    room.on(RoomEvent.Connected, () => {
      setNetworkStatus("connected");
      autoReconnectAttempts = 0;
      clearAutoReconnectTimer();
      syncRoomState();
    });
    room.on(RoomEvent.Disconnected, () => {
      setNetworkStatus("disconnected");
      syncRoomState();
      if (cancelled || leavingRef.current || connectingRef.current) return;
      if (autoReconnectAttempts >= 2) return;
      autoReconnectAttempts += 1;
      clearAutoReconnectTimer();
      autoReconnectTimer = setTimeout(() => {
        if (cancelled || leavingRef.current || connectingRef.current) return;
        setNotice(
          "Ket noi bi ngat. Dang tu dong xin token moi va reconnect...",
        );
        void connectRoom();
      }, 1200);
    });
    room.on(RoomEvent.Reconnecting, () => {
      setNetworkStatus("reconnecting");
      setReconnectCount((prev) => prev + 1);
      syncRoomState();
    });
    room.on(RoomEvent.Reconnected, () => {
      setNetworkStatus("connected");
      setLastReconnectedAt(new Date().toISOString());
      syncRoomState();
    });
    room.on(RoomEvent.ParticipantConnected, syncRoomState);
    room.on(RoomEvent.ParticipantDisconnected, syncRoomState);
    room.on(RoomEvent.TrackMuted, syncRoomState);
    room.on(RoomEvent.TrackUnmuted, syncRoomState);
    room.on(RoomEvent.LocalTrackPublished, syncRoomState);
    room.on(RoomEvent.LocalTrackUnpublished, syncRoomState);
    room.on(RoomEvent.ConnectionQualityChanged, (qualityUpdate, participant) => {
      if (participant?.isLocal) {
        setConnectionQuality(qualityUpdate);
      }
    });
    room.on(RoomEvent.TrackSubscribed, (track) => {
      if (track?.kind === "audio") {
        attachRemoteAudioTrack(track);
      }
      syncRoomState();
    });
    room.on(RoomEvent.TrackUnsubscribed, (track) => {
      if (track?.kind === "audio") {
        detachRemoteAudioTrack(track);
      }
      syncRoomState();
    });
    room.on(RoomEvent.DataReceived, (payload, participant, _kind, topic) => {
      if (topic && topic !== "live-transcript") return;
      try {
        const decoded = new TextDecoder().decode(payload);
        const parsed = JSON.parse(decoded);
        if (!parsed || typeof parsed !== "object") return;
        const type = String(parsed.type || "").toLowerCase();
        if (!type.includes("transcript")) return;
        pushVoiceFeed({
          id: parsed.id || `${parsed.type || "chunk"}-${Date.now()}`,
          speaker: parsed.speaker || parsed.role || "user",
          text: parsed.text || parsed.content || "",
          source: "data-channel",
          createdAt: parsed.created_at || new Date().toISOString(),
        });
      } catch {
        if (payload?.byteLength) {
          pushVoiceFeed({
            id: `dc-${Date.now()}`,
            speaker: participant?.identity || "remote",
            text: "[received transcript payload]",
            source: "data-channel",
          });
        }
      }
    });

    async function connectRoom() {
      setConnecting(true);
      setError("");
      setNetworkStatus("connecting");
      try {
        const joined = await joinLiveSession({ sessionId });
        if (cancelled) return;
        setSession(joined.session);
        setLocalRole(joined.participant?.role || "learner");
        setHostSettings(readHostSettings(joined.session?.session_metadata));

        try {
          await room.connect(joined.livekit.url, joined.livekit.token);
        } catch (err) {
          const raw = err instanceof Error ? err.message : String(err);
          if (!String(raw || "").toLowerCase().includes("could not establish pc connection")) {
            throw err;
          }
          room.disconnect();
          if (!cancelled) {
            setNotice("Mang dang han che WebRTC truc tiep. Dang thu relay mode...");
          }
          await room.connect(joined.livekit.url, joined.livekit.token, {
            rtcConfig: { iceTransportPolicy: "relay" },
          });
        }
        await room.localParticipant.setMicrophoneEnabled(true);
        try {
          await room.localParticipant.setCameraEnabled(true);
        } catch {
          // Camera permission may be denied.
        }

        syncRoomState();
        await Promise.all([refreshBackendParticipants(), refreshSessionEvents()]);
        if (joined.session?.session_metadata?.ai_enabled !== false) {
          try {
            await ensureLiveAiTeacherPresence({ sessionId });
            await refreshBackendParticipants();
          } catch {
            // Presence call failure should not block joining live room.
          }
        }
      } catch (err) {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : String(err);
          setError(humanizeLiveError(message));
          setNetworkStatus("disconnected");
        }
      } finally {
        if (!cancelled) setConnecting(false);
      }
    }

    void connectRoom();

    return () => {
      cancelled = true;
      clearAutoReconnectTimer();
      if (room.state === "connected") {
        void leaveLiveSession({ sessionId, keepalive: true }).catch(() => {});
      }
      clearRemoteAudio();
      room.disconnect();
      roomRef.current = null;
    };
  }, [
    attachRemoteAudioTrack,
    authStatus,
    clearRemoteAudio,
    detachRemoteAudioTrack,
    refreshBackendParticipants,
    refreshSessionEvents,
    sessionId,
    syncParticipants,
  ]);

  useEffect(() => {
    if (!aiScrollRef.current) return;
    aiScrollRef.current.scrollTop = aiScrollRef.current.scrollHeight;
  }, [aiMessages]);

  const speakAiAnswer = useCallback(
    async (text) => {
      const normalized = String(text || "").trim();
      if (!voiceAutoSpeakEnabled || !normalized || !connected || !hostSettings.aiEnabled) return;
      if (typeof window === "undefined") return;

      stopCurrentSpeech();
      const sequence = ttsRequestSeqRef.current + 1;
      ttsRequestSeqRef.current = sequence;
      const abortController = new AbortController();
      activeTtsAbortRef.current = abortController;

      try {
        const { blob } = await synthesizeLiveAiTeacherVoice({
          sessionId,
          text: normalized,
          signal: abortController.signal,
        });
        if (ttsRequestSeqRef.current !== sequence || !voiceAutoSpeakEnabled) return;
        const objectUrl = URL.createObjectURL(blob);
        activeTtsUrlRef.current = objectUrl;
        const audio = new Audio(objectUrl);
        activeTtsAudioRef.current = audio;
        audio.onended = () => {
          if (activeTtsAudioRef.current === audio) {
            activeTtsAudioRef.current = null;
          }
          if (activeTtsUrlRef.current === objectUrl) {
            URL.revokeObjectURL(objectUrl);
            activeTtsUrlRef.current = "";
          }
        };
        audio.onerror = () => {
          if (activeTtsAudioRef.current === audio) {
            activeTtsAudioRef.current = null;
          }
          if (activeTtsUrlRef.current === objectUrl) {
            URL.revokeObjectURL(objectUrl);
            activeTtsUrlRef.current = "";
          }
        };
        await audio.play();
      } catch (err) {
        if (err?.name !== "AbortError") {
          const message = err instanceof Error ? err.message : String(err);
          if (isVoiceBackendCapabilityError(message)) {
            setVoiceBackendAvailable(false);
          }
          const synth = speechSynthesisRef.current || window.speechSynthesis;
          if (synth) {
            try {
              synth.cancel();
              const utterance = new SpeechSynthesisUtterance(normalized);
              utterance.lang = "vi-VN";
              synth.speak(utterance);
            } catch {
              // Ignore browser TTS fallback failure.
            }
          }
        }
      } finally {
        if (activeTtsAbortRef.current === abortController) {
          activeTtsAbortRef.current = null;
        }
      }
    },
    [
      connected,
      hostSettings.aiEnabled,
      isVoiceBackendCapabilityError,
      sessionId,
      stopCurrentSpeech,
      voiceAutoSpeakEnabled,
    ],
  );

  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const hasRecorder = typeof window.MediaRecorder !== "undefined";
    const hasGetUserMedia = Boolean(navigator?.mediaDevices?.getUserMedia);
    const hasBrowserRecognition = Boolean(
      window.SpeechRecognition || window.webkitSpeechRecognition,
    );
    speechSynthesisRef.current = window.speechSynthesis || null;
    setVoiceSupported(Boolean((hasRecorder && hasGetUserMedia) || hasBrowserRecognition));

    return () => {
      if (voiceTimeoutRef.current) {
        clearTimeout(voiceTimeoutRef.current);
        voiceTimeoutRef.current = null;
      }
      const recorder = mediaRecorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        recorder.ondataavailable = null;
        recorder.onerror = null;
        recorder.onstop = null;
        try {
          recorder.stop();
        } catch {
          // no-op
        }
      }
      if (mediaStreamRef.current) {
        for (const track of mediaStreamRef.current.getTracks()) {
          track.stop();
        }
        mediaStreamRef.current = null;
      }
      const recognition = recognitionRef.current;
      if (recognition) {
        try {
          recognition.stop();
        } catch {
          // no-op
        }
        recognitionRef.current = null;
      }
      for (const timeoutId of pendingAiRequestsRef.current.values()) {
        clearTimeout(timeoutId);
      }
      pendingAiRequestsRef.current.clear();
      completedAiRequestIdsRef.current.clear();
      stopCurrentSpeech();
    };
  }, [stopCurrentSpeech]);

  useEffect(() => {
    const chronological = [...sessionEvents].sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    );
    for (const event of chronological) {
      const eventId = String(event.id || "");
      if (!eventId || processedVoiceEventIdsRef.current.has(eventId)) continue;
      processedVoiceEventIdsRef.current.add(eventId);

      const payload = event.payload && typeof event.payload === "object" ? event.payload : {};
      const eventType = String(event.event_type || "");
      const requestId = String(payload.request_id || "").trim();

      if (eventType === "voice_user_final") {
        pushVoiceFeed({
          id: eventId,
          speaker: "user",
          text: payload.text || payload.answer || "",
          source: "live-event",
          createdAt: event.created_at,
        });
      }

      if (eventType === "ai_transcript_chunk" && payload.partial === true && payload.text) {
        if (requestId) {
          freezePendingAiFallback(requestId);
          if (completedAiRequestIdsRef.current.has(requestId)) continue;
        }
        setAiMessages((prev) => {
          if (!requestId) return prev;
          const finalId = `request-${requestId}`;
          if (prev.some((msg) => msg.id === finalId)) return prev;
          const streamId = `stream-${requestId}`;
          const providerLabel = String(payload.provider || "ai_teacher");
          const modelLabel = String(payload.model || "").trim();
          const meta = modelLabel
            ? `${providerLabel} · ${modelLabel} · streaming`
            : `${providerLabel} · streaming`;
          const content = String(payload.text || "").trim();
          if (!content) return prev;
          const existingIndex = prev.findIndex((msg) => msg.id === streamId);
          if (existingIndex === -1) {
            return [
              ...prev,
              {
                id: streamId,
                role: "assistant",
                content,
                meta,
              },
            ];
          }
          const next = [...prev];
          next[existingIndex] = {
            ...next[existingIndex],
            content,
            meta,
          };
          return next;
        });
      }

      if (eventType === "ai_voice_ready" && payload.text) {
        if (requestId && completedAiRequestIdsRef.current.has(requestId)) continue;

        pushVoiceFeed({
          id: requestId ? `ai-ready-${requestId}` : eventId,
          speaker: "ai",
          text: payload.text || payload.answer || "",
          source: "live-event",
          createdAt: event.created_at,
        });

        setAiMessages((prev) => {
          const messageId = requestId ? `request-${requestId}` : `event-${eventId}`;
          if (prev.some((msg) => msg.id === messageId)) return prev;
          const providerLabel = String(payload.provider || "ai_teacher");
          const modelLabel = String(payload.model || "").trim();
          const next = prev.filter((msg) => msg.id !== `stream-${requestId}`);
          return [
            ...next,
            {
              id: messageId,
              role: "assistant",
              content: String(payload.text),
              meta: modelLabel ? `${providerLabel} · ${modelLabel}` : providerLabel,
              suggestedActions: normalizeAiSuggestedActions(payload.suggested_actions),
              references: normalizeAiReferences(payload.references),
              checkpointPrompt: String(payload.checkpoint_prompt || "").trim(),
            },
          ];
        });
        if (requestId) {
          markAiRequestCompleted(requestId);
        }
        void speakAiAnswer(payload.text);
      }
    }
  }, [
    freezePendingAiFallback,
    markAiRequestCompleted,
    pushVoiceFeed,
    sessionEvents,
    speakAiAnswer,
  ]);

  const handRaisedMap = useMemo(() => {
    const map = new Map();
    const chronological = [...sessionEvents].sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    );
    for (const event of chronological) {
      const identity = event.participant_identity || event.payload?.participant_identity;
      if (!identity) continue;
      if (event.event_type === "raise_hand") {
        map.set(identity, true);
      } else if (event.event_type === "lower_hand") {
        map.delete(identity);
      }
    }
    return map;
  }, [sessionEvents]);

  const localHandRaised = localIdentity ? Boolean(handRaisedMap.get(localIdentity)) : false;
  const canModerate = connected && canModerateRole(localRole);
  const canManageSettings = connected && localRole === "host";

  const mergedParticipants = useMemo(() => {
    const backendByIdentity = new Map(
      backendParticipants.map((item) => [item.participant_identity, item]),
    );

    const merged = participants.map((participant) => {
      const server = backendByIdentity.get(participant.identity);
      return {
        ...participant,
        backendId: server?.id || null,
        role: server?.role || (participant.isLocal ? localRole : "learner"),
        isAi: Boolean(server?.is_ai),
        handRaised: Boolean(handRaisedMap.get(participant.identity)),
      };
    });

    const known = new Set(merged.map((item) => item.identity));
    for (const server of backendParticipants) {
      if (known.has(server.participant_identity)) continue;
      merged.push({
        id: server.participant_identity,
        identity: server.participant_identity,
        name: server.display_name || server.participant_identity,
        isLocal: localIdentity === server.participant_identity,
        microphoneEnabled: false,
        cameraEnabled: false,
        backendId: server.id,
        role: server.role,
        isAi: Boolean(server.is_ai),
        handRaised: Boolean(handRaisedMap.get(server.participant_identity)),
      });
    }

    return merged;
  }, [backendParticipants, handRaisedMap, localIdentity, localRole, participants]);

  const pinnedTile = useMemo(
    () => videoTiles.find((tile) => tile.identity === pinnedIdentity) || null,
    [pinnedIdentity, videoTiles],
  );

  const secondaryTiles = useMemo(() => {
    if (!pinnedTile) return videoTiles;
    return videoTiles.filter((tile) => tile.identity !== pinnedTile.identity);
  }, [pinnedTile, videoTiles]);

  const setParticipantBusy = useCallback((participantId, busy) => {
    if (!participantId) return;
    setParticipantActionBusy((prev) => ({ ...prev, [participantId]: busy }));
  }, []);

  const toggleMicrophone = useCallback(async () => {
    const room = roomRef.current;
    if (!room || room.state !== "connected") return;
    await room.localParticipant.setMicrophoneEnabled(!microphoneEnabled);
    setMicrophoneEnabled(room.localParticipant.isMicrophoneEnabled || false);
    syncParticipants();
  }, [microphoneEnabled, syncParticipants]);

  const toggleCamera = useCallback(async () => {
    const room = roomRef.current;
    if (!room || room.state !== "connected") return;
    await room.localParticipant.setCameraEnabled(!cameraEnabled);
    setCameraEnabled(room.localParticipant.isCameraEnabled || false);
    syncParticipants();
  }, [cameraEnabled, syncParticipants]);

  const reconnectNow = useCallback(async () => {
    const room = roomRef.current;
    if (!room || !sessionId) return;
    setConnecting(true);
    setNotice("");
    try {
      const joined = await joinLiveSession({ sessionId });
      if (room.state === "connected" || room.state === "reconnecting") {
        room.disconnect();
      }
      try {
        await room.connect(joined.livekit.url, joined.livekit.token);
      } catch (err) {
        const raw = err instanceof Error ? err.message : String(err);
        if (!String(raw || "").toLowerCase().includes("could not establish pc connection")) {
          throw err;
        }
        room.disconnect();
        setNotice("Mang dang han che WebRTC truc tiep. Dang thu relay mode...");
        await room.connect(joined.livekit.url, joined.livekit.token, {
          rtcConfig: { iceTransportPolicy: "relay" },
        });
      }
      setSession(joined.session);
      setHostSettings(readHostSettings(joined.session?.session_metadata));
      setNetworkStatus("connected");
      setNotice("Da reconnect thanh cong.");
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setNotice(`Reconnect loi: ${humanizeLiveError(message)}`);
      setNetworkStatus("disconnected");
    } finally {
      setConnecting(false);
    }
  }, [sessionId]);

  const leaveRoom = useCallback(async () => {
    const room = roomRef.current;
    if (!room || leaving) return;

    setLeaving(true);
    try {
      await leaveLiveSession({ sessionId });
    } catch {
      // Ignore leave errors and disconnect local room anyway.
    } finally {
      if (voiceTimeoutRef.current) {
        clearTimeout(voiceTimeoutRef.current);
        voiceTimeoutRef.current = null;
      }
      const recorder = mediaRecorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        recorder.ondataavailable = null;
        recorder.onerror = null;
        recorder.onstop = null;
        try {
          recorder.stop();
        } catch {
          // no-op
        }
      }
      mediaRecorderRef.current = null;
      if (mediaStreamRef.current) {
        for (const track of mediaStreamRef.current.getTracks()) {
          track.stop();
        }
        mediaStreamRef.current = null;
      }
      const recognition = recognitionRef.current;
      if (recognition) {
        try {
          recognition.stop();
        } catch {
          // no-op
        }
        recognitionRef.current = null;
      }
      setVoiceListening(false);
      setVoiceInterimText("");
      stopCurrentSpeech();
      clearRemoteAudio();
      room.disconnect();
      setConnected(false);
      setParticipants([]);
      setBackendParticipants([]);
      setVideoTiles([]);
      setSessionEvents([]);
      setLeaving(false);
      setNetworkStatus("disconnected");
    }
  }, [clearRemoteAudio, leaving, sessionId, stopCurrentSpeech]);

  const handleToggleHand = useCallback(async () => {
    if (!connected || !localIdentity) return;
    const nextRaised = !localHandRaised;
    try {
      await createLiveSessionEvent({
        sessionId,
        eventType: nextRaised ? "raise_hand" : "lower_hand",
        payload: {
          participant_identity: localIdentity,
          state: nextRaised ? "raised" : "lowered",
        },
      });
      await refreshSessionEvents();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setNotice(`Khong cap nhat duoc raise hand: ${message || "khong ro"}`);
    }
  }, [connected, localHandRaised, localIdentity, refreshSessionEvents, sessionId]);

  const applyHostSettings = useCallback(
    async (patch) => {
      if (!canManageSettings) return;
      setSettingsBusy(true);
      setNotice("");
      try {
        const updated = await updateLiveHostSettings({
          sessionId,
          lockRoom:
            typeof patch.lockRoom === "boolean" ? patch.lockRoom : hostSettings.lockRoom,
          aiEnabled:
            typeof patch.aiEnabled === "boolean" ? patch.aiEnabled : hostSettings.aiEnabled,
        });
        setSession(updated);
        const next = readHostSettings(updated?.session_metadata);
        setHostSettings(next);
        setNotice(
          `Host settings da cap nhat: lock=${next.lockRoom ? "on" : "off"}, AI=${next.aiEnabled ? "on" : "off"}`,
        );
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setNotice(`Cap nhat host settings loi: ${message || "khong ro"}`);
      } finally {
        setSettingsBusy(false);
      }
    },
    [canManageSettings, hostSettings.aiEnabled, hostSettings.lockRoom, sessionId],
  );

  const handleMuteAll = useCallback(async () => {
    if (!canModerate || moderationLoading) return;
    setModerationLoading(true);
    setNotice("");
    try {
      const result = await hostMuteAllLiveParticipants({
        sessionId,
        includeCohosts: false,
      });
      setNotice(`Mute all: processed=${result.processed || 0}, failed=${result.failed || 0}`);
      await refreshBackendParticipants();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setNotice(`Mute all loi: ${message || "khong ro"}`);
    } finally {
      setModerationLoading(false);
    }
  }, [canModerate, moderationLoading, refreshBackendParticipants, sessionId]);

  const handleToggleCohost = useCallback(
    async (participant) => {
      if (!canModerate || !participant?.backendId || participant.isAi) return;
      if (participant.isLocal) return;

      const nextRole = participant.role === "cohost" ? "learner" : "cohost";
      setParticipantBusy(participant.backendId, true);
      setNotice("");
      try {
        await updateLiveParticipantRole({
          sessionId,
          participantId: participant.backendId,
          role: nextRole,
        });
        setNotice(`${participant.name}: ${participant.role || "learner"} -> ${nextRole}`);
        await refreshBackendParticipants();
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setNotice(`Cap nhat role loi: ${message || "khong ro"}`);
      } finally {
        setParticipantBusy(participant.backendId, false);
      }
    },
    [canModerate, refreshBackendParticipants, sessionId, setParticipantBusy],
  );

  const handleRemoveParticipant = useCallback(
    async (participant) => {
      if (!canModerate || !participant?.backendId || participant.isLocal) return;
      setParticipantBusy(participant.backendId, true);
      setNotice("");
      try {
        const result = await hostRemoveLiveParticipant({
          sessionId,
          participantId: participant.backendId,
        });
        if (result?.detail) {
          setNotice(`Remove co canh bao: ${result.detail}`);
        } else {
          setNotice(`Da remove ${participant.name}`);
        }
        await refreshBackendParticipants();
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setNotice(`Remove participant loi: ${message || "khong ro"}`);
      } finally {
        setParticipantBusy(participant.backendId, false);
      }
    },
    [canModerate, refreshBackendParticipants, sessionId, setParticipantBusy],
  );

  const handleSelectMission = useCallback(
    (missionId) => {
      setSelectedMissionId(missionId);
      const mission = missionById.get(missionId);
      if (mission && !aiInput.trim()) {
        setAiInput(mission.prompt);
      }
      setSideTab("chat");
    },
    [aiInput, missionById],
  );

  const sendQuestionToAiTeacher = useCallback(
    async (question, { source = "text" } = {}) => {
      const normalizedQuestion = String(question || "").trim();
      if (!normalizedQuestion || !connected || aiLoading || !hostSettings.aiEnabled) return;
      const requestId = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

      const userMessage = {
        id: `${Date.now()}-u`,
        role: "user",
        content: normalizedQuestion,
      };
      setAiMessages((prev) => [...prev, userMessage]);
      setAiInput("");
      setAiLoading(true);

      try {
        const history = [...aiHistoryPayload, { role: "user", content: normalizedQuestion }];
        const fallbackTimeoutId = setTimeout(() => {
          void (async () => {
            if (!pendingAiRequestsRef.current.has(requestId)) return;
            try {
              const reply = await askLiveAiTeacher({
                sessionId,
                message: normalizedQuestion,
                mode: aiMode,
                history: history.slice(-8),
              });
              if (!pendingAiRequestsRef.current.has(requestId)) return;
              markAiRequestCompleted(requestId);
              setAiMessages((prev) => {
                const messageId = `request-${requestId}`;
                if (prev.some((msg) => msg.id === messageId)) return prev;
                const providerLabel = String(reply.provider || "ai_teacher");
                const modelLabel = String(reply.model || "").trim();
                return [
                  ...prev,
                  {
                    id: messageId,
                    role: "assistant",
                    content: reply.answer,
                    meta: modelLabel ? `${providerLabel} · ${modelLabel}` : providerLabel,
                    suggestedActions: normalizeAiSuggestedActions(reply.suggested_actions),
                    references: normalizeAiReferences(reply.references),
                    checkpointPrompt: String(reply?.checkpoint?.prompt || "").trim(),
                  },
                ];
              });
              pushVoiceFeed({
                id: `fallback-ai-${requestId}`,
                speaker: "ai",
                text: reply.answer,
                source: "fallback-api",
              });
              await publishDataChannelTranscript({
                id: `fallback-ai-${requestId}`,
                type: "ai_transcript_chunk",
                speaker: "ai",
                text: reply.answer,
                created_at: new Date().toISOString(),
              });
              void speakAiAnswer(reply.answer);
            } catch (err) {
              if (!pendingAiRequestsRef.current.has(requestId)) return;
              markAiRequestCompleted(requestId);
              const message = err instanceof Error ? err.message : String(err);
              setAiMessages((prev) => [
                ...prev,
                {
                  id: `${Date.now()}-e`,
                  role: "assistant",
                  content: `AI teacher loi: ${message || "khong the tra loi"}`,
                  meta: "error",
                },
              ]);
            }
          })();
        }, 12000);
        pendingAiRequestsRef.current.set(requestId, fallbackTimeoutId);
        setAiLoading(true);

        await createLiveSessionEvent({
          sessionId,
          eventType: "ai_voice_request",
          payload: {
            request_id: requestId,
            mode: aiMode,
            text: normalizedQuestion,
            source,
            participant_identity: localIdentity,
          },
        });
        await createLiveSessionEvent({
          sessionId,
          eventType: "voice_user_final",
          payload: {
            request_id: requestId,
            mode: aiMode,
            text: normalizedQuestion,
            source,
            participant_identity: localIdentity,
          },
        });
        pushVoiceFeed({
          id: `local-${requestId}`,
          speaker: "user",
          text: normalizedQuestion,
          source: "local-voice",
        });
        await publishDataChannelTranscript({
          id: requestId,
          type: "voice_user_chunk",
          speaker: "user",
          text: normalizedQuestion,
          created_at: new Date().toISOString(),
        });
      } catch (err) {
        markAiRequestCompleted(requestId);
        const message = err instanceof Error ? err.message : String(err);
        setAiMessages((prev) => [
          ...prev,
          {
            id: `${Date.now()}-e`,
            role: "assistant",
            content: `AI teacher loi: ${message || "khong the tra loi"}`,
            meta: "error",
          },
        ]);
      }
    },
    [
      aiHistoryPayload,
      aiLoading,
      aiMode,
      connected,
      hostSettings.aiEnabled,
      localIdentity,
      markAiRequestCompleted,
      publishDataChannelTranscript,
      pushVoiceFeed,
      sessionId,
      speakAiAnswer,
    ],
  );

  const askAiTeacher = useCallback(
    async (event) => {
      event.preventDefault();
      await sendQuestionToAiTeacher(aiInput, { source: "text" });
    },
    [aiInput, sendQuestionToAiTeacher],
  );

  const stopVoiceCapture = useCallback(() => {
    if (voiceTimeoutRef.current) {
      clearTimeout(voiceTimeoutRef.current);
      voiceTimeoutRef.current = null;
    }
    const recognition = recognitionRef.current;
    if (recognition) {
      try {
        recognition.stop();
      } catch {
        // no-op
      }
    }
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === "inactive") return;
    try {
      recorder.stop();
    } catch {
      setVoiceListening(false);
    }
  }, []);

  const submitVoiceTranscript = useCallback(
    async (text) => {
      const finalText = String(text || "").trim();
      if (!finalText) return;
      setVoiceLastFinalText(finalText);

      if (voiceWakePhraseRequired && !hasWakePhrase(finalText)) {
        setNotice("Voice command can wake phrase 'co giao oi' de kich hoat AI.");
        return;
      }

      await sendQuestionToAiTeacher(finalText, { source: "voice" });
    },
    [sendQuestionToAiTeacher, voiceWakePhraseRequired],
  );

  const startBrowserRecognitionCapture = useCallback(() => {
    if (typeof window === "undefined") return false;
    const RecognitionCtor =
      window.SpeechRecognition || window.webkitSpeechRecognition || null;
    if (!RecognitionCtor) return false;

    try {
      const recognition = new RecognitionCtor();
      recognitionRef.current = recognition;
      voiceTranscriptBufferRef.current = "";
      voiceInterimBufferRef.current = "";

      recognition.lang = "vi-VN";
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      recognition.onresult = (event) => {
        let interim = "";
        for (let i = event.resultIndex; i < event.results.length; i += 1) {
          const result = event.results[i];
          const text = String(result?.[0]?.transcript || "").trim();
          if (!text) continue;
          if (result.isFinal) {
            voiceTranscriptBufferRef.current = `${voiceTranscriptBufferRef.current} ${text}`.trim();
          } else {
            interim = `${interim} ${text}`.trim();
          }
        }
        voiceInterimBufferRef.current = interim;
        setVoiceInterimText(interim);
      };

      recognition.onerror = () => {
        setVoiceListening(false);
        setVoiceInterimText("");
      };

      recognition.onend = () => {
        setVoiceListening(false);
        const finalText = `${voiceTranscriptBufferRef.current} ${voiceInterimBufferRef.current}`.trim();
        voiceTranscriptBufferRef.current = "";
        voiceInterimBufferRef.current = "";
        setVoiceInterimText("");
        recognitionRef.current = null;
        if (finalText) {
          void submitVoiceTranscript(finalText);
        }
      };

      recognition.start();
      setVoiceListening(true);
      setVoiceInterimText("Dang nghe (fallback trinh duyet)...");
      setNotice("Backend STT khong kha dung, da chuyen sang fallback trinh duyet.");
      if (voiceTimeoutRef.current) {
        clearTimeout(voiceTimeoutRef.current);
      }
      voiceTimeoutRef.current = setTimeout(() => {
        stopVoiceCapture();
      }, 15000);
      return true;
    } catch {
      return false;
    }
  }, [stopVoiceCapture, submitVoiceTranscript]);

  const submitRecordedVoice = useCallback(
    async (audioBlob) => {
      const blob = audioBlob instanceof Blob ? audioBlob : null;
      if (!blob || blob.size <= 0) {
        setNotice("Khong thu duoc du lieu am thanh de nhan dang.");
        return;
      }
      try {
        const mimeType = String(blob.type || "audio/webm");
        const extension = mimeType.includes("wav")
          ? "wav"
          : mimeType.includes("mp4") || mimeType.includes("mpeg")
            ? "m4a"
            : "webm";
        const file = new File(
          [blob],
          `voice-${Date.now()}.${extension}`,
          { type: mimeType },
        );
        const result = await transcribeLiveAiTeacherVoice({
          sessionId,
          file,
        });
        const transcript = String(result?.transcript || "").trim();
        if (!transcript) {
          setNotice("Khong nhan dang duoc noi dung giong noi.");
          return;
        }
        setVoiceLastFinalText(transcript);
        await submitVoiceTranscript(transcript);
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        if (isVoiceBackendCapabilityError(message)) {
          setVoiceBackendAvailable(false);
          setNotice(
            "Backend STT/TTS hien tai khong co quyen audio model. Da chuyen fallback trinh duyet, bam lai Start voice.",
          );
          return;
        }
        setNotice(`STT loi: ${message || "khong nhan dang duoc giong noi"}`);
      }
    },
    [isVoiceBackendCapabilityError, sessionId, submitVoiceTranscript],
  );

  const startVoiceCapture = useCallback(async () => {
    if (!voiceSupported || !connected || aiLoading) return;
    if (typeof window === "undefined") return;

    stopCurrentSpeech(); // Barge-in: user starts speaking, AI must stop speaking.
    const hasMediaRecorder = typeof window.MediaRecorder !== "undefined";
    const hasGetUserMedia = Boolean(navigator?.mediaDevices?.getUserMedia);
    if (!voiceBackendAvailable) {
      if (!startBrowserRecognitionCapture()) {
        setNotice("Khong the bat fallback STT tren trinh duyet hien tai.");
      }
      return;
    }
    if (!hasMediaRecorder || !hasGetUserMedia) {
      if (!startBrowserRecognitionCapture()) {
        setNotice("Trinh duyet khong ho tro ghi am realtime.");
      }
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      mediaChunksRef.current = [];

      const preferredMimeTypes = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/mp4",
      ];
      const chosenMimeType = preferredMimeTypes.find(
        (item) => window.MediaRecorder.isTypeSupported(item),
      );
      const recorder = chosenMimeType
        ? new window.MediaRecorder(stream, { mimeType: chosenMimeType })
        : new window.MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event?.data && event.data.size > 0) {
          mediaChunksRef.current.push(event.data);
        }
      };
      recorder.onerror = () => {
        setVoiceListening(false);
        setVoiceInterimText("");
      };
      recorder.onstop = () => {
        setVoiceListening(false);
        setVoiceInterimText("");
        const type = chosenMimeType || mediaChunksRef.current[0]?.type || "audio/webm";
        const recordedBlob = new Blob(mediaChunksRef.current, { type });
        mediaChunksRef.current = [];

        if (mediaStreamRef.current) {
          for (const track of mediaStreamRef.current.getTracks()) {
            track.stop();
          }
          mediaStreamRef.current = null;
        }
        mediaRecorderRef.current = null;
        if (recordedBlob.size > 0) {
          void submitRecordedVoice(recordedBlob);
        }
      };

      recorder.start(250);
      setVoiceListening(true);
      setVoiceInterimText("Dang thu am...");
      setNotice("");
      if (voiceTimeoutRef.current) {
        clearTimeout(voiceTimeoutRef.current);
      }
      voiceTimeoutRef.current = setTimeout(() => {
        stopVoiceCapture();
      }, 15000);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setNotice(`Khong mo duoc microphone: ${message || "khong ro"}`);
      setVoiceListening(false);
      setVoiceInterimText("");
    }
  }, [
    aiLoading,
    connected,
    startBrowserRecognitionCapture,
    stopCurrentSpeech,
    stopVoiceCapture,
    submitRecordedVoice,
    voiceBackendAvailable,
    voiceSupported,
  ]);

  const sortedEvents = useMemo(() => {
    return [...sessionEvents].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );
  }, [sessionEvents]);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[1500px] flex-col gap-4 bg-zinc-50/60 px-3 py-4 sm:px-4 sm:py-6">
      <header className="rounded-xl border border-zinc-200 bg-white p-3 shadow-sm sm:p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <h1 className="text-xl font-semibold sm:text-2xl">Phong hoc live 3D</h1>
            <p className="text-xs text-zinc-500 sm:text-sm">Session: {session?.id || sessionId || "N/A"}</p>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={[
                "rounded-full px-2 py-1 text-[11px] font-medium",
                networkStatus === "connected"
                  ? "bg-emerald-100 text-emerald-700"
                  : networkStatus === "reconnecting" || connecting
                    ? "bg-amber-100 text-amber-700"
                    : "bg-zinc-200 text-zinc-700",
              ].join(" ")}
            >
              {networkStatus}
            </span>
            <span className={`rounded-full bg-zinc-100 px-2 py-1 text-[11px] font-medium ${quality.tone}`}>
              chat luong: {quality.label}
            </span>
            <span className="rounded-full bg-zinc-100 px-2 py-1 text-[11px] font-medium text-zinc-700">
              role: {roleLabel(localRole)}
            </span>
            <Link
              href="/dashboard"
              className="rounded-md border border-zinc-300 px-3 py-2 text-xs font-medium hover:bg-zinc-50 sm:text-sm"
            >
              Ve dashboard
            </Link>
          </div>
        </div>
        <div className="mt-2 flex flex-wrap gap-3 text-xs text-zinc-500">
          <span>reconnect: {reconnectCount}</span>
          <span>participants: {mergedParticipants.length}</span>
          {lastReconnectedAt ? <span>last recovery: {new Date(lastReconnectedAt).toLocaleTimeString()}</span> : null}
          {hostSettings.lockRoom ? (
            <span className="rounded bg-amber-100 px-2 py-0.5 text-amber-700">room locked</span>
          ) : null}
          {!hostSettings.aiEnabled ? (
            <span className="rounded bg-zinc-200 px-2 py-0.5 text-zinc-700">AI disabled</span>
          ) : null}
        </div>
      </header>

      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
      ) : null}

      {notice ? (
        <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">{notice}</div>
      ) : null}

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.75fr)_380px]">
        <div className="space-y-4">
          <div className="rounded-2xl border border-zinc-200 bg-zinc-950/95 p-3 shadow-lg sm:p-4">
            {pinnedTile ? (
              <div className="space-y-3">
                <VideoTile
                  tile={pinnedTile}
                  pinned={true}
                  handRaised={Boolean(handRaisedMap.get(pinnedTile.identity))}
                  onTogglePin={(identity) =>
                    setPinnedIdentity((prev) => (prev === identity ? null : identity))
                  }
                />
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {secondaryTiles.map((tile) => (
                    <VideoTile
                      key={tile.identity}
                      tile={tile}
                      pinned={false}
                      handRaised={Boolean(handRaisedMap.get(tile.identity))}
                      onTogglePin={(identity) =>
                        setPinnedIdentity((prev) => (prev === identity ? null : identity))
                      }
                    />
                  ))}
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {videoTiles.length === 0 ? (
                  <div className="col-span-full rounded-xl border border-zinc-800 bg-zinc-900 p-6 text-center text-sm text-zinc-400">
                    Chua co participant video.
                  </div>
                ) : (
                  videoTiles.map((tile) => (
                    <VideoTile
                      key={tile.identity}
                      tile={tile}
                      pinned={false}
                      handRaised={Boolean(handRaisedMap.get(tile.identity))}
                      onTogglePin={(identity) =>
                        setPinnedIdentity((prev) => (prev === identity ? null : identity))
                      }
                    />
                  ))
                )}
              </div>
            )}
          </div>

          <div className="sticky bottom-2 z-10 rounded-2xl border border-zinc-200 bg-white/95 p-3 shadow-lg backdrop-blur sm:p-4">
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
              <button
                type="button"
                onClick={toggleMicrophone}
                disabled={!connected}
                className={[
                  "inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border px-3 text-sm font-medium",
                  microphoneEnabled
                    ? "border-emerald-300 bg-emerald-50 text-emerald-700"
                    : "border-zinc-300 bg-white text-zinc-700",
                  !connected ? "opacity-50" : "hover:bg-zinc-50",
                ].join(" ")}
              >
                {microphoneEnabled ? <Mic className="h-4 w-4" /> : <MicOff className="h-4 w-4" />}
                {microphoneEnabled ? "Mic on" : "Mic off"}
              </button>

              <button
                type="button"
                onClick={toggleCamera}
                disabled={!connected}
                className={[
                  "inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border px-3 text-sm font-medium",
                  cameraEnabled
                    ? "border-emerald-300 bg-emerald-50 text-emerald-700"
                    : "border-zinc-300 bg-white text-zinc-700",
                  !connected ? "opacity-50" : "hover:bg-zinc-50",
                ].join(" ")}
              >
                {cameraEnabled ? <Camera className="h-4 w-4" /> : <CameraOff className="h-4 w-4" />}
                {cameraEnabled ? "Cam on" : "Cam off"}
              </button>

              <button
                type="button"
                onClick={handleToggleHand}
                disabled={!connected}
                className={[
                  "inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border px-3 text-sm font-medium",
                  localHandRaised
                    ? "border-amber-300 bg-amber-50 text-amber-700"
                    : "border-zinc-300 bg-white text-zinc-700",
                  !connected ? "opacity-50" : "hover:bg-zinc-50",
                ].join(" ")}
              >
                <Hand className="h-4 w-4" />
                {localHandRaised ? "Lower hand" : "Raise hand"}
              </button>

              <button
                type="button"
                onClick={reconnectNow}
                disabled={connecting}
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-zinc-300 bg-white px-3 text-sm font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
              >
                <RefreshCcw className="h-4 w-4" />
                {connecting ? "Dang reconnect..." : "Reconnect"}
              </button>

              <button
                type="button"
                onClick={leaveRoom}
                disabled={!connected || leaving}
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-red-300 bg-red-50 px-3 text-sm font-medium text-red-700 hover:bg-red-100 disabled:opacity-50"
              >
                <AlertTriangle className="h-4 w-4" />
                {leaving ? "Dang roi..." : "Roi phong"}
              </button>
            </div>
          </div>
        </div>

        <aside className="space-y-4">
          <section className="rounded-xl border border-zinc-200 bg-white p-3">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-zinc-900">Heritage 3D Micro-Missions</h2>
              <Radio className="h-4 w-4 text-zinc-500" />
            </div>
            <HeritageStage3D
              missions={HERITAGE_MISSIONS}
              selectedMissionId={selectedMissionId}
              onSelectMission={handleSelectMission}
            />
            <div className="mt-3 grid grid-cols-2 gap-2">
              {HERITAGE_MISSIONS.map((mission) => (
                <button
                  key={mission.id}
                  type="button"
                  onClick={() => handleSelectMission(mission.id)}
                  className={[
                    "rounded-md border px-2 py-1.5 text-left text-xs font-medium",
                    mission.id === selectedMissionId
                      ? "border-zinc-400 bg-zinc-100 text-zinc-900"
                      : "border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50",
                  ].join(" ")}
                >
                  {mission.label}
                </button>
              ))}
            </div>
          </section>

          <section className="rounded-xl border border-zinc-200 bg-white p-3">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-zinc-900">Voice AI (Backend STT/TTS)</h3>
              <Waves className="h-4 w-4 text-amber-700" />
            </div>
            <div className="mb-2 text-[11px] text-zinc-500">
              Che do voice: {voiceBackendAvailable ? "backend-first" : "browser fallback"}
            </div>
            {!voiceSupported ? (
              <p className="text-xs text-zinc-500">
                Trinh duyet hien tai khong ho tro voice API can thiet (MediaRecorder hoac SpeechRecognition).
              </p>
            ) : (
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={voiceListening ? stopVoiceCapture : startVoiceCapture}
                    disabled={!connected || aiLoading || !hostSettings.aiEnabled}
                    className={[
                      "inline-flex min-h-10 items-center justify-center gap-2 rounded-md border px-2 text-xs font-medium",
                      voiceListening
                        ? "border-emerald-300 bg-emerald-50 text-emerald-700"
                        : "border-zinc-300 bg-white text-zinc-700",
                      !connected || !hostSettings.aiEnabled ? "opacity-50" : "hover:bg-zinc-50",
                    ].join(" ")}
                  >
                    <Mic className="h-3.5 w-3.5" />
                    {voiceListening ? "Dang nghe..." : "Start voice"}
                  </button>
                  <button
                    type="button"
                    onMouseDown={startVoiceCapture}
                    onMouseUp={stopVoiceCapture}
                    onMouseLeave={() => {
                      if (voiceListening) stopVoiceCapture();
                    }}
                    onTouchStart={startVoiceCapture}
                    onTouchEnd={stopVoiceCapture}
                    disabled={!connected || aiLoading || !hostSettings.aiEnabled}
                    className="inline-flex min-h-10 items-center justify-center rounded-md border border-amber-300 bg-amber-50 px-2 text-xs font-medium text-amber-800 hover:bg-amber-100 disabled:opacity-50"
                  >
                    Nhan giu de noi
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setVoiceWakePhraseRequired((prev) => !prev)}
                    className="inline-flex min-h-10 items-center justify-center rounded-md border border-zinc-300 px-2 text-xs text-zinc-700 hover:bg-zinc-50"
                  >
                    Wake phrase: {voiceWakePhraseRequired ? "ON" : "OFF"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setVoiceAutoSpeakEnabled((prev) => !prev)}
                    className="inline-flex min-h-10 items-center justify-center gap-1 rounded-md border border-zinc-300 px-2 text-xs text-zinc-700 hover:bg-zinc-50"
                  >
                    {voiceAutoSpeakEnabled ? (
                      <Volume2 className="h-3.5 w-3.5" />
                    ) : (
                      <VolumeX className="h-3.5 w-3.5" />
                    )}
                    Auto speak: {voiceAutoSpeakEnabled ? "ON" : "OFF"}
                  </button>
                </div>

                {voiceInterimText ? (
                  <div className="rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-800">
                    Trang thai voice: {voiceInterimText}
                  </div>
                ) : null}
                {voiceLastFinalText ? (
                  <div className="rounded-md border border-zinc-200 bg-zinc-50 px-2 py-1 text-xs text-zinc-700">
                    Last voice: {voiceLastFinalText}
                  </div>
                ) : null}

                <ul className="max-h-28 space-y-1 overflow-auto rounded-md border border-zinc-200 bg-zinc-50 p-2 text-[11px]">
                  {voiceTranscriptFeed.length === 0 ? (
                    <li className="text-zinc-500">Transcript feed se hien thi o day.</li>
                  ) : (
                    voiceTranscriptFeed.map((item) => (
                      <li key={item.id} className="rounded border border-zinc-200 bg-white px-2 py-1">
                        <div className="mb-0.5 flex items-center justify-between text-[10px] text-zinc-500">
                          <span>{item.speaker}</span>
                          <span>{new Date(item.createdAt).toLocaleTimeString()}</span>
                        </div>
                        <div className="text-zinc-700">{item.text}</div>
                      </li>
                    ))
                  )}
                </ul>
              </div>
            )}
          </section>

          <section className="rounded-xl border border-zinc-200 bg-white p-3">
            <div className="mb-3 flex gap-2">
              {[
                { id: "chat", label: "AI Chat", icon: Sparkles },
                { id: "participants", label: "Participants", icon: Users },
                { id: "events", label: "Events", icon: Radio },
              ].map((tab) => {
                const Icon = tab.icon;
                const active = sideTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setSideTab(tab.id)}
                    className={[
                      "inline-flex min-h-10 items-center gap-1 rounded-md border px-3 text-xs font-medium",
                      active
                        ? "border-zinc-900 bg-zinc-900 text-white"
                        : "border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50",
                    ].join(" ")}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {sideTab === "chat" ? (
              <div>
                <div className="mb-2 flex items-center justify-between gap-2">
                  <h3 className="text-sm font-semibold text-zinc-900">AI giao vien</h3>
                  <select
                    value={aiMode}
                    onChange={(e) => setAiMode(e.target.value)}
                    className="rounded-md border border-zinc-300 px-2 py-1 text-xs"
                  >
                    <option value="hint-first">hint-first</option>
                    <option value="direct-answer">direct-answer</option>
                  </select>
                </div>

                {!hostSettings.aiEnabled ? (
                  <div className="mb-2 rounded-md border border-zinc-300 bg-zinc-100 p-2 text-xs text-zinc-700">
                    AI dang bi host tat. Bat lai trong host panel de tiep tuc tro giup.
                  </div>
                ) : null}

                <div
                  ref={aiScrollRef}
                  className="h-64 space-y-2 overflow-auto rounded-md border border-zinc-200 bg-zinc-50 p-2"
                >
                  {aiMessages.map((message) => (
                    <div
                      key={message.id}
                      className={[
                        "rounded-md px-3 py-2 text-sm",
                        message.role === "user"
                          ? "bg-zinc-900 text-white"
                          : "bg-white text-zinc-800",
                      ].join(" ")}
                    >
                      <div className="whitespace-pre-wrap">{message.content}</div>
                      {message.checkpointPrompt ? (
                        <div className="mt-2 rounded border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-800">
                          <div className="font-medium">Checkpoint nhanh</div>
                          <div className="mt-0.5">{message.checkpointPrompt}</div>
                          <button
                            type="button"
                            onClick={() =>
                              void sendQuestionToAiTeacher(message.checkpointPrompt, {
                                source: "checkpoint",
                              })
                            }
                            disabled={aiLoading || !connected || !hostSettings.aiEnabled}
                            className="mt-1 rounded border border-amber-300 bg-white px-2 py-1 text-[11px] text-amber-800 hover:bg-amber-100 disabled:opacity-50"
                          >
                            Tra loi checkpoint
                          </button>
                        </div>
                      ) : null}
                      {Array.isArray(message.suggestedActions) && message.suggestedActions.length > 0 ? (
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {message.suggestedActions.map((action, idx) => (
                            <button
                              key={`${message.id}-action-${idx}`}
                              type="button"
                              onClick={() =>
                                void sendQuestionToAiTeacher(action.prompt, {
                                  source: "guided-next-step",
                                })
                              }
                              disabled={aiLoading || !connected || !hostSettings.aiEnabled}
                              className="rounded border border-zinc-300 bg-zinc-100 px-2 py-1 text-[11px] text-zinc-800 hover:bg-zinc-200 disabled:opacity-50"
                              title={action.prompt}
                            >
                              {action.label}
                            </button>
                          ))}
                        </div>
                      ) : null}
                      {Array.isArray(message.references) && message.references.length > 0 ? (
                        <div className="mt-2 rounded border border-zinc-200 bg-zinc-100/70 px-2 py-1 text-[11px] text-zinc-700">
                          <div className="font-medium text-zinc-600">Nguon tham khao noi bo</div>
                          <ul className="mt-1 space-y-1">
                            {message.references.map((ref, idx) => (
                              <li key={`${message.id}-ref-${idx}`}>
                                <span className="font-medium">{ref.title}</span>
                                {ref.snippet ? <span>: {ref.snippet}</span> : null}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                      {message.meta ? (
                        <div className="mt-1 text-[11px] opacity-70">{message.meta}</div>
                      ) : null}
                    </div>
                  ))}
                </div>

                <form onSubmit={askAiTeacher} className="mt-2 space-y-2">
                  <textarea
                    rows={3}
                    value={aiInput}
                    onChange={(e) => setAiInput(e.target.value)}
                    placeholder="Hoi AI giao vien ve noi dung di san..."
                    className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
                  />
                  <button
                    type="submit"
                    disabled={
                      !connected ||
                      aiLoading ||
                      !aiInput.trim() ||
                      !hostSettings.aiEnabled
                    }
                    className="w-full rounded-md bg-zinc-900 px-3 py-2 text-sm text-white disabled:opacity-50"
                  >
                    {aiLoading ? "AI dang tra loi..." : "Gui cho AI giao vien"}
                  </button>
                </form>
              </div>
            ) : null}

            {sideTab === "participants" ? (
              <div>
                <div className="mb-2 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-zinc-900">Danh sach participant</h3>
                  {canModerate ? (
                    <button
                      type="button"
                      onClick={handleMuteAll}
                      disabled={moderationLoading}
                      className="rounded-md border border-zinc-300 px-2 py-1 text-xs hover:bg-zinc-50 disabled:opacity-50"
                    >
                      {moderationLoading ? "Dang mute..." : "Mute all"}
                    </button>
                  ) : null}
                </div>

                <ul className="max-h-72 space-y-2 overflow-auto text-sm">
                  {mergedParticipants.length === 0 ? (
                    <li className="text-zinc-500">Chua co ai trong phong.</li>
                  ) : (
                    mergedParticipants.map((participant) => (
                      <li
                        key={participant.id}
                        className="rounded-md border border-zinc-200 px-3 py-2"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <div className="flex items-center gap-1 font-medium">
                              <span>{participant.name}{participant.isLocal ? " (ban)" : ""}</span>
                              {participant.handRaised ? (
                                <Hand className="h-3.5 w-3.5 text-amber-500" />
                              ) : null}
                            </div>
                            <div className="text-xs text-zinc-500">
                              role: {roleLabel(participant.role)}
                            </div>
                            <div className="text-xs text-zinc-500">
                              mic: {participant.microphoneEnabled ? "on" : "off"} | cam:{" "}
                              {participant.cameraEnabled ? "on" : "off"}
                            </div>
                          </div>

                          <div className="flex shrink-0 gap-1">
                            <button
                              type="button"
                              onClick={() =>
                                setPinnedIdentity((prev) =>
                                  prev === participant.identity ? null : participant.identity,
                                )
                              }
                              className="rounded border border-zinc-300 px-2 py-1 text-[11px] hover:bg-zinc-50"
                            >
                              {pinnedIdentity === participant.identity ? "Unpin" : "Pin"}
                            </button>

                            {canModerate && !participant.isLocal && !participant.isAi ? (
                              <>
                                <button
                                  type="button"
                                  onClick={() => void handleToggleCohost(participant)}
                                  disabled={Boolean(participantActionBusy[participant.backendId])}
                                  className="rounded border border-zinc-300 px-2 py-1 text-[11px] hover:bg-zinc-50 disabled:opacity-50"
                                >
                                  {participant.role === "cohost"
                                    ? "Set learner"
                                    : "Set cohost"}
                                </button>
                                <button
                                  type="button"
                                  onClick={() => void handleRemoveParticipant(participant)}
                                  disabled={Boolean(participantActionBusy[participant.backendId])}
                                  className="rounded border border-red-300 px-2 py-1 text-[11px] text-red-700 hover:bg-red-50 disabled:opacity-50"
                                >
                                  Remove
                                </button>
                              </>
                            ) : null}
                          </div>
                        </div>
                      </li>
                    ))
                  )}
                </ul>
              </div>
            ) : null}

            {sideTab === "events" ? (
              <div>
                <h3 className="mb-2 text-sm font-semibold text-zinc-900">Live events</h3>
                <ul className="max-h-72 space-y-2 overflow-auto text-xs">
                  {sortedEvents.length === 0 ? (
                    <li className="text-zinc-500">Chua co event.</li>
                  ) : (
                    sortedEvents.map((event) => (
                      <li
                        key={event.id}
                        className="rounded-md border border-zinc-200 bg-zinc-50 px-2 py-2"
                      >
                        <div className="mb-1 flex items-center justify-between gap-2">
                          <EventBadge eventType={event.event_type} />
                          <span className="text-zinc-500">
                            {new Date(event.created_at).toLocaleTimeString()}
                          </span>
                        </div>
                        <div className="text-zinc-700">
                          {event.participant_identity || "system"}
                        </div>
                      </li>
                    ))
                  )}
                </ul>
              </div>
            ) : null}
          </section>

          {canManageSettings ? (
            <section className="rounded-xl border border-zinc-200 bg-white p-3">
              <h3 className="mb-2 text-sm font-semibold text-zinc-900">Host panel</h3>
              <div className="grid grid-cols-1 gap-2">
                <button
                  type="button"
                  disabled={settingsBusy}
                  onClick={() =>
                    void applyHostSettings({
                      lockRoom: !hostSettings.lockRoom,
                    })
                  }
                  className="inline-flex min-h-11 items-center justify-between rounded-md border border-zinc-300 px-3 text-sm hover:bg-zinc-50 disabled:opacity-50"
                >
                  <span className="inline-flex items-center gap-2">
                    {hostSettings.lockRoom ? (
                      <Lock className="h-4 w-4 text-amber-600" />
                    ) : (
                      <LockOpen className="h-4 w-4 text-emerald-600" />
                    )}
                    Lock room
                  </span>
                  <span className="text-xs text-zinc-500">
                    {hostSettings.lockRoom ? "ON" : "OFF"}
                  </span>
                </button>

                <button
                  type="button"
                  disabled={settingsBusy}
                  onClick={() =>
                    void applyHostSettings({
                      aiEnabled: !hostSettings.aiEnabled,
                    })
                  }
                  className="inline-flex min-h-11 items-center justify-between rounded-md border border-zinc-300 px-3 text-sm hover:bg-zinc-50 disabled:opacity-50"
                >
                  <span className="inline-flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-zinc-600" />
                    AI teacher
                  </span>
                  <span className="text-xs text-zinc-500">
                    {hostSettings.aiEnabled ? "ON" : "OFF"}
                  </span>
                </button>
              </div>
              <p className="mt-2 text-xs text-zinc-500">
                Lock room chan learner moi vao phong. AI toggle dieu khien chat AI teacher.
              </p>
            </section>
          ) : null}
        </aside>
      </section>

      <div ref={audioContainerRef} />
    </main>
  );
}
