"use client";

/**
 * CaptionsFeed — live transcript of the conversation (you + AI teacher),
 * newest at the bottom, auto-scrolls. Meet-style closed-captions look.
 */

import { useEffect, useRef } from "react";

/** A speaker role in the live transcript. */
type Speaker = "user" | "assistant" | "system";

/** A single caption/transcript line rendered in the feed. */
export interface CaptionItem {
  id: string | number;
  speaker?: Speaker | string;
  /** Optional override for the displayed speaker name. */
  name?: string | null;
  text: string;
  /** When true, the line is still streaming in (renders a blinking cursor). */
  streaming?: boolean;
  provider_mode?: "live" | "fallback" | "guardrail" | "mock" | "demo" | string;
  guardrail_status?: string;
  is_fallback?: boolean;
  is_synthetic?: boolean;
  fallback_indicator?: string | null;
}

interface CaptionsFeedProps {
  items?: CaptionItem[];
  emptyHint?: string;
}

function speakerMeta(speaker: CaptionItem["speaker"]): { name: string; cls: string } {
  if (speaker === "assistant") return { name: "Cô giáo AI", cls: "text-sky-300" };
  if (speaker === "system") return { name: "Hệ thống", cls: "text-zinc-400" };
  return { name: "Bạn", cls: "text-emerald-300" };
}

function renderProvenanceBadge(item: CaptionItem) {
  if (item.speaker !== "assistant") return null;

  if (item.is_fallback || item.provider_mode === "fallback" || item.provider_mode === "mock" || item.provider_mode === "demo") {
    return (
      <span
        className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-500/20 text-amber-300 ring-1 ring-amber-500/30"
        title={item.fallback_indicator || "Phản hồi dự phòng ngoại tuyến"}
        aria-label="Phản hồi dự phòng ngoại tuyến"
      >
        Dự phòng
      </span>
    );
  }

  if (item.provider_mode === "guardrail" || item.guardrail_status === "blocked") {
    return (
      <span
        className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-rose-500/20 text-rose-300 ring-1 ring-rose-500/30"
        title="Nội dung được lọc bởi bộ kiểm duyệt an toàn"
        aria-label="Nội dung lọc bởi kiểm duyệt an toàn"
      >
        Kiểm duyệt
      </span>
    );
  }

  if (item.provider_mode === "live") {
    return (
      <span
        className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-500/20 text-emerald-300 ring-1 ring-emerald-500/30"
        title="AI trực tiếp phản hồi"
        aria-label="AI trực tiếp"
      >
        AI Live
      </span>
    );
  }

  return null;
}

export default function CaptionsFeed({
  items = [],
  emptyHint = "Phụ đề sẽ hiện ở đây khi bắt đầu trò chuyện.",
}: CaptionsFeedProps) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [items]);

  if (!items.length) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="flex h-full items-center justify-center px-6 text-center text-sm text-zinc-400 contrast-more:text-zinc-200"
      >
        {emptyHint}
      </div>
    );
  }

  return (
    <div
      role="log"
      aria-live="polite"
      aria-atomic="false"
      aria-relevant="additions text"
      aria-label="Phụ đề đối thoại trực tiếp"
      tabIndex={0}
      className="flex h-full flex-col gap-2 overflow-y-auto px-4 py-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1 rounded-lg contrast-more:border contrast-more:border-border"
    >
      {items.map((item) => {
        const m = speakerMeta(item.speaker);
        const name = item.name || m.name;
        return (
          <div
            key={item.id}
            className={`text-sm leading-relaxed ${item.streaming ? "opacity-80" : ""}`}
          >
            <span className={`mr-2 font-semibold ${m.cls} contrast-more:underline`}>{name}:</span>
            {renderProvenanceBadge(item)}
            <span className="text-zinc-100 contrast-more:text-white font-normal ml-1">{item.text}</span>
            {item.streaming ? (
              <span
                className="ml-1 inline-block h-3 w-1.5 translate-y-0.5 animate-pulse rounded-sm bg-zinc-300 align-middle"
                aria-hidden="true"
              />
            ) : null}
          </div>
        );
      })}
      <div ref={endRef} />
    </div>
  );
}
