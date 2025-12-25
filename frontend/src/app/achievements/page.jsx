"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import Skeleton from "@/components/Skeleton";
import { getAllBadges, getLeaderboard, getMyBadges } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

const TABS = {
    BADGES: "badges",
    LEADERBOARD: "leaderboard",
};

export default function AchievementsPage() {
    const [activeTab, setActiveTab] = useState(TABS.BADGES);

    return (
        <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                    <h1 className="text-3xl font-display font-bold tracking-tight text-foreground">
                        Thành Tích
                    </h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Theo dõi huy hiệu đã nhận và xem thứ hạng của bạn trên
                        bảng xếp hạng.
                    </p>
                </div>
            </div>

            <div className="mt-6 rounded-2xl border border-border bg-card p-2">
                <div
                    className="grid grid-cols-2 gap-2"
                    role="tablist"
                    aria-label="Tab thành tích"
                >
                    <button
                        type="button"
                        role="tab"
                        aria-selected={activeTab === TABS.BADGES}
                        onClick={() => setActiveTab(TABS.BADGES)}
                        className={[
                            "rounded-xl px-4 py-2 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                            activeTab === TABS.BADGES
                                ? "bg-background text-foreground shadow-sm"
                                : "text-muted-foreground hover:bg-muted hover:text-foreground",
                        ].join(" ")}
                    >
                        Huy Hiệu
                    </button>
                    <button
                        type="button"
                        role="tab"
                        aria-selected={activeTab === TABS.LEADERBOARD}
                        onClick={() => setActiveTab(TABS.LEADERBOARD)}
                        className={[
                            "rounded-xl px-4 py-2 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                            activeTab === TABS.LEADERBOARD
                                ? "bg-background text-foreground shadow-sm"
                                : "text-muted-foreground hover:bg-muted hover:text-foreground",
                        ].join(" ")}
                    >
                        Bảng Xếp Hạng
                    </button>
                </div>
            </div>

            <div className="mt-8">
                <div
                    className={activeTab === TABS.BADGES ? "block" : "hidden"}
                    role="tabpanel"
                >
                    <BadgesTab visible={activeTab === TABS.BADGES} />
                </div>
                <div
                    className={
                        activeTab === TABS.LEADERBOARD ? "block" : "hidden"
                    }
                    role="tabpanel"
                >
                    <LeaderboardTab visible={activeTab === TABS.LEADERBOARD} />
                </div>
            </div>
        </main>
    );
}

