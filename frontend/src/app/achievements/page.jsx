"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import Skeleton from "@/components/Skeleton";
import {
    celebrateMilestone,
    createShare,
    deleteShare,
    getAllBadges,
    getLeaderboard,
    getMyBadges,
    getMyShares,
    getPendingMilestones,
} from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

const TABS = {
    BADGES: "badges",
    LEADERBOARD: "leaderboard",
};

const SHARE_VISIBILITY_OPTIONS = [
    { value: "public", label: "Công khai" },
    { value: "followers", label: "Người theo dõi" },
    { value: "private", label: "Riêng tư" },
];

const SHARE_TYPE_LABELS = {
    achievement: "Thành tích",
    badge: "Huy hiệu",
    streak: "Streak",
    level_up: "Lên hạng",
    certificate: "Chứng nhận",
};

const MILESTONE_LABELS = {
    first_motif_discovered: "Khám phá họa tiết đầu tiên",
    first_quiz_passed: "Vượt qua quiz đầu tiên",
    first_lesson_completed: "Hoàn thành bài học đầu tiên",
    first_badge_earned: "Nhận huy hiệu đầu tiên",
    first_streak_7: "Duy trì streak 7 ngày",
    onboarding_completed: "Hoàn thành onboarding",
};

function asArray(value) {
    return Array.isArray(value) ? value : [];
}

function formatDate(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    return date.toLocaleDateString("vi-VN");
}

function milestoneLabel(milestoneType) {
    return MILESTONE_LABELS[milestoneType] || milestoneType || "Cột mốc";
}

function shareTypeLabel(shareType) {
    return SHARE_TYPE_LABELS[shareType] || shareType || "Bài chia sẻ";
}

