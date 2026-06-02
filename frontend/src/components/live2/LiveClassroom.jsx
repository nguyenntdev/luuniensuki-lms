"use client";

/**
 * LiveClassroom — a simple, Google-Meet / Teams-style room for the realtime AI
 * teacher. Pre-join screen -> joined room with a central AI presence orb, live
 * captions, a bottom control bar, and a slide-in participants/chat panel.
 *
 * Voice loop is hands-free (continuous mic + client VAD) via useRealtimeVoice,
 * wired to the existing working endpoints (transcribe / ai-teacher reply / tts).
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Loader2, Mic, Sparkles } from "lucide-react";

import {
  askLiveAiTeacher,
  createLiveSessionEvent,
  joinLiveSession,
  leaveLiveSession,
  listLiveSessionParticipants,
  synthesizeLiveAiTeacherVoice,
  transcribeLiveAiTeacherVoice,
} from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

import CaptionsFeed from "./CaptionsFeed";
import ControlBar from "./ControlBar";
import ConversationOrb from "./ConversationOrb";
import SidePanel from "./SidePanel";
import { TURN, useRealtimeVoice } from "./useRealtimeVoice";

export default function LiveClassroom({ sessionId }) {
  const currentUser = useAuthStore((s) => s.user);

  const [phase, setPhase] = useState("prejoin"); // prejoin | joining | joined | left
  const [error, setError] = useState("");
  const [participants, setParticipants] = useState([]);
  const [captions, setCaptions] = useState([]);
  const [chat, setChat] = useState([]);
  const [chatUnread, setChatUnread] = useState(0);

  const [micOn, setMicOn] = useState(true);
  const [captionsOn, setCaptionsOn] = useState(true);
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelTab, setPanelTab] = useState("people");

  const pushCaption = useCallback(({ speaker, text }) => {
    setCaptions((prev) =>
      [
        ...prev,
        { id: `${speaker}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`, speaker, text },
      ].slice(-80),
    );
  }, []);

  const voice = useRealtimeVoice({
    sessionId,
    enabled: phase === "joined" && micOn,
    onTranscript: pushCaption,
    transcribe: transcribeLiveAiTeacherVoice,
    askTeacher: ({ sessionId: sid, message }) =>
      askLiveAiTeacher({ sessionId: sid, message, mode: "hint-first" }),
    synthesize: synthesizeLiveAiTeacherVoice,
  });

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

  const join = useCallback(async () => {
    setError("");
    setPhase("joining");
    try {
      await joinLiveSession({ sessionId });
      setPhase("joined");
      pushCaption({ speaker: "system", text: "Đã vào phòng. Cô giáo AI đang lắng nghe." });
    } catch (err) {
      setError(String(err?.message || err || "Không vào được phòng."));
      setPhase("prejoin");
    }
  }, [pushCaption, sessionId]);

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
      const optimistic = {
        id: `c-${Date.now()}`,
        sender: currentUser?.display_name || "Bạn",
        text,
      };
      setChat((prev) => [...prev, optimistic]);
      try {
        await createLiveSessionEvent({
          sessionId,
          eventType: "live_chat_message",
          payload: { message: text },
        });
      } catch {
        /* keep optimistic message */
      }
    },
    [currentUser?.display_name, sessionId],
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
            <div className="mb-4 rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-300 ring-1 ring-red-500/30">
              {error}
            </div>
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
            onClick={() => {
              setCaptions([]);
              setPhase("prejoin");
            }}
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
        {voice.error ? (
          <div className="rounded-full bg-red-500/10 px-3 py-1 text-xs text-red-300 ring-1 ring-red-500/30">
            {voice.error}
          </div>
        ) : null}
      </header>

      <div className="flex flex-1 gap-4 overflow-hidden px-4 pb-3">
        {/* Stage */}
        <section className="flex flex-1 flex-col gap-4">
          <div className="grid flex-1 place-items-center rounded-2xl bg-[radial-gradient(circle_at_50%_30%,rgba(56,118,189,0.12),rgba(9,9,11,0.96))] ring-1 ring-white/10">
            <ConversationOrb
              state={voice.state}
              level={voice.level}
              onClick={voice.state === TURN.SPEAKING ? voice.interrupt : undefined}
            />
          </div>

          {captionsOn ? (
            <div className="h-40 shrink-0 rounded-2xl bg-zinc-900/80 ring-1 ring-white/10">
              <CaptionsFeed items={captions} />
            </div>
          ) : null}
        </section>

        {/* Side panel */}
        {panelOpen ? (
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
