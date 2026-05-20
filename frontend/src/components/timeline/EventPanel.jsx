"use client";

import { useEffect, useRef } from "react";

export default function EventPanel({ event, onClose }) {
  const closeRef = useRef(null);

  useEffect(() => {
    closeRef.current?.focus();
    function onKey(e) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (!event) return null;

  return (
    <aside
      className="mt-6 rounded-lg border border-border bg-card p-6 shadow-md"
      role="dialog"
      aria-modal="false"
      aria-labelledby={`event-${event.id}-title`}
      aria-live="polite"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p
            className="text-xs font-semibold uppercase tracking-wide"
            style={{ color: event.era?.color_hex || "var(--muted-foreground)" }}
          >
            {event.era?.name_vi}
          </p>
          <h2
            id={`event-${event.id}-title`}
            className="mt-1 text-xl font-bold"
          >
            {event.name_vi}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {event.occurred_on}
          </p>
        </div>
        <button
          ref={closeRef}
          type="button"
          onClick={onClose}
          aria-label="Đóng panel"
          className="rounded-md border border-border px-3 py-1 text-sm hover:bg-muted focus-visible:ring-2 focus-visible:ring-primary"
        >
          Đóng
        </button>
      </div>
      <p className="mt-4 text-sm leading-relaxed">{event.description_vi}</p>
      {event.motif ? (
        <div className="mt-4 rounded-md border border-border bg-muted/40 p-3">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">
            Hoạ tiết liên quan
          </p>
          <p className="font-semibold">{event.motif.name}</p>
        </div>
      ) : null}
      {event.urn ? (
        <div className="mt-3 rounded-md border border-border bg-muted/40 p-3">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">
            Đỉnh liên quan
          </p>
          <p className="font-semibold">{event.urn.name}</p>
        </div>
      ) : null}
    </aside>
  );
}
