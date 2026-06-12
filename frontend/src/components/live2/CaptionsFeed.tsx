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
      <div className="flex h-full items-center justify-center px-6 text-center text-sm text-zinc-500">
        {emptyHint}
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-2 overflow-y-auto px-4 py-3">
      {items.map((item) => {
        const m = speakerMeta(item.speaker);
        const name = item.name || m.name;
        return (
          <div
            key={item.id}
            className={`text-sm leading-relaxed ${item.streaming ? "opacity-80" : ""}`}
          >
            <span className={`mr-2 font-semibold ${m.cls}`}>{name}:</span>
            <span className="text-zinc-100">{item.text}</span>
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
