"use client";

import { forwardRef, useEffect, useRef } from "react";

const TimelineTrack = forwardRef(function TimelineTrack(
  { events, meta, selectedId, onSelect },
  ref,
) {
  const trackRef = useRef(null);
  // Compose ref so parent can also reach into the DOM.
  useEffect(() => {
    if (!ref) return;
    if (typeof ref === "function") ref(trackRef.current);
    else ref.current = trackRef.current;
  }, [ref]);

  function handleKeyDown(e, idx) {
    if (e.key === "ArrowRight") {
      e.preventDefault();
      const next = events[Math.min(idx + 1, events.length - 1)];
      if (next) {
        const el = trackRef.current?.querySelector(
          `[data-event-id="${next.id}"]`,
        );
        el?.focus();
      }
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      const prev = events[Math.max(idx - 1, 0)];
      if (prev) {
        const el = trackRef.current?.querySelector(
          `[data-event-id="${prev.id}"]`,
        );
        el?.focus();
      }
    } else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect(events[idx].id);
    }
  }

  const minYear = meta?.min_year ?? 1800;
  const maxYear = meta?.max_year ?? 1950;
  const yearSpan = Math.max(1, maxYear - minYear);

  function position(year) {
    return ((year - minYear) / yearSpan) * 100;
  }

  return (
    <div
      ref={trackRef}
      role="listbox"
      aria-label="Dòng thời gian di sản"
      className="relative h-32 overflow-x-auto rounded-lg border border-border bg-muted/40 p-4"
    >
      <div
        className="absolute left-4 right-4 top-1/2 h-1 -translate-y-1/2 rounded-full bg-border"
        aria-hidden="true"
      />
      <ul className="relative z-10 flex h-full items-center" role="presentation">
        {events.map((event, idx) => {
          const year = Number((event.occurred_on || "").slice(0, 4)) || minYear;
          const left = position(year);
          const selected = event.id === selectedId;
          return (
            <li
              key={event.id}
              role="option"
              aria-selected={selected}
              aria-label={`${event.name_vi} — ${event.occurred_on}`}
              data-event-id={event.id}
              tabIndex={idx === 0 && !selectedId ? 0 : selected ? 0 : -1}
              onKeyDown={(e) => handleKeyDown(e, idx)}
              onClick={() => onSelect(event.id)}
              className={`absolute -translate-x-1/2 cursor-pointer outline-none transition focus-visible:scale-110 focus-visible:ring-4 focus-visible:ring-primary/50 ${
                selected ? "scale-110" : ""
              }`}
              style={{ left: `${left}%` }}
            >
              <div
                className="h-4 w-4 rounded-full border-2 border-background shadow"
                style={{ backgroundColor: event.era?.color_hex || "#666" }}
              />
              <span className="mt-1 block whitespace-nowrap text-xs text-muted-foreground">
                {year}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
});

export default TimelineTrack;
