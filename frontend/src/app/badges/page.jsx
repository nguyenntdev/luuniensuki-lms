"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { getAllBadges, getMyBadges } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export default function BadgesPage() {
  const token = useAuthStore((s) => s.accessToken);
  const fetchMe = useAuthStore((s) => s.fetchMe);

  const [allBadges, setAllBadges] = useState([]);
  const [earnedBadges, setEarnedBadges] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (token) fetchMe();
  }, [token, fetchMe]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        // Always fetch all badges
        const badgesRes = await getAllBadges();
        if (cancelled) return;
        setAllBadges(badgesRes);

        // If logged in, fetch earned badges
        if (token) {
          const earnedRes = await getMyBadges({ token });
          if (!cancelled) setEarnedBadges(earnedRes);
        } else {
          setEarnedBadges([]);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [token]);

  // Merge badges to determine status
  const badges = useMemo(() => {
    // Create a map of earned badges for quick lookup
    const earnedMap = new Map();
    earnedBadges.forEach((ub) => {
      // ub is UserBadgeOut { badge: BadgeOut, earned_at: ... }
      if (ub.badge && ub.badge.slug) {
        earnedMap.set(ub.badge.slug, ub);
      }
    });

    return allBadges.map((badge) => {
      const earnedData = earnedMap.get(badge.slug);
      return {
        ...badge,
        earned: !!earnedData,
        earnedAt: earnedData?.earned_at,
      };
    });
  }, [allBadges, earnedBadges]);

  if (!token) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-10">
        <div className="rounded-xl border bg-card p-6">
          <h1 className="text-xl font-display font-semibold">Badges</h1>
          <p className="mt-2 text-sm text-muted-foreground">Please sign in to view your earned badges.</p>
          <div className="mt-4">
            <Link href="/login" className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">
              Login
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-display font-semibold text-foreground">Badges Gallery</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Collect badges by completing lessons and quizzes.
          </p>
        </div>
        <div className="flex gap-3">
          <Link href="/profile" className="text-sm font-medium text-primary hover:text-primary/80">
            Dashboard →
          </Link>
        </div>
      </div>

      {error ? <div className="mt-6 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}
      {loading && badges.length === 0 ? <div className="mt-6 text-sm text-muted-foreground">Loading…</div> : null}

      <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {badges.map((badge) => (
          <div
            key={badge.id}
            className={[
              "group relative flex flex-col items-center rounded-xl border p-4 text-center transition",
              badge.earned ? "bg-card border-primary/20 shadow-sm" : "bg-muted/50 border-border",
            ].join(" ")}
          >
            <div className={[
                "relative mb-3 flex h-20 w-20 items-center justify-center rounded-full text-4xl",
                badge.earned ? "bg-primary/10" : "bg-muted grayscale opacity-70"
            ].join(" ")}>
              {badge.icon_url && /^[\p{Emoji}]/u.test(badge.icon_url) ? (
                  <span>{badge.icon_url}</span>
              ) : badge.icon_url ? (
                  <img
                    src={badge.icon_url}
                    alt={badge.name}
                    className="h-16 w-16 object-contain"
                  />
              ) : (
                  <span>🏅</span>
              )}
              
              {/* Status Icon Overlay */}
              <div className={[
                  "absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full border-2 border-background text-xs",
                  badge.earned ? "bg-success text-success-foreground" : "bg-muted-foreground text-muted"
              ].join(" ")}>
                  {badge.earned ? "✓" : "🔒"}
              </div>
            </div>

            <h3 className={[
                "font-display font-semibold", 
                badge.earned ? "text-foreground" : "text-muted-foreground"
            ].join(" ")}>
                {badge.name}
            </h3>
            
            <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                {badge.description}
            </p>

            {badge.earned && badge.earnedAt && (
                <div className="mt-3 text-[10px] font-medium text-primary bg-primary/10 px-2 py-1 rounded-full">
                    Earned {new Date(badge.earnedAt).toLocaleDateString()}
                </div>
            )}
          </div>
        ))}
      </div>
    </main>
  );
}
