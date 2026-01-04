"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import Skeleton from "@/components/Skeleton";
import {
    getDashboardSummary,
    refreshRecommendations,
    logAnalyticsEvent,
} from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

const STATUS_LABELS = {
    hidden: "Chưa mở",
    discovered: "Đã khám phá",
    learned: "Đã học",
    mastered: "Đã thành thạo",
};

export default function DashboardPage() {
    const status = useAuthStore((s) => s.status);
    const user = useAuthStore((s) => s.user);
    const fetchMe = useAuthStore((s) => s.fetchMe);

    const [urns, setUrns] = useState([]);
    const [collectionStats, setCollectionStats] = useState(null);
    const [streak, setStreak] = useState(null);
    const [questSummary, setQuestSummary] = useState(null);
    const [recommendations, setRecommendations] = useState(null);
    const [recommendationError, setRecommendationError] = useState(null);
    const [recommendationRefreshing, setRecommendationRefreshing] =
        useState(false);
    const [pathMotifs, setPathMotifs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const hasLoggedRef = useRef(false);

    useEffect(() => {
        if (status === "authed" && !user) fetchMe();
    }, [status, user, fetchMe]);

    useEffect(() => {
        if (status !== "authed") return;
        let cancelled = false;

        async function load() {
            setLoading(true);
            setError(null);
            try {
                const summary = await getDashboardSummary();
                if (cancelled) return;

                setUrns(summary?.urns || []);
                setCollectionStats(summary?.collection_stats || null);
                setStreak(summary?.streak || null);
                setQuestSummary(summary?.quest_summary || null);
                setRecommendations(summary?.recommendations || null);
                setPathMotifs(summary?.path_motifs || []);
                setRecommendationError(null);
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
    }, [status]);

    const startingUrn = useMemo(() => {
        if (!user?.starting_urn_id) return null;
        return urns.find((u) => u.id === user.starting_urn_id) || null;
    }, [urns, user?.starting_urn_id]);

    useEffect(() => {
        if (status !== "authed" || !user || hasLoggedRef.current) return;
        hasLoggedRef.current = true;
        logAnalyticsEvent({
            name: "dashboard_view",
            payload: {
                starting_urn_id: user.starting_urn_id || null,
                source: "client",
            },
            path: "/dashboard",
        }).catch(() => null);
    }, [status, user]);

    const pathMotifsWithStatus = useMemo(() => {
        return pathMotifs.map((motif) => ({
            ...motif,
            status: motif.status || "hidden",
        }));
    }, [pathMotifs]);

    const pathCounts = useMemo(() => {
        const counts = { total: 0, discovered: 0, learned: 0, mastered: 0 };
        for (const motif of pathMotifsWithStatus) {
            counts.total += 1;
            if (motif.status === "discovered") counts.discovered += 1;
            if (motif.status === "learned") counts.learned += 1;
            if (motif.status === "mastered") counts.mastered += 1;
        }
        return counts;
    }, [pathMotifsWithStatus]);

    const resumeTarget = useMemo(() => {
        if (!pathMotifsWithStatus.length) return null;
        return (
            pathMotifsWithStatus.find((m) => m.status === "learned") ||
            pathMotifsWithStatus.find((m) => m.status === "discovered") ||
            pathMotifsWithStatus.find((m) => m.status === "hidden")
        );
    }, [pathMotifsWithStatus]);

    const resumeAction = useMemo(() => {
        if (!resumeTarget) return null;
        if (resumeTarget.status === "learned") {
            return {
                title: "Hoàn thành trắc nghiệm",
                description: resumeTarget.name,
                href: `/motif/${resumeTarget.id}/quiz`,
                status: resumeTarget.status,
                motifId: resumeTarget.id,
            };
        }
        if (resumeTarget.status === "discovered") {
            return {
                title: "Tiếp tục bài học",
                description: resumeTarget.name,
                href: `/motif/${resumeTarget.id}`,
                status: resumeTarget.status,
                motifId: resumeTarget.id,
            };
        }
        return {
            title: "Khám phá họa tiết mới",
            description: startingUrn?.name || "Bắt đầu với lộ trình đã chọn",
            href: startingUrn ? `/urns/${startingUrn.slug}` : "/explore",
            status: "hidden",
            motifId: null,
        };
    }, [resumeTarget, startingUrn]);

    const completionPercent = pathCounts.total
        ? Math.round((pathCounts.mastered / pathCounts.total) * 100)
        : 0;

    const nextUpList = useMemo(() => {
        return pathMotifsWithStatus
            .filter((m) => m.status !== "mastered")
            .slice(0, 4);
    }, [pathMotifsWithStatus]);

    const recommendationItems = useMemo(() => {
        return Array.isArray(recommendations?.items)
            ? recommendations.items
            : [];
    }, [recommendations]);

    const remediationItems = useMemo(
        () =>
            recommendationItems.filter((item) => item?.kind === "remediation"),
        [recommendationItems],
    );

    const nextRecommendationItems = useMemo(
        () =>
            recommendationItems.filter((item) => item?.kind !== "remediation"),
        [recommendationItems],
    );

    function handleResumeClick() {
        if (status !== "authed" || !resumeAction) return;
        logAnalyticsEvent({
            name: "resume_click",
            payload: {
                motif_id: resumeAction.motifId,
                status: resumeAction.status,
                starting_urn_id: user?.starting_urn_id || null,
                source: "client",
            },
            path: "/dashboard",
        }).catch(() => null);
    }

    async function handleRefreshRecommendations() {
        if (status !== "authed") return;
        setRecommendationRefreshing(true);
        setRecommendationError(null);
        try {
            const res = await refreshRecommendations({
                useLlm: Boolean(user?.ai_personalization_enabled),
            });
            setRecommendations(res || null);
        } catch (err) {
            setRecommendationError(
                err instanceof Error ? err.message : String(err),
            );
        } finally {
            setRecommendationRefreshing(false);
        }
    }

    if (status !== "authed") {
        return (
            <main className="mx-auto max-w-5xl px-6 py-10">
                <div className="rounded-xl border border-border bg-card p-6">
                    <h1 className="text-xl font-display font-semibold">
                        Learning Hub
                    </h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Vui lòng đăng nhập để xem tiến trình học tập.
                    </p>
                    <div className="mt-4">
                        <Link
                            href="/login"
                            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
                        >
                            Đăng nhập
                        </Link>
                    </div>
                </div>
            </main>
        );
    }

    return (
        <main className="mx-auto max-w-6xl px-6 py-10 pb-24">
            <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-display font-bold text-foreground">
                        Learning Hub
                    </h1>
                    <p className="mt-1 text-sm text-muted-foreground">
                        Theo dõi tiến trình, tiếp tục lộ trình, và hoàn thành
                        các thử thách tiếp theo.
                    </p>
                </div>
                <div className="flex flex-wrap gap-2">
                    <Link
                        href="/explore"
                        className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted"
                    >
                        Khám phá Cửu Đỉnh
                    </Link>
                    <Link
                        href="/collection"
                        className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted"
                    >
                        Bộ sưu tập
                    </Link>
                </div>
            </div>

            {error ? (
                <div className="mt-6 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
                    {error}
                </div>
            ) : null}

            <div className="mt-8 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
                <div className="space-y-6">
                    <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                        {loading ? (
                            <div className="space-y-3">
                                <Skeleton className="h-5 w-40" />
                                <Skeleton className="h-4 w-64" />
                                <Skeleton className="h-10 w-32" />
                            </div>
                        ) : resumeAction ? (
                            <>
                                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                    Tiếp tục
                                </div>
                                <div className="mt-2 text-xl font-display font-semibold text-foreground">
                                    {resumeAction.title}
                                </div>
                                <p className="mt-1 text-sm text-muted-foreground">
                                    {resumeAction.description}
                                </p>
                                <div className="mt-4">
                                    <Link
                                        href={resumeAction.href}
                                        onClick={handleResumeClick}
                                        className="inline-flex items-center rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                                    >
                                        Bắt đầu →
                                    </Link>
                                </div>
                            </>
                        ) : (
                            <div className="text-sm text-muted-foreground">
                                Chưa có dữ liệu lộ trình.
                            </div>
                        )}
                    </div>

                    <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                        <div className="flex items-baseline justify-between">
                            <div>
                                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                    Quest đang theo
                                </div>
                                <div className="mt-1 text-lg font-display font-semibold text-foreground">
                                    {loading ? (
                                        <Skeleton className="h-4 w-40" />
                                    ) : questSummary?.quest_name ? (
                                        questSummary.quest_name
                                    ) : (
                                        "Chưa chọn quest"
                                    )}
                                </div>
                            </div>
                            {questSummary ? (
                                <span className="text-xs text-muted-foreground">
                                    {Math.round(
                                        questSummary.progress_percent || 0,
                                    )}
                                    %
                                </span>
                            ) : null}
                        </div>

                        {questSummary ? (
                            <>
                                <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-muted">
                                    <div
                                        className="h-full bg-primary transition-all"
                                        style={{
                                            width: `${Math.round(
                                                questSummary.progress_percent ||
                                                    0,
                                            )}%`,
                                        }}
                                    />
                                </div>
                                <div className="mt-3 text-sm text-muted-foreground">
                                    {questSummary.next_step_title ? (
                                        <>
                                            Bước tiếp theo:{" "}
                                            <span className="text-foreground">
                                                {questSummary.next_step_title}
                                            </span>
                                        </>
                                    ) : (
                                        "Hãy mở quest để xem chi tiết."
                                    )}
                                </div>
                            </>
                        ) : (
                            <div className="mt-3 text-sm text-muted-foreground">
                                Chọn quest phù hợp để bắt đầu hành trình học
                                tập.
                            </div>
                        )}

                        <div className="mt-4">
                            <Link
                                href={
                                    questSummary?.quest_slug
                                        ? `/quests/${questSummary.quest_slug}`
                                        : "/quests"
                                }
                                className="text-sm font-semibold text-primary hover:text-primary/80"
                            >
                                {questSummary ? "Xem quest" : "Khám phá quest"}{" "}
                                →
                            </Link>
                        </div>
                    </div>

                    <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                        <div className="flex items-baseline justify-between">
                            <div>
                                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                    Lộ trình hiện tại
                                </div>
                                <div className="mt-1 text-lg font-display font-semibold text-foreground">
                                    {startingUrn?.name || "—"}
                                </div>
                            </div>
                            <div className="text-xs text-muted-foreground">
                                {pathCounts.mastered}/{pathCounts.total} hoàn
                                thành
                            </div>
                        </div>

                        <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-muted">
                            <div
                                className="h-full bg-primary transition-all"
                                style={{ width: `${completionPercent}%` }}
                            />
                        </div>

                        <div className="mt-4 grid gap-3 sm:grid-cols-3">
                            <div className="rounded-lg bg-secondary/40 p-3 text-center">
                                <div className="text-xs text-muted-foreground">
                                    Khám phá
                                </div>
                                <div className="mt-1 text-lg font-display font-semibold text-foreground">
                                    {pathCounts.discovered}
                                </div>
                            </div>
                            <div className="rounded-lg bg-secondary/40 p-3 text-center">
                                <div className="text-xs text-muted-foreground">
                                    Đã học
                                </div>
                                <div className="mt-1 text-lg font-display font-semibold text-foreground">
                                    {pathCounts.learned}
                                </div>
                            </div>
                            <div className="rounded-lg bg-secondary/40 p-3 text-center">
                                <div className="text-xs text-muted-foreground">
                                    Thành thạo
                                </div>
                                <div className="mt-1 text-lg font-display font-semibold text-foreground">
                                    {pathCounts.mastered}
                                </div>
                            </div>
                        </div>

                        <div className="mt-4 text-xs text-muted-foreground">
                            Hoàn thành:{" "}
                            <span className="font-display tabular-nums">
                                {completionPercent}%
                            </span>
                        </div>
                    </div>

                    <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                        <div className="flex items-baseline justify-between">
                            <h2 className="font-display text-lg font-semibold text-foreground">
                                Next Up
                            </h2>
                            {loading ? (
                                <span className="text-xs text-muted-foreground">
                                    Đang tải...
                                </span>
                            ) : null}
                        </div>
                        {nextUpList.length ? (
                            <div className="mt-4 space-y-3">
                                {nextUpList.map((motif) => (
                                    <div
                                        key={motif.id}
                                        className="flex items-center justify-between rounded-xl border border-border bg-secondary/30 px-4 py-3"
                                    >
                                        <div>
                                            <div className="text-sm font-semibold text-foreground">
                                                {motif.name}
                                            </div>
                                            <div className="mt-1 text-xs text-muted-foreground">
                                                {STATUS_LABELS[motif.status] ||
                                                    motif.status}
                                            </div>
                                        </div>
                                        <Link
                                            href={
                                                motif.status === "learned"
                                                    ? `/motif/${motif.id}/quiz`
                                                    : motif.status ===
                                                            "hidden" &&
                                                        startingUrn
                                                      ? `/urns/${startingUrn.slug}`
                                                      : `/motif/${motif.id}`
                                            }
                                            className="text-xs font-semibold text-primary hover:text-primary/80"
                                        >
                                            {motif.status === "learned"
                                                ? "Làm quiz"
                                                : motif.status === "hidden"
                                                  ? "Khám phá"
                                                  : "Xem bài học"}
                                        </Link>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="mt-4 text-sm text-muted-foreground">
                                Bạn đã hoàn thành tất cả họa tiết trong lộ trình
                                này.
                            </div>
                        )}
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                        <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                            Streak
                        </div>
                        {loading ? (
                            <div className="mt-3 space-y-2">
                                <Skeleton className="h-5 w-24" />
                                <Skeleton className="h-3 w-32" />
                            </div>
                        ) : (
                            <div className="mt-3">
                                <div className="text-3xl font-display font-bold text-foreground">
                                    {streak?.current_streak ?? 0} ngày
                                </div>
                                <div className="mt-1 text-xs text-muted-foreground">
                                    Kỷ lục: {streak?.longest_streak ?? 0} ·
                                    Freeze: {streak?.streak_freezes ?? 0}
                                </div>
                                {streak?.days_since_last_active != null &&
                                streak.days_since_last_active > 0 ? (
                                    <div className="mt-3 rounded-lg bg-bronze/10 p-3 text-xs text-bronze">
                                        Bạn đã nghỉ{" "}
                                        {streak.days_since_last_active} ngày.
                                        Hoàn thành một bài học để giữ streak.
                                    </div>
                                ) : null}
                            </div>
                        )}
                    </div>

                    <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                        <div className="flex items-center justify-between">
                            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                Gợi ý tiếp theo
                            </div>
                            <div className="flex items-center gap-2">
                                {recommendations?.source === "llm" ? (
                                    <span className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-700">
                                        AI
                                    </span>
                                ) : null}
                                <button
                                    type="button"
                                    onClick={handleRefreshRecommendations}
                                    disabled={recommendationRefreshing}
                                    className="text-xs font-semibold text-primary hover:text-primary/80 disabled:opacity-60"
                                >
                                    {recommendationRefreshing
                                        ? "Đang làm mới..."
                                        : "Làm mới"}
                                </button>
                            </div>
                        </div>
                        {recommendations?.ai?.provider ? (
                            <div className="mt-2 text-[11px] text-muted-foreground">
                                AI: {recommendations.ai.provider}
                                {recommendations.ai.model
                                    ? ` · ${recommendations.ai.model}`
                                    : ""}
                            </div>
                        ) : null}

                        {recommendationError ? (
                            <div className="mt-3 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
                                {recommendationError}
                            </div>
                        ) : null}

                        {loading ? (
                            <div className="mt-3 space-y-2">
                                <Skeleton className="h-4 w-3/4" />
                                <Skeleton className="h-4 w-2/3" />
                            </div>
                        ) : recommendationItems.length ? (
                            <div className="mt-4 space-y-3">
                                {remediationItems.length ? (
                                    <div>
                                        <div className="text-xs font-semibold uppercase tracking-wider text-amber-600">
                                            Cần ôn tập
                                        </div>
                                        <div className="mt-2 space-y-2">
                                            {remediationItems.map(
                                                (item, idx) => (
                                                    <Link
                                                        key={`remed-${idx}`}
                                                        href={
                                                            item.href ||
                                                            "/collection"
                                                        }
                                                        className="block rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 hover:bg-amber-100"
                                                    >
                                                        <div className="font-semibold">
                                                            {item.title}
                                                        </div>
                                                        {item.description ? (
                                                            <div className="text-xs">
                                                                {
                                                                    item.description
                                                                }
                                                            </div>
                                                        ) : null}
                                                    </Link>
                                                ),
                                            )}
                                        </div>
                                    </div>
                                ) : null}

                                <div>
                                    <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                        Tiếp tục học
                                    </div>
                                    <div className="mt-2 space-y-2">
                                        {nextRecommendationItems.map(
                                            (item, idx) => (
                                                <Link
                                                    key={`rec-${idx}`}
                                                    href={
                                                        item.href || "/explore"
                                                    }
                                                    className="block rounded-lg border border-border bg-secondary/40 px-3 py-2 text-sm text-foreground hover:bg-secondary/60"
                                                >
                                                    <div className="font-semibold">
                                                        {item.title}
                                                    </div>
                                                    {item.description ? (
                                                        <div className="text-xs text-muted-foreground">
                                                            {item.description}
                                                        </div>
                                                    ) : null}
                                                </Link>
                                            ),
                                        )}
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="mt-3 text-sm text-muted-foreground">
                                Chưa có gợi ý nào. Hãy hoàn thành bài học hoặc
                                quest để nhận đề xuất mới.
                            </div>
                        )}

                        {user?.ai_personalization_enabled === false ? (
                            <div className="mt-4 rounded-lg bg-muted/60 p-3 text-xs text-muted-foreground">
                                Cá nhân hóa AI đang tắt. Bật lại trong hồ sơ để
                                nhận gợi ý nâng cao.
                            </div>
                        ) : null}
                    </div>

                    <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                        <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                            Daily Goal
                        </div>
                        <div className="mt-3 text-sm text-foreground">
                            Hoàn thành 1 bài học hoặc 1 bài kiểm tra để tăng
                            điểm và giữ streak.
                        </div>
                        <div className="mt-4 flex flex-col gap-2">
                            <Link
                                href={
                                    startingUrn
                                        ? `/urns/${startingUrn.slug}`
                                        : "/explore"
                                }
                                className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted"
                            >
                                Khám phá họa tiết
                            </Link>
                            <Link
                                href="/collection"
                                className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted"
                            >
                                Xem bộ sưu tập
                            </Link>
                        </div>
                    </div>

                    <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                        <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                            Tổng quan
                        </div>
                        {loading ? (
                            <div className="mt-3 space-y-2">
                                <Skeleton className="h-4 w-28" />
                                <Skeleton className="h-4 w-24" />
                            </div>
                        ) : (
                            <div className="mt-3 space-y-2 text-sm text-muted-foreground">
                                <div>
                                    Đã khám phá:{" "}
                                    <span className="font-display tabular-nums text-foreground">
                                        {collectionStats?.discovered ?? 0}
                                    </span>
                                </div>
                                <div>
                                    Đã học:{" "}
                                    <span className="font-display tabular-nums text-foreground">
                                        {collectionStats?.learned ?? 0}
                                    </span>
                                </div>
                                <div>
                                    Thành thạo:{" "}
                                    <span className="font-display tabular-nums text-foreground">
                                        {collectionStats?.mastered ?? 0}
                                    </span>
                                </div>
                                <div>
                                    Tổng họa tiết:{" "}
                                    <span className="font-display tabular-nums text-foreground">
                                        {collectionStats?.total ?? 0}
                                    </span>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </main>
    );
}
