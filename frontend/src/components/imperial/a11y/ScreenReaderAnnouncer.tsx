"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  subscribeScreenReaderAnnouncements,
  announceToScreenReader,
  announceMapNavigation,
  announceMarkerSelection,
  announceGameFeedback,
  type ScreenReaderAnnouncement,
  type ScreenReaderPoliteness,
  type MapNavigationAnnouncementDetails,
  type MarkerSelectionDetails,
  type GameFeedbackDetails,
} from "@/lib/imperial/a11y-utils";

export interface ScreenReaderAnnouncerProps {
  /** Optional declarative announcement message */
  announcement?: string;
  /** Politeness level if using declarative announcement */
  politeness?: ScreenReaderPoliteness;
  /** Delay in milliseconds before clearing the live region to allow repeat announcements */
  clearDelay?: number;
  /** Optional ID for testing or reference */
  id?: string;
}

/**
 * ScreenReaderAnnouncer: Accessible ARIA Live Region component.
 *
 * Provides dedicated Polite and Assertive ARIA live regions for announcing:
 * - Aerial Map navigation (pan, zoom, fit, layer toggles)
 * - Monument marker selections (names, Han-Nom titles, historical conditions)
 * - Gamified learning feedback (correct/incorrect answers, XP, streaks, level-ups)
 *
 * Complies with WCAG 2.2 AA (Success Criterion 4.1.3: Status Messages).
 */
export default function ScreenReaderAnnouncer({
  announcement,
  politeness = "polite",
  clearDelay = 6000,
  id = "imperial-live-announcer",
}: ScreenReaderAnnouncerProps) {
  const [politeText, setPoliteText] = useState<string>("");
  const [assertiveText, setAssertiveText] = useState<string>("");

  const politeTimerRef = useRef<NodeJS.Timeout | null>(null);
  const assertiveTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Subscribe to programmatic announcements from a11y-utils bus
  useEffect(() => {
    const unsubscribe = subscribeScreenReaderAnnouncements(
      (item: ScreenReaderAnnouncement) => {
        if (item.politeness === "assertive") {
          if (assertiveTimerRef.current) clearTimeout(assertiveTimerRef.current);
          setAssertiveText(item.message);
          assertiveTimerRef.current = setTimeout(() => {
            setAssertiveText("");
          }, clearDelay);
        } else {
          if (politeTimerRef.current) clearTimeout(politeTimerRef.current);
          setPoliteText(item.message);
          politeTimerRef.current = setTimeout(() => {
            setPoliteText("");
          }, clearDelay);
        }
      },
    );

    return () => {
      unsubscribe();
      if (politeTimerRef.current) clearTimeout(politeTimerRef.current);
      if (assertiveTimerRef.current) clearTimeout(assertiveTimerRef.current);
    };
  }, [clearDelay]);

  // Handle direct declarative prop updates
  useEffect(() => {
    if (!announcement) return;

    if (politeness === "assertive") {
      if (assertiveTimerRef.current) clearTimeout(assertiveTimerRef.current);
      setAssertiveText(announcement);
      assertiveTimerRef.current = setTimeout(() => {
        setAssertiveText("");
      }, clearDelay);
    } else {
      if (politeTimerRef.current) clearTimeout(politeTimerRef.current);
      setPoliteText(announcement);
      politeTimerRef.current = setTimeout(() => {
        setPoliteText("");
      }, clearDelay);
    }
  }, [announcement, politeness, clearDelay]);

  return (
    <div
      id={id}
      className="sr-only"
      aria-hidden="false"
      data-testid="imperial-screen-reader-announcer"
    >
      {/* Polite Live Region: Status, map navigation, marker details */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        data-testid="live-region-polite"
      >
        {politeText}
      </div>

      {/* Assertive Live Region: Urgent errors, quiz failures, timers */}
      <div
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        data-testid="live-region-assertive"
      >
        {assertiveText}
      </div>
    </div>
  );
}

/**
 * Convenient React Hook for triggering accessible announcements from any imperial component.
 */
export function useScreenReaderAnnouncer() {
  const announce = useCallback(
    (message: string, politeness: ScreenReaderPoliteness = "polite") => {
      announceToScreenReader(message, politeness);
    },
    [],
  );

  const announceMap = useCallback(
    (
      action: "pan" | "zoom_in" | "zoom_out" | "fit" | "scale_1to1" | "zone_filter" | "toggle_labels",
      details?: MapNavigationAnnouncementDetails,
    ) => {
      announceMapNavigation(action, details);
    },
    [],
  );

  const announceMarker = useCallback(
    (details: MarkerSelectionDetails) => {
      announceMarkerSelection(details);
    },
    [],
  );

  const announceFeedback = useCallback(
    (feedback: GameFeedbackDetails) => {
      announceGameFeedback(feedback);
    },
    [],
  );

  return {
    announce,
    announceMap,
    announceMarker,
    announceFeedback,
  };
}
