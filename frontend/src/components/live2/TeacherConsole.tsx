"use client";

/**
 * TeacherConsole — in-room "Teacher Co-pilot" side panel for a live AI-teacher
 * classroom. Shown to hosts/teachers. Wires existing @/lib/api functions to
 * surface engagement metrics, a question queue, class controls and participant
 * management. Self-contained; the parent supplies sessionId, participants and
 * the polled live `events` stream.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  X,
  RefreshCw,
  Lock,
  Bot,
  MicOff,
  UserMinus,
  ShieldCheck,
  AlertTriangle,
  PhoneOff,
} from "lucide-react";

import {
  getLiveSessionDashboard,
  updateLiveHostSettings,
  hostMuteAllLiveParticipants,
  hostRemoveLiveParticipant,
  updateLiveParticipantRole,
  endLiveSession,
} from "@/lib/api";

const GRADE_OPTIONS = [
  { value: "primary", label: "Tiểu học" },
  { value: "middle_school", label: "THCS" },
  { value: "high_school", label: "THPT" },
  { value: "university", label: "Đại học" },
];

const ROLE_OPTIONS = [
  { value: "learner", label: "Học sinh" },
  { value: "cohost", label: "Trợ giảng" },
];

const REFRESH_INTERVAL_MS = 15000;

/** A transient status line shown under an action (settings/mute/end/etc). */
interface StatusInfo {
  type?: "error" | "success" | "info";
  message?: string;
}

/** A live-session participant (subset of the API shape used by the console). */
export interface LiveParticipant {
  id?: string | number;
  participant_identity?: string | null;
  participant_user_id?: string | number | null;
  user_id?: string | number | null;
  display_name?: string | null;
  role?: string | null;
  is_ai?: boolean;
  left_at?: string | null;
}

/** A polled live-session event (transcript / chat / raise-hand / actions). */
export interface LiveEvent {
  id: string | number;
  event_type?: string;
  event_source?: string;
  participant_identity?: string | null;
  participant_user_id?: string | number | null;
  created_at?: string;
  payload?: Record<string, unknown> | null;
}

/** Engagement metrics from the host dashboard. */
interface EngagementMetrics {
  user_turns?: number;
  ai_turns?: number;
  hand_raises?: number;
  interaction_score?: number;
  low_interaction?: boolean;
}

/** AI cost summary from the host dashboard. */
interface AiCost {
  total_usd?: number;
  ceiling_usd?: number;
}

/** Host dashboard payload returned by getLiveSessionDashboard. */
interface DashboardData {
  session?: {
    lock_room?: boolean;
    ai_enabled?: boolean;
    grade_level?: string;
    ai_cost_ceiling_usd?: number | null;
  };
  metrics?: { engagement?: EngagementMetrics };
  ai_cost?: AiCost;
}

function errMessage(err: unknown): string {
  if (!err) return "Đã xảy ra lỗi";
  if (typeof err === "string") return err;
  const e = err as { message?: string; detail?: string };
  return e.message || e.detail || "Đã xảy ra lỗi";
}

