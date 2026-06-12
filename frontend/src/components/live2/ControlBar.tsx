"use client";

/**
 * ControlBar — Google Meet / Teams style bottom control bar. Round icon
 * buttons with clear on/off states and tooltips. Purely presentational; the
 * parent wires the handlers.
 */

import type { ReactNode } from "react";
import {
  Captions,
  CaptionsOff,
  Mic,
  MicOff,
  MessageSquare,
  PhoneOff,
  Users,
} from "lucide-react";

interface ControlButtonProps {
  active?: boolean;
  danger?: boolean;
  onClick?: () => void;
  title: string;
  children: ReactNode;
  badge?: ReactNode;
}

function ControlButton({ active, danger, onClick, title, children, badge }: ControlButtonProps) {
  const base =
    "relative grid h-12 w-12 place-items-center rounded-full transition-colors outline-none focus-visible:ring-2 focus-visible:ring-white/40";
  const tone = danger
    ? "bg-red-600 text-white hover:bg-red-500"
    : active
      ? "bg-white text-zinc-900 hover:bg-zinc-200"
      : "bg-zinc-700/80 text-zinc-100 hover:bg-zinc-600";
  return (
    <button type="button" onClick={onClick} title={title} aria-label={title} className={`${base} ${tone}`}>
      {children}
      {badge ? (
        <span className="absolute -right-1 -top-1 grid h-5 min-w-5 place-items-center rounded-full bg-sky-500 px-1 text-[10px] font-semibold text-white">
          {badge}
        </span>
      ) : null}
    </button>
  );
}

interface ControlBarProps {
  micOn?: boolean;
  onToggleMic?: () => void;
  captionsOn?: boolean;
  onToggleCaptions?: () => void;
  onToggleParticipants?: () => void;
  participantCount?: number;
  onToggleChat?: () => void;
  chatUnread?: number;
  onLeave?: () => void;
}

export default function ControlBar({
  micOn,
  onToggleMic,
  captionsOn,
  onToggleCaptions,
  onToggleParticipants,
  participantCount = 0,
  onToggleChat,
  chatUnread = 0,
  onLeave,
}: ControlBarProps) {
  return (
    <div className="flex items-center justify-center gap-3 rounded-2xl bg-zinc-900/90 px-4 py-3 shadow-lg ring-1 ring-white/10 backdrop-blur">
      <ControlButton active={micOn} onClick={onToggleMic} title={micOn ? "Tắt micro" : "Bật micro"}>
        {micOn ? <Mic className="h-5 w-5" /> : <MicOff className="h-5 w-5" />}
      </ControlButton>

      <ControlButton active={captionsOn} onClick={onToggleCaptions} title={captionsOn ? "Ẩn phụ đề" : "Hiện phụ đề"}>
        {captionsOn ? <Captions className="h-5 w-5" /> : <CaptionsOff className="h-5 w-5" />}
      </ControlButton>

      <ControlButton onClick={onToggleParticipants} title="Người tham gia" badge={participantCount || null}>
        <Users className="h-5 w-5" />
      </ControlButton>

      <ControlButton onClick={onToggleChat} title="Trò chuyện" badge={chatUnread || null}>
        <MessageSquare className="h-5 w-5" />
      </ControlButton>

      <div className="mx-1 h-8 w-px bg-white/10" />

      <ControlButton danger onClick={onLeave} title="Rời phòng">
        <PhoneOff className="h-5 w-5" />
      </ControlButton>
    </div>
  );
}
