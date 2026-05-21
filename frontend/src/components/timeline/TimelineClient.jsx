"use client";

import { useEffect, useRef, useState } from "react";
import { fetchTimelineEvents, logAnalyticsEvent } from "@/lib/api";
import CompareModal from "./CompareModal";
import EventPanel from "./EventPanel";
import TimelineTrack from "./TimelineTrack";

// Module-level cache keyed by query window. Survives client-side route
// changes within the same SPA session — refresh on hard reload.
const cache = new Map();
const CACHE_TTL_MS = 5 * 60 * 1000;

function cacheKey(from, to) {
  return `${from ?? ""}_${to ?? ""}`;
}

export default function TimelineClient({ from, to } = {}) {
  const [events, setEvents] = useState(() => {
    const hit = cache.get(cacheKey(from, to));
    return hit && Date.now() - hit.at < CACHE_TTL_MS ? hit.events : [];
  });
  const [meta, setMeta] = useState(() => {
    const hit = cache.get(cacheKey(from, to));
    return hit && Date.now() - hit.at < CACHE_TTL_MS
      ? hit.meta
      : { min_year: null, max_year: null };
  });
  const [loading, setLoading] = useState(() => {
    const hit = cache.get(cacheKey(from, to));
    return !(hit && Date.now() - hit.at < CACHE_TTL_MS);
  });
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [comparePair, setComparePair] = useState(null); // { a, b } or null
  const trackRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    const key = cacheKey(from, to);
    const hit = cache.get(key);
    if (hit && Date.now() - hit.at < CACHE_TTL_MS) {
      setEvents(hit.events);
      setMeta(hit.meta);
      setLoading(false);
    } else {
      setLoading(true);
      fetchTimelineEvents({ from, to })
        .then((data) => {
          if (!mounted) return;
          const evts = Array.isArray(data?.events) ? data.events : [];
          const m = data?.meta || { min_year: null, max_year: null };
          cache.set(key, { events: evts, meta: m, at: Date.now() });
          setEvents(evts);
          setMeta(m);
          setLoading(false);
        })
        .catch((err) => {
          if (!mounted) return;
          setError(err?.message || "Không tải được dòng thời gian");
          setLoading(false);
        });
    }
    // Fire one analytics event per page mount, not per cache read.
    try {
      logAnalyticsEvent({ name: "timeline_viewed", path: "/timeline" });
    } catch {
      // best-effort analytics
    }
    return () => {
      mounted = false;
    };
  }, [from, to]);

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
          onCompare={(motifA, motifB) => setComparePair({ a: motifA, b: motifB })}
        />
      ) : null}
      {comparePair ? (
        <CompareModal
          motifA={comparePair.a}
          motifB={comparePair.b}
          onClose={() => setComparePair(null)}
        />
      ) : null}
    </div>
  );
}