function formatTime(value?: string | null): string {
  if (!value) return "";
  try {
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

function formatUsd(value: unknown): string {
  const n = Number(value);
  if (!Number.isFinite(n)) return "$0.00";
  return `$${n.toFixed(2)}`;
}

function StatusLine({ status }: { status?: StatusInfo | null }) {
  if (!status || !status.message) return null;
  const tone =
    status.type === "error"
      ? "text-rose-400"
      : status.type === "success"
        ? "text-emerald-400"
        : "text-zinc-400";
  return <p className={`mt-1 text-xs ${tone}`}>{status.message}</p>;
}

function MetricCard({
  label,
  value,
  accent = "text-sky-300",
}: {
  label: string;
  value: React.ReactNode;
  accent?: string;
}) {
  return (
    <div className="rounded-xl bg-zinc-800/70 px-3 py-2 ring-1 ring-white/5">
      <div className="text-[11px] uppercase tracking-wide text-zinc-500">{label}</div>
      <div className={`mt-0.5 text-lg font-semibold ${accent}`}>{value}</div>
    </div>
  );
}

interface TeacherConsoleProps {
  sessionId: string | number;
  participants?: LiveParticipant[];
  events?: LiveEvent[];
  onClose?: () => void;
}

export default function TeacherConsole({
  sessionId,
  participants = [],
  events = [],
  onClose,
}: TeacherConsoleProps) {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [dashboardStatus, setDashboardStatus] = useState<StatusInfo | null>(null);

  // Class controls (settings) form state.
  const [lockRoom, setLockRoom] = useState(false);
  const [aiEnabled, setAiEnabled] = useState(true);
  const [gradeLevel, setGradeLevel] = useState("middle_school");
  const [costCeiling, setCostCeiling] = useState("");
  const [savingSettings, setSavingSettings] = useState(false);
  const [settingsStatus, setSettingsStatus] = useState<StatusInfo | null>(null);

  const [muting, setMuting] = useState(false);
  const [muteStatus, setMuteStatus] = useState<StatusInfo | null>(null);

  const [ending, setEnding] = useState(false);
  const [endStatus, setEndStatus] = useState<StatusInfo | null>(null);

  // Per-participant transient state.
  const [participantStatus, setParticipantStatus] = useState<Record<string, StatusInfo | null>>({});
  const [busyParticipants, setBusyParticipants] = useState<Record<string, boolean>>({});

  // Locally-dismissed raise_hand events ("Đã xử lý").
  const [dismissed, setDismissed] = useState<Set<string | number>>(() => new Set());

  const settingsInitialized = useRef(false);

  const loadDashboard = useCallback(
    async ({ silent = false }: { silent?: boolean } = {}) => {
      if (!sessionId) return;
      if (!silent) setLoading(true);
      try {
        const data = (await getLiveSessionDashboard({ sessionId })) as DashboardData | null;
        setDashboard(data || null);
        setDashboardStatus(null);

        // Initialize the settings form once from the session config.
        const session = data?.session || {};
        if (!settingsInitialized.current) {
          if (typeof session.lock_room === "boolean") setLockRoom(session.lock_room);
          if (typeof session.ai_enabled === "boolean") setAiEnabled(session.ai_enabled);
          if (typeof session.grade_level === "string" && session.grade_level) {
            setGradeLevel(session.grade_level);
          }
          const ceiling =
            session.ai_cost_ceiling_usd ?? data?.ai_cost?.ceiling_usd ?? null;
          if (ceiling != null && Number.isFinite(Number(ceiling))) {
            setCostCeiling(String(ceiling));
          }
          settingsInitialized.current = true;
        }
      } catch (err) {
        setDashboardStatus({ type: "error", message: `Lỗi: ${errMessage(err)}` });
      } finally {
        if (!silent) setLoading(false);
      }
    },
    [sessionId],
  );

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  // Auto-refresh dashboard every 15s (silent so it doesn't flash the spinner).
  useEffect(() => {
    if (!sessionId) return undefined;
    const id = setInterval(() => {
      loadDashboard({ silent: true });
    }, REFRESH_INTERVAL_MS);
    return () => clearInterval(id);
  }, [sessionId, loadDashboard]);

  // Map participant identifiers -> display name for resolving event authors.
  const nameByKey = useMemo(() => {
    const map = new Map<string, string>();
    for (const p of participants || []) {
      const label = p?.display_name || "Học sinh";
      if (p?.participant_identity != null) {
        map.set(`identity:${p.participant_identity}`, label);
      }
      if (p?.user_id != null) map.set(`user:${p.user_id}`, label);
    }
    return map;
  }, [participants]);

  const resolveName = useCallback(
    (ev: LiveEvent | null | undefined) => {
      if (!ev) return "Học sinh";
      if (ev.participant_user_id != null) {
        const byUser = nameByKey.get(`user:${ev.participant_user_id}`);
        if (byUser) return byUser;
      }
      if (ev.participant_identity != null) {
        const byIdentity = nameByKey.get(`identity:${ev.participant_identity}`);
        if (byIdentity) return byIdentity;
      }
      return "Học sinh";
    },
    [nameByKey],
  );

  // Question queue: most recent raise_hand events not locally dismissed.
  const questionQueue = useMemo(() => {
    const list = (events || [])
      .filter((ev) => ev?.event_type === "raise_hand")
      .filter((ev) => !dismissed.has(ev.id));
    // events arrive newest-last; show newest first, cap at 10.
    return list.slice(-10).reverse();
  }, [events, dismissed]);

  // Recent AI teacher replies.
  const aiReplies = useMemo(() => {
    const list = (events || [])
      .filter((ev) => ev?.event_type === "ai_teacher_reply")
      .map((ev) => ({
        id: ev.id,
        answer: (ev?.payload?.answer as string) || "",
        created_at: ev.created_at,
      }))
      .filter((r) => r.answer);
    return list.slice(-3).reverse();
  }, [events]);

  const engagement: EngagementMetrics = useMemo(
    () => dashboard?.metrics?.engagement || {},
    [dashboard],
  );
  const aiCost: AiCost = dashboard?.ai_cost || {};

  const lowInteraction = useMemo(
    () =>
      engagement?.low_interaction ||
      (events || []).some(
        (ev) =>
          ev?.event_type === "session_action" &&
          ev?.payload?.action_type === "low_interaction_warning",
      ),
    [engagement, events],
  );

  const manageable = useMemo(
    () => (participants || []).filter((p) => !p?.is_ai && !p?.left_at),
    [participants],
  );

  const dismissQuestion = useCallback((id: string | number) => {
    setDismissed((prev) => {
      const next = new Set(prev);
      next.add(id);
      return next;
    });
  }, []);

  const handleSaveSettings = useCallback(async () => {
    if (!sessionId) return;
    setSavingSettings(true);
    setSettingsStatus(null);
    try {
      const ceilingNum = costCeiling === "" ? undefined : Number(costCeiling);
      await updateLiveHostSettings({
        sessionId,
        lockRoom,
        aiEnabled,
        gradeLevel,
        aiCostCeilingUsd: Number.isFinite(ceilingNum) ? ceilingNum : undefined,
      });
      setSettingsStatus({ type: "success", message: "Đã lưu" });
      loadDashboard({ silent: true });
    } catch (err) {
      setSettingsStatus({ type: "error", message: `Lỗi: ${errMessage(err)}` });
    } finally {
      setSavingSettings(false);
    }
  }, [sessionId, lockRoom, aiEnabled, gradeLevel, costCeiling, loadDashboard]);

  const handleMuteAll = useCallback(async () => {
    if (!sessionId) return;
    setMuting(true);
    setMuteStatus(null);
    try {
      await hostMuteAllLiveParticipants({ sessionId, includeCohosts: false });
      setMuteStatus({ type: "success", message: "Đã tắt mic tất cả" });
    } catch (err) {
      setMuteStatus({ type: "error", message: `Lỗi: ${errMessage(err)}` });
    } finally {
      setMuting(false);
    }
  }, [sessionId]);

  const setPStatus = useCallback((id: string | number, status: StatusInfo | null) => {
    setParticipantStatus((prev) => ({ ...prev, [id]: status }));
  }, []);

  const setPBusy = useCallback((id: string | number, busy: boolean) => {
    setBusyParticipants((prev) => ({ ...prev, [id]: busy }));
  }, []);

  const handleRoleChange = useCallback(
    async (participantId: string | number | undefined, role: string) => {
      if (!sessionId || !participantId) return;
      setPBusy(participantId, true);
      setPStatus(participantId, null);
      try {
        await updateLiveParticipantRole({ sessionId, participantId, role });
        setPStatus(participantId, { type: "success", message: "Đã cập nhật vai trò" });
      } catch (err) {
        setPStatus(participantId, { type: "error", message: `Lỗi: ${errMessage(err)}` });
      } finally {
        setPBusy(participantId, false);
      }
    },
    [sessionId, setPBusy, setPStatus],
  );

  const handleRemove = useCallback(
    async (participantId: string | number | undefined) => {
      if (!sessionId || !participantId) return;
      if (typeof window !== "undefined") {
        const ok = window.confirm("Mời người này ra khỏi phòng?");
        if (!ok) return;
      }
      setPBusy(participantId, true);
      setPStatus(participantId, null);
      try {
        await hostRemoveLiveParticipant({ sessionId, participantId });
        setPStatus(participantId, { type: "success", message: "Đã mời ra" });
      } catch (err) {
        setPStatus(participantId, { type: "error", message: `Lỗi: ${errMessage(err)}` });
      } finally {
        setPBusy(participantId, false);
      }
    },
    [sessionId, setPBusy, setPStatus],
  );

  const handleEndSession = useCallback(async () => {
    if (!sessionId) return;
    if (typeof window !== "undefined") {
      const ok = window.confirm("Kết thúc buổi học cho tất cả mọi người?");
      if (!ok) return;
    }
    setEnding(true);
    setEndStatus(null);
    try {
      await endLiveSession({ sessionId });
      setEndStatus({ type: "success", message: "Đã kết thúc buổi học" });
    } catch (err) {
      setEndStatus({ type: "error", message: `Lỗi: ${errMessage(err)}` });
    } finally {
      setEnding(false);
    }
  }, [sessionId]);

  return (
    <aside className="flex h-full w-full max-w-sm flex-col overflow-hidden rounded-2xl bg-zinc-950/95 text-zinc-100 ring-1 ring-white/10">
      {/* 1. Header */}
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-sky-400" />
          <h2 className="text-sm font-semibold">Bảng điều khiển giáo viên</h2>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Đóng"
          className="rounded-full p-1.5 text-zinc-400 hover:bg-white/10 hover:text-zinc-200"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto px-4 py-4">
        {/* 2. Engagement summary */}
        <section>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
              Tương tác lớp học
            </h3>
            <button
              type="button"
              onClick={() => loadDashboard()}
              disabled={loading}
              className="inline-flex items-center gap-1 rounded-md bg-zinc-800 px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-700 disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              Làm mới
            </button>
          </div>

          {lowInteraction ? (
            <div className="mb-2 flex items-start gap-2 rounded-lg bg-amber-500/10 px-3 py-2 text-xs text-amber-300 ring-1 ring-amber-500/30">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>Lớp đang ít tương tác. Hãy thử đặt câu hỏi hoặc gọi tên học sinh.</span>
            </div>
          ) : null}

          <div className="grid grid-cols-2 gap-2">
            <MetricCard label="Số lượt hỏi" value={engagement.user_turns ?? 0} />
            <MetricCard
              label="AI trả lời"
              value={engagement.ai_turns ?? 0}
              accent="text-emerald-300"
            />
            <MetricCard label="Giơ tay" value={engagement.hand_raises ?? 0} accent="text-amber-300" />
            <MetricCard
              label="Điểm tương tác"
              value={engagement.interaction_score ?? 0}
              accent="text-sky-300"
            />
            <div className="col-span-2 rounded-xl bg-zinc-800/70 px-3 py-2 ring-1 ring-white/5">
              <div className="text-[11px] uppercase tracking-wide text-zinc-500">Chi phí AI</div>
              <div className="mt-0.5 text-lg font-semibold text-fuchsia-300">
                {formatUsd(aiCost.total_usd)}
                <span className="ml-1 text-xs font-normal text-zinc-500">
                  / {formatUsd(aiCost.ceiling_usd)}
                </span>
              </div>
            </div>
          </div>
          <StatusLine status={dashboardStatus} />
        </section>

        {/* 3. Question queue */}
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-400">
            Hàng đợi câu hỏi
          </h3>
          {questionQueue.length === 0 ? (
            <p className="rounded-lg bg-zinc-800/40 px-3 py-3 text-center text-xs text-zinc-500">
              Chưa có ai giơ tay.
            </p>
          ) : (
            <ul className="space-y-1.5">
              {questionQueue.map((ev) => (
                <li
                  key={ev.id}
                  className="flex items-center justify-between gap-2 rounded-lg bg-zinc-800/60 px-3 py-2 ring-1 ring-white/5"
                >
                  <div className="min-w-0">
                    <div className="truncate text-sm text-zinc-100">{resolveName(ev)}</div>
                    <div className="text-[11px] text-zinc-500">{formatTime(ev.created_at)}</div>
                  </div>
                  <button
                    type="button"
                    onClick={() => dismissQuestion(ev.id)}
                    className="shrink-0 rounded-md bg-sky-600/80 px-2 py-1 text-xs font-medium text-white hover:bg-sky-500"
                  >
                    Đã xử lý
                  </button>
                </li>
              ))}
            </ul>
          )}

          {aiReplies.length > 0 ? (
            <div className="mt-3">
              <div className="mb-1 text-[11px] font-medium uppercase tracking-wide text-zinc-500">
                AI vừa trả lời
              </div>
              <ul className="space-y-1.5">
                {aiReplies.map((r) => (
                  <li
                    key={r.id}
                    className="rounded-lg bg-zinc-800/40 px-3 py-2 text-xs text-zinc-300 ring-1 ring-white/5"
                  >
                    <div className="line-clamp-3">{r.answer}</div>
                    <div className="mt-1 text-[10px] text-zinc-600">{formatTime(r.created_at)}</div>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>

        {/* 4. Class controls */}
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-400">
            Điều khiển lớp
          </h3>
          <div className="space-y-3 rounded-xl bg-zinc-800/50 p-3 ring-1 ring-white/5">
            <label className="flex items-center justify-between gap-3 text-sm">
              <span className="inline-flex items-center gap-2 text-zinc-200">
                <Lock className="h-4 w-4 text-zinc-400" />
                Khoá phòng
              </span>
              <input
                type="checkbox"
                checked={lockRoom}
                onChange={(e) => setLockRoom(e.target.checked)}
                className="h-4 w-4 accent-sky-500"
              />
            </label>

            <label className="flex items-center justify-between gap-3 text-sm">
              <span className="inline-flex items-center gap-2 text-zinc-200">
                <Bot className="h-4 w-4 text-zinc-400" />
                Bật AI
              </span>
              <input
                type="checkbox"
                checked={aiEnabled}
                onChange={(e) => setAiEnabled(e.target.checked)}
                className="h-4 w-4 accent-sky-500"
              />
            </label>

            <label className="block text-sm">
              <span className="mb-1 block text-zinc-300">Cấp học</span>
              <select
                value={gradeLevel}
                onChange={(e) => setGradeLevel(e.target.value)}
                className="w-full rounded-lg bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none ring-1 ring-white/10 focus:ring-2 focus:ring-sky-500/40"
              >
                {GRADE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm">
              <span className="mb-1 block text-zinc-300">Trần chi phí AI (USD)</span>
              <input
                type="number"
                min="0"
                step="0.01"
                value={costCeiling}
                onChange={(e) => setCostCeiling(e.target.value)}
                placeholder="0.00"
                className="w-full rounded-lg bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none ring-1 ring-white/10 focus:ring-2 focus:ring-sky-500/40"
              />
            </label>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleSaveSettings}
                disabled={savingSettings}
                className="flex-1 rounded-lg bg-sky-600 px-3 py-2 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50"
              >
                {savingSettings ? "Đang lưu…" : "Lưu cài đặt"}
              </button>
            </div>
            <StatusLine status={settingsStatus} />

            <div className="border-t border-white/10 pt-3">
              <button
                type="button"
                onClick={handleMuteAll}
                disabled={muting}
                className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-zinc-700 px-3 py-2 text-sm font-medium text-zinc-100 hover:bg-zinc-600 disabled:opacity-50"
              >
                <MicOff className="h-4 w-4" />
                {muting ? "Đang tắt…" : "Tắt mic tất cả"}
              </button>
              <StatusLine status={muteStatus} />
            </div>
          </div>
        </section>

        {/* 5. Participants management */}
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-400">
            Quản lý người tham gia
          </h3>
          {manageable.length === 0 ? (
            <p className="rounded-lg bg-zinc-800/40 px-3 py-3 text-center text-xs text-zinc-500">
              Chưa có học sinh nào.
            </p>
          ) : (
            <ul className="space-y-2">
              {manageable.map((p) => {
                const busy = !!busyParticipants[p.id ?? ""];
                const status = participantStatus[p.id ?? ""];
                return (
                  <li
                    key={p.id || p.participant_identity}
                    className="rounded-lg bg-zinc-800/60 px-3 py-2 ring-1 ring-white/5"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="min-w-0 text-sm text-zinc-100">
                        <span className="truncate">{p.display_name || "Học sinh"}</span>
                      </div>
                      <div className="flex shrink-0 items-center gap-2">
                        <select
                          value={p.role === "cohost" ? "cohost" : "learner"}
                          disabled={busy}
                          onChange={(e) => handleRoleChange(p.id, e.target.value)}
                          className="rounded-md bg-zinc-900 px-2 py-1 text-xs text-zinc-100 outline-none ring-1 ring-white/10 focus:ring-2 focus:ring-sky-500/40 disabled:opacity-50"
                        >
                          {ROLE_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                        <button
                          type="button"
                          onClick={() => handleRemove(p.id)}
                          disabled={busy}
                          aria-label="Mời ra"
                          title="Mời ra"
                          className="inline-flex items-center gap-1 rounded-md bg-rose-600/80 px-2 py-1 text-xs font-medium text-white hover:bg-rose-500 disabled:opacity-50"
                        >
                          <UserMinus className="h-3.5 w-3.5" />
                          Mời ra
                        </button>
                      </div>
                    </div>
                    <StatusLine status={status} />
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </div>

      {/* 6. Footer */}
      <div className="border-t border-white/10 px-4 py-3">
        <button
          type="button"
          onClick={handleEndSession}
          disabled={ending}
          className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-rose-600 px-3 py-2 text-sm font-semibold text-white hover:bg-rose-500 disabled:opacity-50"
        >
          <PhoneOff className="h-4 w-4" />
          {ending ? "Đang kết thúc…" : "Kết thúc buổi học"}
        </button>
        <StatusLine status={endStatus} />
      </div>
    </aside>
  );
}
