"use client";

import { forwardRef, useCallback, useImperativeHandle, useRef } from "react";
import type { TimelineEra, TimelineEvent } from "./EventPanel";

/** Min/max year bounds used to position markers along the track. */
export interface TimelineMeta {
  min_year?: number | null;
  max_year?: number | null;
}

interface TimelineTrackProps {
  events: TimelineEvent[];
  meta?: TimelineMeta;
  selectedId: string | number | null;
  onSelect: (id: string | number) => void;
  /** Optional set of event ids to emphasise (e.g. from a ?entity= deep link). */
  highlightedIds?: Set<string | number>;
}

const TimelineTrack = forwardRef<HTMLDivElement, TimelineTrackProps>(
  function TimelineTrack({ events, meta, selectedId, onSelect, highlightedIds }, ref) {
    const trackRef = useRef<HTMLDivElement | null>(null);
    // Expose the underlying DOM element directly via the forwarded ref.
    // Using `useImperativeHandle` avoids the timing race that a `useEffect`
    // assignment introduces (the effect runs after render, so a parent
    // requestAnimationFrame callback can fire before the ref is populated).
    useImperativeHandle(
      ref,
      () => trackRef.current as HTMLDivElement,
      [],
    );

    const focusEvent = useCallback(
      (id: string | number) => {
        const el = trackRef.current?.querySelector<HTMLElement>(`[data-event-id="${id}"]`);
        el?.focus();
      },
      [],
    );

    function handleKeyDown(e: React.KeyboardEvent<HTMLLIElement>, idx: number) {
      if (e.key === "ArrowRight") {
        e.preventDefault();
        const next = events[Math.min(idx + 1, events.length - 1)];
        if (next) focusEvent(next.id);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        const prev = events[Math.max(idx - 1, 0)];
        if (prev) focusEvent(prev.id);
      } else if (e.key === "Home") {
        e.preventDefault();
        if (events[0]) focusEvent(events[0].id);
      } else if (e.key === "End") {
        e.preventDefault();
        const last = events[events.length - 1];
        if (last) focusEvent(last.id);
      } else if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onSelect(events[idx].id);
      }
    }

    const minYear = meta?.min_year ?? 1800;
    const maxYear = meta?.max_year ?? 1950;
    const yearSpan = Math.max(1, maxYear - minYear);

    function position(year: number) {
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
          {events.map((event: TimelineEvent, idx: number) => {
            const year = Number((event.occurred_on || "").slice(0, 4)) || minYear;
            const left = position(year);
            const selected = event.id === selectedId;
            const highlighted = highlightedIds?.has(event.id) ?? false;
            // Roving tabindex: only the selected (or first when none selected)
            // element is tabbable; the rest are focusable by arrow keys.
            const tabbable = selected || (!selectedId && idx === 0);
            return (
              <li
                key={event.id}
                role="option"
                aria-selected={selected}
                aria-label={`${event.name_vi} — ${event.occurred_on}`}
                data-event-id={event.id}
                tabIndex={tabbable ? 0 : -1}
                onKeyDown={(e) => handleKeyDown(e, idx)}
                onClick={() => onSelect(event.id)}
                className={`absolute -translate-x-1/2 cursor-pointer outline-none transition focus-visible:scale-110 focus-visible:ring-4 focus-visible:ring-primary/50 ${
                  selected ? "scale-110" : ""
                }`}
                style={{ left: `${left}%` }}
              >
                <div
                  className="h-4 w-4 rounded-full border-2 border-background shadow"
                  style={{ backgroundColor: (event.era as TimelineEra | undefined)?.color_hex || "#666" }}
                />
                {highlighted ? (
                  <span
                    className="absolute -inset-1.5 rounded-full border-2 border-primary/70"
                    aria-hidden="true"
                  />
                ) : null}
                <span className="mt-1 block whitespace-nowrap text-xs text-muted-foreground">
                  {year}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    );
  },
);

export default TimelineTrack;
