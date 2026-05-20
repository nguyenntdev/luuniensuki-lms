"use client";

import { useEffect, useRef, useState } from "react";
import { fetchTimelineEvents, logAnalyticsEvent } from "@/lib/api";
import EventPanel from "./EventPanel";
import TimelineTrack from "./TimelineTrack";

export default function TimelineClient() {
  const [events, setEvents] = useState([]);
  const [meta, setMeta] = useState({ min_year: null, max_year: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const trackRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    fetchTimelineEvents()
      .then((data) => {
        if (!mounted) return;
        setEvents(Array.isArray(data?.events) ? data.events : []);
        setMeta(data?.meta || { min_year: null, max_year: null });
        setLoading(false);
        try {
          logAnalyticsEvent({ name: "timeline_viewed", path: "/timeline" });
        } catch {
          // best-effort analytics
        }
      })
      .catch((err) => {
        if (!mounted) return;
        setError(err?.message || "Không tải được dòng thời gian");
        setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const selectedEvent = events.find((e) => e.id === selectedId) || null;

  if (loading) {
    return (
      <div className="px-6 py-12 text-sm text-muted-foreground" role="status">
        Đang tải dòng thời gian…
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="px-6 py-12 text-sm text-destructive"
        role="alert"
        aria-live="assertive"
      >
        {error}
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="px-6 py-12 text-sm text-muted-foreground">
        Chưa có sự kiện lịch sử nào.
      </div>
    );
  }

  return (
    <div id="timeline-events" className="relative px-6 py-8">
      <TimelineTrack
        ref={trackRef}
        events={events}
        meta={meta}
        selectedId={selectedId}
        onSelect={(id) => setSelectedId(id)}
      />
      {selectedEvent ? (
        <EventPanel
          event={selectedEvent}
          onClose={() => {
            setSelectedId(null);
            // Return focus to the marker that was open.
            requestAnimationFrame(() => {
              const el = trackRef.current?.querySelector(
                `[data-event-id="${selectedEvent.id}"]`,
              );
              if (el) el.focus();
            });
          }}
        />
      ) : null}
    </div>
  );
}
