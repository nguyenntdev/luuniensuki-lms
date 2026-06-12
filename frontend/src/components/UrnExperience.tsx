"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { shallow } from "zustand/shallow";

import { getMyStreak, getQuestSummary, getRecommendations } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import ViewerControlsHint from "@/components/viewer/ViewerControlsHint";
import {
    makeSelectNextUnmasteredMotif,
    selectMotifProgressSummary,
    useMotifStore,
} from "@/stores/motifStore";

type MotifId = string | number;

interface RecommendationItem {
    title?: string;
    description?: string;
    href?: string;
}

interface Recommendations {
    items?: RecommendationItem[];
}

interface QuestSummary {
    quest_name?: string;
    progress_percent?: number;
    next_step_title?: string;
    next_objective?: { title?: string } | null;
}

interface Streak {
    current_streak?: number;
}

interface UrnExperienceProps {
    urnSlug: string;
}

interface UrnExperienceContentProps {
    urnSlug: string;
    searchParams: ReturnType<typeof useSearchParams>;
}

const UrnViewer = dynamic(() => import("@/components/UrnViewer"), {
    ssr: false,
    loading: () => (
        <div className="absolute inset-0 flex items-center justify-center bg-black text-sm text-white/70">
            Đang Tải Trình Xem 3D…
        </div>
    ),
});

export default function UrnExperience({ urnSlug }: UrnExperienceProps) {
    const searchParams = useSearchParams();

    return (
        <UrnExperienceContent urnSlug={urnSlug} searchParams={searchParams} />
    );
}