function getShareHref(share) {
    if (share?.share_url) {
        try {
            const url = new URL(share.share_url);
            return url.pathname || `/share/${share.id}`;
        } catch {
            if (String(share.share_url).startsWith("/")) {
                return share.share_url;
            }
        }
    }
    return `/share/${share?.id}`;
}

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
                        Theo dõi huy hiệu, cột mốc và bảng xếp hạng của bạn.
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
                        Huy Hiệu & Chia Sẻ
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
    const [pendingMilestones, setPendingMilestones] = useState([]);
    const [myShares, setMyShares] = useState([]);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [feedback, setFeedback] = useState(null);

    const [activeShareBadgeId, setActiveShareBadgeId] = useState(null);
    const [shareCaption, setShareCaption] = useState("");
    const [shareVisibility, setShareVisibility] = useState("public");
    const [submittingShareBadgeId, setSubmittingShareBadgeId] = useState(null);
    const [celebratingMilestoneId, setCelebratingMilestoneId] = useState(null);
    const [deletingShareId, setDeletingShareId] = useState(null);

    const loadedForUserRef = useRef(undefined);

    useEffect(() => {
        if (!visible) return;
        const userKey = user?.id || status;
        if (loadedForUserRef.current === userKey) return;

        let cancelled = false;

        async function load() {
            setLoading(true);
            setError(null);
            setFeedback(null);
            try {
                if (status !== "authed") {
                    setAllBadges([]);
                    setEarnedBadges([]);
                    setPendingMilestones([]);
                    setMyShares([]);
                    loadedForUserRef.current = userKey;
                    return;
                }

                const [badgesRes, earnedRes, pendingRes, sharesRes] =
                    await Promise.all([
                        getAllBadges(),
                        getMyBadges(),
                        getPendingMilestones(),
                        getMyShares({ page: 1, pageSize: 8 }),
                    ]);

                if (cancelled) return;

                setAllBadges(asArray(badgesRes));
                setEarnedBadges(asArray(earnedRes));
                setPendingMilestones(asArray(pendingRes?.pending_milestones));
                setMyShares(asArray(sharesRes?.shares));
                loadedForUserRef.current = userKey;
            } catch (err) {
                if (!cancelled) {
                    setError(err instanceof Error ? err.message : String(err));
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        load();
        return () => {
            cancelled = true;
        };
    }, [visible, status, user]);

    const badges = useMemo(() => {
        const earnedMap = new Map();
        earnedBadges.forEach((userBadge) => {
            if (userBadge?.badge?.slug) {
                earnedMap.set(userBadge.badge.slug, userBadge);
            }
        });

        return allBadges.map((badge) => {
            const earnedData = earnedMap.get(badge.slug);
            return {
                ...badge,
                earned: Boolean(earnedData),
                earnedAt: earnedData?.earned_at,
            };
        });
    }, [allBadges, earnedBadges]);

    async function refreshMyShares() {
        const sharesRes = await getMyShares({ page: 1, pageSize: 8 });
        setMyShares(asArray(sharesRes?.shares));
    }

    function openShareComposer(badge) {
        setFeedback(null);
        setShareCaption(`Mình vừa mở khóa huy hiệu "${badge.name}"!`);
        setShareVisibility("public");
        setActiveShareBadgeId(badge.id);
    }

    async function submitBadgeShare(badge) {
        setSubmittingShareBadgeId(badge.id);
        setFeedback(null);
        try {
            await createShare({
                shareType: "badge",
                contentId: badge.id,
                caption: shareCaption.trim() || `Mình vừa mở khóa huy hiệu "${badge.name}"!`,
                visibility: shareVisibility,
            });
            await refreshMyShares();
            setFeedback("Đã chia sẻ huy hiệu thành công.");
            setActiveShareBadgeId(null);
        } catch (err) {
            setFeedback(err instanceof Error ? err.message : String(err));
        } finally {
            setSubmittingShareBadgeId(null);
        }
    }

    async function handleCelebrateMilestone(milestone) {
        setCelebratingMilestoneId(milestone.id);
        setFeedback(null);
        try {
            const res = await celebrateMilestone({ milestoneId: milestone.id });
            setPendingMilestones((prev) =>
                prev.filter((item) => item.id !== milestone.id),
            );
            setFeedback(res?.message || "Đã ghi nhận cột mốc.");
        } catch (err) {
            setFeedback(err instanceof Error ? err.message : String(err));
        } finally {
            setCelebratingMilestoneId(null);
        }
    }

    async function handleDeleteShare(shareId) {
        setDeletingShareId(shareId);
        setFeedback(null);
        try {
            await deleteShare({ shareId });
            setMyShares((prev) => prev.filter((item) => item.id !== shareId));
            setFeedback("Đã xóa bài chia sẻ.");
        } catch (err) {
            setFeedback(err instanceof Error ? err.message : String(err));
        } finally {
            setDeletingShareId(null);
        }
    }

    if (status !== "authed") {
        return (
            <div className="rounded-2xl border border-border bg-card p-6">
                <h2 className="text-xl font-display font-semibold text-foreground">
                    Huy Hiệu
                </h2>
                <p className="mt-2 text-sm text-muted-foreground">
                    Vui lòng đăng nhập để xem huy hiệu, chia sẻ thành tích và theo dõi cột mốc.
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
                        Huy Hiệu & Cột Mốc
                    </h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                        Chia sẻ huy hiệu, theo dõi cột mốc và giữ động lực mỗi ngày.
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

            {!error && feedback ? (
                <div className="mt-6 rounded-lg bg-primary/10 p-3 text-sm text-primary">
                    {feedback}
                </div>
            ) : null}

            {loading && badges.length === 0 ? (
                <div className="mt-6 text-sm text-muted-foreground">Đang tải…</div>
            ) : null}

            <section className="mt-8 rounded-2xl border border-border bg-card p-4">
                <div className="flex items-center justify-between gap-2">
                    <h3 className="text-base font-display font-semibold text-foreground">
                        Milestone Highlights
                    </h3>
                    <span className="text-xs text-muted-foreground">
                        {pendingMilestones.length} chưa ghi nhận
                    </span>
                </div>

                {pendingMilestones.length === 0 ? (
                    <p className="mt-3 text-sm text-muted-foreground">
                        Bạn đã ghi nhận hết các cột mốc gần đây.
                    </p>
                ) : (
                    <div className="mt-4 grid gap-3 md:grid-cols-2">
                        {pendingMilestones.map((milestone) => (
                            <div
                                key={milestone.id}
                                className="rounded-xl border border-border bg-background p-3"
                            >
                                <p className="text-sm font-medium text-foreground">
                                    {milestoneLabel(milestone.milestone_type)}
                                </p>
                                <p className="mt-1 text-xs text-muted-foreground">
                                    {formatDate(milestone.achieved_at)}
                                </p>
                                <button
                                    type="button"
                                    disabled={celebratingMilestoneId === milestone.id}
                                    onClick={() => handleCelebrateMilestone(milestone)}
                                    className="mt-3 rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground disabled:opacity-60"
                                >
                                    {celebratingMilestoneId === milestone.id
                                        ? "Đang ghi nhận..."
                                        : "Ghi nhận"}
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
                {badges.map((badge) => (
                    <div
                        key={badge.id || badge.slug}
                        className={[
                            "group relative flex flex-col items-center rounded-xl border p-4 text-center transition-all duration-200",
                            badge.earned
                                ? "bg-card border-primary/30 shadow-md shadow-primary/10 ring-2 ring-primary/20 hover:shadow-lg hover:scale-[1.02]"
                                : "bg-muted/30 border-border/50",
                        ].join(" ")}
                    >
                        <div
                            className={[
                                "relative mb-3 flex h-20 w-20 items-center justify-center rounded-full text-4xl",
                                badge.earned
                                    ? "bg-gradient-to-br from-primary/20 to-primary/5"
                                    : "bg-muted/50 grayscale opacity-50",
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
                                        ? "bg-emerald-500 text-white"
                                        : "bg-muted-foreground/50 text-muted",
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
                            <div className="mt-3 rounded-full bg-emerald-500/10 px-2 py-1 text-[10px] font-medium text-emerald-600">
                                Đã nhận {formatDate(badge.earnedAt)}
                            </div>
                        ) : null}

                        {badge.earned ? (
                            <button
                                type="button"
                                onClick={() => openShareComposer(badge)}
                                className="mt-3 rounded-full border border-primary/30 px-3 py-1 text-[11px] font-semibold text-primary transition hover:bg-primary/10"
                            >
                                Chia sẻ
                            </button>
                        ) : null}

                        {activeShareBadgeId === badge.id ? (
                            <div className="mt-3 w-full rounded-lg border border-border bg-background p-2 text-left">
                                <label className="block text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                                    Nội dung
                                </label>
                                <textarea
                                    value={shareCaption}
                                    onChange={(event) =>
                                        setShareCaption(event.target.value)
                                    }
                                    maxLength={500}
                                    rows={2}
                                    className="mt-1 w-full rounded-md border border-border bg-card px-2 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                                />
                                <label className="mt-2 block text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                                    Quyền xem
                                </label>
                                <select
                                    value={shareVisibility}
                                    onChange={(event) =>
                                        setShareVisibility(event.target.value)
                                    }
                                    className="mt-1 w-full rounded-md border border-border bg-card px-2 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                                >
                                    {SHARE_VISIBILITY_OPTIONS.map((option) => (
                                        <option key={option.value} value={option.value}>
                                            {option.label}
                                        </option>
                                    ))}
                                </select>

                                <div className="mt-2 flex gap-2">
                                    <button
                                        type="button"
                                        onClick={() => submitBadgeShare(badge)}
                                        disabled={submittingShareBadgeId === badge.id}
                                        className="rounded-md bg-primary px-2.5 py-1.5 text-[11px] font-semibold text-primary-foreground disabled:opacity-60"
                                    >
                                        {submittingShareBadgeId === badge.id
                                            ? "Đang gửi..."
                                            : "Đăng"}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setActiveShareBadgeId(null)}
                                        className="rounded-md border border-border px-2.5 py-1.5 text-[11px] font-semibold text-muted-foreground"
                                    >
                                        Hủy
                                    </button>
                                </div>
                            </div>
                        ) : null}
                    </div>
                ))}
            </div>

            <section className="mt-10 rounded-2xl border border-border bg-card p-4">
                <div className="flex items-center justify-between gap-2">
                    <h3 className="text-base font-display font-semibold text-foreground">
                        Bài chia sẻ gần đây
                    </h3>
                    <span className="text-xs text-muted-foreground">
                        {myShares.length} bài
                    </span>
                </div>

                {myShares.length === 0 ? (
                    <p className="mt-3 text-sm text-muted-foreground">
                        Bạn chưa có bài chia sẻ nào.
                    </p>
                ) : (
                    <div className="mt-4 space-y-2">
                        {myShares.map((share) => (
                            <div
                                key={share.id}
                                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border bg-background px-3 py-2"
                            >
                                <div className="min-w-0">
                                    <Link
                                        href={getShareHref(share)}
                                        className="truncate text-sm font-semibold text-foreground hover:text-primary"
                                    >
                                        {shareTypeLabel(share.share_type)}
                                    </Link>
                                    <p className="truncate text-xs text-muted-foreground">
                                        {share.caption || "Không có mô tả"}
                                    </p>
                                </div>

                                <div className="flex items-center gap-3">
                                    <span className="text-xs text-muted-foreground">
                                        {share.view_count || 0} lượt xem
                                    </span>
                                    <button
                                        type="button"
                                        disabled={deletingShareId === share.id}
                                        onClick={() => handleDeleteShare(share.id)}
                                        className="rounded-md border border-border px-2 py-1 text-xs font-medium text-muted-foreground hover:text-foreground disabled:opacity-60"
                                    >
                                        {deletingShareId === share.id
                                            ? "Đang xóa..."
                                            : "Xóa"}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>
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
                const normalized = Array.isArray(res)
                    ? res
                    : Array.isArray(res?.entries)
                      ? res.entries
                      : [];

                if (!cancelled) {
                    setEntries(normalized);
                    loadedOnceRef.current = true;
                }
            } catch (err) {
                if (!cancelled) {
                    setError(err instanceof Error ? err.message : String(err));
                }
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
                                    <tr key={i} className="border-t border-border">
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
                                    {entries.map((entry, index) => (
                                        <tr
                                            key={entry.user_id || `${entry.rank}-${index}`}
                                            className="border-t border-border"
                                        >
                                            <td className="px-4 py-3 font-display tabular-nums text-xs text-muted-foreground">
                                                {entry.rank}
                                            </td>
                                            <td className="px-4 py-3 font-medium text-foreground">
                                                {entry.display_name}
                                            </td>
                                            <td className="px-4 py-3 text-muted-foreground">
                                                {entry.title}
                                            </td>
                                            <td className="px-4 py-3 text-right font-display tabular-nums font-semibold text-primary">
                                                {entry.total_xp}
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
