"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Check, Lock } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import toast from "react-hot-toast";

import { useAuthStore } from "@/stores/authStore";
import { useMotifStore } from "@/stores/motifStore";

import { completeLesson, getMotifDetail } from "@/lib/api";

const STATUS_META = {
    hidden: {
        label: "Chưa Mở",
        className: "bg-muted/60 text-muted-foreground border-border",
    },
    discovered: {
        label: "Đã Khám Phá",
        className: "bg-info/10 text-info border-info/20",
    },
    learned: {
        label: "Đã Học",
        className: "bg-success/10 text-success border-success/20",
    },
    mastered: {
        label: "Đã Thành Thạo",
        className: "bg-bronze/10 text-bronze border-bronze/20",
    },
};

const PROGRESS_STEPS = [
    { key: "discovered", label: "Khám Phá", xp: 25 },
    { key: "learned", label: "Bài Học", xp: 50 },
    { key: "mastered", label: "Trắc Nghiệm", xp: 75 },
];

const STATUS_RANK = {
    hidden: -1,
    discovered: 0,
    learned: 1,
    mastered: 2,
};

const NEXT_ACTION_HINTS = {
    hidden: "Khám phá họa tiết trên mô hình 3D.",
    discovered: "Hoàn thành bài học để mở khóa quiz.",
    learned: "Làm trắc nghiệm để thành thạo.",
    mastered: "Chọn họa tiết tiếp theo để tiếp tục.",
};

const SIDEBAR_ANIMATION_MS = 320;

function countWords(text) {
    if (!text) return 0;
    return String(text).replace(/\s+/g, " ").trim().split(" ").filter(Boolean)
        .length;
}

function firstSentence(text, maxLen = 160) {
    if (!text) return null;
    const cleaned = String(text).replace(/\s+/g, " ").trim();
    if (!cleaned) return null;
    const match = cleaned.match(/^(.+?[.!?])(\s|$)/);
    const sentence = (match?.[1] || cleaned).trim();
    if (sentence.length <= maxLen) return sentence;
    return `${sentence.slice(0, Math.max(0, maxLen - 1)).trimEnd()}…`;
}

