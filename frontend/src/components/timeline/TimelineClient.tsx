"use client";

import { useEffect, useRef, useState } from "react";
import {
  fetchTimelineEvents,
  getHistoryEntityById,
  getHistoryEntityBySlug,
  getHistoryEvents,
  logAnalyticsEvent,
  type HistoryEventItem,
} from "@/lib/api";
import { deburr, entityName, type HistoryEntity } from "@/lib/history";
import CompareModal from "./CompareModal";
import EventPanel from "./EventPanel";
import type { TimelineEvent, TimelineMotifRef } from "./EventPanel";
import type { TimelineMeta } from "./TimelineTrack";
import TimelineTrack from "./TimelineTrack";

/** Response payload of the timeline events endpoint. */
interface TimelineResponse {
  events?: TimelineEvent[];
  meta?: TimelineMeta;
}

/** A cached query window result. */
interface CacheEntry {
  events: TimelineEvent[];
  meta: TimelineMeta;
  at: number;
}

type YearBound = number | string | undefined;

interface TimelineClientProps {
  from?: YearBound;
  to?: YearBound;
  /** Optional entity id or slug from `?entity=` — deep-links to relevant events. */
  entity?: string | null;
}

// Module-level cache keyed by query window. Survives client-side route
// changes within the same SPA session — refresh on hard reload.
const cache = new Map<string, CacheEntry>();
const CACHE_TTL_MS = 5 * 60 * 1000;

function cacheKey(from: YearBound, to: YearBound): string {
  return `${from ?? ""}_${to ?? ""}`;
}

export default function TimelineClient({ from, to, entity }: TimelineClientProps = {}) {
  const [events, setEvents] = useState<TimelineEvent[]>(() => {
    const hit = cache.get(cacheKey(from, to));
    return hit && Date.now() - hit.at < CACHE_TTL_MS ? hit.events : [];
  });
  const [meta, setMeta] = useState<TimelineMeta>(() => {
    const hit = cache.get(cacheKey(from, to));
    return hit && Date.now() - hit.at < CACHE_TTL_MS
      ? hit.meta
      : { min_year: null, max_year: null };
  });
  const [loading, setLoading] = useState<boolean>(() => {
    const hit = cache.get(cacheKey(from, to));
    return !(hit && Date.now() - hit.at < CACHE_TTL_MS);
  });
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | number | null>(null);
  const [comparePair, setComparePair] = useState<{ a: TimelineMotifRef; b: TimelineMotifRef } | null>(null);
  const [highlightedIds, setHighlightedIds] = useState<Set<string | number>>(new Set());
  const [entityNote, setEntityNote] = useState<string | null>(null);
  const [matchKeys, setMatchKeys] = useState<Set<string> | null>(null);
  const [matchedHistoryNames, setMatchedHistoryNames] = useState<Set<string>>(new Set());
  const [entityLabel, setEntityLabel] = useState<string | null>(null);
  const trackRef = useRef<HTMLDivElement | null>(null);

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
          const d = data as TimelineResponse | null | undefined;
          const evts = Array.isArray(d?.events) ? (d as TimelineResponse).events! : [];
          const m = d?.meta || { min_year: null, max_year: null };
          cache.set(key, { events: evts, meta: m, at: Date.now() });
          setEvents(evts);
          setMeta(m);
          setLoading(false);
        })
        .catch((err) => {
          if (!mounted) return;
          setError((err as { message?: string })?.message || "Không tải được dòng thời gian");
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

  // Resolve the ?entity= deep link into search keys + matched history events.
  useEffect(() => {
    if (!entity) {
      setMatchKeys(null);
      setMatchedHistoryNames(new Set());
      setEntityLabel(null);
      return;
    }
    let mounted = true;
    const keys = new Set<string>();
    const addKey = (value: unknown) => {
      const d = deburr(value);
      if (d) keys.add(d);
    };
    addKey(entity);
    (async () => {
      let entityObj: HistoryEntity | null = null;
      try {
        const isUuid =
          /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
            entity,
          );
        const raw = isUuid
          ? await getHistoryEntityById(entity)
          : await getHistoryEntityBySlug(entity);
        entityObj = (raw as HistoryEntity | null | undefined) || null;
      } catch {
        entityObj = null;
      }
      if (!mounted) return;
      if (entityObj) {
        addKey(entityObj.name_vi);
        addKey(entityObj.name_en);
        addKey(entityObj.slug);
        setEntityLabel(entityName(entityObj) || entity);
      } else {
        setEntityLabel(entity);
      }

      let historyEvents: HistoryEventItem[] = [];
      try {
        const res = await getHistoryEvents();
        historyEvents = Array.isArray(res?.items) ? res.items : [];
      } catch {
        historyEvents = [];
      }
      if (!mounted) return;
      const matchedNames = new Set<string>();
      for (const ev of historyEvents) {
        const hay = deburr(
          `${ev.name_vi || ""} ${ev.slug || ""} ${ev.description_vi || ""} ${ev.name_en || ""}`,
        );
        let matched = false;
        for (const k of keys) {
          if (k && hay.includes(k)) {
            matched = true;
            break;
          }
        }
        if (matched) {
          const dn = deburr(ev.name_vi);
          if (dn) matchedNames.add(dn);
        }
      }
      if (!mounted) return;
      setMatchKeys(keys);
      setMatchedHistoryNames(matchedNames);
    })();
    return () => {
      mounted = false;
    };
  }, [entity]);

  // Highlight/select timeline events that mention the deep-linked entity.
  useEffect(() => {
    if (!entity || !matchKeys || events.length === 0) {
      setHighlightedIds(new Set());
      if (entity) {
        setEntityNote(entityLabel ? `Không tìm thấy sự kiện liên quan đến “${entityLabel}”.` : null);
      }
      return;
    }
    const matched = new Set<string | number>();
    for (const ev of events) {
      const hay = deburr(`${ev.name_vi || ""} ${ev.description_vi || ""}`);
      let matchedDirect = false;
      for (const k of matchKeys) {
        if (k && hay.includes(k)) {
          matchedDirect = true;
          break;
        }
      }
      const nameMatch = matchedHistoryNames.has(deburr(ev.name_vi));
      if (matchedDirect || nameMatch) matched.add(ev.id);
    }
    setHighlightedIds(matched);
    if (matched.size > 0) {
      const first = events.find((e) => matched.has(e.id));
      if (first) setSelectedId(first.id);
      setEntityNote(
        `Có ${matched.size} sự kiện liên quan đến “${entityLabel || entity}”.`,
      );
    } else {
      setEntityNote(
        `Không tìm thấy sự kiện liên quan đến “${entityLabel || entity}”.`,
      );
    }
  }, [entity, entityLabel, events, matchKeys, matchedHistoryNames]);

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
        highlightedIds={highlightedIds}
        onSelect={(id) => setSelectedId(id)}
      />
      {entityNote ? (
        <p
          role="status"
          className="mt-4 rounded-md border border-border/70 bg-secondary/40 px-4 py-2 text-xs text-muted-foreground"
        >
          {entityNote}
        </p>
      ) : null}
      {selectedEvent ? (
        <EventPanel
          event={selectedEvent}
          onClose={() => {
            setSelectedId(null);
            // Return focus to the marker that was open.
            requestAnimationFrame(() => {
              const el = trackRef.current?.querySelector<HTMLElement>(
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