function UrnExperienceContent({
    urnSlug,
    searchParams,
}: UrnExperienceContentProps) {
    const status = useAuthStore((s) => s.status);
    const user = useAuthStore((s) => s.user);
    const router = useRouter();

    const ensureMotifsLoaded = useMotifStore((s) => s.ensureMotifsLoaded);
    const hydrateProgressForUrn = useMotifStore((s) => s.hydrateProgressForUrn);
    const loadingMotifs = useMotifStore((s) => s.loadingMotifs);
    const loadingProgress = useMotifStore((s) => s.loadingProgress);
    const selectedMotifId = useMotifStore((s) => s.selectedMotifId);

    const focusNext = searchParams?.get("focus") === "next";
    const originMotifId = searchParams?.get("fromMotif") || null;
    useEffect(() => {
        if (!urnSlug) return;
        ensureMotifsLoaded(urnSlug);
        if (status === "authed") {
            hydrateProgressForUrn(urnSlug);
        }
    }, [urnSlug, ensureMotifsLoaded, hydrateProgressForUrn, status]);

    const [highlightedMotifId, setHighlightedMotifId] = useState<
        MotifId | null
    >(null);
    const [focusMotifId, setFocusMotifId] = useState<MotifId | null>(null);
    const [viewMode, setViewMode] = useState("standard");
    const [recommendations, setRecommendations] =
        useState<Recommendations | null>(null);
    const [questSummary, setQuestSummary] = useState<QuestSummary | null>(null);
    const [journeyError, setJourneyError] = useState<string | null>(null);
    const [streak, setStreak] = useState<Streak | null>(null);

    const progressSummary = useMotifStore(selectMotifProgressSummary, shallow);
    const nextUnmasteredSelector = useMemo(
        () => makeSelectNextUnmasteredMotif(originMotifId),
        [originMotifId],
    );
    const nextUnmasteredMotif = useMotifStore(nextUnmasteredSelector);

    const highlightTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(
        null,
    );
    const autoFocusRef = useRef(false);

    const triggerHighlight = useCallback((motifId: MotifId | null) => {
        if (!motifId) return;
        setHighlightedMotifId(motifId);
        if (highlightTimeoutRef.current) {
            clearTimeout(highlightTimeoutRef.current);
        }
        highlightTimeoutRef.current = setTimeout(() => {
            setHighlightedMotifId(null);
        }, 12000);
    }, []);

    const triggerFocusNext = useCallback(() => {
        if (!nextUnmasteredMotif?.id) return;
        triggerHighlight(nextUnmasteredMotif.id);
        setFocusMotifId(nextUnmasteredMotif.id);
    }, [nextUnmasteredMotif, triggerHighlight]);

    useEffect(() => {
        if (!focusNext || autoFocusRef.current) return;
        if (!nextUnmasteredMotif?.id) return;
        autoFocusRef.current = true;
        triggerFocusNext();
    }, [focusNext, nextUnmasteredMotif, triggerFocusNext]);

    useEffect(() => {
        return () => {
            if (highlightTimeoutRef.current) {
                clearTimeout(highlightTimeoutRef.current);
            }
        };
    }, []);

    useEffect(() => {
        if (status !== "authed") return;
        let cancelled = false;

        async function loadJourney() {
            setJourneyError(null);
            try {
                const [recRes, questRes, streakRes] = await Promise.allSettled([
                    getRecommendations(),
                    getQuestSummary(),
                    getMyStreak(),
                ]);
                if (cancelled) return;
                if (recRes.status === "fulfilled") {
                    setRecommendations(
                        (recRes.value as Recommendations) || null,
                    );
                }
                if (questRes.status === "fulfilled") {
                    setQuestSummary((questRes.value as QuestSummary) || null);
                }
                if (streakRes.status === "fulfilled") {
                    setStreak((streakRes.value as Streak) || null);
                }

                const firstError =
                    recRes.status === "rejected"
                        ? recRes.reason
                        : questRes.status === "rejected"
                          ? questRes.reason
                          : null;
                if (firstError) {
                    setJourneyError(
                        firstError instanceof Error
                            ? firstError.message
                            : String(firstError),
                    );
                }
            } catch (err) {
                if (cancelled) return;
                setJourneyError(
                    err instanceof Error ? err.message : String(err),
                );
            }
        }

        loadJourney();
        return () => {
            cancelled = true;
        };
    }, [status, urnSlug]);

    const urnMotifProgress = useMemo(() => {
        const total = progressSummary.total;
        const discovered = Math.min(progressSummary.discovered, total);
        const mastered = Math.min(progressSummary.mastered, total);
        const discoveredPercent = total
            ? Math.max(0, Math.min(100, (discovered / total) * 100))
            : 0;
        const masteredPercent = total
            ? Math.max(0, Math.min(100, (mastered / total) * 100))
            : 0;

        return {
            total,
            discovered,
            mastered,
            discoveredPercent,
            masteredPercent,
        };
    }, [progressSummary]);

    const allMotifsMastered = useMemo(() => {
        return (
            urnMotifProgress.total > 0 &&
            urnMotifProgress.mastered === urnMotifProgress.total
        );
    }, [urnMotifProgress]);

    const undiscoveredCount = progressSummary.undiscovered;

    const totalLabel =
        urnMotifProgress.total > 0
            ? String(urnMotifProgress.total)
            : loadingMotifs
              ? "…"
              : "0";
    const barWidth = urnMotifProgress.total
        ? `${urnMotifProgress.masteredPercent}%`
        : loadingMotifs || loadingProgress
          ? "35%"
          : "0%";
    const remainingMastery = Math.max(
        0,
        urnMotifProgress.total - urnMotifProgress.mastered,
    );

    const journeyStep = useMemo(() => {
        if (!urnMotifProgress.total) {
            return { title: "Chưa có họa tiết để khám phá", detail: null };
        }
        if (allMotifsMastered) {
            return {
                title: "Sẵn sàng làm bài kiểm tra cuối đỉnh",
                detail: null,
            };
        }
        if (undiscoveredCount > 0) {
            return {
                title: "Khám phá họa tiết tiếp theo",
                detail: nextUnmasteredMotif?.name || null,
            };
        }
        return {
            title: "Hoàn thành bài học và trắc nghiệm cho họa tiết đã mở",
            detail: nextUnmasteredMotif?.name || null,
        };
    }, [
        urnMotifProgress.total,
        allMotifsMastered,
        undiscoveredCount,
        nextUnmasteredMotif,
    ]);

    const recommendationItems = useMemo(() => {
        return Array.isArray(recommendations?.items)
            ? recommendations.items
            : [];
    }, [recommendations]);
    const topRecommendation = recommendationItems[0];
    const modeOptions = [
        { key: "standard", label: "Chuẩn" },
        { key: "scan", label: "Quét" },
        { key: "mastery", label: "Thành thạo" },
    ];

    const handleOpenLesson = useCallback(() => {
        if (!selectedMotifId) return;
        router.push(`/motif/${selectedMotifId}`);
    }, [router, selectedMotifId]);

    const handleOpenQuiz = useCallback(() => {
        if (!selectedMotifId) return;
        router.push(`/motif/${selectedMotifId}/quiz`);
    }, [router, selectedMotifId]);

    useEffect(() => {
        function handleKeyDown(event: KeyboardEvent) {
            const tagName = (event?.target as HTMLElement | null)?.tagName;
            if (tagName && ["INPUT", "TEXTAREA", "SELECT"].includes(tagName)) {
                return;
            }
            if (event.repeat) return;

            const key = String(event.key || "").toLowerCase();
            if (key === "n") {
                event.preventDefault();
                triggerFocusNext();
            } else if (key === "h") {
                event.preventDefault();
                setViewMode((prev) => (prev === "scan" ? "standard" : "scan"));
            } else if (key === "l") {
                event.preventDefault();
                handleOpenLesson();
            } else if (key === "q") {
                event.preventDefault();
                handleOpenQuiz();
            }
        }

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [handleOpenLesson, handleOpenQuiz, triggerFocusNext]);

    return (
        <div className="fixed inset-0 w-full overflow-hidden bg-black">
            <div className="pointer-events-none absolute left-0 top-0 z-10 w-full px-4 py-3 text-white">
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="pointer-events-auto flex flex-wrap items-center gap-2 rounded-full border border-white/10 bg-black/45 px-2 py-1 text-xs shadow-[0_10px_30px_rgba(0,0,0,0.35)] backdrop-blur-md">
                        <Link
                            href="/"
                            className="rounded-full px-3 py-1.5 font-medium text-white/80 hover:bg-white/10 hover:text-white"
                        >
                            Trang Chủ
                        </Link>
                        <Link
                            href="/profile"
                            className="rounded-full px-3 py-1.5 font-medium text-white/80 hover:bg-white/10 hover:text-white"
                        >
                            Bảng Điều Khiển
                        </Link>
                        {urnSlug && allMotifsMastered ? (
                            <Link
                                href={`/urns/${urnSlug}/exam`}
                                className="rounded-full bg-primary/90 px-3 py-1.5 font-semibold text-primary-foreground shadow-sm hover:bg-primary"
                            >
                                🎓 Bài kiểm tra
                            </Link>
                        ) : null}
                    </div>

                    <div className="pointer-events-auto flex flex-wrap items-center justify-end gap-2 text-xs">
                        <div className="flex items-center gap-1 rounded-full border border-white/10 bg-black/45 p-1 backdrop-blur-md">
                            {modeOptions.map((mode) => {
                                const isActive = viewMode === mode.key;
                                return (
                                    <button
                                        key={mode.key}
                                        type="button"
                                        onClick={() => setViewMode(mode.key)}
                                        className={[
                                            "rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-wide transition",
                                            isActive
                                                ? "bg-white/90 text-black"
                                                : "text-white/70 hover:bg-white/10 hover:text-white",
                                        ].join(" ")}
                                        aria-pressed={isActive}
                                    >
                                        {mode.label}
                                    </button>
                                );
                            })}
                        </div>
                        <div className="rounded-full border border-white/10 bg-black/45 px-3 py-1.5 backdrop-blur-md">
                            Đỉnh:{" "}
                            <span className="font-mono text-white/90">
                                {urnSlug}
                            </span>
                        </div>
                        <div className="rounded-full border border-white/10 bg-black/45 px-3 py-1.5 backdrop-blur-md">
                            {user?.display_name ||
                                (status === "authed" ? "Đang Tải…" : "Khách")}
                        </div>
                    </div>
                </div>

                <div className="mt-3 flex w-full justify-center">
                    <div className="pointer-events-auto w-full max-w-lg rounded-2xl border border-white/10 bg-black/45 px-4 py-3 shadow-[0_12px_34px_rgba(0,0,0,0.4)] backdrop-blur-md">
                        <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-white/90">
                            <div>
                                Đã khám phá:{" "}
                                <span className="font-display tabular-nums">
                                    {urnMotifProgress.discovered}
                                </span>
                                /
                                <span className="font-display tabular-nums">
                                    {totalLabel}
                                </span>{" "}
                                họa tiết
                            </div>
                            {streak?.current_streak != null ? (
                                <div className="text-xs text-white/70">
                                    🔥{" "}
                                    <span className="font-display tabular-nums">
                                        {streak.current_streak}
                                    </span>{" "}
                                    ngày liên tiếp
                                </div>
                            ) : null}
                        </div>
                        <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-white/70">
                            <span>
                                Đã thành thạo:{" "}
                                <span className="font-display tabular-nums">
                                    {urnMotifProgress.mastered}
                                </span>
                                /
                                <span className="font-display tabular-nums">
                                    {totalLabel}
                                </span>
                            </span>
                            {allMotifsMastered ? (
                                <span className="rounded-full bg-primary/25 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white">
                                    Sẵn sàng kiểm tra
                                </span>
                            ) : null}
                        </div>
                        <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-white/10">
                            <div
                                className={[
                                    "h-full rounded-full bg-primary transition-[width] duration-500 ease-out",
                                    (loadingMotifs || loadingProgress) &&
                                    urnMotifProgress.total === 0
                                        ? "animate-pulse"
                                        : "",
                                ].join(" ")}
                                style={{ width: barWidth }}
                                role="progressbar"
                                aria-label="Tiến độ thành thạo họa tiết"
                                aria-valuenow={urnMotifProgress.mastered}
                                aria-valuemin={0}
                                aria-valuemax={
                                    urnMotifProgress.total || undefined
                                }
                            />
                        </div>
                    </div>
                </div>
            </div>

            <div className="pointer-events-none absolute bottom-4 left-4 z-10 w-[min(380px,92vw)] text-white">
                <div className="pointer-events-auto rounded-2xl border border-white/10 bg-black/45 p-4 shadow-[0_12px_34px_rgba(0,0,0,0.4)] backdrop-blur-md">
                    <div className="flex items-center justify-between gap-3">
                        <div className="text-sm font-semibold">Hành trình</div>
                        <div className="text-[10px] font-medium text-white/60">
                            Còn {remainingMastery} họa tiết
                        </div>
                    </div>

                    <div className="mt-2 text-[11px] uppercase tracking-wide text-white/50">
                        Bước tiếp theo
                    </div>
                    <div className="text-sm font-medium text-white">
                        {journeyStep.title}
                    </div>
                    {journeyStep.detail ? (
                        <div className="mt-1 text-xs text-white/70">
                            {journeyStep.detail}
                        </div>
                    ) : null}

                    <div className="mt-3 flex flex-wrap gap-2">
                        <button
                            type="button"
                            onClick={triggerFocusNext}
                            disabled={
                                !nextUnmasteredMotif?.id || allMotifsMastered
                            }
                            className={[
                                "inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-semibold transition",
                                !nextUnmasteredMotif?.id || allMotifsMastered
                                    ? "border-white/10 bg-white/5 text-white/40 cursor-not-allowed"
                                    : "border-white/20 bg-white/10 text-white hover:bg-white/15",
                            ].join(" ")}
                        >
                            Tập trung họa tiết
                        </button>
                        {urnSlug && allMotifsMastered ? (
                            <Link
                                href={`/urns/${urnSlug}/exam`}
                                className="inline-flex items-center gap-2 rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground shadow-sm hover:bg-primary/90"
                            >
                                Bắt đầu bài kiểm tra
                            </Link>
                        ) : null}
                    </div>

                    {journeyError ? (
                        <div className="mt-3 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-white/70">
                            {journeyError}
                        </div>
                    ) : null}

                    {topRecommendation ? (
                        <div className="mt-3 rounded-lg border border-white/10 bg-white/5 p-3">
                            <div className="text-[11px] uppercase tracking-wide text-white/50">
                                Gợi ý
                            </div>
                            <div className="mt-1 text-sm font-medium text-white">
                                {topRecommendation.title}
                            </div>
                            {topRecommendation.description ? (
                                <div className="mt-1 text-xs text-white/70">
                                    {topRecommendation.description}
                                </div>
                            ) : null}
                            {topRecommendation.href ? (
                                <Link
                                    href={topRecommendation.href}
                                    className="mt-2 inline-flex text-xs font-semibold text-primary hover:text-primary/80"
                                >
                                    Xem gợi ý →
                                </Link>
                            ) : null}
                        </div>
                    ) : null}

                    {questSummary ? (
                        <div className="mt-3 rounded-lg border border-white/10 bg-white/5 p-3">
                            <div className="text-[11px] uppercase tracking-wide text-white/50">
                                Nhiệm vụ
                            </div>
                            <div className="mt-1 text-sm font-medium text-white">
                                {questSummary.quest_name}
                            </div>
                            <div className="mt-1 text-xs text-white/70">
                                {Math.round(questSummary.progress_percent || 0)}
                                %
                                {questSummary.next_step_title
                                    ? ` · ${questSummary.next_step_title}`
                                    : ""}
                            </div>
                            {questSummary.next_objective?.title ? (
                                <div className="mt-1 text-xs text-white/60">
                                    {questSummary.next_objective.title}
                                </div>
                            ) : null}
                        </div>
                    ) : null}

                    <div className="mt-3 text-[10px] text-white/50">
                        Phím tắt: N tiếp theo · H quét · L bài học · Q trắc nghiệm
                    </div>
                </div>
            </div>

            <UrnViewer
                urnSlug={urnSlug}
                userId={user?.id || null}
                highlightedMotifId={highlightedMotifId}
                focusMotifId={focusMotifId}
                viewMode={viewMode}
                className="absolute inset-0"
            />

            <ViewerControlsHint />
        </div>
    );
}