function ProgressStepper({ status }) {
    const completedThrough = STATUS_RANK[status] ?? -1;
    const lastStepIndex = PROGRESS_STEPS.length - 1;
    const currentIndex = completedThrough >= 0 ? completedThrough + 1 : null;

    const getLineClassName = (state) => {
        if (state === "completed") return "bg-success";
        if (state === "current") return "bg-primary";
        return "bg-muted/70";
    };

    const getStepState = (idx) => {
        if (completedThrough >= idx) return "completed";
        if (currentIndex === idx) return "current";
        return "locked";
    };

    return (
        <div className="w-full rounded-xl border border-border bg-background/40 p-3">
            <div className="grid grid-cols-3 items-start gap-0">
                {PROGRESS_STEPS.map((step, idx) => {
                    const isLast = idx === lastStepIndex;
                    const stepState = getStepState(idx);

                    const leftLineState =
                        idx === 0
                            ? null
                            : completedThrough >= idx - 1
                              ? "completed"
                              : "locked";
                    const rightLineState = isLast
                        ? null
                        : completedThrough >= idx
                          ? "completed"
                          : "locked";

                    const circleClassName =
                        stepState === "completed"
                            ? "bg-success text-success-foreground"
                            : stepState === "current"
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted/60 text-muted-foreground border border-border";

                    const labelClassName =
                        stepState === "locked"
                            ? "text-muted-foreground"
                            : "text-foreground";

                    const xpClassName =
                        stepState === "completed"
                            ? "text-success"
                            : stepState === "current"
                              ? "text-primary"
                              : "text-muted-foreground";

                    const srState =
                        stepState === "completed"
                            ? "Hoàn thành"
                            : stepState === "current"
                              ? "Hiện tại"
                              : "Chưa mở";

                    return (
                        <div
                            key={step.key}
                            className="relative flex flex-col items-center text-center"
                        >
                            {idx > 0 ? (
                                <div
                                    aria-hidden="true"
                                    className={[
                                        "absolute left-0 right-1/2 top-3.5 z-0 h-[2px] -translate-y-1/2 rounded-full",
                                        getLineClassName(leftLineState),
                                    ].join(" ")}
                                />
                            ) : null}

                            {!isLast ? (
                                <div
                                    aria-hidden="true"
                                    className={[
                                        "absolute left-1/2 right-0 top-3.5 z-0 h-[2px] -translate-y-1/2 rounded-full",
                                        getLineClassName(rightLineState),
                                    ].join(" ")}
                                />
                            ) : null}

                            <div className="relative">
                                {stepState === "current" ? (
                                    <span
                                        aria-hidden="true"
                                        className="absolute -inset-1 z-[1] rounded-full bg-primary/25 animate-ping motion-reduce:animate-none"
                                    />
                                ) : null}

                                <div
                                    className={[
                                        "relative z-10 flex h-7 w-7 items-center justify-center rounded-full text-[11px] font-semibold",
                                        circleClassName,
                                    ].join(" ")}
                                >
                                    {stepState === "completed" ? (
                                        <Check
                                            className="h-4 w-4"
                                            aria-hidden="true"
                                        />
                                    ) : stepState === "locked" ? (
                                        <Lock
                                            className="h-4 w-4"
                                            aria-hidden="true"
                                        />
                                    ) : (
                                        <span aria-hidden="true">
                                            {idx + 1}
                                        </span>
                                    )}
                                </div>
                            </div>

                            <div
                                className={[
                                    "mt-2 text-[11px] font-semibold leading-tight",
                                    labelClassName,
                                ].join(" ")}
                            >
                                {step.label}
                            </div>
                            <div
                                className={[
                                    "mt-0.5 text-[10px] font-medium tabular-nums",
                                    xpClassName,
                                ].join(" ")}
                            >
                                {step.xp} XP
                            </div>
                            <span className="sr-only">
                                {step.label}: {srState}, {step.xp} XP
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

export default function LessonSidebar() {
    const router = useRouter();
    const authStatus = useAuthStore((s) => s.status);
    const fetchMe = useAuthStore((s) => s.fetchMe);

    const sidebarOpen = useMotifStore((s) => s.sidebarOpen);
    const selectedMotifId = useMotifStore((s) => s.selectedMotifId);
    const motifsById = useMotifStore((s) => s.motifsById);
    const foundByMotifId = useMotifStore((s) => s.foundByMotifId);
    const progressByMotifId = useMotifStore((s) => s.progressByMotifId);
    const closeSidebar = useMotifStore((s) => s.closeSidebar);
    const applyProgressUpdate = useMotifStore((s) => s.applyProgressUpdate);

    const [renderMotifId, setRenderMotifId] = useState(null);
    const [shouldRender, setShouldRender] = useState(false);
    const [panelOpen, setPanelOpen] = useState(false);
    const [completingLesson, setCompletingLesson] = useState(false);

    useEffect(() => {
        if (!sidebarOpen || !selectedMotifId) return;
        setRenderMotifId(selectedMotifId);
    }, [sidebarOpen, selectedMotifId]);

    useEffect(() => {
        if (!sidebarOpen) return;
        setShouldRender(true);
        const raf = window.requestAnimationFrame(() => setPanelOpen(true));
        return () => window.cancelAnimationFrame(raf);
    }, [sidebarOpen]);

    useEffect(() => {
        if (sidebarOpen) return;
        setPanelOpen(false);
        if (!shouldRender) return;
        const t = window.setTimeout(() => {
            setShouldRender(false);
            setRenderMotifId(null);
        }, SIDEBAR_ANIMATION_MS);
        return () => window.clearTimeout(t);
    }, [sidebarOpen, shouldRender]);

    useEffect(() => {
        if (!shouldRender) return;
        const prevOverflow = document.body.style.overflow;
        document.body.style.overflow = "hidden";
        return () => {
            document.body.style.overflow = prevOverflow;
        };
    }, [shouldRender]);

    useEffect(() => {
        if (!sidebarOpen) return;
        const onKeyDown = (e) => {
            if (e.key === "Escape") closeSidebar();
        };
        window.addEventListener("keydown", onKeyDown);
        return () => window.removeEventListener("keydown", onKeyDown);
    }, [closeSidebar, sidebarOpen]);

    const activeMotifId = renderMotifId || selectedMotifId;
    const motif = useMemo(
        () => (activeMotifId ? motifsById[activeMotifId] : null),
        [motifsById, activeMotifId],
    );
    const isFound = Boolean(activeMotifId && foundByMotifId[activeMotifId]);
    const progress = activeMotifId ? progressByMotifId[activeMotifId] : null;

    const progressStatus = useMemo(() => {
        const raw = progress?.status || (isFound ? "discovered" : "hidden");
        return STATUS_META[raw] ? raw : "hidden";
    }, [isFound, progress?.status]);
    const nextActionHint =
        NEXT_ACTION_HINTS[progressStatus] || "Tiếp tục hành trình của bạn.";

    const quizUnlocked = useMemo(
        () => progressStatus === "learned" || progressStatus === "mastered",
        [progressStatus],
    );

    const lessonCacheRef = useRef(new Map());
    const [lesson, setLesson] = useState(null);
    const [lessonLoading, setLessonLoading] = useState(false);
    const [lessonError, setLessonError] = useState(null);

    useEffect(() => {
        if (!sidebarOpen || !activeMotifId) return;

        if (lessonCacheRef.current.has(activeMotifId)) {
            setLesson(lessonCacheRef.current.get(activeMotifId));
            setLessonLoading(false);
            setLessonError(null);
            return;
        }

        let alive = true;
        setLesson(null);
        setLessonLoading(true);
        setLessonError(null);

        getMotifDetail(activeMotifId)
            .then((data) => {
                if (!alive) return;
                const nextLesson = data?.lesson || null;
                lessonCacheRef.current.set(activeMotifId, nextLesson);
                setLesson(nextLesson);
            })
            .catch((err) => {
                if (!alive) return;
                setLessonError(
                    err instanceof Error ? err.message : String(err),
                );
                setLesson(null);
            })
            .finally(() => {
                if (!alive) return;
                setLessonLoading(false);
            });

        return () => {
            alive = false;
        };
    }, [activeMotifId, sidebarOpen]);

    const sections = useMemo(() => {
        const introText = lesson?.intro_text || motif?.lesson_intro || "";
        const description = lesson?.description || "";
        const symbolism = lesson?.symbolism || "";
        const historicalContext = lesson?.historical_context || "";
        const funFact = lesson?.fun_fact || "";

        return [
            {
                key: "description",
                title: "Bài học",
                icon: "📖",
                text: description,
            },
            {
                key: "intro_text",
                title: "Giới thiệu",
                icon: "📝",
                text: introText,
            },
            {
                key: "symbolism",
                title: "Ý nghĩa biểu tượng",
                icon: "🔮",
                text: symbolism,
            },
            {
                key: "historical_context",
                title: "Bối cảnh lịch sử",
                icon: "📜",
                text: historicalContext,
            },
            {
                key: "fun_fact",
                title: "Điều thú vị",
                icon: "⭐",
                text: funFact,
            },
        ].filter((s) => Boolean(s.text?.trim()));
    }, [lesson, motif?.lesson_intro]);

    const wordCount = useMemo(
        () => sections.reduce((sum, s) => sum + countWords(s.text), 0),
        [sections],
    );
    const readingTimeMinutes = useMemo(
        () => (wordCount ? Math.max(1, Math.ceil(wordCount / 200)) : 0),
        [wordCount],
    );
    const keyTakeaways = useMemo(
        () =>
            sections
                .map((s) => ({ ...s, summary: firstSentence(s.text) }))
                .filter((s) => Boolean(s.summary)),
        [sections],
    );

    const quizDisabledReason = useMemo(() => {
        if (authStatus !== "authed") return "Đăng nhập để làm trắc nghiệm.";
        if (!isFound) return "Họa tiết chưa được mở khóa.";
        if (!quizUnlocked) return "Hoàn thành bài học để mở khóa trắc nghiệm.";
        return null;
    }, [authStatus, isFound, quizUnlocked]);

    const handleCompleteLesson = useCallback(async () => {
        if (authStatus !== "authed" || !activeMotifId) return;
        if (completingLesson) return;

        setCompletingLesson(true);
        try {
            const res = await completeLesson({ motifId: activeMotifId });
            applyProgressUpdate({
                motifId: activeMotifId,
                status: res.status,
                xpAwarded: res.xp_awarded,
                totalXp: res.total_xp,
            });
            await fetchMe();

            const label = STATUS_META[res.status]?.label || res.status;
            toast.success(
                `Đã lưu: ${label}${typeof res.xp_awarded === "number" ? ` (+${res.xp_awarded} XP)` : ""}`,
            );
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            toast.error(msg);
        } finally {
            setCompletingLesson(false);
        }
    }, [
        activeMotifId,
        applyProgressUpdate,
        authStatus,
        completingLesson,
        fetchMe,
    ]);

    const handleTakeQuiz = useCallback(() => {
        if (!activeMotifId) return;
        if (quizDisabledReason) {
            toast.error(quizDisabledReason);
            return;
        }
        closeSidebar();
        router.push(`/motif/${activeMotifId}/quiz`);
    }, [activeMotifId, closeSidebar, quizDisabledReason, router]);

    if (!shouldRender || !motif) return null;

    return (
        <div className="fixed inset-0 z-40 pointer-events-none">
            <div
                className={[
                    "pointer-events-auto absolute inset-0 bg-background/40 backdrop-blur-[2px] transition-opacity duration-300",
                    panelOpen ? "opacity-100" : "opacity-0 pointer-events-none",
                ].join(" ")}
                onClick={closeSidebar}
                aria-hidden="true"
            />

            <aside
                className={[
                    "pointer-events-auto absolute right-0 top-0 h-full w-full max-w-[560px] bg-card/95 shadow-2xl border-l border-white/10 backdrop-blur-md",
                    "transform-gpu transition-transform duration-300 ease-out",
                    panelOpen ? "translate-x-0" : "translate-x-full",
                ].join(" ")}
            >
                <div className="flex h-full flex-col">
                    <div className="flex items-start justify-between gap-4 border-b border-white/10 p-4">
                        <div className="min-w-0">
                            <div className="mb-3">
                                <ProgressStepper status={progressStatus} />
                            </div>

                            <h2 className="truncate text-xl font-display font-semibold text-foreground">
                                {motif.name}
                            </h2>
                            {motif.name_en ? (
                                <p className="truncate text-sm text-muted-foreground">
                                    {motif.name_en}
                                </p>
                            ) : null}

                            <div className="mt-3 flex flex-wrap items-center gap-2">
                                <span className="rounded-full bg-muted px-2 py-1 text-xs text-muted-foreground">
                                    {motif.category} · {motif.rarity}
                                </span>
                                {readingTimeMinutes ? (
                                    <span className="rounded-full bg-muted px-2 py-1 text-xs text-muted-foreground">
                                        ⏱️ {readingTimeMinutes} phút đọc
                                    </span>
                                ) : null}
                                <span
                                    className={[
                                        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium",
                                        (
                                            STATUS_META[progressStatus] ||
                                            STATUS_META.hidden
                                        ).className,
                                    ].join(" ")}
                                >
                                    {
                                        (
                                            STATUS_META[progressStatus] ||
                                            STATUS_META.hidden
                                        ).label
                                    }
                                </span>
                            </div>
                        </div>

                        <button
                            onClick={closeSidebar}
                            className="shrink-0 rounded-md border border-border px-3 py-2 text-sm text-muted-foreground hover:bg-muted"
                        >
                            Đóng
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 pb-[calc(1.25rem+env(safe-area-inset-bottom))]">
                        {authStatus !== "authed" ? (
                            <div className="mb-4 rounded-lg bg-bronze/10 p-3 text-sm text-bronze">
                                Đăng nhập để lưu tiến trình của bạn.{" "}
                                <Link
                                    href="/login"
                                    className="font-medium underline"
                                >
                                    Đăng nhập
                                </Link>
                            </div>
                        ) : null}

                        <div className="mb-3 rounded-lg border border-border bg-background/40 px-3 py-2">
                            <div className="text-[10px] uppercase tracking-wide text-muted-foreground/80">
                                Bước tiếp theo
                            </div>
                            <div className="mt-1 text-sm text-foreground">
                                {nextActionHint}
                            </div>
                        </div>

                        <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
                            <button
                                type="button"
                                onClick={handleCompleteLesson}
                                disabled={
                                    authStatus !== "authed" || completingLesson
                                }
                                className={[
                                    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-semibold transition-colors",
                                    authStatus !== "authed" || completingLesson
                                        ? "bg-muted text-muted-foreground cursor-not-allowed"
                                        : "bg-primary text-primary-foreground hover:bg-primary/90",
                                ].join(" ")}
                            >
                                {authStatus === "authed"
                                    ? completingLesson
                                        ? "Đang Lưu…"
                                        : "Hoàn Thành Bài Học"
                                    : "Đăng Nhập Để Lưu"}
                            </button>

                            <button
                                type="button"
                                onClick={handleTakeQuiz}
                                disabled={Boolean(quizDisabledReason)}
                                className={[
                                    "inline-flex items-center justify-center rounded-lg border px-4 py-2 text-sm font-semibold transition-colors",
                                    quizDisabledReason
                                        ? "border-border bg-muted/50 text-muted-foreground cursor-not-allowed"
                                        : "border-border bg-card text-foreground hover:bg-muted",
                                ].join(" ")}
                            >
                                Làm Trắc Nghiệm
                            </button>
                        </div>

                        {quizDisabledReason ? (
                            <p className="mb-4 text-xs text-muted-foreground">
                                {quizDisabledReason}
                            </p>
                        ) : null}

                        <div className="mb-4 flex flex-wrap items-center gap-2">
                            <Link
                                href={`/motif/${motif.id}`}
                                className="rounded-lg border border-border px-3 py-2 text-sm font-medium text-foreground hover:bg-muted"
                                onClick={closeSidebar}
                            >
                                Mở bài học đầy đủ →
                            </Link>
                        </div>

                        {motif.thumbnail_url ? (
                            <div className="mb-4 overflow-hidden rounded-xl bg-muted">
                                <img
                                    src={motif.thumbnail_url}
                                    alt={motif.name}
                                    className="w-full object-cover"
                                />
                            </div>
                        ) : null}

                        <div className="mb-3 flex items-start justify-between gap-3">
                            <div>
                                <h3 className="text-sm font-display font-semibold text-foreground">
                                    Bài học
                                </h3>
                                <p className="mt-1 text-xs text-muted-foreground">
                                    {wordCount ? `${wordCount} từ` : "—"}
                                </p>
                            </div>
                            {lessonLoading ? (
                                <span className="rounded-full bg-muted px-2 py-1 text-xs text-muted-foreground">
                                    Đang tải…
                                </span>
                            ) : null}
                        </div>

                        {lessonError ? (
                            <div className="mb-4 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
                                Không tải được nội dung bài học: {lessonError}
                            </div>
                        ) : null}

                        {sections.length ? (
                            <div className="space-y-4">
                                {sections.map((section) => (
                                    <section
                                        key={section.key}
                                        className="rounded-xl border border-border bg-background/50 p-4"
                                    >
                                        <div className="flex items-start gap-3">
                                            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-muted text-lg">
                                                {section.icon}
                                            </div>
                                            <div className="min-w-0">
                                                <h4 className="text-sm font-display font-semibold text-foreground">
                                                    {section.title}
                                                </h4>
                                                <div className="mt-2 whitespace-pre-wrap text-sm leading-6 text-muted-foreground">
                                                    {section.text}
                                                </div>
                                            </div>
                                        </div>
                                    </section>
                                ))}

                                <section className="rounded-xl border border-border bg-background/50 p-4">
                                    <h4 className="text-sm font-display font-semibold text-foreground">
                                        Ý chính
                                    </h4>
                                    {keyTakeaways.length ? (
                                        <ul className="mt-3 space-y-2 text-sm leading-6 text-muted-foreground">
                                            {keyTakeaways.map((t) => (
                                                <li
                                                    key={t.key}
                                                    className="flex gap-2"
                                                >
                                                    <span className="shrink-0">
                                                        {t.icon}
                                                    </span>
                                                    <span className="min-w-0">
                                                        <span className="font-medium text-foreground">
                                                            {t.title}:
                                                        </span>{" "}
                                                        {t.summary}
                                                    </span>
                                                </li>
                                            ))}
                                        </ul>
                                    ) : (
                                        <p className="mt-2 text-sm leading-6 text-muted-foreground">
                                            Chưa có nội dung để tóm tắt.
                                        </p>
                                    )}
                                </section>
                            </div>
                        ) : (
                            <div className="rounded-lg border border-border bg-muted/20 p-4 text-sm text-muted-foreground">
                                Chưa có nội dung bài học.
                            </div>
                        )}

                        {progress?.xpAwarded ? (
                            <div className="mt-6 rounded-lg bg-muted p-4 text-sm text-muted-foreground">
                                <div>
                                    XP nhận được:{" "}
                                    <span className="font-display tabular-nums">
                                        {progress.xpAwarded}
                                    </span>
                                </div>
                                <div>
                                    Tổng XP:{" "}
                                    <span className="font-display tabular-nums">
                                        {progress.totalXp}
                                    </span>
                                </div>
                            </div>
                        ) : null}
                    </div>
                </div>
            </aside>
        </div>
    );
}
