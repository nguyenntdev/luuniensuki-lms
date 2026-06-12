"use client";

/**
 * ConversationOrb — the central "AI presence" visual that reflects the turn
 * state: idle / listening (pulses with mic level) / thinking (spinner) /
 * speaking (animated rings). Purely presentational.
 */

import { TURN } from "./useRealtimeVoice";
import type { TurnState } from "./useRealtimeVoice";
type OrbColor = "zinc" | "emerald" | "amber" | "sky";

interface StateMeta {
  label: string;
  sub: string;
  color: OrbColor;
}

const STATE_META: Record<TurnState, StateMeta> = {
  [TURN.IDLE]: { label: "Sẵn sàng", sub: "Nhấn để bắt đầu trò chuyện", color: "zinc" },
  [TURN.LISTENING]: { label: "Đang nghe…", sub: "Hãy nói, cô giáo AI đang lắng nghe", color: "emerald" },
  [TURN.THINKING]: { label: "Đang suy nghĩ…", sub: "Cô giáo đang soạn câu trả lời", color: "amber" },
  [TURN.SPEAKING]: { label: "Đang trả lời…", sub: "Nói chen vào để ngắt lời", color: "sky" },
};

const COLOR: Record<OrbColor, { ring: string; glow: string; text: string; dot: string }> = {
  zinc: { ring: "ring-zinc-600/40", glow: "bg-zinc-500/20", text: "text-zinc-300", dot: "bg-zinc-400" },
  emerald: { ring: "ring-emerald-400/50", glow: "bg-emerald-500/25", text: "text-emerald-300", dot: "bg-emerald-400" },
  amber: { ring: "ring-amber-400/50", glow: "bg-amber-500/25", text: "text-amber-300", dot: "bg-amber-400" },
  sky: { ring: "ring-sky-400/50", glow: "bg-sky-500/25", text: "text-sky-300", dot: "bg-sky-400" },
};

interface ConversationOrbProps {
  state: TurnState;
  level?: number;
  onClick?: () => void;
}

export default function ConversationOrb({ state, level = 0, onClick }: ConversationOrbProps) {
  const meta = STATE_META[state] || STATE_META[TURN.IDLE];
  const c = COLOR[meta.color];
  // Scale the orb a touch with mic level while listening.
  const scale = state === TURN.LISTENING ? 1 + Math.min(0.18, level * 0.18) : 1;

  return (
    <div className="flex flex-col items-center justify-center gap-5 select-none">
      <button
        type="button"
        onClick={onClick}
        className="relative grid place-items-center outline-none"
        aria-label={meta.label}
      >
        {/* outer glow */}
        <span
          className={`absolute h-44 w-44 rounded-full blur-2xl transition-opacity ${c.glow} ${
            state === TURN.IDLE ? "opacity-40" : "opacity-90"
          }`}
        />
        {/* speaking rings */}
        {state === TURN.SPEAKING ? (
          <>
            <span className={`absolute h-40 w-40 animate-ping rounded-full ${c.glow}`} />
            <span className={`absolute h-52 w-52 animate-pulse rounded-full ring-2 ${c.ring}`} />
          </>
        ) : null}
        {/* core */}
        <span
          className={`relative grid h-32 w-32 place-items-center rounded-full bg-[radial-gradient(circle_at_30%_25%,rgba(255,255,255,0.12),rgba(9,9,11,0.9))] ring-2 ${c.ring} transition-transform`}
          style={{ transform: `scale(${scale})` }}
        >
          {state === TURN.THINKING ? (
            <span className="h-8 w-8 animate-spin rounded-full border-2 border-amber-300/30 border-t-amber-300" />
          ) : (
            <span className={`h-5 w-5 rounded-full ${c.dot} ${state === TURN.LISTENING ? "animate-pulse" : ""}`} />
          )}
        </span>
      </button>

      <div className="text-center">
        <div className={`text-lg font-semibold ${c.text}`}>{meta.label}</div>
        <div className="mt-1 text-xs text-zinc-400">{meta.sub}</div>
      </div>

      {/* mic level meter */}
      <div className="h-1.5 w-48 overflow-hidden rounded-full bg-zinc-800">
        <div
          className={`h-full rounded-full transition-[width] duration-75 ${c.dot}`}
          style={{ width: `${Math.round(Math.min(1, level) * 100)}%` }}
        />
      </div>
    </div>
  );
}
