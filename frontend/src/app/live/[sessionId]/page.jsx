"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ConnectionQuality, Room, RoomEvent, Track } from "livekit-client";
import {
  Camera,
  CameraOff,
  CheckCircle2,
  Copy,
  Hand,
  Headphones,
  Keyboard,
  Lock,
  LockOpen,
  MessageSquare,
  Mic,
  MicOff,
  MonitorUp,
  MonitorX,
  Pin,
  PinOff,
  PhoneOff,
  Radio,
  RefreshCcw,
  Send,
  Settings,
  Sparkles,
  Volume2,
  VolumeX,
  Wifi,
  Waves,
  Users,
} from "lucide-react";

import HeritageStage3D from "@/components/live/HeritageStage3D";
import {
  askLiveAiTeacher,
  createLiveSessionEvent,
  ensureLiveAiTeacherPresence,
  getLiveSessionObservability,
  hostMuteAllLiveParticipants,
  hostRemoveLiveParticipant,
  endLiveSession,
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
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const HERITAGE_MISSIONS = [
  {
    id: "dinh-top",
    label: "Đỉnh",
    prompt:
      "Gợi ý cách nhìn bố cục tổng thể trên đỉnh và ý nghĩa biểu tượng của bộ phận này.",
    position: [0.0, 1.12, 0.0],
  },
  {
    id: "motif-band",
    label: "Họa tiết",
    prompt:
      "Phân tích nhanh một họa tiết di sản trong vùng thân đỉnh: hình dáng, ý nghĩa, bối cảnh lịch sử.",
    position: [0.92, 0.67, 0.36],
  },
  {
    id: "inscription",
    label: "Chữ khắc",
    prompt:
      "Giải thích vai trò của phần chữ khắc trên đỉnh và cách đọc nguồn tư liệu để hiểu đúng nghĩa.",
    position: [-0.88, 0.52, -0.42],
  },
  {
    id: "pedestal",
    label: "Chân đế",
    prompt:
      "Tại sao chân đế có ý nghĩa trong ngôn ngữ tạo hình di sản? Gợi ý cách liên hệ với bối cảnh triều Nguyễn.",
    position: [0.18, -0.04, 0.98],
  },
];

const SMALLEST_CAO_DINH_MODEL_URL = "/assets/models/CAO-DINH-v1-512.glb";

const HERITAGE_MISSION_MODEL_BY_ID = Object.freeze({
  "dinh-top": SMALLEST_CAO_DINH_MODEL_URL,
  "motif-band": SMALLEST_CAO_DINH_MODEL_URL,
  inscription: SMALLEST_CAO_DINH_MODEL_URL,
  pedestal: SMALLEST_CAO_DINH_MODEL_URL,
});

const LIVE_TTS_ENABLED = process.env.NEXT_PUBLIC_LIVE_TTS_ENABLED !== "false";
const DEFAULT_DEVICE_ID = "default";
const HERITAGE_PANEL_CLASS =
  "relative overflow-hidden rounded-2xl border border-amber-500/18 bg-[linear-gradient(135deg,rgba(24,18,12,0.96),rgba(9,9,11,0.94))] p-3 shadow-[0_14px_46px_rgba(0,0,0,0.28)] ring-1 ring-white/5";
const HERITAGE_FIELD_CLASS =
  "rounded-xl border border-amber-500/15 bg-black/30 shadow-inner shadow-black/20";
const HERITAGE_SELECT_TRIGGER_CLASS =
  "h-10 rounded-xl border-amber-500/20 bg-black/35 text-sm text-amber-50 shadow-inner shadow-black/20";
const HERITAGE_BUTTON_CLASS =
  "rounded-xl border-amber-500/25 bg-black/25 text-amber-100 normal-case tracking-normal hover:border-amber-300/50 hover:bg-amber-500/10";

const WAKE_PHRASES = ["co giao oi", "co giao", "ai teacher"];

const AI_MODE_OPTIONS = [
  { value: "hint-first", label: "Gợi ý trước" },
  { value: "direct-answer", label: "Trả lời trực tiếp" },
];

const GRADE_LEVEL_OPTIONS = [
  { value: "primary", label: "Tiểu học" },
  { value: "middle_school", label: "Trung học cơ sở" },
  { value: "high_school", label: "Trung học phổ thông" },
  { value: "university", label: "Đại học" },
];

const AI_QUICK_PROMPTS = [
  "Tóm tắt phần trọng tâm của Cao Đỉnh trong 3 ý dễ nhớ.",
  "Đặt cho lớp một câu hỏi kiểm tra nhanh về biểu tượng trên đỉnh.",
  "Giải thích vì sao họa tiết di sản cần đọc cùng bối cảnh lịch sử.",
];

function normalizeSpeechText(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function sanitizeTextForSpeech(value) {
  let text = String(value || "");
  if (!text) return "";

  // Keep readable content while stripping markdown syntax/noise.
  text = text.replace(/```[\s\S]*?```/g, (block) => block.replace(/```/g, "").trim());
  text = text.replace(/`([^`]+)`/g, "$1");
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1");
  text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, "$1");
  text = text.replace(/^#{1,6}\s+/gm, "");
  text = text.replace(/^>\s?/gm, "");
  text = text.replace(/^\s*[-*+]\s+/gm, "");
  text = text.replace(/^\s*\d+\.\s+/gm, "");
  text = text.replace(/\*\*([^*]+)\*\*/g, "$1");
  text = text.replace(/__([^_]+)__/g, "$1");
  text = text.replace(/\*([^*]+)\*/g, "$1");
  text = text.replace(/_([^_]+)_/g, "$1");
  text = text.replace(/~~([^~]+)~~/g, "$1");
  text = text.replace(/\*{2,}/g, " ");
  text = text.replace(/_{2,}/g, " ");
  text = text.replace(/~{2,}/g, " ");
  text = text.replace(/`{1,3}/g, " ");
  text = text.replace(/(^|\s)[>#]+(?=\s|$)/g, " ");
  text = text.replace(/\|/g, " ");
  text = text.replace(/\s+/g, " ").trim();
  return text;
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
    name: participant.name || participant.identity || "Người dùng",
    isLocal,
    microphoneEnabled: getTrackEnabledState(participant.audioTrackPublications),
    cameraEnabled: getTrackEnabledState(participant.videoTrackPublications),
  };
}

function roleLabel(role) {
  if (role === "host") return "Chủ phòng";
  if (role === "cohost") return "Đồng chủ phòng";
  if (role === "ai_teacher") return "Trợ giảng AI";
  return "Học viên";
}

function networkStatusLabel(status) {
  if (status === "connected") return "Đã kết nối";
  if (status === "reconnecting") return "Đang kết nối lại";
  if (status === "degraded") return "AI dự phòng";
  if (status === "waiting") return "Đang chờ duyệt";
  if (status === "disconnected") return "Mất kết nối";
  return "Đang chờ";
}

function voiceSpeakerLabel(speaker) {
  if (speaker === "assistant") return "AI giáo viên";
  if (speaker === "user") return "Bạn";
  if (speaker === "system") return "Hệ thống";
  return speaker || "Ẩn danh";
}

function canModerateRole(role) {
  return role === "host" || role === "cohost";
}

function humanizeLiveError(raw) {
  const message = String(raw || "").trim();
  const normalized = message.toLowerCase();

  if (normalized.includes("request-uri too large") || normalized.includes("http 414")) {
    return "Server đang chặn URL kết nối quá dài (nginx 414). Đã chuyển sang chế độ kết nối tương thích để vào phòng ổn định hơn.";
  }
  if (normalized.includes("v1 rtc path not found")) {
    return "Server LiveKit đang không tương thích đường kết nối mới. Hệ thống sẽ thử kết nối bằng chế độ tương thích.";
  }
  if (
    normalized.includes("invalid authorization token") ||
    normalized.includes("token might be expired") ||
    normalized.includes("unauthorized") ||
    normalized.includes("not allowed")
  ) {
    return "Token phòng live đã hết hạn hoặc không hợp lệ. Bấm Kết nối lại để cấp token mới.";
  }
  if (normalized.includes("could not establish pc connection")) {
    return "Không tạo được kết nối WebRTC peer connection. Hệ thống sẽ ưu tiên relay mode và bạn có thể bấm Kết nối lại để thử lại.";
  }
  if (normalized.includes("livekit api credentials are not configured")) {
    return "Hệ thống LiveKit chưa được cấu hình đầy đủ trên server.";
  }
  if (normalized.includes("disconnected")) {
    return "Phòng live bị ngắt kết nối. Thử reconnect để vào lại nhanh.";
  }
  return message || "Không thể kết nối phòng live.";
}

function isLivekitNonRetryableError(raw) {
  const normalized = String(raw || "").toLowerCase();
  return (
    normalized.includes("invalid authorization token") ||
    normalized.includes("token might be expired") ||
    normalized.includes("unauthorized") ||
    normalized.includes("not allowed") ||
    normalized.includes("forbidden")
  );
}

function isPeerConnectionSetupError(raw) {
  const normalized = String(raw || "").toLowerCase();
  return (
    normalized.includes("could not establish pc connection") ||
    normalized.includes("pc connection") ||
    normalized.includes("webrtc") ||
    (normalized.includes("ice") && normalized.includes("failed"))
  );
}

function isLockedRoomError(raw) {
  const normalized = String(raw || "").toLowerCase();
  return (
    normalized.includes("currently locked by host") ||
    normalized.includes("room is currently locked") ||
    normalized.includes("phòng") && normalized.includes("khóa")
  );
}

function isTypingTarget(target) {
  if (!target) return false;
  const tagName = String(target.tagName || "").toLowerCase();
  return (
    tagName === "input" ||
    tagName === "textarea" ||
    tagName === "select" ||
    Boolean(target.isContentEditable)
  );
}

function deviceOptionValue(deviceId) {
  return String(deviceId || DEFAULT_DEVICE_ID);
}

function resolveDeviceId(value) {
  const normalized = String(value || DEFAULT_DEVICE_ID);
  return normalized === DEFAULT_DEVICE_ID ? undefined : normalized;
}

function labelMediaDevice(device, fallback, index) {
  const label = String(device?.label || "").trim();
  if (label) return label;
  return `${fallback} ${index + 1}`;
}

function devicePermissionMeta(state) {
  if (state === "granted") return { label: "Đã cấp quyền", tone: "text-emerald-300" };
  if (state === "denied") return { label: "Chưa cấp quyền", tone: "text-red-300" };
  if (state === "unavailable") return { label: "Không hỗ trợ", tone: "text-amber-300" };
  return { label: "Chưa kiểm tra", tone: "text-zinc-400" };
}

function networkProbeMeta(probe) {
  if (probe.status === "ok") {
    return {
      label: `Server ổn${probe.latencyMs ? ` (${probe.latencyMs}ms)` : ""}`,
      tone: "text-emerald-300",
    };
  }
  if (probe.status === "checking") return { label: "Đang kiểm tra", tone: "text-amber-300" };
  if (probe.status === "error") return { label: "Server/đường truyền lỗi", tone: "text-red-300" };
  return { label: "Chưa kiểm tra", tone: "text-zinc-400" };
}

function formatPercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "0%";
  return `${Math.round(number * 1000) / 10}%`;
}

async function applyAudioOutputToElement(element, deviceId) {
  if (!element || typeof element.setSinkId !== "function") return false;
  const sinkId = resolveDeviceId(deviceId) || "";
  await element.setSinkId(sinkId);
  return true;
}

function collectLivekitUrlCandidates(primaryUrl) {
  const urls = [];
  const pushUnique = (candidate) => {
    const normalized = String(candidate || "").trim();
    if (!normalized) return;
    if (!urls.includes(normalized)) urls.push(normalized);
  };

  pushUnique(primaryUrl);

  if (typeof window !== "undefined" && window.location?.origin) {
    const origin = window.location.origin.replace(/\/+$/, "");
    pushUnique(`${origin}/livekit/`);
    pushUnique(`${origin}/livekit`);
  }

  try {
    const parsed = new URL(String(primaryUrl || ""));
    if (parsed.pathname && !parsed.pathname.endsWith("/")) {
      pushUnique(`${parsed.origin}${parsed.pathname}/`);
    }
    if (parsed.protocol === "wss:" || parsed.protocol === "ws:") {
      pushUnique(`${parsed.protocol}//${parsed.host}/livekit/`);
      pushUnique(`${parsed.protocol}//${parsed.host}/livekit`);
      if (parsed.protocol === "wss:" && parsed.port && parsed.port !== "443") {
        pushUnique(`wss://${parsed.hostname}/livekit/`);
        pushUnique(`wss://${parsed.hostname}/livekit`);
      }
    }
  } catch {
    // Keep only valid URL candidates.
  }

  return urls;
}

function qualityMeta(quality) {
  const poor = ConnectionQuality?.Poor;
  const good = ConnectionQuality?.Good;
  const excellent = ConnectionQuality?.Excellent;

  if (quality === excellent) {
    return { label: "Tốt", tone: "text-emerald-700" };
  }
  if (quality === good) {
    return { label: "Ổn", tone: "text-amber-700" };
  }
  if (quality === poor) {
    return { label: "Kém", tone: "text-red-700" };
  }
  return { label: "Chưa rõ", tone: "text-zinc-500" };
}

function readHostSettings(metadata) {
  const source = metadata && typeof metadata === "object" ? metadata : {};
  const rawCeiling = Number(source.ai_cost_ceiling_usd);
  return {
    lockRoom: Boolean(source.lock_room),
    aiEnabled: source.ai_enabled !== false,
    gradeLevel: String(source.grade_level || "middle_school").trim() || "middle_school",
    aiCostCeilingUsd:
      Number.isFinite(rawCeiling) && rawCeiling > 0 ? rawCeiling : 3.0,
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
      label: label || "Học tiếp",
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

function normalizeAiCitations(raw) {
  if (!Array.isArray(raw)) return [];
  const items = [];
  for (const entry of raw) {
    if (!entry || typeof entry !== "object") continue;
    const tag = String(entry.tag || "").trim();
    const title = String(entry.title || "").trim();
    if (!tag || !title) continue;
    items.push({ tag, title });
  }
  return items.slice(0, 5);
}

function normalizeAiRubric(raw) {
  if (!raw || typeof raw !== "object") return null;
  const understandingLevel = String(raw.understanding_level || "").trim();
  if (!understandingLevel) return null;
  const knowledgeGaps = Array.isArray(raw.knowledge_gaps)
    ? raw.knowledge_gaps.map((item) => String(item || "").trim()).filter(Boolean).slice(0, 3)
    : [];
  const nextSteps = Array.isArray(raw.next_steps)
    ? raw.next_steps.map((item) => String(item || "").trim()).filter(Boolean).slice(0, 3)
    : [];
  return {
    understandingLevel,
    knowledgeGaps,
    nextSteps,
  };
}

function isScreenSharePublication(pub) {
  return pub?.source === Track.Source.ScreenShare || pub?.source === "screen_share";
}

function isCameraPublication(pub) {
  return Boolean(pub?.track) && !isScreenSharePublication(pub);
}

function hasScreenShareTrack(participant) {
  if (!participant?.videoTrackPublications) return false;
  return Array.from(participant.videoTrackPublications.values()).some(
    (pub) => Boolean(pub.track) && isScreenSharePublication(pub),
  );
}

function displayParticipantName(participant, fallback = "Người dùng") {
  return participant?.name || participant?.identity || fallback;
}

function HeritagePanel({ children, className = "" }) {
  return (
    <section className={[HERITAGE_PANEL_CLASS, className].filter(Boolean).join(" ")}>
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-amber-300/45 to-transparent" />
      <div className="pointer-events-none absolute -right-16 -top-16 h-36 w-36 rounded-full bg-amber-500/10 blur-3xl" />
      <div className="relative">{children}</div>
    </section>
  );
}

function HeritagePanelHeader({ icon: Icon, eyebrow, title, description, action }) {
  return (
    <div className="mb-3 flex items-start justify-between gap-3">
      <div>
        {eyebrow ? (
          <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.24em] text-amber-300/75">
            {eyebrow}
          </div>
        ) : null}
        <h2 className="text-sm font-semibold text-amber-50">{title}</h2>
        {description ? (
          <p className="mt-0.5 text-xs leading-relaxed text-stone-400">{description}</p>
        ) : null}
      </div>
      {action || (Icon ? (
        <div className="rounded-full border border-amber-500/20 bg-amber-500/10 p-2 text-amber-200">
          <Icon className="h-4 w-4" />
        </div>
      ) : null)}
    </div>
  );
}

function HeritageStat({ label, value, tone = "text-amber-100" }) {
  return (
    <div className="rounded-xl border border-amber-500/15 bg-black/30 px-3 py-2 shadow-inner shadow-black/20">
      <span className="block text-[10px] font-medium uppercase tracking-[0.18em] text-stone-500">
        {label}
      </span>
      <span className={`text-sm font-semibold ${tone}`}>{value}</span>
    </div>
  );
}

function EventBadge({ eventType }) {
  if (eventType === "raise_hand") {
    return <span className="rounded bg-amber-100 px-2 py-0.5 text-[10px] text-amber-700">Giơ tay</span>;
  }
  if (eventType === "live_chat_message") {
    return <span className="rounded bg-sky-100 px-2 py-0.5 text-[10px] text-sky-700">Tin nhắn</span>;
  }
  if (eventType === "join_request") {
    return <span className="rounded bg-blue-100 px-2 py-0.5 text-[10px] text-blue-700">Xin vào phòng</span>;
  }
  if (eventType === "participant_joined") {
    return <span className="rounded bg-emerald-100 px-2 py-0.5 text-[10px] text-emerald-700">Tham gia</span>;
  }
  if (eventType === "participant_left") {
    return <span className="rounded bg-stone-800 px-2 py-0.5 text-[10px] text-stone-200">Rời phòng</span>;
  }
  return <span className="rounded bg-stone-800 px-2 py-0.5 text-[10px] text-stone-200">{eventType}</span>;
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
        "relative overflow-hidden rounded-2xl border bg-[radial-gradient(circle_at_50%_0%,rgba(180,120,45,0.16),rgba(9,9,11,0.98)_58%)] shadow-[0_24px_80px_rgba(0,0,0,0.36)]",
        pinned
          ? "border-amber-300/80 ring-2 ring-amber-300/30"
          : "border-amber-500/15",
      ].join(" ")}
    >
      <div className="pointer-events-none absolute inset-0 z-10 bg-[linear-gradient(135deg,rgba(250,204,21,0.08),transparent_30%,rgba(20,184,166,0.05)_72%,transparent)]" />
      {tile.track ? (
        <video
          ref={videoRef}
          autoPlay
          muted={tile.isLocal}
          playsInline
          className={[
            "aspect-video w-full bg-zinc-950",
            tile.isScreenShare ? "object-contain" : "object-cover",
          ].join(" ")}
        />
      ) : (
        <div className="flex aspect-video w-full items-center justify-center bg-[radial-gradient(circle_at_center,rgba(120,83,37,0.28),rgba(9,9,11,0.98)_62%)]">
          <div className="rounded-full border border-amber-400/20 bg-black/40 px-5 py-3 text-sm text-amber-50 shadow-inner shadow-amber-950/40">
            {tile.name}
          </div>
        </div>
      )}

      <div className="absolute inset-x-0 bottom-0 z-20 flex items-center justify-between bg-gradient-to-t from-black/95 via-black/60 to-transparent p-3 text-xs text-amber-50">
        <div className="flex items-center gap-2">
          <span className="truncate">
            {tile.name}{tile.isLocal ? " (bạn)" : ""}
          </span>
          {tile.isScreenShare ? (
            <Badge className="rounded bg-sky-500/20 px-1.5 py-0 text-[10px] text-sky-100 hover:bg-sky-500/20">
              Màn hình
            </Badge>
          ) : null}
          {handRaised ? <Hand className="h-3.5 w-3.5 text-amber-300" /> : null}
        </div>
        <Button
          type="button"
          variant="outline"
          size="icon-xs"
          onClick={() => onTogglePin(tile.identity)}
          className="rounded-full border-amber-400/25 bg-black/50 text-amber-100 hover:border-amber-300/70 hover:bg-amber-500/10"
          aria-label={pinned ? "Bỏ ghim người tham gia" : "Ghim người tham gia"}
        >
          {pinned ? <PinOff className="h-3.5 w-3.5" /> : <Pin className="h-3.5 w-3.5" />}
        </Button>
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
    gradeLevel: "middle_school",
    aiCostCeilingUsd: 3.0,
  });
  const [settingsBusy, setSettingsBusy] = useState(false);
  const [networkStatus, setNetworkStatus] = useState("disconnected");
  const [aiFallbackMode, setAiFallbackMode] = useState(false);
  const [connectionQuality, setConnectionQuality] = useState(null);
  const [reconnectCount, setReconnectCount] = useState(0);
  const [lastReconnectedAt, setLastReconnectedAt] = useState(null);
  const [microphoneEnabled, setMicrophoneEnabled] = useState(false);
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [screenShareEnabled, setScreenShareEnabled] = useState(false);
  const [pinnedIdentity, setPinnedIdentity] = useState(null);
  const [sideTab, setSideTab] = useState("ai");
  const [selectedMissionId, setSelectedMissionId] = useState(HERITAGE_MISSIONS[0].id);

  const [moderationLoading, setModerationLoading] = useState(false);
  const [participantActionBusy, setParticipantActionBusy] = useState({});
  const [notice, setNotice] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [chatSending, setChatSending] = useState(false);
  const [sessionEnding, setSessionEnding] = useState(false);
  const [waitingForHost, setWaitingForHost] = useState(false);
  const [deviceBusy, setDeviceBusy] = useState(false);
  const [devicePermissionState, setDevicePermissionState] = useState("unknown");
  const [mediaDevices, setMediaDevices] = useState({
    audioinput: [],
    videoinput: [],
    audiooutput: [],
  });
  const [selectedMicrophoneId, setSelectedMicrophoneId] = useState(DEFAULT_DEVICE_ID);
  const [selectedCameraId, setSelectedCameraId] = useState(DEFAULT_DEVICE_ID);
  const [selectedSpeakerId, setSelectedSpeakerId] = useState(DEFAULT_DEVICE_ID);
  const [networkProbe, setNetworkProbe] = useState({
    status: "idle",
    latencyMs: null,
    checkedAt: null,
  });
  const [observability, setObservability] = useState(null);

  const [aiMode, setAiMode] = useState("hint-first");
  const [aiInput, setAiInput] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiMessages, setAiMessages] = useState([
    {
      id: "seed-1",
      role: "assistant",
      content:
        "Mình đã sẵn sàng hỗ trợ lớp học. Hãy hỏi về Cao Đỉnh, họa tiết, chữ khắc hoặc yêu cầu mình tạo một câu hỏi kiểm tra nhanh.",
      meta: "AI giáo viên",
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
  const selectedMicrophoneIdRef = useRef(DEFAULT_DEVICE_ID);
  const selectedCameraIdRef = useRef(DEFAULT_DEVICE_ID);

  const [voiceSupported, setVoiceSupported] = useState(false);
  const [voiceBackendAvailable, setVoiceBackendAvailable] = useState(true);
  const [voiceListening, setVoiceListening] = useState(false);
  const [voiceWakePhraseRequired, setVoiceWakePhraseRequired] = useState(true);
  const [voiceAutoSpeakEnabled, setVoiceAutoSpeakEnabled] = useState(LIVE_TTS_ENABLED);
  const [voiceInterimText, setVoiceInterimText] = useState("");
  const [voiceLastFinalText, setVoiceLastFinalText] = useState("");
  const [voiceTranscriptFeed, setVoiceTranscriptFeed] = useState([]);

  useEffect(() => {
    connectingRef.current = connecting;
  }, [connecting]);

  useEffect(() => {
    leavingRef.current = leaving;
  }, [leaving]);

  useEffect(() => {
    selectedMicrophoneIdRef.current = selectedMicrophoneId;
  }, [selectedMicrophoneId]);

  useEffect(() => {
    selectedCameraIdRef.current = selectedCameraId;
  }, [selectedCameraId]);

  const localIdentity = useMemo(
    () => (currentUser?.id ? `user-${currentUser.id}` : null),
    [currentUser?.id],
  );

  const quality = useMemo(() => qualityMeta(connectionQuality), [connectionQuality]);
  const aiInteractionReady = connected || aiFallbackMode;
  const ttsAutoSpeakActive = LIVE_TTS_ENABLED && voiceAutoSpeakEnabled;
  const missionById = useMemo(
    () => new Map(HERITAGE_MISSIONS.map((mission) => [mission.id, mission])),
    [],
  );
  const selectedMissionModelUrl = useMemo(
    () =>
      HERITAGE_MISSION_MODEL_BY_ID[selectedMissionId] ||
      SMALLEST_CAO_DINH_MODEL_URL,
    [selectedMissionId],
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
      message.includes("audio model") ||
      message.includes("not available in group") ||
      message.includes("edge tts fallback failed") ||
      message.includes("gtts fallback failed") ||
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

  const refreshMediaDevices = useCallback(async () => {
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.enumerateDevices) {
      setDevicePermissionState("unavailable");
      return;
    }

    const devices = await navigator.mediaDevices.enumerateDevices();
    const grouped = {
      audioinput: [],
      videoinput: [],
      audiooutput: [],
    };

    for (const device of devices) {
      if (device.kind === "audioinput") grouped.audioinput.push(device);
      if (device.kind === "videoinput") grouped.videoinput.push(device);
      if (device.kind === "audiooutput") grouped.audiooutput.push(device);
    }

    setMediaDevices(grouped);
    setSelectedMicrophoneId((current) =>
      current === DEFAULT_DEVICE_ID ||
      grouped.audioinput.some((device) => device.deviceId === current)
        ? current
        : DEFAULT_DEVICE_ID,
    );
    setSelectedCameraId((current) =>
      current === DEFAULT_DEVICE_ID ||
      grouped.videoinput.some((device) => device.deviceId === current)
        ? current
        : DEFAULT_DEVICE_ID,
    );
    setSelectedSpeakerId((current) =>
      current === DEFAULT_DEVICE_ID ||
      grouped.audiooutput.some((device) => device.deviceId === current)
        ? current
        : DEFAULT_DEVICE_ID,
    );
  }, []);

  const runPreflightCheck = useCallback(async () => {
    setDeviceBusy(true);
    setNotice("");
    setNetworkProbe((prev) => ({ ...prev, status: "checking" }));

    try {
      if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
        setDevicePermissionState("unavailable");
      } else {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
          video: true,
        });
        stream.getTracks().forEach((track) => track.stop());
        setDevicePermissionState("granted");
        await refreshMediaDevices();
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setDevicePermissionState("denied");
      setNotice(
        `Trình duyệt chưa cấp quyền mic/camera. Hãy bật quyền thiết bị rồi kiểm tra lại. Chi tiết: ${message}`,
      );
    }

    try {
      const startedAt = performance.now();
      const response = await fetch("/health", {
        cache: "no-store",
        credentials: "same-origin",
      });
      const latencyMs = Math.round(performance.now() - startedAt);
      setNetworkProbe({
        status: response.ok ? "ok" : "error",
        latencyMs,
        checkedAt: new Date().toISOString(),
      });
    } catch {
      setNetworkProbe({
        status: "error",
        latencyMs: null,
        checkedAt: new Date().toISOString(),
      });
    } finally {
      setDeviceBusy(false);
    }
  }, [refreshMediaDevices]);

  useEffect(() => {
    void refreshMediaDevices().catch(() => {
      setDevicePermissionState("unavailable");
    });

    if (typeof navigator === "undefined" || !navigator.mediaDevices) return undefined;
    const onDeviceChange = () => {
      void refreshMediaDevices().catch(() => {});
    };
    navigator.mediaDevices.addEventListener?.("devicechange", onDeviceChange);
    return () => {
      navigator.mediaDevices.removeEventListener?.("devicechange", onDeviceChange);
    };
  }, [refreshMediaDevices]);

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
    void applyAudioOutputToElement(mediaElement, selectedSpeakerId).catch(() => {});
    audioContainerRef.current.appendChild(mediaElement);
    audioTracksRef.current.set(track.sid, { track, el: mediaElement });
  }, [selectedSpeakerId]);

  useEffect(() => {
    for (const { el } of audioTracksRef.current.values()) {
      void applyAudioOutputToElement(el, selectedSpeakerId).catch(() => {
        setNotice("Trình duyệt không cho phép đổi loa đầu ra cho phiên live này.");
      });
    }
  }, [selectedSpeakerId]);

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
      const localVideoPublications = Array.from(localParticipant.videoTrackPublications.values());
      const localScreenPub = localVideoPublications.find(
        (pub) => Boolean(pub.track) && isScreenSharePublication(pub),
      );
      const localVideoPub = localVideoPublications.find(isCameraPublication);
      if (localScreenPub) {
        nextVideoTiles.push({
          identity: `${localParticipant.identity}:screen`,
          ownerIdentity: localParticipant.identity,
          name: `${displayParticipantName(localParticipant, "Bạn")} đang chia sẻ`,
          isLocal: true,
          isScreenShare: true,
          track: localScreenPub.track,
        });
      }
      nextVideoTiles.push({
        identity: localParticipant.identity,
        ownerIdentity: localParticipant.identity,
        name: localParticipant.name || localParticipant.identity || "Bạn",
        isLocal: true,
        isScreenShare: false,
        track: localVideoPub?.track || null,
      });
    }

    for (const remote of room.remoteParticipants.values()) {
      nextParticipants.push(toParticipantViewModel(remote, false));
      const remoteVideoPublications = Array.from(remote.videoTrackPublications.values());
      const screenPub = remoteVideoPublications.find(
        (pub) => Boolean(pub.track) && isScreenSharePublication(pub),
      );
      const firstVideoPub = remoteVideoPublications.find(isCameraPublication);
      if (screenPub) {
        nextVideoTiles.push({
          identity: `${remote.identity}:screen`,
          ownerIdentity: remote.identity,
          name: `${displayParticipantName(remote)} đang chia sẻ`,
          isLocal: false,
          isScreenShare: true,
          track: screenPub.track,
        });
      }
      nextVideoTiles.push({
        identity: remote.identity,
        ownerIdentity: remote.identity,
        name: remote.name || remote.identity || "Người dùng",
        isLocal: false,
        isScreenShare: false,
        track: firstVideoPub?.track || null,
      });
    }

    setParticipants(nextParticipants);
    setVideoTiles(nextVideoTiles);
    setScreenShareEnabled(hasScreenShareTrack(room.localParticipant));
  }, []);

  const connectLivekitWithFallback = useCallback(async ({ room, livekitUrl, token }) => {
    const urlCandidates = collectLivekitUrlCandidates(livekitUrl);
    const attempts = [];
    const baseOptions = {
      websocketTimeout: 20000,
      peerConnectionTimeout: 22000,
      maxRetries: 2,
    };
    for (const candidateUrl of urlCandidates) {
      attempts.push({
        url: candidateUrl,
        relayOnly: false,
        options: baseOptions,
      });
      attempts.push({
        url: candidateUrl,
        relayOnly: true,
        options: {
          ...baseOptions,
          peerConnectionTimeout: 30000,
          rtcConfig: {
            iceTransportPolicy: "relay",
            bundlePolicy: "max-bundle",
            iceCandidatePoolSize: 0,
          },
        },
      });
      attempts.push({
        url: candidateUrl,
        relayOnly: true,
        options: {
          ...baseOptions,
          websocketTimeout: 25000,
          peerConnectionTimeout: 36000,
          maxRetries: 3,
          rtcConfig: {
            iceTransportPolicy: "relay",
            bundlePolicy: "max-bundle",
            iceCandidatePoolSize: 0,
          },
        },
      });
    }

    let lastError = null;
    for (let index = 0; index < attempts.length; index += 1) {
      const attempt = attempts[index];
      const hasMore = index < attempts.length - 1;
      try {
        await room.connect(attempt.url, token, attempt.options);
        if (attempt.relayOnly && index > 0) {
          setNotice("Đã kết nối thành công bằng relay mode.");
        }
        return;
      } catch (err) {
        lastError = err;
        const raw = err instanceof Error ? err.message : String(err);
        if (isLivekitNonRetryableError(raw) || !hasMore) {
          throw err;
        }
        try {
          room.disconnect();
        } catch {
          // no-op
        }
        if (!attempt.relayOnly) {
          setNotice("Mạng đang hạn chế WebRTC trực tiếp. Đang thử relay mode...");
        } else {
          setNotice("Đang thử tuyến relay dự phòng khác...");
        }
      }
    }

    if (lastError) throw lastError;
    throw new Error("Không thể kết nối LiveKit.");
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

  const refreshObservability = useCallback(async () => {
    if (!sessionId || !canModerateRole(localRole)) return;
    try {
      const snapshot = await getLiveSessionObservability({ sessionId });
      setObservability(snapshot || null);
    } catch {
      // Observability is staff-only and should never interrupt the meeting.
    }
  }, [localRole, sessionId]);

  const requestHostAdmit = useCallback(async () => {
    if (!sessionId || !localIdentity) return;
    try {
      const event = await createLiveSessionEvent({
        sessionId,
        eventType: "join_request",
        payload: {
          participant_identity: localIdentity,
          display_name: currentUser?.full_name || currentUser?.email || "Học viên",
          requested_at: new Date().toISOString(),
        },
      });
      if (event?.id) {
        setSessionEvents((prev) =>
          prev.some((item) => item.id === event.id) ? prev : [event, ...prev],
        );
      }
    } catch {
      // Locked-room join requests are best-effort; the retry button still works.
    }
  }, [currentUser?.email, currentUser?.full_name, localIdentity, sessionId]);

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
        await Promise.all([
          refreshBackendParticipants(),
          refreshSessionEvents(),
          refreshObservability(),
        ]);
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
  }, [connected, refreshBackendParticipants, refreshObservability, refreshSessionEvents]);

  useEffect(() => {
    if (!sessionId) return;
    if (authStatus === "checking") return;
    if (authStatus !== "authed") {
      setError("Bạn cần đăng nhập để vào phòng live.");
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
      setAiFallbackMode(false);
      setWaitingForHost(false);
      setConnecting(false);
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
          "Kết nối bị ngắt. Đang tự động xin token mới và reconnect...",
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
      setConnecting(false);
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
      try {
        const decoded = new TextDecoder().decode(payload);
        const parsed = JSON.parse(decoded);
        if (!parsed || typeof parsed !== "object") return;
        const type = String(parsed.type || "").toLowerCase();
        if (topic === "live-chat" || type === "live_chat_message") {
          const text = String(parsed.text || parsed.content || "").trim();
          if (!text) return;
          const eventId = String(parsed.id || `chat-${Date.now()}`);
          setSessionEvents((prev) => {
            if (prev.some((event) => String(event.id) === eventId)) return prev;
            return [
              ...prev,
              {
                id: eventId,
                event_type: "live_chat_message",
                participant_identity: participant?.identity || parsed.participant_identity || "",
                payload: {
                  text,
                  display_name: parsed.display_name || participant?.name || participant?.identity || "",
                  participant_identity:
                    parsed.participant_identity || participant?.identity || "",
                },
                created_at: parsed.created_at || new Date().toISOString(),
              },
            ];
          });
          return;
        }
        if (topic && topic !== "live-transcript") return;
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
      setWaitingForHost(false);
      setNetworkStatus("connecting");
      try {
        const joined = await joinLiveSession({ sessionId });
        if (cancelled) return;
        setSession(joined.session);
        setLocalRole(joined.participant?.role || "learner");
        setHostSettings(readHostSettings(joined.session?.session_metadata));

        await connectLivekitWithFallback({
          room,
          livekitUrl: joined.livekit.url,
          token: joined.livekit.token,
        });
        setAiFallbackMode(false);
        await room.localParticipant.setMicrophoneEnabled(true, {
          deviceId: resolveDeviceId(selectedMicrophoneIdRef.current),
        });
        try {
          await room.localParticipant.setCameraEnabled(true, {
            deviceId: resolveDeviceId(selectedCameraIdRef.current),
          });
        } catch {
          // Camera permission may be denied.
        }

        syncRoomState();
        await Promise.all([
          refreshBackendParticipants(),
          refreshSessionEvents(),
          refreshObservability(),
        ]);
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
          if (isPeerConnectionSetupError(message)) {
            setAiFallbackMode(true);
            setError("");
            setConnected(false);
            setNotice(
              "Mạng đang chặn WebRTC media. Đã chuyển sang chế độ AI dự phòng (chat/STT/TTS) để bạn vẫn test được tính năng AI Teacher.",
            );
            setNetworkStatus("degraded");
          } else if (isLockedRoomError(message)) {
            setAiFallbackMode(false);
            setConnected(false);
            setWaitingForHost(true);
            setNetworkStatus("waiting");
            setError(
              "Phòng đang khóa. Yêu cầu vào phòng đã được gửi cho chủ phòng; bạn có thể bấm Kết nối lại sau khi được mở khóa.",
            );
            void requestHostAdmit();
          } else {
            setError(humanizeLiveError(message));
            setNetworkStatus("disconnected");
          }
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
    connectLivekitWithFallback,
    clearRemoteAudio,
    detachRemoteAudioTrack,
    refreshBackendParticipants,
    refreshObservability,
    refreshSessionEvents,
    requestHostAdmit,
    sessionId,
    syncParticipants,
  ]);

  useEffect(() => {
    if (!aiScrollRef.current) return;
    aiScrollRef.current.scrollTop = aiScrollRef.current.scrollHeight;
  }, [aiMessages]);

  const speakAiAnswer = useCallback(
    async (text) => {
      const normalized = sanitizeTextForSpeech(text);
      if (!ttsAutoSpeakActive || !normalized || !aiInteractionReady || !hostSettings.aiEnabled) return;
      if (typeof window === "undefined") return;
      const speakInBrowser = () => {
        const synth = speechSynthesisRef.current || window.speechSynthesis;
        if (!synth) return;
        try {
          synth.cancel();
          const utterance = new SpeechSynthesisUtterance(normalized);
          utterance.lang = "vi-VN";
          synth.speak(utterance);
        } catch {
          // Ignore browser TTS fallback failure.
        }
      };
      if (!voiceBackendAvailable) {
        speakInBrowser();
        return;
      }

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
        if (ttsRequestSeqRef.current !== sequence || !ttsAutoSpeakActive) return;
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
          speakInBrowser();
        }
      } finally {
        if (activeTtsAbortRef.current === abortController) {
          activeTtsAbortRef.current = null;
        }
      }
    },
    [
      aiInteractionReady,
      hostSettings.aiEnabled,
      isVoiceBackendCapabilityError,
      sessionId,
      stopCurrentSpeech,
      ttsAutoSpeakActive,
      voiceBackendAvailable,
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
                  citations: normalizeAiCitations(payload.citations),
                  rubric: normalizeAiRubric(payload.rubric),
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

  const applySelectedDevices = useCallback(async () => {
    const room = roomRef.current;
    if (!room || room.state !== "connected" || !room.localParticipant) {
      setNotice("Bạn có thể chọn thiết bị trước, hệ thống sẽ dùng khi kết nối vào phòng.");
      return;
    }

    setDeviceBusy(true);
    setNotice("");
    try {
      if (room.localParticipant.isMicrophoneEnabled) {
        await room.localParticipant.setMicrophoneEnabled(true, {
          deviceId: resolveDeviceId(selectedMicrophoneId),
        });
      }
      if (room.localParticipant.isCameraEnabled) {
        await room.localParticipant.setCameraEnabled(true, {
          deviceId: resolveDeviceId(selectedCameraId),
        });
      }
      setMicrophoneEnabled(room.localParticipant.isMicrophoneEnabled || false);
      setCameraEnabled(room.localParticipant.isCameraEnabled || false);
      syncParticipants();
      setNotice("Đã áp dụng thiết bị cho phiên live.");
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setNotice(`Không áp dụng được thiết bị đã chọn: ${message}`);
    } finally {
      setDeviceBusy(false);
    }
  }, [selectedCameraId, selectedMicrophoneId, syncParticipants]);

  const toggleMicrophone = useCallback(async () => {
    const room = roomRef.current;
    if (!room || room.state !== "connected") return;
    await room.localParticipant.setMicrophoneEnabled(!microphoneEnabled, {
      deviceId: resolveDeviceId(selectedMicrophoneId),
    });
    setMicrophoneEnabled(room.localParticipant.isMicrophoneEnabled || false);
    syncParticipants();
  }, [microphoneEnabled, selectedMicrophoneId, syncParticipants]);

  const toggleCamera = useCallback(async () => {
    const room = roomRef.current;
    if (!room || room.state !== "connected") return;
    await room.localParticipant.setCameraEnabled(!cameraEnabled, {
      deviceId: resolveDeviceId(selectedCameraId),
    });
    setCameraEnabled(room.localParticipant.isCameraEnabled || false);
    syncParticipants();
  }, [cameraEnabled, selectedCameraId, syncParticipants]);

  const toggleScreenShare = useCallback(async () => {
    const room = roomRef.current;
    if (!room || room.state !== "connected" || !room.localParticipant) return;
    setNotice("");
    try {
      const nextEnabled = !hasScreenShareTrack(room.localParticipant);
      await room.localParticipant.setScreenShareEnabled(nextEnabled, { audio: true });
      setScreenShareEnabled(hasScreenShareTrack(room.localParticipant));
      syncParticipants();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setNotice(`Không thể chia sẻ màn hình: ${message || "trình duyệt đã hủy quyền chia sẻ"}`);
      setScreenShareEnabled(hasScreenShareTrack(room.localParticipant));
    }
  }, [syncParticipants]);

  const reconnectNow = useCallback(async () => {
    const room = roomRef.current;
    if (!room || !sessionId) return;
    setConnecting(true);
    setNotice("");
    setWaitingForHost(false);
    try {
      const joined = await joinLiveSession({ sessionId });
      if (room.state === "connected" || room.state === "reconnecting") {
        room.disconnect();
      }
      await connectLivekitWithFallback({
        room,
        livekitUrl: joined.livekit.url,
        token: joined.livekit.token,
      });
      setAiFallbackMode(false);
      setSession(joined.session);
      setHostSettings(readHostSettings(joined.session?.session_metadata));
      setNetworkStatus("connected");
      setError("");
      setNotice("Đã reconnect thành công.");
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      if (isPeerConnectionSetupError(message)) {
        setAiFallbackMode(true);
        setNetworkStatus("degraded");
        setNotice(
          "Không dựng được kết nối media WebRTC. Đã giữ chế độ AI dự phòng để bạn tiếp tục test.",
        );
      } else if (isLockedRoomError(message)) {
        setWaitingForHost(true);
        setNetworkStatus("waiting");
        setError(
          "Phòng đang khóa. Yêu cầu vào phòng đã được gửi cho chủ phòng; thử kết nối lại sau khi được duyệt hoặc phòng được mở khóa.",
        );
        void requestHostAdmit();
      } else {
        setNotice(`Kết nối lại lỗi: ${humanizeLiveError(message)}`);
        setNetworkStatus("disconnected");
      }
    } finally {
      setConnecting(false);
    }
  }, [connectLivekitWithFallback, requestHostAdmit, sessionId]);

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
      setScreenShareEnabled(false);
      setLeaving(false);
      setAiFallbackMode(false);
      setNetworkStatus("disconnected");
    }
  }, [clearRemoteAudio, leaving, sessionId, stopCurrentSpeech]);

  const copyInviteLink = useCallback(async () => {
    const href =
      typeof window !== "undefined"
        ? `${window.location.origin}/live/${sessionId}`
        : `/live/${sessionId}`;
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(href);
      }
      setNotice("Đã sao chép liên kết phòng live.");
    } catch {
      setNotice(`Liên kết phòng: ${href}`);
    }
  }, [sessionId]);

  const handleEndSession = useCallback(async () => {
    if (!canManageSettings || sessionEnding) return;
    const confirmed =
      typeof window === "undefined" ||
      window.confirm("Kết thúc phiên live cho tất cả người tham gia?");
    if (!confirmed) return;

    setSessionEnding(true);
    setNotice("");
    try {
      await endLiveSession({ sessionId });
      setNotice("Đã kết thúc phiên live và bắt đầu tạo báo cáo sau buổi học.");
      await leaveRoom();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setNotice(`Kết thúc phiên lỗi: ${message || "không rõ"}`);
    } finally {
      setSessionEnding(false);
    }
  }, [canManageSettings, leaveRoom, sessionEnding, sessionId]);

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
      setNotice(`Không cập nhật được raise hand: ${message || "không rõ"}`);
    }
  }, [connected, localHandRaised, localIdentity, refreshSessionEvents, sessionId]);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const onKeyDown = (event) => {
      if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
      if (isTypingTarget(event.target)) return;
      const key = String(event.key || "").toLowerCase();

      if (key === "m") {
        event.preventDefault();
        void toggleMicrophone();
      } else if (key === "v") {
        event.preventDefault();
        void toggleCamera();
      } else if (key === "h") {
        event.preventDefault();
        void handleToggleHand();
      } else if (key === "s") {
        event.preventDefault();
        void toggleScreenShare();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [handleToggleHand, toggleCamera, toggleMicrophone, toggleScreenShare]);

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
          gradeLevel:
            typeof patch.gradeLevel === "string"
              ? patch.gradeLevel
              : hostSettings.gradeLevel,
          aiCostCeilingUsd:
            typeof patch.aiCostCeilingUsd === "number"
              ? patch.aiCostCeilingUsd
              : hostSettings.aiCostCeilingUsd,
        });
        setSession(updated);
        const next = readHostSettings(updated?.session_metadata);
        setHostSettings(next);
        setNotice(
          `Đã cập nhật thiết lập chủ phòng: khóa phòng=${next.lockRoom ? "bật" : "tắt"}, AI=${next.aiEnabled ? "bật" : "tắt"}, persona=${next.gradeLevel}, trần chi phí=${next.aiCostCeilingUsd}`,
        );
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setNotice(`Cập nhật thiết lập chủ phòng lỗi: ${message || "không rõ"}`);
      } finally {
        setSettingsBusy(false);
      }
    },
    [
      canManageSettings,
      hostSettings.aiCostCeilingUsd,
      hostSettings.aiEnabled,
      hostSettings.gradeLevel,
      hostSettings.lockRoom,
      sessionId,
    ],
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
      setNotice(`Tắt mic tất cả: processed=${result.processed || 0}, failed=${result.failed || 0}`);
      await refreshBackendParticipants();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setNotice(`Tắt mic tất cả lỗi: ${message || "không rõ"}`);
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
        setNotice(`Cập nhật role lỗi: ${message || "không rõ"}`);
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
          setNotice(`Cảnh báo khi loại: ${result.detail}`);
        } else {
          setNotice(`Đã loại ${participant.name}`);
        }
        await refreshBackendParticipants();
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setNotice(`Loại người tham gia lỗi: ${message || "không rõ"}`);
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
      setSideTab("ai");
    },
    [aiInput, missionById],
  );

  const sendQuestionToAiTeacher = useCallback(
    async (question, { source = "text" } = {}) => {
      const normalizedQuestion = String(question || "").trim();
      if (!normalizedQuestion || !aiInteractionReady || aiLoading || !hostSettings.aiEnabled) return;
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
                gradeLevel: hostSettings.gradeLevel,
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
                    citations: normalizeAiCitations(reply.citations),
                    rubric: normalizeAiRubric(reply.rubric),
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
                  content: `AI giáo viên lỗi: ${message || "không thể trả lời"}`,
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
            content: `AI giáo viên lỗi: ${message || "không thể trả lời"}`,
            meta: "error",
          },
        ]);
      }
    },
    [
      aiHistoryPayload,
      aiInteractionReady,
      aiLoading,
      aiMode,
      hostSettings.aiEnabled,
      hostSettings.gradeLevel,
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

  const sendClassChatMessage = useCallback(
    async (event) => {
      event.preventDefault();
      const text = chatInput.trim();
      if (!text || chatSending || !aiInteractionReady || !localIdentity) return;

      setChatSending(true);
      setNotice("");
      const clientId = `chat-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
      const payload = {
        id: clientId,
        type: "live_chat_message",
        text,
        display_name: currentUser?.display_name || currentUser?.username || "Bạn",
        participant_identity: localIdentity,
        created_at: new Date().toISOString(),
      };

      try {
        const eventRecord = await createLiveSessionEvent({
          sessionId,
          eventType: "live_chat_message",
          payload,
        });
        setChatInput("");
        if (eventRecord?.id) {
          setSessionEvents((prev) =>
            prev.some((item) => item.id === eventRecord.id) ? prev : [...prev, eventRecord],
          );
        }
        const room = roomRef.current;
        if (room?.state === "connected" && room.localParticipant) {
          const encoded = new TextEncoder().encode(JSON.stringify(payload));
          await room.localParticipant.publishData(encoded, {
            reliable: true,
            topic: "live-chat",
          });
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setNotice(`Gửi tin nhắn lỗi: ${message || "không rõ"}`);
      } finally {
        setChatSending(false);
      }
    },
    [
      aiInteractionReady,
      chatInput,
      chatSending,
      currentUser?.display_name,
      currentUser?.username,
      localIdentity,
      sessionId,
    ],
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
        setNotice("Voice command cần wake phrase 'cô giáo ơi' để kích hoạt AI.");
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
      setVoiceInterimText("Đang nghe (fallback trình duyệt)...");
      setNotice("Backend STT không khả dụng, đã chuyển sang fallback trình duyệt.");
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
        setNotice("Không thu được dữ liệu âm thanh để nhận dạng.");
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
          setNotice("Không nhận dạng được nội dung giọng nói.");
          return;
        }
        setVoiceLastFinalText(transcript);
        await submitVoiceTranscript(transcript);
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        if (isVoiceBackendCapabilityError(message)) {
          setVoiceBackendAvailable(false);
          setNotice(
            "Backend STT/TTS hiện tại không có quyền audio model. Đã chuyển fallback trình duyệt, bấm lại Bắt đầu nói.",
          );
          return;
        }
        setNotice(`STT lỗi: ${message || "không nhận dạng được giọng nói"}`);
      }
    },
    [isVoiceBackendCapabilityError, sessionId, submitVoiceTranscript],
  );

  const startVoiceCapture = useCallback(async () => {
    if (!voiceSupported || !aiInteractionReady || aiLoading) return;
    if (typeof window === "undefined") return;

    stopCurrentSpeech(); // Barge-in: user starts speaking, AI must stop speaking.
    const hasMediaRecorder = typeof window.MediaRecorder !== "undefined";
    const hasGetUserMedia = Boolean(navigator?.mediaDevices?.getUserMedia);
    if (!voiceBackendAvailable) {
      if (!startBrowserRecognitionCapture()) {
        setNotice("Không thể bật fallback STT trên trình duyệt hiện tại.");
      }
      return;
    }
    if (!hasMediaRecorder || !hasGetUserMedia) {
      if (!startBrowserRecognitionCapture()) {
        setNotice("Trình duyệt không hỗ trợ ghi âm realtime.");
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
      setVoiceInterimText("Đang thu âm...");
      setNotice("");
      if (voiceTimeoutRef.current) {
        clearTimeout(voiceTimeoutRef.current);
      }
      voiceTimeoutRef.current = setTimeout(() => {
        stopVoiceCapture();
      }, 15000);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setNotice(`Không mở được microphone: ${message || "không rõ"}`);
      setVoiceListening(false);
      setVoiceInterimText("");
    }
  }, [
    aiInteractionReady,
    aiLoading,
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

  const classChatMessages = useMemo(() => {
    const seen = new Set();
    return [...sessionEvents]
      .filter((event) => event.event_type === "live_chat_message")
      .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
      .map((event) => {
        const payload = event.payload && typeof event.payload === "object" ? event.payload : {};
        const id = String(payload.id || event.id || "");
        if (!id || seen.has(id)) return null;
        seen.add(id);
        const identity = String(
          payload.participant_identity || event.participant_identity || "",
        ).trim();
        return {
          id,
          text: String(payload.text || payload.content || "").trim(),
          displayName:
            String(payload.display_name || "").trim() ||
            (identity === localIdentity ? "Bạn" : identity || "Người tham gia"),
          identity,
          createdAt: event.created_at || payload.created_at || new Date().toISOString(),
        };
      })
      .filter((item) => item?.text);
  }, [localIdentity, sessionEvents]);

  const permissionMeta = devicePermissionMeta(devicePermissionState);
  const probeMeta = networkProbeMeta(networkProbe);
  const speakerRoutingSupported =
    typeof HTMLMediaElement !== "undefined" &&
    typeof HTMLMediaElement.prototype.setSinkId === "function";

  return (
    <main className="dark relative isolate mx-auto flex min-h-screen w-full max-w-[1560px] flex-col gap-4 overflow-hidden bg-[#080604] px-3 py-4 text-stone-100 sm:px-4 sm:py-6">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_18%_0%,rgba(180,124,54,0.34),transparent_30%),radial-gradient(circle_at_86%_10%,rgba(20,184,166,0.16),transparent_28%),linear-gradient(180deg,#0b0704_0%,#11100e_46%,#050505_100%)]" />
      <div className="pointer-events-none absolute inset-0 -z-10 opacity-[0.08] [background-image:linear-gradient(rgba(255,255,255,0.18)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.18)_1px,transparent_1px)] [background-size:34px_34px]" />
      <Card className="relative overflow-hidden rounded-3xl border-amber-500/25 bg-[linear-gradient(135deg,rgba(38,25,12,0.95),rgba(12,10,9,0.92)_52%,rgba(3,10,11,0.92))] py-0 shadow-[0_24px_90px_rgba(0,0,0,0.38)] ring-1 ring-white/10 backdrop-blur">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-amber-200/60 to-transparent" />
        <CardHeader className="gap-4 p-4 sm:p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-2xl space-y-2">
              <div className="text-[11px] font-semibold uppercase tracking-[0.28em] text-amber-300/80">
                Cửu Đỉnh Live Studio
              </div>
              <CardTitle className="text-2xl font-semibold normal-case tracking-tight text-amber-50 sm:text-3xl">
                Phòng học live 3D về di sản triều Nguyễn
              </CardTitle>
              <p className="text-sm leading-relaxed text-stone-300">
                Sân khấu WebRTC, AI giáo viên và mô hình Cao Đỉnh nhẹ cho nhiệm vụ vi mô trong một không gian học lịch sử trực tiếp.
              </p>
              <p className="text-xs text-stone-500">
                Mã phiên: {session?.id || sessionId || "Chưa có"}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge
                variant="outline"
                className={[
                  "rounded-full px-2.5 py-1 text-[11px] font-medium",
                  networkStatus === "connected"
                    ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
                    : networkStatus === "degraded"
                      ? "border-sky-500/40 bg-sky-500/10 text-sky-300"
                    : networkStatus === "reconnecting" || connecting
                      ? "border-amber-500/40 bg-amber-500/10 text-amber-300"
                      : "border-stone-700 bg-stone-900/70 text-stone-300",
                ].join(" ")}
              >
                {networkStatusLabel(networkStatus)}
              </Badge>
              <Badge variant="secondary" className={`rounded-full border border-amber-500/15 bg-black/25 text-[11px] font-medium ${quality.tone}`}>
                Chất lượng: {quality.label}
              </Badge>
              <Badge variant="secondary" className="rounded-full border border-amber-500/15 bg-black/25 text-[11px] font-medium text-amber-100">
                Vai trò: {roleLabel(localRole)}
              </Badge>
              <Button
                asChild
                variant="outline"
                size="sm"
                className={HERITAGE_BUTTON_CLASS}
              >
                <Link href={`/live/${sessionId}/dashboard`}>Bảng điều khiển phiên</Link>
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={copyInviteLink}
                className={HERITAGE_BUTTON_CLASS}
              >
                <Copy className="h-4 w-4" />
                Mời vào phòng
              </Button>
              <Button
                asChild
                variant="outline"
                size="sm"
                className={HERITAGE_BUTTON_CLASS}
              >
                <Link href="/dashboard">Về trang quản trị</Link>
              </Button>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs text-stone-400 sm:grid-cols-4">
            <div className="rounded-2xl border border-amber-500/15 bg-black/25 px-3 py-2">
              <span className="block text-[10px] uppercase tracking-[0.2em] text-stone-500">Reconnect</span>
              <span className="text-amber-100">{reconnectCount} lần</span>
            </div>
            <div className="rounded-2xl border border-amber-500/15 bg-black/25 px-3 py-2">
              <span className="block text-[10px] uppercase tracking-[0.2em] text-stone-500">Thành viên</span>
              <span className="text-amber-100">{mergedParticipants.length} người</span>
            </div>
            {lastReconnectedAt ? (
              <div className="rounded-2xl border border-amber-500/15 bg-black/25 px-3 py-2">
                <span className="block text-[10px] uppercase tracking-[0.2em] text-stone-500">Khôi phục</span>
                <span className="text-amber-100">{new Date(lastReconnectedAt).toLocaleTimeString()}</span>
              </div>
            ) : null}
            {hostSettings.lockRoom ? (
              <Badge className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[11px] text-amber-200 hover:bg-amber-500/10">
                Phòng đã khóa
              </Badge>
            ) : null}
            {!hostSettings.aiEnabled ? (
              <Badge className="rounded-full border border-stone-600 bg-stone-900/70 px-2 py-0.5 text-[11px] text-stone-300 hover:bg-stone-900/70">
                AI đã tắt
              </Badge>
            ) : null}
          </div>
        </CardHeader>
      </Card>

      {error ? (
        <Alert variant="destructive">
          <AlertTitle>Lỗi phiên học trực tiếp</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {waitingForHost ? (
        <Alert className="border-sky-500/40 bg-sky-500/10 text-sky-100">
          <AlertTitle>Đang chờ chủ phòng duyệt</AlertTitle>
          <AlertDescription className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <span>
              Phòng đang khóa. Hệ thống đã gửi tín hiệu xin vào phòng; hãy thử kết nối lại sau khi chủ phòng mở khóa.
            </span>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={reconnectNow}
              disabled={connecting}
              className="shrink-0 rounded-md border-sky-400/50 bg-sky-950/50 text-sky-100 normal-case tracking-normal hover:bg-sky-900/70"
            >
              {connecting ? "Đang thử lại..." : "Thử vào lại"}
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}

      {notice ? (
        <Alert className="border-amber-500/40 bg-amber-500/10 text-amber-100">
          <AlertTitle>Thông báo</AlertTitle>
          <AlertDescription>{notice}</AlertDescription>
        </Alert>
      ) : null}

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.8fr)_400px]">
        <div className="space-y-4">
          <div className="relative overflow-hidden rounded-3xl border border-amber-500/20 bg-[linear-gradient(135deg,rgba(9,9,11,0.98),rgba(29,20,12,0.92))] p-3 shadow-[0_28px_100px_rgba(0,0,0,0.45)] ring-1 ring-white/5 sm:p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <div className="text-[10px] font-semibold uppercase tracking-[0.24em] text-amber-300/70">
                  Sân khấu học trực tiếp
                </div>
                <h2 className="text-sm font-semibold text-amber-50">Video, chia sẻ màn hình và lớp học</h2>
              </div>
              <Badge className="rounded-full border border-teal-400/25 bg-teal-500/10 px-2.5 py-1 text-[11px] text-teal-200 hover:bg-teal-500/10">
                {videoTiles.length} tile
              </Badge>
            </div>
            {pinnedTile ? (
              <div className="space-y-3">
                <VideoTile
                  tile={pinnedTile}
                  pinned={true}
                  handRaised={Boolean(handRaisedMap.get(pinnedTile.ownerIdentity || pinnedTile.identity))}
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
                      handRaised={Boolean(handRaisedMap.get(tile.ownerIdentity || tile.identity))}
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
                  <div className="col-span-full rounded-2xl border border-dashed border-amber-500/20 bg-black/25 p-8 text-center text-sm text-stone-400">
                    <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full border border-amber-500/20 bg-amber-500/10 text-amber-200">
                      <CameraOff className="h-5 w-5" />
                    </div>
                    Chưa có người tham gia có video. Khi học viên bật camera hoặc chia sẻ màn hình, tile sẽ xuất hiện ở đây.
                  </div>
                ) : (
                  videoTiles.map((tile) => (
                    <VideoTile
                      key={tile.identity}
                      tile={tile}
                      pinned={false}
                      handRaised={Boolean(handRaisedMap.get(tile.ownerIdentity || tile.identity))}
                      onTogglePin={(identity) =>
                        setPinnedIdentity((prev) => (prev === identity ? null : identity))
                      }
                    />
                  ))
                )}
              </div>
            )}
          </div>

          <div className="sticky bottom-2 z-10 rounded-3xl border border-amber-500/20 bg-black/70 p-3 shadow-[0_20px_70px_rgba(0,0,0,0.42)] backdrop-blur-xl sm:p-4">
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
              <Button
                type="button"
                variant="outline"
                onClick={toggleMicrophone}
                disabled={!connected}
                className={[
                  "h-11 rounded-2xl px-3 text-sm normal-case tracking-normal",
                  microphoneEnabled
                    ? "border-emerald-500/50 bg-emerald-500/15 text-emerald-200 hover:bg-emerald-500/25"
                    : "border-zinc-700 bg-zinc-800 text-zinc-200 hover:bg-zinc-700",
                ].join(" ")}
                title="Phím tắt: M"
              >
                {microphoneEnabled ? <Mic className="h-4 w-4" /> : <MicOff className="h-4 w-4" />}
                {microphoneEnabled ? "Mic bật" : "Mic tắt"}
              </Button>

              <Button
                type="button"
                variant="outline"
                onClick={toggleCamera}
                disabled={!connected}
                className={[
                  "h-11 rounded-2xl px-3 text-sm normal-case tracking-normal",
                  cameraEnabled
                    ? "border-emerald-500/50 bg-emerald-500/15 text-emerald-200 hover:bg-emerald-500/25"
                    : "border-zinc-700 bg-zinc-800 text-zinc-200 hover:bg-zinc-700",
                ].join(" ")}
                title="Phím tắt: V"
              >
                {cameraEnabled ? <Camera className="h-4 w-4" /> : <CameraOff className="h-4 w-4" />}
                {cameraEnabled ? "Camera bật" : "Camera tắt"}
              </Button>

              <Button
                type="button"
                variant="outline"
                onClick={handleToggleHand}
                disabled={!connected}
                className={[
                  "h-11 rounded-2xl px-3 text-sm normal-case tracking-normal",
                  localHandRaised
                    ? "border-amber-500/50 bg-amber-500/15 text-amber-200 hover:bg-amber-500/25"
                    : "border-zinc-700 bg-zinc-800 text-zinc-200 hover:bg-zinc-700",
                ].join(" ")}
                title="Phím tắt: H"
              >
                <Hand className="h-4 w-4" />
                {localHandRaised ? "Hạ tay" : "Giơ tay"}
              </Button>

              <Button
                type="button"
                variant="outline"
                onClick={toggleScreenShare}
                disabled={!connected}
                className={[
                  "h-11 rounded-2xl px-3 text-sm normal-case tracking-normal",
                  screenShareEnabled
                    ? "border-sky-500/50 bg-sky-500/15 text-sky-200 hover:bg-sky-500/25"
                    : "border-zinc-700 bg-zinc-800 text-zinc-200 hover:bg-zinc-700",
                ].join(" ")}
                title="Phím tắt: S"
              >
                {screenShareEnabled ? (
                  <MonitorX className="h-4 w-4" />
                ) : (
                  <MonitorUp className="h-4 w-4" />
                )}
                {screenShareEnabled ? "Dừng chia sẻ" : "Chia sẻ"}
              </Button>

              <Button
                type="button"
                variant="outline"
                onClick={reconnectNow}
                disabled={connecting}
                className="h-11 rounded-2xl border-amber-500/20 bg-black/30 px-3 text-sm text-amber-100 normal-case tracking-normal hover:bg-amber-500/10"
              >
                <RefreshCcw className="h-4 w-4" />
                {connecting ? "Đang kết nối lại..." : "Kết nối lại"}
              </Button>

              <Button
                type="button"
                variant="destructive"
                onClick={leaveRoom}
                disabled={(!connected && !aiFallbackMode) || leaving}
                className="h-11 rounded-2xl border-red-500/40 bg-red-500/10 px-3 text-sm text-red-200 hover:bg-red-500/20 normal-case tracking-normal"
              >
                <PhoneOff className="h-4 w-4" />
                {leaving ? "Đang rời..." : "Rời phòng"}
              </Button>
            </div>
          </div>
        </div>

        <aside className="flex flex-col gap-4 xl:sticky xl:top-4 xl:self-start">
          <HeritagePanel className="order-4">
            <HeritagePanelHeader
              icon={Settings}
              eyebrow="Trước giờ học"
              title="Thiết bị & preflight"
              description="Chọn thiết bị, kiểm tra quyền mic/camera và đường truyền trước khi học."
            />

            <div className="space-y-3">
              <div className="grid grid-cols-1 gap-2">
                <label className="space-y-1">
                  <span className="inline-flex items-center gap-1.5 text-xs font-medium text-stone-300">
                    <Mic className="h-3.5 w-3.5" />
                    Micro
                  </span>
                  <Select value={selectedMicrophoneId} onValueChange={setSelectedMicrophoneId}>
                    <SelectTrigger className={HERITAGE_SELECT_TRIGGER_CLASS}>
                      <SelectValue placeholder="Chọn micro" />
                    </SelectTrigger>
                    <SelectContent className="rounded-xl border-amber-500/20 bg-stone-950 text-amber-50">
                      <SelectItem value={DEFAULT_DEVICE_ID}>Micro mặc định</SelectItem>
                      {mediaDevices.audioinput
                        .filter((device) => deviceOptionValue(device.deviceId) !== DEFAULT_DEVICE_ID)
                        .map((device, index) => (
                          <SelectItem key={device.deviceId || `mic-${index}`} value={deviceOptionValue(device.deviceId)}>
                            {labelMediaDevice(device, "Micro", index)}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </label>

                <label className="space-y-1">
                  <span className="inline-flex items-center gap-1.5 text-xs font-medium text-stone-300">
                    <Camera className="h-3.5 w-3.5" />
                    Camera
                  </span>
                  <Select value={selectedCameraId} onValueChange={setSelectedCameraId}>
                    <SelectTrigger className={HERITAGE_SELECT_TRIGGER_CLASS}>
                      <SelectValue placeholder="Chọn camera" />
                    </SelectTrigger>
                    <SelectContent className="rounded-xl border-amber-500/20 bg-stone-950 text-amber-50">
                      <SelectItem value={DEFAULT_DEVICE_ID}>Camera mặc định</SelectItem>
                      {mediaDevices.videoinput
                        .filter((device) => deviceOptionValue(device.deviceId) !== DEFAULT_DEVICE_ID)
                        .map((device, index) => (
                          <SelectItem key={device.deviceId || `cam-${index}`} value={deviceOptionValue(device.deviceId)}>
                            {labelMediaDevice(device, "Camera", index)}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </label>

                <label className="space-y-1">
                  <span className="inline-flex items-center gap-1.5 text-xs font-medium text-stone-300">
                    <Headphones className="h-3.5 w-3.5" />
                    Loa / tai nghe
                  </span>
                  <Select
                    value={selectedSpeakerId}
                    onValueChange={setSelectedSpeakerId}
                    disabled={!speakerRoutingSupported && mediaDevices.audiooutput.length === 0}
                  >
                    <SelectTrigger className={HERITAGE_SELECT_TRIGGER_CLASS}>
                      <SelectValue placeholder="Chọn loa" />
                    </SelectTrigger>
                    <SelectContent className="rounded-xl border-amber-500/20 bg-stone-950 text-amber-50">
                      <SelectItem value={DEFAULT_DEVICE_ID}>Loa mặc định</SelectItem>
                      {mediaDevices.audiooutput
                        .filter((device) => deviceOptionValue(device.deviceId) !== DEFAULT_DEVICE_ID)
                        .map((device, index) => (
                          <SelectItem key={device.deviceId || `speaker-${index}`} value={deviceOptionValue(device.deviceId)}>
                            {labelMediaDevice(device, "Loa", index)}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </label>
              </div>

              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={runPreflightCheck}
                  disabled={deviceBusy}
                  className={`h-10 text-sm ${HERITAGE_BUTTON_CLASS}`}
                >
                  <Wifi className="h-4 w-4" />
                  {deviceBusy ? "Đang kiểm tra..." : "Kiểm tra"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={applySelectedDevices}
                  disabled={deviceBusy}
                  className="h-10 rounded-xl border-teal-500/40 bg-teal-500/10 text-sm text-teal-100 normal-case tracking-normal hover:bg-teal-500/20"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  Áp dụng
                </Button>
              </div>

              <div className="grid grid-cols-1 gap-2 text-xs sm:grid-cols-2">
                <div className={HERITAGE_FIELD_CLASS + " px-3 py-2"}>
                  <span className="block text-stone-500">Quyền thiết bị</span>
                  <span className={`font-medium ${permissionMeta.tone}`}>{permissionMeta.label}</span>
                </div>
                <div className={HERITAGE_FIELD_CLASS + " px-3 py-2"}>
                  <span className="block text-stone-500">Đường truyền</span>
                  <span className={`font-medium ${probeMeta.tone}`}>{probeMeta.label}</span>
                </div>
              </div>

              <div className={HERITAGE_FIELD_CLASS + " px-3 py-2 text-xs text-stone-400"}>
                <div className="mb-1 inline-flex items-center gap-1.5 font-medium text-amber-100">
                  <Keyboard className="h-3.5 w-3.5" />
                  Phím tắt
                </div>
                <div>M: mic, V: camera, H: giơ tay, S: chia sẻ màn hình.</div>
              </div>
            </div>
          </HeritagePanel>

          <HeritagePanel className="order-2">
            <HeritagePanelHeader
              icon={Radio}
              eyebrow="Bảo vật 3D"
              title="Nhiệm vụ vi mô di sản"
              description="Chọn điểm quan sát trên Cao Đỉnh, AI sẽ biến câu hỏi thành nhiệm vụ ngắn trong lớp."
            />
            <HeritageStage3D
              missions={HERITAGE_MISSIONS}
              selectedMissionId={selectedMissionId}
              onSelectMission={handleSelectMission}
              modelUrl={selectedMissionModelUrl}
            />
            <div className="mt-3 grid grid-cols-2 gap-2">
              {HERITAGE_MISSIONS.map((mission) => (
                <Button
                  key={mission.id}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleSelectMission(mission.id)}
                  className={[
                    "h-9 justify-start rounded-xl px-2 text-left text-xs normal-case tracking-normal",
                    mission.id === selectedMissionId
                      ? "border-amber-300/50 bg-amber-500/15 text-amber-100 hover:bg-amber-500/25"
                      : "border-amber-500/15 bg-black/25 text-stone-300 hover:border-amber-400/40 hover:bg-amber-500/10",
                  ].join(" ")}
                >
                  {mission.label}
                </Button>
              ))}
            </div>
          </HeritagePanel>

          <HeritagePanel className="order-3">
            <HeritagePanelHeader
              icon={Waves}
              eyebrow="Âm thanh lớp học"
              title="Giọng nói AI (STT/TTS)"
              description="Tương tác bằng giọng nói, giữ ngữ cảnh lớp và ưu tiên tiếng Việt có dấu."
            />
            <div className="mb-2 text-[11px] text-stone-400">
              Chế độ giọng nói: {voiceBackendAvailable ? "backend ưu tiên" : "trình duyệt dự phòng"}
              {aiFallbackMode ? " · WebRTC media dự phòng" : ""}
            </div>
            {!voiceSupported ? (
              <p className="text-xs text-stone-400">
                Trình duyệt hiện tại không hỗ trợ API giọng nói cần thiết (MediaRecorder hoặc SpeechRecognition).
              </p>
            ) : (
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={voiceListening ? stopVoiceCapture : startVoiceCapture}
                    disabled={!aiInteractionReady || aiLoading || !hostSettings.aiEnabled}
                    className={[
                      "h-10 rounded-xl px-2 text-xs normal-case tracking-normal",
                      voiceListening
                        ? "border-emerald-500/40 bg-emerald-500/15 text-emerald-200 hover:bg-emerald-500/25"
                        : "border-amber-500/20 bg-black/25 text-amber-100 hover:bg-amber-500/10",
                    ].join(" ")}
                  >
                    <Mic className="h-3.5 w-3.5" />
                    {voiceListening ? "Đang nghe..." : "Bắt đầu nói"}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onMouseDown={startVoiceCapture}
                    onMouseUp={stopVoiceCapture}
                    onMouseLeave={() => {
                      if (voiceListening) stopVoiceCapture();
                    }}
                    onTouchStart={startVoiceCapture}
                    onTouchEnd={stopVoiceCapture}
                    disabled={!aiInteractionReady || aiLoading || !hostSettings.aiEnabled}
                    className="h-10 rounded-xl border-amber-500/40 bg-amber-500/10 px-2 text-xs text-amber-200 hover:bg-amber-500/20 normal-case tracking-normal"
                  >
                    Nhấn giữ để nói
                  </Button>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setVoiceWakePhraseRequired((prev) => !prev)}
                    className={`h-10 px-2 text-xs ${HERITAGE_BUTTON_CLASS}`}
                  >
                    Từ khóa kích hoạt: {voiceWakePhraseRequired ? "BẬT" : "TẮT"}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setVoiceAutoSpeakEnabled((prev) => !prev)}
                    className={`h-10 px-2 text-xs ${HERITAGE_BUTTON_CLASS}`}
                  >
                    {ttsAutoSpeakActive ? (
                      <Volume2 className="h-3.5 w-3.5" />
                    ) : (
                      <VolumeX className="h-3.5 w-3.5" />
                    )}
                    Tự đọc: {ttsAutoSpeakActive ? "BẬT" : "TẮT"}
                  </Button>
                </div>

                {voiceInterimText ? (
                  <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-xs text-amber-200">
                    Trạng thái giọng nói: {voiceInterimText}
                  </div>
                ) : null}
                {voiceLastFinalText ? (
                  <div className="rounded-xl border border-amber-500/15 bg-black/25 px-2 py-1 text-xs text-stone-200">
                    Câu nói gần nhất: {voiceLastFinalText}
                  </div>
                ) : null}

                <ul className="max-h-28 space-y-1 overflow-auto rounded-xl border border-amber-500/15 bg-black/25 p-2 text-[11px]">
                  {voiceTranscriptFeed.length === 0 ? (
                    <li className="text-stone-500">Biên bản giọng nói sẽ hiển thị ở đây.</li>
                  ) : (
                    voiceTranscriptFeed.map((item) => (
                      <li key={item.id} className="rounded-lg border border-amber-500/15 bg-black/25 px-2 py-1">
                        <div className="mb-0.5 flex items-center justify-between text-[10px] text-stone-500">
                          <span>{voiceSpeakerLabel(item.speaker)}</span>
                          <span>{new Date(item.createdAt).toLocaleTimeString()}</span>
                        </div>
                        <div className="text-stone-200">{item.text}</div>
                      </li>
                    ))
                  )}
                </ul>
              </div>
            )}
          </HeritagePanel>

          <HeritagePanel className="order-1">
            <div className="mb-3 grid grid-cols-4 gap-2">
              {[
                { id: "ai", label: "AI giáo viên", icon: Sparkles },
                { id: "chat", label: "Tin nhắn", icon: MessageSquare },
                { id: "participants", label: "Người tham gia", icon: Users },
                { id: "events", label: "Sự kiện live", icon: Radio },
              ].map((tab) => {
                const Icon = tab.icon;
                const active = sideTab === tab.id;
                return (
                  <Button
                    key={tab.id}
                    type="button"
                    variant={active ? "default" : "outline"}
                    size="sm"
                    onClick={() => setSideTab(tab.id)}
                    aria-label={tab.label}
                    className={[
                      "h-10 gap-1 rounded-xl px-2 text-xs normal-case tracking-normal",
                      active
                        ? "border-teal-400/40 bg-teal-500/15 text-teal-100 hover:bg-teal-500/25"
                        : "border-amber-500/15 bg-black/25 text-stone-300 hover:border-amber-400/40 hover:bg-amber-500/10",
                    ].join(" ")}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    <span className="hidden sm:inline">{tab.label}</span>
                  </Button>
                );
              })}
            </div>

            {sideTab === "ai" ? (
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-teal-300/80">
                      Chat-first
                    </div>
                    <h3 className="text-base font-semibold text-amber-50">AI giáo viên</h3>
                    <p className="mt-0.5 text-xs leading-relaxed text-stone-400">
                      Hỏi nhanh, nhận gợi ý, kiểm tra hiểu bài và chuyển tiếp sang nhiệm vụ 3D.
                    </p>
                  </div>
                  <Select value={aiMode} onValueChange={setAiMode}>
                    <SelectTrigger className="h-9 min-w-[150px] rounded-xl border border-amber-500/20 bg-black/30 px-2 text-xs text-amber-50 sm:min-w-[190px]">
                      <SelectValue placeholder="Chọn chế độ trả lời" />
                    </SelectTrigger>
                    <SelectContent className="rounded-xl border border-amber-500/20 bg-stone-950 text-amber-50">
                      {AI_MODE_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value} className="rounded text-xs">
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {!hostSettings.aiEnabled ? (
                  <div className="rounded-xl border border-amber-500/20 bg-black/25 p-3 text-xs leading-relaxed text-stone-300">
                    AI đang bị chủ phòng tắt. Bật lại trong bảng điều khiển chủ phòng để tiếp tục trợ giúp.
                  </div>
                ) : null}

                <div
                  ref={aiScrollRef}
                  className="h-[420px] space-y-3 overflow-auto rounded-2xl border border-amber-500/15 bg-[linear-gradient(180deg,rgba(0,0,0,0.34),rgba(8,7,6,0.52))] p-3"
                >
                  {aiMessages.map((message) => (
                    <div
                      key={message.id}
                      className={[
                        "max-w-[92%] rounded-2xl px-3 py-2 text-sm shadow-sm",
                        message.role === "user"
                          ? "ml-auto border border-teal-400/25 bg-teal-500/15 text-teal-50"
                          : "mr-auto border border-amber-500/15 bg-[linear-gradient(135deg,rgba(42,31,18,0.82),rgba(0,0,0,0.35))] text-stone-100",
                      ].join(" ")}
                    >
                      <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.18em] opacity-65">
                        {message.role === "user" ? "Bạn" : "AI giáo viên"}
                      </div>
                      <div className="whitespace-pre-wrap break-words leading-relaxed">{message.content}</div>
                      {message.checkpointPrompt ? (
                        <div className="mt-2 rounded-xl border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-xs text-amber-100">
                          <div className="font-medium">Câu hỏi kiểm tra nhanh</div>
                          <div className="mt-0.5">{message.checkpointPrompt}</div>
                          <Button
                            type="button"
                            variant="outline"
                            size="xs"
                            onClick={() =>
                              void sendQuestionToAiTeacher(message.checkpointPrompt, {
                                source: "checkpoint",
                              })
                            }
                            disabled={aiLoading || !aiInteractionReady || !hostSettings.aiEnabled}
                            className="mt-1 rounded-lg border-amber-500/40 bg-black/25 px-2 py-1 text-[11px] text-amber-100 hover:bg-amber-500/10 normal-case tracking-normal"
                          >
                            Trả lời câu hỏi
                          </Button>
                        </div>
                      ) : null}
                      {Array.isArray(message.suggestedActions) && message.suggestedActions.length > 0 ? (
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {message.suggestedActions.map((action, idx) => (
                            <Button
                              key={`${message.id}-action-${idx}`}
                              type="button"
                              variant="outline"
                              size="xs"
                              onClick={() =>
                                void sendQuestionToAiTeacher(action.prompt, {
                                  source: "guided-next-step",
                                })
                              }
                              disabled={aiLoading || !aiInteractionReady || !hostSettings.aiEnabled}
                              className="rounded-lg border-amber-500/20 bg-black/25 px-2 py-1 text-[11px] text-amber-100 hover:bg-amber-500/10 normal-case tracking-normal"
                              title={action.prompt}
                            >
                              {action.label}
                            </Button>
                          ))}
                        </div>
                      ) : null}
                      {Array.isArray(message.references) && message.references.length > 0 ? (
                        <div className="mt-2 rounded-xl border border-amber-500/15 bg-black/25 px-2 py-1 text-[11px] text-stone-300">
                          <div className="font-medium text-amber-100">Nguồn tham khảo nội bộ</div>
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
                      {Array.isArray(message.citations) && message.citations.length > 0 ? (
                        <div className="mt-2 text-[11px] text-stone-400">
                          Trích dẫn:{" "}
                          {message.citations.map((item) => `${item.tag}(${item.title})`).join(", ")}
                        </div>
                      ) : null}
                      {message.rubric ? (
                        <div className="mt-2 rounded-xl border border-sky-500/25 bg-sky-500/10 px-2 py-1 text-[11px] text-sky-200">
                          <div className="font-medium">Đánh giá mức độ hiểu: {message.rubric.understandingLevel}</div>
                          {Array.isArray(message.rubric.knowledgeGaps) &&
                          message.rubric.knowledgeGaps.length > 0 ? (
                            <div className="mt-0.5">
                              Lỗ hổng kiến thức: {message.rubric.knowledgeGaps.join(" | ")}
                            </div>
                          ) : null}
                        </div>
                      ) : null}
                      {message.meta ? (
                        <div className="mt-1 text-[11px] opacity-70">{message.meta}</div>
                      ) : null}
                    </div>
                  ))}
                  {aiLoading ? (
                    <div className="mr-auto max-w-[86%] rounded-2xl border border-amber-500/15 bg-black/35 px-3 py-2 text-xs leading-relaxed text-stone-300">
                      AI đang soạn câu trả lời theo ngữ cảnh lớp học...
                    </div>
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-1.5">
                  {AI_QUICK_PROMPTS.map((prompt) => (
                    <Button
                      key={prompt}
                      type="button"
                      variant="outline"
                      size="xs"
                      onClick={() => setAiInput(prompt)}
                      disabled={aiLoading || !hostSettings.aiEnabled}
                      className="rounded-full border-amber-500/20 bg-black/25 px-2.5 py-1 text-[11px] text-amber-100 hover:bg-amber-500/10 normal-case tracking-normal"
                    >
                      {prompt.length > 44 ? `${prompt.slice(0, 44)}...` : prompt}
                    </Button>
                  ))}
                </div>

                <form onSubmit={askAiTeacher} className="space-y-2">
                  <textarea
                    rows={2}
                    value={aiInput}
                    onChange={(e) => setAiInput(e.target.value)}
                    placeholder="Nhập câu hỏi cho AI giáo viên..."
                    className="w-full resize-none rounded-2xl border border-amber-500/20 bg-black/30 px-3 py-2 text-sm leading-relaxed text-amber-50 outline-none placeholder:text-stone-500 focus:border-teal-400/60 focus:ring-2 focus:ring-teal-500/20"
                  />
                  <Button
                    type="submit"
                    disabled={
                      !aiInteractionReady ||
                      aiLoading ||
                      !aiInput.trim() ||
                      !hostSettings.aiEnabled
                    }
                    className="h-11 w-full rounded-2xl bg-teal-700/90 px-3 py-2 text-sm font-semibold text-white hover:bg-teal-600 normal-case tracking-normal"
                  >
                    <Send className="h-4 w-4" />
                    {aiLoading ? "Đang gửi..." : "Gửi câu hỏi"}
                  </Button>
                  {!aiInteractionReady ? (
                    <p className="text-[11px] leading-relaxed text-stone-500">
                      Đang chuẩn bị kết nối phòng. Bạn vẫn có thể nhập trước câu hỏi và gửi khi hệ thống sẵn sàng.
                    </p>
                  ) : null}
                </form>
              </div>
            ) : null}

            {sideTab === "chat" ? (
              <div>
                <div className="mb-2 flex items-center justify-between gap-2">
                  <h3 className="text-sm font-semibold text-amber-50">Tin nhắn lớp học</h3>
                  <Badge variant="secondary" className="rounded-full border border-amber-500/15 bg-black/25 text-[11px] text-amber-100">
                    {classChatMessages.length} tin
                  </Badge>
                </div>

                <div className="h-72 space-y-2 overflow-auto rounded-2xl border border-amber-500/15 bg-black/25 p-2">
                  {classChatMessages.length === 0 ? (
                    <div className="flex h-full items-center justify-center rounded-2xl border border-dashed border-amber-500/20 text-sm text-stone-500">
                      Chưa có tin nhắn lớp học.
                    </div>
                  ) : (
                    classChatMessages.map((message) => {
                      const isMine = message.identity === localIdentity;
                      return (
                        <div
                          key={message.id}
                          className={[
                            "max-w-[92%] rounded-2xl px-3 py-2 text-sm",
                            isMine
                              ? "ml-auto border border-teal-400/20 bg-teal-500/15 text-teal-50"
                              : "mr-auto border border-amber-500/15 bg-black/35 text-stone-100",
                          ].join(" ")}
                        >
                          <div className="mb-1 flex items-center justify-between gap-3 text-[11px] opacity-75">
                            <span>{isMine ? "Bạn" : message.displayName}</span>
                            <span>{new Date(message.createdAt).toLocaleTimeString()}</span>
                          </div>
                          <div className="whitespace-pre-wrap break-words">{message.text}</div>
                        </div>
                      );
                    })
                  )}
                </div>

                <form onSubmit={sendClassChatMessage} className="mt-2 flex gap-2">
                  <Input
                    value={chatInput}
                    onChange={(event) => setChatInput(event.target.value)}
                    placeholder="Nhập tin nhắn cho lớp..."
                    maxLength={1000}
                    disabled={!aiInteractionReady || chatSending}
                    className="h-10 flex-1 rounded-2xl border border-amber-500/20 bg-black/30 px-3 text-sm text-amber-50 placeholder:text-stone-500"
                  />
                  <Button
                    type="submit"
                    disabled={!chatInput.trim() || !aiInteractionReady || chatSending}
                    className="h-10 rounded-2xl bg-teal-700/90 px-3 text-sm text-white hover:bg-teal-600 normal-case tracking-normal"
                    aria-label="Gửi tin nhắn lớp học"
                  >
                    <Send className="h-4 w-4" />
                    Gửi
                  </Button>
                </form>
              </div>
            ) : null}

            {sideTab === "participants" ? (
              <div>
                <div className="mb-2 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-amber-50">Danh sách người tham gia</h3>
                  {canModerate ? (
                    <Button
                      type="button"
                      variant="outline"
                      size="xs"
                      onClick={handleMuteAll}
                      disabled={moderationLoading}
                      className={`px-2 py-1 text-xs ${HERITAGE_BUTTON_CLASS}`}
                    >
                      {moderationLoading ? "Đang tắt mic..." : "Tắt mic tất cả"}
                    </Button>
                  ) : null}
                </div>

                <ul className="max-h-72 space-y-2 overflow-auto text-sm">
                  {mergedParticipants.length === 0 ? (
                    <li className="rounded-2xl border border-dashed border-amber-500/20 p-4 text-center text-stone-500">Chưa có ai trong phòng.</li>
                  ) : (
                    mergedParticipants.map((participant) => (
                      <li
                        key={participant.id}
                        className="rounded-2xl border border-amber-500/15 bg-black/25 px-3 py-2 text-stone-100"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <div className="flex items-center gap-1 font-medium">
                              <span>{participant.name}{participant.isLocal ? " (bạn)" : ""}</span>
                              {participant.handRaised ? (
                                <Hand className="h-3.5 w-3.5 text-amber-500" />
                              ) : null}
                            </div>
                            <div className="text-xs text-stone-500">
                              Vai trò: {roleLabel(participant.role)}
                            </div>
                            <div className="text-xs text-stone-500">
                              Mic: {participant.microphoneEnabled ? "bật" : "tắt"} | Camera:{" "}
                              {participant.cameraEnabled ? "bật" : "tắt"}
                            </div>
                          </div>

                          <div className="flex shrink-0 gap-1">
                            <Button
                              type="button"
                              variant="outline"
                              size="xs"
                              onClick={() =>
                                setPinnedIdentity((prev) =>
                                  prev === participant.identity ? null : participant.identity,
                                )
                              }
                              className={`px-2 py-1 text-[11px] ${HERITAGE_BUTTON_CLASS}`}
                            >
                              {pinnedIdentity === participant.identity ? "Bỏ ghim" : "Ghim"}
                            </Button>

                            {canModerate && !participant.isLocal && !participant.isAi ? (
                              <>
                                <Button
                                  type="button"
                                  variant="outline"
                                  size="xs"
                                  onClick={() => void handleToggleCohost(participant)}
                                  disabled={Boolean(participantActionBusy[participant.backendId])}
                                  className={`px-2 py-1 text-[11px] ${HERITAGE_BUTTON_CLASS}`}
                                >
                                  {participant.role === "cohost"
                                    ? "Trả về học viên"
                                    : "Đặt đồng chủ phòng"}
                                </Button>
                                <Button
                                  type="button"
                                  variant="outline"
                                  size="xs"
                                  onClick={() => void handleRemoveParticipant(participant)}
                                  disabled={Boolean(participantActionBusy[participant.backendId])}
                                  className="rounded-xl border-red-500/40 bg-red-500/10 px-2 py-1 text-[11px] text-red-200 hover:bg-red-500/20 normal-case tracking-normal"
                                >
                                  Mời ra
                                </Button>
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
                <h3 className="mb-2 text-sm font-semibold text-amber-50">Sự kiện trực tiếp</h3>
                <ul className="max-h-72 space-y-2 overflow-auto text-xs">
                  {sortedEvents.length === 0 ? (
                    <li className="rounded-2xl border border-dashed border-amber-500/20 p-4 text-center text-stone-500">Chưa có sự kiện.</li>
                  ) : (
                    sortedEvents.map((event) => (
                      <li
                        key={event.id}
                        className="rounded-2xl border border-amber-500/15 bg-black/25 px-2 py-2"
                      >
                        <div className="mb-1 flex items-center justify-between gap-2">
                          <EventBadge eventType={event.event_type} />
                          <span className="text-stone-500">
                            {new Date(event.created_at).toLocaleTimeString()}
                          </span>
                        </div>
                        <div className="text-stone-200">
                          {event.participant_identity || "Hệ thống"}
                        </div>
                      </li>
                    ))
                  )}
                </ul>
              </div>
            ) : null}
          </HeritagePanel>

          {canManageSettings ? (
            <HeritagePanel className="order-5">
              <HeritagePanelHeader
                icon={Lock}
                eyebrow="Điều phối"
                title="Bảng điều khiển chủ phòng"
                description="Khóa phòng, theo dõi sức khỏe AI và cấu hình persona cho phiên học."
              />
              <div className="grid grid-cols-1 gap-2">
                <Button
                  type="button"
                  variant="outline"
                  disabled={settingsBusy}
                  onClick={() =>
                    void applyHostSettings({
                      lockRoom: !hostSettings.lockRoom,
                    })
                  }
	                  className={`h-11 justify-between px-3 text-sm ${HERITAGE_BUTTON_CLASS}`}
                >
                  <span className="inline-flex items-center gap-2">
                    {hostSettings.lockRoom ? (
                      <Lock className="h-4 w-4 text-amber-600" />
                    ) : (
                      <LockOpen className="h-4 w-4 text-emerald-600" />
                    )}
                    Khóa phòng
                  </span>
	                  <span className="text-xs text-stone-400">
                    {hostSettings.lockRoom ? "BẬT" : "TẮT"}
                  </span>
                </Button>

	                <div className={HERITAGE_FIELD_CLASS + " px-3 py-3"}>
                  <div className="mb-2 flex items-center justify-between gap-2">
	                    <span className="inline-flex items-center gap-2 text-sm font-medium text-amber-50">
                      <Waves className="h-4 w-4 text-teal-300" />
                      Sức khỏe AI live
                    </span>
                    <Button
                      type="button"
                      variant="outline"
                      size="xs"
                      onClick={() => void refreshObservability()}
	                      className={`px-2 py-1 text-[11px] ${HERITAGE_BUTTON_CLASS}`}
                    >
                      Làm mới
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
	                    <div className={HERITAGE_FIELD_CLASS + " px-2 py-2"}>
	                      <span className="block text-stone-500">Success rate</span>
                      <span className="font-semibold text-emerald-300">
                        {formatPercent(observability?.success_rate ?? 1)}
                      </span>
                    </div>
	                    <div className={HERITAGE_FIELD_CLASS + " px-2 py-2"}>
	                      <span className="block text-stone-500">Error budget</span>
                      <span className="font-semibold text-sky-300">
                        {formatPercent(observability?.error_budget ?? 1)}
                      </span>
                    </div>
	                    <div className={HERITAGE_FIELD_CLASS + " px-2 py-2"}>
	                      <span className="block text-stone-500">Drop rate</span>
                      <span className="font-semibold text-amber-300">
                        {formatPercent(observability?.drop_rate ?? 0)}
                      </span>
                    </div>
	                    <div className={HERITAGE_FIELD_CLASS + " px-2 py-2"}>
	                      <span className="block text-stone-500">P95 latency</span>
	                      <span className="font-semibold text-amber-100">
                        {Math.round(Number(observability?.p95_latency_ms || 0))}ms
                      </span>
                    </div>
                  </div>
	                  <p className="mt-2 text-[11px] text-stone-500">
                    Dữ liệu lấy từ observability backend cho STT/TTS/AI, dùng để theo dõi chất lượng phiên live.
                  </p>
                </div>

                <Button
                  type="button"
                  variant="outline"
                  disabled={settingsBusy}
                  onClick={() =>
                    void applyHostSettings({
                      aiEnabled: !hostSettings.aiEnabled,
                    })
                  }
	                  className={`h-11 justify-between px-3 text-sm ${HERITAGE_BUTTON_CLASS}`}
                >
                  <span className="inline-flex items-center gap-2">
	                    <Sparkles className="h-4 w-4 text-amber-300" />
                    AI giáo viên
                  </span>
	                  <span className="text-xs text-stone-400">
                    {hostSettings.aiEnabled ? "BẬT" : "TẮT"}
                  </span>
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  disabled={settingsBusy || sessionEnding}
                  onClick={handleEndSession}
	                  className="h-11 justify-between rounded-xl border-red-500/40 bg-red-500/10 px-3 text-sm text-red-200 normal-case tracking-normal hover:bg-red-500/20"
                >
                  <span className="inline-flex items-center gap-2">
                    <PhoneOff className="h-4 w-4" />
                    Kết thúc phiên
                  </span>
                  <span className="text-xs text-red-600 dark:text-red-300">
                    {sessionEnding ? "ĐANG XỬ LÝ" : "HOST"}
                  </span>
                </Button>

	                <div className={HERITAGE_FIELD_CLASS + " px-3 py-2"}>
	                  <label className="mb-1 block text-xs font-medium text-stone-300">
                    Persona AI (cấp độ)
                  </label>
                  <div className="flex items-center gap-2">
                    <Select
                      value={hostSettings.gradeLevel}
                      onValueChange={(value) =>
                        setHostSettings((prev) => ({
                          ...prev,
                          gradeLevel: value,
                        }))
                      }
                    >
	                      <SelectTrigger className={HERITAGE_SELECT_TRIGGER_CLASS + " flex-1"}>
                        <SelectValue placeholder="Chọn cấp độ" />
                      </SelectTrigger>
	                      <SelectContent className="rounded-xl border border-amber-500/20 bg-stone-950 text-amber-50">
                        {GRADE_LEVEL_OPTIONS.map((option) => (
                          <SelectItem key={option.value} value={option.value} className="rounded text-sm">
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={settingsBusy}
                      onClick={() =>
                        void applyHostSettings({
                          gradeLevel: hostSettings.gradeLevel,
                        })
                      }
	                      className={`px-3 text-xs ${HERITAGE_BUTTON_CLASS}`}
                    >
                      Lưu
                    </Button>
                  </div>
                </div>

	                <div className={HERITAGE_FIELD_CLASS + " px-3 py-2"}>
	                  <label className="mb-1 block text-xs font-medium text-stone-300">
                    Trần chi phí AI (USD)
                  </label>
                  <div className="flex items-center gap-2">
                    <Input
                      type="number"
                      min={0.1}
                      step={0.1}
                      value={hostSettings.aiCostCeilingUsd}
                      onChange={(e) =>
                        setHostSettings((prev) => ({
                          ...prev,
                          aiCostCeilingUsd: Number(e.target.value || 0),
                        }))
                      }
	                      className="h-10 flex-1 rounded-xl border border-amber-500/20 bg-black/30 px-2 text-sm text-amber-50"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={settingsBusy}
                      onClick={() =>
                        void applyHostSettings({
                          aiCostCeilingUsd: Number(hostSettings.aiCostCeilingUsd || 0),
                        })
                      }
	                      className={`px-3 text-xs ${HERITAGE_BUTTON_CLASS}`}
                    >
                      Lưu
                    </Button>
                  </div>
                </div>
              </div>
	              <p className="mt-2 text-xs text-stone-500">
                Khóa phòng sẽ chặn học viên mới. Nút AI điều khiển trợ giảng AI, cấp độ và giới hạn chi phí.
              </p>
            </HeritagePanel>
          ) : null}
        </aside>
      </section>

      <div ref={audioContainerRef} />
    </main>
  );
}
