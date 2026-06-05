"use client";

/**
 * LiveClassroom v2 — Meet/Teams-style room for the realtime AI teacher.
 *
 * Adds over v1: a live 3D avatar (with orb fallback + toggle), a SHARED
 * transcript/chat/raise-hand driven by polling /events (so multiple students
 * see each other), AI quick-action chips (explain simpler / deeper / quiz /
 * summarize), a raise-hand button, and a Teacher Co-pilot console for hosts.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Loader2, Mic, Sparkles, Hand, Bot, CircleUserRound, GraduationCap } from "lucide-react";

import {
  askLiveAiTeacher,
  createLiveSessionEvent,
  joinLiveSession,
  leaveLiveSession,
  listLiveSessionEvents,
  listLiveSessionParticipants,
  synthesizeLiveAiTeacherVoice,
  transcribeLiveAiTeacherVoice,
} from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

import AiAvatar from "./AiAvatar";
import CaptionsFeed from "./CaptionsFeed";
import ControlBar from "./ControlBar";
import ConversationOrb from "./ConversationOrb";
import SidePanel from "./SidePanel";
import TeacherConsole from "./TeacherConsole";
import { TURN, useRealtimeVoice } from "./useRealtimeVoice";

// Quick-action chips the student can tap to steer the AI.
const QUICK_ACTIONS = [
  { key: "simpler", label: "Giải thích đơn giản hơn", mode: "explain-simpler", message: "Giải thích lại nội dung vừa rồi một cách đơn giản, dễ hiểu hơn." },
  { key: "deeper", label: "Tìm hiểu sâu hơn", mode: "go-deeper", message: "Hãy nói sâu hơn về chủ đề vừa rồi." },
  { key: "quiz", label: "Kiểm tra em", mode: "quiz", message: "Hãy ra một câu hỏi ngắn để kiểm tra em về nội dung vừa học." },
  { key: "summarize", label: "Tóm tắt", mode: "summarize", message: "Hãy tóm tắt những ý chính vừa học." },
];

export default function LiveClassroom({ sessionId }) {
  const currentUser = useAuthStore((s) => s.user);

  const [phase, setPhase] = useState("prejoin"); // prejoin | joining | joined | left
  const [error, setError] = useState("");
  const [participants, setParticipants] = useState([]);
  const [events, setEvents] = useState([]);
  const [systemCaptions, setSystemCaptions] = useState([]);
  const [chatUnread, setChatUnread] = useState(0);

  const [micOn, setMicOn] = useState(true);
  const [captionsOn, setCaptionsOn] = useState(true);
  const [useAvatar, setUseAvatar] = useState(true);
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelTab, setPanelTab] = useState("people");
  const [teacherOpen, setTeacherOpen] = useState(false);
  const [handRaised, setHandRaised] = useState(false);

  const eventCursorRef = useRef(null);
  const seenEventIdsRef = useRef(new Set());

  const displayName = currentUser?.display_name || currentUser?.email?.split("@")[0] || "Bạn";
  const isHost = useMemo(() => {
    const role = String(currentUser?.role || "").toLowerCase();
    if (role === "admin" || role === "teacher") return true;
    const me = participants.find((p) => p.user_id && currentUser?.id && p.user_id === currentUser.id);
    return me ? me.role === "host" || me.role === "cohost" : false;
  }, [participants, currentUser]);

  const voice = useRealtimeVoice({
    sessionId,
    enabled: phase === "joined" && micOn,
    transcribe: transcribeLiveAiTeacherVoice,
    askTeacher: ({ sessionId: sid, message, mode }) =>
      askLiveAiTeacher({ sessionId: sid, message, mode: mode || "hint-first", speakerName: displayName }),
    synthesize: synthesizeLiveAiTeacherVoice,
  });

  // Resolve a display name for an event author.
  const nameFor = useCallback(
    (ev) => {
      if (ev?.participant_user_id && currentUser?.id && ev.participant_user_id === currentUser.id) return displayName;
      const byUser = participants.find((p) => p.user_id && p.user_id === ev?.participant_user_id);
      if (byUser) return byUser.display_name || "Học sinh";
      const byId = participants.find((p) => p.participant_identity === ev?.participant_identity);
      if (byId) return byId.display_name || (byId.is_ai ? "Cô giáo AI" : "Học sinh");
      return ev?.event_source === "ai_teacher_api" || ev?.event_source === "ai_agent" ? "Cô giáo AI" : "Học sinh";
    },
    [participants, currentUser, displayName],
  );

  // Derive the shared transcript (captions) from polled events + local system msgs.
  const captions = useMemo(() => {
    const items = [];
    for (const ev of events) {
      const p = ev.payload || {};
      if (ev.event_type === "ai_teacher_user_message" || ev.event_type === "voice_user_final") {
        const text = String(p.message || p.text || "").trim();
        if (text) items.push({ id: ev.id, speaker: "user", name: nameFor(ev), text, at: ev.created_at });
      } else if (ev.event_type === "ai_teacher_reply" || ev.event_type === "ai_voice_ready") {
        const text = String(p.answer || p.text || "").trim();
        if (text) items.push({ id: ev.id, speaker: "assistant", name: "Cô giáo AI", text, at: ev.created_at });
      }
    }
    const merged = [...items, ...systemCaptions];
    merged.sort((a, b) => String(a.at || "").localeCompare(String(b.at || "")));
    return merged.slice(-80);
  }, [events, systemCaptions, nameFor]);

  // Derive shared chat from live_chat_message events.
  const chat = useMemo(() => {
    return events
      .filter((ev) => ev.event_type === "live_chat_message")
      .map((ev) => ({
        id: ev.id,
        sender: nameFor(ev),
        text: String(ev.payload?.message || "").trim(),
      }))
      .filter((m) => m.text)
      .slice(-100);
  }, [events, nameFor]);

  const pushSystem = useCallback((text) => {
    setSystemCaptions((prev) => [
      ...prev,
      { id: `sys-${Date.now()}`, speaker: "system", text, at: new Date().toISOString() },
    ].slice(-20));
  }, []);

  // Poll participants while joined.
  useEffect(() => {
    if (phase !== "joined") return undefined;
    let alive = true;
    const load = async () => {
      try {
        const res = await listLiveSessionParticipants({ sessionId });
        if (alive) setParticipants(Array.isArray(res) ? res : res?.participants || []);
      } catch {
        /* transient */
      }
    };
    load();
    const id = setInterval(load, 5000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [phase, sessionId]);

  // Poll the shared event stream (transcript + chat + raise-hand) for everyone.
  useEffect(() => {
    if (phase !== "joined") return undefined;
    let alive = true;
    const load = async () => {
      try {
        const res = await listLiveSessionEvents({ sessionId, limit: 80, since: eventCursorRef.current });
        const list = Array.isArray(res) ? res : res?.events || [];
        if (!alive || list.length === 0) return;
        const fresh = list.filter((ev) => ev?.id && !seenEventIdsRef.current.has(ev.id));
        if (fresh.length === 0) return;
        fresh.forEach((ev) => seenEventIdsRef.current.add(ev.id));
        const last = list[list.length - 1];
        if (last?.created_at) eventCursorRef.current = last.created_at;
        setEvents((prev) => [...prev, ...fresh].slice(-300));
        if (fresh.some((ev) => ev.event_type === "live_chat_message") && panelTab !== "chat") {
          setChatUnread((n) => n + fresh.filter((ev) => ev.event_type === "live_chat_message").length);
        }
      } catch {
        /* transient */
      }
    };
    load();
    const id = setInterval(load, 1800);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [phase, sessionId, panelTab]);

  const join = useCallback(async () => {
    setError("");
    setPhase("joining");
    try {
      await joinLiveSession({ sessionId });
      setPhase("joined");
      pushSystem("Đã vào phòng. Cô giáo AI đang lắng nghe.");
    } catch (err) {
      setError(String(err?.message || err || "Không vào được phòng."));
      setPhase("prejoin");
    }
  }, [pushSystem, sessionId]);

  const leave = useCallback(async () => {
    try {
      voice.stop();
      await leaveLiveSession({ sessionId, keepalive: true });
    } catch {
      /* ignore */
    }
    setPhase("left");
  }, [sessionId, voice]);

  const sendChat = useCallback(
    async (text) => {
      try {
        await createLiveSessionEvent({ sessionId, eventType: "live_chat_message", payload: { message: text } });
      } catch {
        /* best-effort; the poller will surface it once persisted */
      }
    },
    [sessionId],
  );

  const raiseHand = useCallback(async () => {
    setHandRaised(true);
    try {
      await createLiveSessionEvent({ sessionId, eventType: "raise_hand", payload: { name: displayName } });
      pushSystem(`${displayName} đã giơ tay.`);
    } catch {
      /* ignore */
    }
    setTimeout(() => setHandRaised(false), 4000);
  }, [sessionId, displayName, pushSystem]);

  const runQuickAction = useCallback(
    (action) => {
      if (!action || typeof voice.ask !== "function") return;
      voice.ask({ message: action.message, mode: action.mode });
    },
    [voice],
  );

  const openPanel = useCallback((tab) => {
    setPanelTab(tab);
    setPanelOpen(true);
    if (tab === "chat") setChatUnread(0);
  }, []);

  const participantCount = useMemo(
    () => participants.filter((p) => !p.left_at).length,
    [participants],
  );

  // ---- pre-join ------------------------------------------------------------
  if (phase === "prejoin" || phase === "joining") {
    return (
      <main className="grid min-h-screen place-items-center bg-zinc-950 px-4 text-zinc-100">
        <div className="w-full max-w-md rounded-2xl bg-zinc-900 p-8 ring-1 ring-white/10">
          <div className="mb-6 flex items-center gap-3">
            <span className="grid h-11 w-11 place-items-center rounded-full bg-sky-500/20 text-sky-300">
              <Sparkles className="h-5 w-5" />
            </span>
            <div>
              <h1 className="text-lg font-semibold">Lớp học cùng Cô giáo AI</h1>
              <p className="text-sm text-zinc-400">Trò chuyện bằng giọng nói, rảnh tay</p>
            </div>
          </div>
          <ul className="mb-6 space-y-2 text-sm text-zinc-400">
            <li className="flex items-center gap-2"><Mic className="h-4 w-4 text-emerald-400" /> Hãy cho phép trình duyệt dùng micro</li>
            <li className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-sky-400" /> Cứ nói tự nhiên — AI tự nhận biết khi bạn nói xong</li>
            <li className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-amber-400" /> Nói chen vào để ngắt lời AI bất cứ lúc nào</li>
          </ul>
          {error ? (
            <div className="mb-4 rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-300 ring-1 ring-red-500/30">{error}</div>
          ) : null}
          <button
            type="button"
            onClick={join}
            disabled={phase === "joining"}
            className="flex w-full items-center justify-center gap-2 rounded-full bg-sky-600 px-5 py-3 font-semibold text-white transition-colors hover:bg-sky-500 disabled:opacity-60"
          >
            {phase === "joining" ? <Loader2 className="h-5 w-5 animate-spin" /> : null}
            {phase === "joining" ? "Đang vào phòng…" : "Tham gia ngay"}
          </button>
        </div>
      </main>
    );
  }

  if (phase === "left") {
    return (
      <main className="grid min-h-screen place-items-center bg-zinc-950 px-4 text-zinc-100">
        <div className="text-center">
          <h1 className="text-xl font-semibold">Bạn đã rời phòng học</h1>
          <p className="mt-2 text-sm text-zinc-400">Cảm ơn bạn đã tham gia.</p>
          <button
            type="button"
            onClick={() => { setSystemCaptions([]); setPhase("prejoin"); }}
            className="mt-6 rounded-full bg-zinc-800 px-5 py-2.5 text-sm hover:bg-zinc-700"
          >
            Vào lại
          </button>
        </div>
      </main>
    );
  }

  // ---- joined room ---------------------------------------------------------
  return (
    <main className="flex h-screen flex-col bg-zinc-950 text-zinc-100">
      <header className="flex items-center justify-between px-5 py-3">
        <div className="flex items-center gap-2 text-sm text-zinc-300">
          <span className="h-2.5 w-2.5 rounded-full bg-red-500" />
          <span className="font-medium">Đang trực tiếp</span>
        </div>
        <div className="flex items-center gap-2">
          {voice.error ? (
            <div className="rounded-full bg-red-500/10 px-3 py-1 text-xs text-red-300 ring-1 ring-red-500/30">{voice.error}</div>
          ) : null}
          <button
            type="button"
            onClick={() => setUseAvatar((v) => !v)}
            title={useAvatar ? "Chuyển sang quả cầu" : "Chuyển sang avatar"}
            className="grid h-9 w-9 place-items-center rounded-full bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
          >
            {useAvatar ? <CircleUserRound className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
          </button>
          {isHost ? (
            <button
              type="button"
              onClick={() => setTeacherOpen((v) => !v)}
              title="Bảng điều khiển giáo viên"
              className={`grid h-9 w-9 place-items-center rounded-full ${teacherOpen ? "bg-sky-600 text-white" : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"}`}
            >
              <GraduationCap className="h-4 w-4" />
            </button>
          ) : null}
        </div>
      </header>

      <div className="flex flex-1 gap-4 overflow-hidden px-4 pb-3">
        <section className="flex flex-1 flex-col gap-4">
          <div className="grid flex-1 place-items-center rounded-2xl bg-[radial-gradient(circle_at_50%_30%,rgba(56,118,189,0.12),rgba(9,9,11,0.96))] ring-1 ring-white/10">
            {useAvatar ? (
              <AiAvatar
                state={voice.state}
                level={voice.level}
                outputLevel={voice.outputLevel}
                onClick={voice.state === TURN.SPEAKING ? voice.interrupt : undefined}
              />
            ) : (
              <ConversationOrb
                state={voice.state}
                level={voice.level}
                onClick={voice.state === TURN.SPEAKING ? voice.interrupt : undefined}
              />
            )}
          </div>

          {/* Quick-action chips + raise hand */}
          <div className="flex flex-wrap items-center justify-center gap-2">
            {QUICK_ACTIONS.map((a) => (
              <button
                key={a.key}
                type="button"
                onClick={() => runQuickAction(a)}
                disabled={voice.state === TURN.THINKING}
                className="rounded-full bg-zinc-800 px-3 py-1.5 text-xs text-zinc-200 ring-1 ring-white/10 transition hover:bg-zinc-700 disabled:opacity-50"
              >
                {a.label}
              </button>
            ))}
            <button
              type="button"
              onClick={raiseHand}
              className={`inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs ring-1 transition ${handRaised ? "bg-amber-500/20 text-amber-300 ring-amber-500/40" : "bg-zinc-800 text-zinc-200 ring-white/10 hover:bg-zinc-700"}`}
            >
              <Hand className="h-3.5 w-3.5" /> Giơ tay
            </button>
          </div>

          {captionsOn ? (
            <div className="h-40 shrink-0 rounded-2xl bg-zinc-900/80 ring-1 ring-white/10">
              <CaptionsFeed items={captions} />
            </div>
          ) : null}
        </section>

        {teacherOpen && isHost ? (
          <TeacherConsole sessionId={sessionId} participants={participants} events={events} onClose={() => setTeacherOpen(false)} />
        ) : panelOpen ? (
          <SidePanel
            open={panelOpen}
            tab={panelTab}
            onTab={setPanelTab}
            onClose={() => setPanelOpen(false)}
            participants={participants}
            messages={chat}
            onSendMessage={sendChat}
          />
        ) : null}
      </div>

      <footer className="px-4 pb-5 pt-1">
        <ControlBar
          micOn={micOn}
          onToggleMic={() => setMicOn((v) => !v)}
          captionsOn={captionsOn}
          onToggleCaptions={() => setCaptionsOn((v) => !v)}
          onToggleParticipants={() => openPanel("people")}
          participantCount={participantCount}
          onToggleChat={() => openPanel("chat")}
          chatUnread={chatUnread}
          onLeave={leave}
        />
      </footer>
    </main>
  );
}
