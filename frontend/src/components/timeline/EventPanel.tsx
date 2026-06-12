"use client";

import { useEffect, useRef } from "react";

/** A motif reference used when launching a comparison from an event. */
export interface TimelineMotifRef {
  id: string | number | null;
  name: string;
  [key: string]: unknown;
}

/** A historical era badge attached to a timeline event. */
export interface TimelineEra {
  id?: string | number;
  name_vi?: string;
  color_hex?: string | null;
}

/** A single timeline event rendered on the track / detail panel. */
export interface TimelineEvent {
  id: string | number;
  name_vi: string;
  occurred_on?: string;
  description_vi?: string;
  era?: TimelineEra | null;
  motif?: TimelineMotifRef | null;
  urn?: { name?: string } | null;
}

interface EventPanelProps {
  event: TimelineEvent | null;
  onClose: () => void;
  onCompare?: (motifA: TimelineMotifRef, motifB: TimelineMotifRef) => void;
}

export default function EventPanel({ event, onClose, onCompare }: EventPanelProps) {
  const closeRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    closeRef.current?.focus();
    function onKey(e: KeyboardEvent) {
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
          {onCompare ? (
            <button
              type="button"
              onClick={() =>
                onCompare(event.motif as TimelineMotifRef, {
                  id: null,
                  name: "Chọn hoạ tiết thứ hai",
                })
              }
              className="mt-2 rounded-md border border-border px-2 py-1 text-xs hover:bg-muted focus-visible:ring-2 focus-visible:ring-primary"
            >
              So sánh với hoạ tiết khác
            </button>
          ) : null}
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
