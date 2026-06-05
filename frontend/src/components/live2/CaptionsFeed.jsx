"use client";

/**
 * CaptionsFeed — live transcript of the conversation (you + AI teacher),
 * newest at the bottom, auto-scrolls. Meet-style closed-captions look.
 */

import { useEffect, useRef } from "react";

function speakerMeta(speaker) {
  if (speaker === "assistant") return { name: "Cô giáo AI", cls: "text-sky-300" };
  if (speaker === "system") return { name: "Hệ thống", cls: "text-zinc-400" };
  return { name: "Bạn", cls: "text-emerald-300" };
}

export default function CaptionsFeed({ items = [], emptyHint = "Phụ đề sẽ hiện ở đây khi bắt đầu trò chuyện." }) {
  const endRef = useRef(null);

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
          <div key={item.id} className="text-sm leading-relaxed">
            <span className={`mr-2 font-semibold ${m.cls}`}>{name}:</span>
            <span className="text-zinc-100">{item.text}</span>
          </div>
        );
      })}
      <div ref={endRef} />
    </div>
  );
}
