"use client";

/**
 * SidePanel — Meet/Teams style slide-in right panel with two tabs:
 * Participants and Chat. Presentational; parent supplies data + handlers.
 */

import { useState } from "react";
import { Send, X } from "lucide-react";

/** A participant row as supplied by the parent (subset of the API shape). */
export interface SidePanelParticipant {
  id?: string | number;
  participant_identity?: string | null;
  display_name?: string | null;
  name?: string | null;
  role?: string | null;
  is_ai?: boolean;
}

/** A chat message rendered in the chat tab. */
export interface SidePanelMessage {
  id: string | number;
  sender?: string | null;
  text: string;
}

type PanelTab = "people" | "chat";

interface SidePanelProps {
  open: boolean;
  tab: PanelTab | string;
  onTab: (tab: PanelTab) => void;
  onClose: () => void;
  participants?: SidePanelParticipant[];
  messages?: SidePanelMessage[];
  onSendMessage?: (text: string) => void;
}

function roleLabel(role?: string | null): string {
  if (role === "host") return "Chủ phòng";
  if (role === "cohost") return "Đồng chủ phòng";
  if (role === "ai_teacher") return "Cô giáo AI";
  return "Học viên";
}

function Avatar({ name, ai }: { name?: string | null; ai?: boolean }) {
  const initial = (name || "?").trim().charAt(0).toUpperCase();
  return (
    <span
      className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-sm font-semibold ${
        ai ? "bg-sky-500/20 text-sky-300" : "bg-emerald-500/20 text-emerald-300"
      }`}
    >
      {ai ? "AI" : initial}
    </span>
  );
}

export default function SidePanel({
  open,
  tab,
  onTab,
  onClose,
  participants = [],
  messages = [],
  onSendMessage,
}: SidePanelProps) {
  const [draft, setDraft] = useState("");

  if (!open) return null;

  const submit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text) return;
    onSendMessage?.(text);
    setDraft("");
  };

  return (
    <aside className="flex h-full w-full max-w-sm flex-col rounded-2xl bg-zinc-900/95 ring-1 ring-white/10">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <div className="flex gap-1 rounded-lg bg-zinc-800 p-1 text-sm">
          <button
            type="button"
            onClick={() => onTab("people")}
            className={`rounded-md px-3 py-1 ${tab === "people" ? "bg-white text-zinc-900" : "text-zinc-300"}`}
          >
            Người tham gia
          </button>
          <button
            type="button"
            onClick={() => onTab("chat")}
            className={`rounded-md px-3 py-1 ${tab === "chat" ? "bg-white text-zinc-900" : "text-zinc-300"}`}
          >
            Trò chuyện
          </button>
        </div>
        <button type="button" onClick={onClose} aria-label="Đóng" className="rounded-full p-1.5 text-zinc-400 hover:bg-white/10">
          <X className="h-4 w-4" />
        </button>
      </div>

      {tab === "people" ? (
        <div className="flex-1 space-y-1 overflow-y-auto px-3 py-3">
          {participants.length === 0 ? (
            <p className="px-2 py-6 text-center text-sm text-zinc-500">Chưa có ai trong phòng.</p>
          ) : (
            participants.map((p) => {
              const ai = p.role === "ai_teacher" || p.is_ai;
              return (
                <div key={p.id || p.participant_identity} className="flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-white/5">
                  <Avatar name={p.display_name || p.name} ai={ai} />
                  <div className="min-w-0">
                    <div className="truncate text-sm text-zinc-100">
                      {p.display_name || p.name || "Người dùng"}
                    </div>
                    <div className="text-xs text-zinc-500">{roleLabel(p.role)}</div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      ) : (
        <>
          <div className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
            {messages.length === 0 ? (
              <p className="py-6 text-center text-sm text-zinc-500">Chưa có tin nhắn.</p>
            ) : (
              messages.map((m) => (
                <div key={m.id} className="text-sm">
                  <span className="mr-2 font-semibold text-zinc-300">{m.sender || "Người dùng"}:</span>
                  <span className="text-zinc-100">{m.text}</span>
                </div>
              ))
            )}
          </div>
          <form onSubmit={submit} className="flex items-center gap-2 border-t border-white/10 p-3">
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Nhập tin nhắn…"
              className="flex-1 rounded-full bg-zinc-800 px-4 py-2 text-sm text-zinc-100 outline-none placeholder:text-zinc-500 focus:ring-2 focus:ring-sky-500/40"
            />
            <button type="submit" aria-label="Gửi" className="grid h-9 w-9 place-items-center rounded-full bg-sky-600 text-white hover:bg-sky-500">
              <Send className="h-4 w-4" />
            </button>
          </form>
        </>
      )}
    </aside>
  );
}