function BadgesTab({ visible }) {
    const status = useAuthStore((s) => s.status);
    const user = useAuthStore((s) => s.user);

    const [allBadges, setAllBadges] = useState([]);
    const [earnedBadges, setEarnedBadges] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const loadedForUserRef = useRef(undefined);

    useEffect(() => {
        if (!visible) return;
        const userKey = user?.id || status;
        if (loadedForUserRef.current === userKey) return;

        let cancelled = false;
        async function load() {
            setLoading(true);
            setError(null);
            try {
                // Always fetch all badges
                if (status !== "authed") {
                    setAllBadges([]);
                    setEarnedBadges([]);
                    loadedForUserRef.current = userKey;
                    return;
                }
                const badgesRes = await getAllBadges();
                if (cancelled) return;
                setAllBadges(badgesRes);

                // If logged in, fetch earned badges
                const earnedRes = await getMyBadges();
                if (cancelled) return;
                setEarnedBadges(earnedRes);

                if (!cancelled) loadedForUserRef.current = userKey;
            } catch (err) {
                if (!cancelled)
                    setError(err instanceof Error ? err.message : String(err));
            } finally {
                if (!cancelled) setLoading(false);
            }
        }
        load();
        return () => {
            cancelled = true;
        };
    }, [visible, status, user]);

    // Merge badges to determine status
    const badges = useMemo(() => {
        const earnedMap = new Map();
        earnedBadges.forEach((ub) => {
            // ub is UserBadgeOut { badge: BadgeOut, earned_at: ... }
            if (ub.badge && ub.badge.slug) earnedMap.set(ub.badge.slug, ub);
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

    if (status !== "authed") {
        return (
            <div className="rounded-2xl border border-border bg-card p-6">
                <h2 className="text-xl font-display font-semibold text-foreground">
                    Huy Hiệu
                </h2>
                <p className="mt-2 text-sm text-muted-foreground">
                    Vui lòng đăng nhập để xem huy hiệu bạn đã nhận.
                </p>
                <div className="mt-4">
                    <Link
                        href="/login"
                        className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
                    >
                        Đăng Nhập
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <section>
            <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-display font-semibold text-foreground">
                        Huy Hiệu
                    </h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                        Nhận huy hiệu bằng cách hoàn thành bài học và bài kiểm
                        tra.
                    </p>
                </div>
                <div className="flex gap-3">
                    <Link
                        href="/profile"
                        className="text-sm font-medium text-primary hover:text-primary/80"
                    >
                        Bảng Điều Khiển →
                    </Link>
                </div>
            </div>

            {error ? (
                <div className="mt-6 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
                    {error}
                </div>
            ) : null}
            {loading && badges.length === 0 ? (
                <div className="mt-6 text-sm text-muted-foreground">
                    Đang tải…
                </div>
            ) : null}

            <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
                {badges.map((badge) => (
                    <div
                        key={badge.id}
                        className={[
                            "group relative flex flex-col items-center rounded-xl border p-4 text-center transition",
                            badge.earned
                                ? "bg-card border-primary/20 shadow-sm"
                                : "bg-muted/50 border-border",
                        ].join(" ")}
                    >
                        <div
                            className={[
                                "relative mb-3 flex h-20 w-20 items-center justify-center rounded-full text-4xl",
                                badge.earned
                                    ? "bg-primary/10"
                                    : "bg-muted grayscale opacity-70",
                            ].join(" ")}
                        >
                            {badge.icon_url &&
                            /^[\p{Emoji}]/u.test(badge.icon_url) ? (
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

                            <div
                                className={[
                                    "absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full border-2 border-background text-xs",
                                    badge.earned
                                        ? "bg-success text-success-foreground"
                                        : "bg-muted-foreground text-muted",
                                ].join(" ")}
                            >
                                {badge.earned ? "✓" : "🔒"}
                            </div>
                        </div>

                        <h3
                            className={[
                                "font-display font-semibold",
                                badge.earned
                                    ? "text-foreground"
                                    : "text-muted-foreground",
                            ].join(" ")}
                        >
                            {badge.name}
                        </h3>

                        <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                            {badge.description}
                        </p>

                        {badge.earned && badge.earnedAt ? (
                            <div className="mt-3 rounded-full bg-primary/10 px-2 py-1 text-[10px] font-medium text-primary">
                                Đã nhận{" "}
                                {new Date(badge.earnedAt).toLocaleDateString(
                                    "vi-VN",
                                )}
                            </div>
                        ) : null}
                    </div>
                ))}
            </div>
        </section>
    );
}

function LeaderboardTab({ visible }) {
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const loadedOnceRef = useRef(false);

    useEffect(() => {
        if (!visible) return;
        if (loadedOnceRef.current) return;

        let cancelled = false;
        async function load() {
            setLoading(true);
            setError(null);
            try {
                const res = await getLeaderboard({ limit: 50 });
                if (!cancelled) {
                    setEntries(res || []);
                    loadedOnceRef.current = true;
                }
            } catch (err) {
                if (!cancelled)
                    setError(err instanceof Error ? err.message : String(err));
            } finally {
                if (!cancelled) setLoading(false);
            }
        }
        load();
        return () => {
            cancelled = true;
        };
    }, [visible]);

    return (
        <section>
            <div>
                <h2 className="text-2xl font-display font-semibold text-foreground">
                    Bảng Xếp Hạng
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                    Những nhà khám phá hàng đầu theo XP.
                </p>
            </div>

            {error ? (
                <div className="mt-6 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
                    {error}
                </div>
            ) : null}

            <div className="mt-8 overflow-hidden rounded-2xl border border-border bg-card">
                <div className="overflow-x-auto">
                    <table className="w-full min-w-[520px] text-left text-sm">
                        <thead className="bg-muted text-xs text-muted-foreground">
                            <tr>
                                <th className="px-4 py-3">Hạng</th>
                                <th className="px-4 py-3">Nhà Khám Phá</th>
                                <th className="px-4 py-3">Danh Hiệu</th>
                                <th className="px-4 py-3 text-right">XP</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                [...Array(10)].map((_, i) => (
                                    <tr
                                        key={i}
                                        className="border-t border-border"
                                    >
                                        <td className="px-4 py-3">
                                            <Skeleton className="h-4 w-6" />
                                        </td>
                                        <td className="px-4 py-3">
                                            <Skeleton className="h-4 w-32" />
                                        </td>
                                        <td className="px-4 py-3">
                                            <Skeleton className="h-4 w-24" />
                                        </td>
                                        <td className="px-4 py-3 text-right">
                                            <Skeleton className="ml-auto h-4 w-12" />
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <>
                                    {entries.map((e) => (
                                        <tr
                                            key={e.user_id}
                                            className="border-t border-border"
                                        >
                                            <td className="px-4 py-3 font-display tabular-nums text-xs text-muted-foreground">
                                                {e.rank}
                                            </td>
                                            <td className="px-4 py-3 font-medium text-foreground">
                                                {e.display_name}
                                            </td>
                                            <td className="px-4 py-3 text-muted-foreground">
                                                {e.title}
                                            </td>
                                            <td className="px-4 py-3 text-right font-display tabular-nums font-semibold text-primary">
                                                {e.total_xp}
                                            </td>
                                        </tr>
                                    ))}
                                    {entries.length === 0 ? (
                                        <tr>
                                            <td
                                                className="px-4 py-6 text-center text-sm text-muted-foreground"
                                                colSpan={4}
                                            >
                                                Chưa có dữ liệu.
                                            </td>
                                        </tr>
                                    ) : null}
                                </>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
    );
}
