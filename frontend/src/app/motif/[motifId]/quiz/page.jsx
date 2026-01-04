"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState, useCallback } from "react";
import toast from "react-hot-toast";

import {
    getMotifDetail,
    getMotifQuiz,
    getMotifsByUrn,
    logAnalyticsEvent,
    submitQuiz,
} from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import { useMotifStore } from "@/stores/motifStore";

export default function MotifQuizPage() {
    const params = useParams();
    const motifId = useMemo(
        () => (typeof params?.motifId === "string" ? params.motifId : ""),
        [params],
    );

    const status = useAuthStore((s) => s.status);
    const fetchMe = useAuthStore((s) => s.fetchMe);
    const progressByMotifId = useMotifStore((s) => s.progressByMotifId);
    const hydrateProgressForUrn = useMotifStore((s) => s.hydrateProgressForUrn);

    const [motif, setMotif] = useState(null);
    const [quiz, setQuiz] = useState(null);
    const [answers, setAnswers] = useState({});
    const [urnMotifs, setUrnMotifs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [submitError, setSubmitError] = useState(null);
    const [result, setResult] = useState(null);
    const [startedAt, setStartedAt] = useState(null);
    const [progressChecked, setProgressChecked] = useState(false);

    // New states for UX enhancements
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [elapsedTime, setElapsedTime] = useState(0);

    // Check if motif is discovered
    const motifProgress = progressByMotifId[motifId];
    const isDiscovered =
        motifProgress?.status && motifProgress.status !== "hidden";
    const continueExploreHref = motif?.urn?.slug
        ? `/urns/${motif.urn.slug}?focus=next&fromMotif=${motifId}`
        : "/explore";

    useEffect(() => {
        let cancelled = false;
        async function load() {
            if (!motifId) return;
            if (status !== "authed") return;

            setLoading(true);
            setError(null);
            setSubmitError(null);
            setResult(null);
            setProgressChecked(false);
            try {
                const motifRes = await getMotifDetail(motifId);
                if (cancelled) return;
                setMotif(motifRes);

                if (motifRes?.urn?.slug) {
                    await hydrateProgressForUrn(motifRes.urn.slug);
                }
                if (cancelled) return;
                setProgressChecked(true);

                const latestProgress =
                    useMotifStore.getState().progressByMotifId[motifId];
                const unlocked =
                    latestProgress?.status &&
                    latestProgress.status !== "hidden";
                if (!unlocked) {
                    setError(
                        "Bạn chưa khám phá họa tiết này. Hãy khám phá trên mô hình 3D trước!",
                    );
                    return;
                }

                const quizRes = await getMotifQuiz({ motifId });
                if (cancelled) return;

                setQuiz(quizRes);
                setAnswers({});
                setStartedAt(Date.now());
                setElapsedTime(0);
                setCurrentQuestionIndex(0);
                const needsMeshOptions = Array.isArray(quizRes?.questions)
                    ? quizRes.questions.some(
                          (q) => q?.question_type === "mesh_location",
                      )
                    : false;
                if (needsMeshOptions && motifRes?.urn?.slug) {
                    try {
                        const urnRes = await getMotifsByUrn(motifRes.urn.slug);
                        if (!cancelled) setUrnMotifs(urnRes?.motifs || []);
                    } catch {
                        if (!cancelled) setUrnMotifs([]);
                    }
                } else {
                    setUrnMotifs([]);
                }

                logAnalyticsEvent({
                    name: "quiz_start",
                    payload: {
                        motif_id: motifId,
                        urn_id: motifRes?.urn?.id || null,
                        source: "client",
                    },
                    path: `/motif/${motifId}/quiz`,
                }).catch(() => null);
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
    }, [motifId, status, hydrateProgressForUrn]);

    // Timer effect
    useEffect(() => {
        if (!startedAt || result || submitting) return;

        const interval = setInterval(() => {
            setElapsedTime(Math.floor((Date.now() - startedAt) / 1000));
        }, 1000);

        return () => clearInterval(interval);
    }, [startedAt, result, submitting]);

    // Keyboard navigation
    useEffect(() => {
        if (result || loading || !quiz?.questions?.length) return;

        function handleKeyDown(e) {
            if (e.key === "ArrowRight") {
                if (currentQuestionIndex < quiz.questions.length - 1) {
                    setCurrentQuestionIndex((prev) => prev + 1);
                }
            } else if (e.key === "ArrowLeft") {
                if (currentQuestionIndex > 0) {
                    setCurrentQuestionIndex((prev) => prev - 1);
                }
            }
        }

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [currentQuestionIndex, quiz, result, loading]);

    function setAnswer(questionId, answer, meta) {
        setAnswers((prev) => ({ ...prev, [questionId]: answer }));
        if (!meta?.type) return;
        logAnalyticsEvent({
            name: "quiz_answer_selected",
            payload: {
                motif_id: motifId,
                question_id: String(questionId),
                question_type: meta.type,
                source: "client",
            },
            path: `/motif/${motifId}/quiz`,
        }).catch(() => null);
    }

    const handleNext = useCallback(() => {
        if (quiz && currentQuestionIndex < quiz.questions.length - 1) {
            setCurrentQuestionIndex((prev) => prev + 1);
        }
    }, [quiz, currentQuestionIndex]);

    const handlePrev = useCallback(() => {
        if (currentQuestionIndex > 0) {
            setCurrentQuestionIndex((prev) => prev - 1);
        }
    }, [currentQuestionIndex]);

    async function handleSubmit() {
        if (status !== "authed") return;
        if (!quiz?.questions?.length) return;
        setSubmitting(true);
        setError(null);
        setSubmitError(null);
        setResult(null);
        try {
            const timeTakenSeconds = startedAt
                ? Math.max(0, Math.round((Date.now() - startedAt) / 1000))
                : undefined;
            const payloadAnswers = quiz.questions.map((q) => ({
                question_id: q.id,
                answer: answers[q.id] ?? "",
            }));

            const res = await submitQuiz({
                motifId,
                answers: payloadAnswers,
                timeTakenSeconds,
            });
            setResult(res);
            logAnalyticsEvent({
                name: "quiz_complete",
                payload: {
                    motif_id: motifId,
                    urn_id: motif?.urn?.id || null,
                    percentage: res.percentage,
                    passed: res.passed,
                    attempts: res.attempts,
                    source: "client",
                },
                path: `/motif/${motifId}/quiz`,
            }).catch(() => null);
            if (res.passed && res.status === "mastered") {
                logAnalyticsEvent({
                    name: "mastery_complete",
                    payload: {
                        motif_id: motifId,
                        urn_id: motif?.urn?.id || null,
                        percentage: res.percentage,
                        source: "client",
                    },
                    path: `/motif/${motifId}/quiz`,
                }).catch(() => null);
            }

            if (res.passed) {
                toast.success(
                    `✅ Chúc mừng! Bạn đã đạt ${res.score}/${res.max_score} điểm!`,
                );
                if (res.xp_awarded > 0) {
                    toast.success(`+${res.xp_awarded} XP`, { icon: "🌟" });
                }
            } else {
                toast.error(`Bạn chưa đạt điểm đậu. Hãy thử lại!`);
            }

            useMotifStore.getState().applyProgressUpdate({
                motifId,
                status: res.status,
                xpAwarded: res.xp_awarded,
                totalXp: res.total_xp,
            });
            await fetchMe();
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            setSubmitError(msg);
            toast.error(`❌ Lỗi: ${msg}`);
        } finally {
            setSubmitting(false);
        }
    }

    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
    }

    if (status !== "authed") {
        return (
            <main className="mx-auto max-w-4xl px-6 py-10">
                <div className="rounded-xl border bg-card p-6">
                    <h1 className="text-xl font-display font-semibold">
                        Bài kiểm tra
                    </h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Vui lòng đăng nhập để làm bài kiểm tra.
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

    // Loading State
    if (loading) {
        return (
            <main className="mx-auto max-w-4xl px-6 py-10">
                <div className="text-center text-sm text-muted-foreground">
                    Đang tải bài kiểm tra...
                </div>
            </main>
        );
    }

    // Error State
    if (error) {
        if (progressChecked && !isDiscovered) {
            return (
                <main className="mx-auto max-w-4xl px-6 py-10">
                    <div className="rounded-2xl border border-border bg-card p-6">
                        <h1 className="text-xl font-display font-semibold text-foreground">
                            Họa tiết đã khóa
                        </h1>
                        <p className="mt-2 text-sm text-muted-foreground">
                            Bạn cần khám phá họa tiết trên mô hình 3D trước khi
                            làm bài kiểm tra.
                        </p>
                        <div className="mt-4 flex flex-wrap gap-3">
                            <Link
                                href="/dashboard"
                                className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
                            >
                                Về Learning Hub
                            </Link>
                            <Link
                                href="/explore"
                                className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted"
                            >
                                Khám phá Cửu Đỉnh
                            </Link>
                        </div>
                    </div>
                </main>
            );
        }

        return (
            <main className="mx-auto max-w-4xl px-6 py-10">
                <div className="rounded-lg bg-destructive/10 p-4 text-sm text-destructive">
                    {error}
                </div>
                <button
                    onClick={() => window.location.reload()}
                    className="mt-4 text-sm font-medium text-primary hover:text-primary/80"
                >
                    Thử lại
                </button>
            </main>
        );
    }

    // Result State
    if (result) {
        return (
            <main className="mx-auto max-w-4xl px-6 py-10">
                <div className="mb-6 flex items-center justify-between">
                    <h1 className="text-2xl font-display font-bold text-foreground">
                        Kết quả bài kiểm tra
                    </h1>
                    <div className="flex items-center gap-3">
                        <Link
                            href={continueExploreHref}
                            className="text-sm font-medium text-primary hover:text-primary/80"
                        >
                            Tiếp tục khám phá →
                        </Link>
                        <Link
                            href="/dashboard"
                            className="text-sm font-medium text-primary hover:text-primary/80"
                        >
                            Về Learning Hub
                        </Link>
                        <Link
                            href={`/motif/${motifId}`}
                            className="text-sm font-medium text-primary hover:text-primary/80"
                        >
                            Quay lại bài học →
                        </Link>
                    </div>
                </div>

                <div className="overflow-hidden rounded-2xl border bg-card shadow-sm transition-all duration-500 ease-out">
                    <div
                        className={`p-8 text-center ${result.passed ? "bg-success/10" : "bg-bronze/10"}`}
                    >
                        <div
                            className={`font-display tabular-nums text-5xl font-bold ${result.passed ? "text-success" : "text-bronze"}`}
                        >
                            {result.percentage}%
                        </div>
                        <div className="mt-2 text-lg font-medium text-foreground">
                            {result.passed
                                ? "Làm rất tốt!"
                                : "Hãy tiếp tục luyện tập!"}
                        </div>
                        <div className="mt-1 text-sm text-muted-foreground">
                            Điểm:{" "}
                            <span className="font-display tabular-nums">
                                {result.score}
                            </span>
                            /
                            <span className="font-display tabular-nums">
                                {result.max_score}
                            </span>{" "}
                            · +
                            <span className="font-display tabular-nums">
                                {result.xp_awarded}
                            </span>{" "}
                            XP nhận được
                        </div>
                    </div>

                    <div className="bg-card p-6">
                        <h3 className="mb-4 font-display font-semibold text-foreground">
                            Xem lại câu trả lời
                        </h3>
                        <div className="space-y-6">
                            {quiz?.questions.map((q, idx) => {
                                const qResult = result.results.find(
                                    (r) => r.question_id === q.id,
                                );
                                const isCorrect = qResult?.correct;
                                const explanation = qResult?.explanation;

                                return (
                                    <div
                                        key={q.id}
                                        className="border-b border-border pb-4 last:border-0 last:pb-0"
                                    >
                                        <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                            Câu hỏi{" "}
                                            <span className="font-display tabular-nums">
                                                {idx + 1}
                                            </span>
                                        </div>
                                        <div className="mt-1 font-medium text-foreground">
                                            {q.question_text}
                                        </div>
                                        <div className="mt-2 text-sm">
                                            <span className="text-muted-foreground">
                                                Câu trả lời của bạn:{" "}
                                            </span>
                                            <span
                                                className={`font-medium ${isCorrect ? "text-success" : "text-destructive"}`}
                                            >
                                                {answers[q.id] || (
                                                    <span className="italic text-muted">
                                                        Bỏ qua
                                                    </span>
                                                )}
                                            </span>
                                            {!isCorrect &&
                                                qResult?.correct_answer && (
                                                    <span className="text-muted-foreground ml-2">
                                                        (Đáp án đúng:{" "}
                                                        <span className="text-success font-medium">
                                                            {
                                                                qResult.correct_answer
                                                            }
                                                        </span>
                                                        )
                                                    </span>
                                                )}
                                        </div>

                                        {explanation && (
                                            <div
                                                className={`mt-3 rounded-lg p-3 text-sm border ${
                                                    isCorrect
                                                        ? "bg-success/10 text-success border-success/20"
                                                        : "bg-destructive/10 text-destructive border-destructive/20"
                                                }`}
                                            >
                                                <span className="font-semibold block mb-1">
                                                    Giải thích:
                                                </span>
                                                {explanation}
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    <div className="flex flex-wrap justify-center gap-3 border-t border-border bg-muted/50 p-6">
                        <Link
                            href={continueExploreHref}
                            className="rounded-lg border border-border px-6 py-2.5 text-sm font-semibold hover:bg-muted"
                        >
                            Tiếp tục khám phá
                        </Link>
                        <Link
                            href="/dashboard"
                            className="rounded-lg border border-border px-6 py-2.5 text-sm font-semibold hover:bg-muted"
                        >
                            Về Learning Hub
                        </Link>
                        <button
                            onClick={() => window.location.reload()}
                            className="rounded-lg bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                        >
                            Làm lại bài kiểm tra
                        </button>
                    </div>
                </div>
            </main>
        );
    }

    // Active Quiz State
    const currentQuestion = quiz?.questions?.[currentQuestionIndex];
    const progressPercent = quiz?.questions?.length
        ? ((currentQuestionIndex + 1) / quiz.questions.length) * 100
        : 0;

    const imageOptions = (() => {
        if (
            !currentQuestion ||
            currentQuestion.question_type !== "image_select"
        )
            return [];
        const raw = Array.isArray(currentQuestion.options)
            ? currentQuestion.options
            : [];
        return raw
            .map((opt, idx) => {
                if (typeof opt === "string") {
                    return {
                        value: opt,
                        label: opt,
                        image:
                            opt.startsWith("http") || opt.includes("/")
                                ? opt
                                : null,
                    };
                }
                if (opt && typeof opt === "object") {
                    const value =
                        opt.value ??
                        opt.answer ??
                        opt.id ??
                        opt.label ??
                        opt.text ??
                        `option-${idx + 1}`;
                    const label =
                        opt.label ??
                        opt.text ??
                        opt.value ??
                        `Option ${idx + 1}`;
                    const image =
                        opt.image_url ||
                        opt.image ||
                        opt.src ||
                        opt.url ||
                        null;
                    return {
                        value: String(value),
                        label: String(label),
                        image,
                    };
                }
                return null;
            })
            .filter(Boolean);
    })();

    const meshOptions = (() => {
        if (
            !currentQuestion ||
            currentQuestion.question_type !== "mesh_location"
        )
            return [];
        if (urnMotifs.length) {
            return urnMotifs
                .filter((m) => m?.mesh_name)
                .map((m) => ({
                    value: m.mesh_name,
                    label: m.name || m.mesh_name,
                }));
        }
        if (Array.isArray(currentQuestion.options)) {
            return currentQuestion.options
                .map((opt, idx) => {
                    if (typeof opt === "string") {
                        return { value: opt, label: opt };
                    }
                    if (opt && typeof opt === "object") {
                        const value =
                            opt.value ??
                            opt.mesh_name ??
                            opt.label ??
                            opt.text ??
                            `option-${idx + 1}`;
                        const label =
                            opt.label ??
                            opt.text ??
                            opt.value ??
                            `Option ${idx + 1}`;
                        return { value: String(value), label: String(label) };
                    }
                    return null;
                })
                .filter(Boolean);
        }
        return [];
    })();

    const choiceOptions = (() => {
        if (!currentQuestion || !Array.isArray(currentQuestion.options))
            return [];
        return currentQuestion.options
            .map((opt, idx) => {
                if (typeof opt === "string") {
                    return { value: opt, label: opt };
                }
                if (opt && typeof opt === "object") {
                    const value =
                        opt.value ??
                        opt.answer ??
                        opt.id ??
                        opt.label ??
                        opt.text ??
                        `option-${idx + 1}`;
                    const label =
                        opt.label ??
                        opt.text ??
                        opt.value ??
                        `Option ${idx + 1}`;
                    return { value: String(value), label: String(label) };
                }
                return null;
            })
            .filter(Boolean);
    })();

    return (
        <main className="mx-auto max-w-3xl px-6 py-10">
            {/* Header */}
            <div className="mb-8">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-display font-bold text-foreground">
                            {motif?.name
                                ? `${motif.name} · Bài kiểm tra`
                                : "Bài kiểm tra"}
                        </h1>
                        <p className="text-sm text-muted-foreground">
                            Câu hỏi{" "}
                            <span className="font-display tabular-nums">
                                {currentQuestionIndex + 1}
                            </span>{" "}
                            /{" "}
                            <span className="font-display tabular-nums">
                                {quiz?.questions?.length ?? "—"}
                            </span>
                        </p>
                    </div>
                    <div className="text-right">
                        <div className="font-display tabular-nums text-lg font-medium text-primary">
                            {formatTime(elapsedTime)}
                        </div>
                        <div className="text-xs text-muted-foreground">
                            Thời gian đã trôi
                        </div>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-muted">
                    <div
                        className="h-full bg-primary transition-all duration-300 ease-out"
                        style={{ width: `${progressPercent}%` }}
                    />
                </div>
            </div>

            {submitError ? (
                <div className="mb-6 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive">
                    <div className="font-semibold">
                        Không thể nộp bài kiểm tra
                    </div>
                    <div className="mt-1">{submitError}</div>
                    <button
                        onClick={handleSubmit}
                        disabled={submitting}
                        className="mt-3 inline-flex items-center gap-2 rounded-md bg-destructive px-3 py-1.5 text-xs font-semibold text-destructive-foreground hover:bg-destructive/90 disabled:cursor-wait disabled:opacity-70"
                    >
                        {submitting ? "Đang thử lại..." : "Thử gửi lại"}
                    </button>
                </div>
            ) : null}

            {/* Question Card */}
            {currentQuestion ? (
                <div className="rounded-2xl border bg-card p-8 shadow-sm">
                    <h2 className="text-lg font-display font-medium text-foreground">
                        {currentQuestion.question_text}
                    </h2>

                    <div className="mt-6 space-y-3">
                        {currentQuestion.question_type === "image_select" ? (
                            imageOptions.length ? (
                                <div className="grid gap-4 sm:grid-cols-2">
                                    {imageOptions.map((opt) => {
                                        const isSelected =
                                            (answers[currentQuestion.id] ??
                                                "") === opt.value;
                                        return (
                                            <button
                                                key={opt.value}
                                                type="button"
                                                onClick={() =>
                                                    setAnswer(
                                                        currentQuestion.id,
                                                        opt.value,
                                                        {
                                                            type: currentQuestion.question_type,
                                                        },
                                                    )
                                                }
                                                className={[
                                                    "overflow-hidden rounded-xl border text-left transition-all",
                                                    isSelected
                                                        ? "border-primary ring-2 ring-primary/40 bg-primary/10"
                                                        : "border-border hover:border-primary/50 hover:bg-muted",
                                                ].join(" ")}
                                            >
                                                <div className="aspect-video w-full bg-muted">
                                                    {opt.image ? (
                                                        <img
                                                            src={opt.image}
                                                            alt={opt.label}
                                                            className="h-full w-full object-cover"
                                                        />
                                                    ) : (
                                                        <div className="flex h-full w-full items-center justify-center text-xs text-muted-foreground">
                                                            Không có hình ảnh
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="px-3 py-2 text-sm font-medium">
                                                    {opt.label}
                                                </div>
                                            </button>
                                        );
                                    })}
                                </div>
                            ) : (
                                <div className="rounded-xl border border-border bg-muted/50 p-4 text-sm text-muted-foreground">
                                    Không có lựa chọn hình ảnh cho câu hỏi này.
                                </div>
                            )
                        ) : currentQuestion.question_type ===
                          "mesh_location" ? (
                            meshOptions.length ? (
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-muted-foreground">
                                        Chọn vị trí họa tiết
                                    </label>
                                    <select
                                        value={
                                            answers[currentQuestion.id] ?? ""
                                        }
                                        onChange={(e) =>
                                            setAnswer(
                                                currentQuestion.id,
                                                e.target.value,
                                                {
                                                    type: currentQuestion.question_type,
                                                },
                                            )
                                        }
                                        className="w-full rounded-xl border-input bg-input px-4 py-3 text-sm text-foreground focus:border-primary focus:ring-primary"
                                    >
                                        <option value="">
                                            -- Chọn vị trí --
                                        </option>
                                        {meshOptions.map((opt) => (
                                            <option
                                                key={opt.value}
                                                value={opt.value}
                                            >
                                                {opt.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    <div className="text-sm text-muted-foreground">
                                        Chưa có dữ liệu vị trí. Nhập mã mesh nếu
                                        biết.
                                    </div>
                                    <input
                                        type="text"
                                        value={
                                            answers[currentQuestion.id] ?? ""
                                        }
                                        onChange={(e) =>
                                            setAnswer(
                                                currentQuestion.id,
                                                e.target.value,
                                                {
                                                    type: currentQuestion.question_type,
                                                },
                                            )
                                        }
                                        className="w-full rounded-xl border-input px-4 py-3 text-sm focus:border-primary focus:ring-primary bg-input"
                                        placeholder="Ví dụ: mesh_name"
                                    />
                                </div>
                            )
                        ) : choiceOptions.length ? (
                            choiceOptions.map((opt) => {
                                const isSelected =
                                    (answers[currentQuestion.id] ?? "") ===
                                    opt.value;
                                return (
                                    <label
                                        key={opt.value}
                                        className={`flex cursor-pointer items-center gap-3 rounded-xl border p-4 transition-all duration-200 ${
                                            isSelected
                                                ? "border-primary bg-primary/10 ring-1 ring-primary"
                                                : "border-border hover:bg-muted hover:border-input"
                                        }`}
                                    >
                                        <div
                                            className={`flex h-5 w-5 items-center justify-center rounded-full border ${
                                                isSelected
                                                    ? "border-primary bg-primary"
                                                    : "border-input bg-card"
                                            }`}
                                        >
                                            {isSelected && (
                                                <div className="h-2 w-2 rounded-full bg-primary-foreground" />
                                            )}
                                        </div>
                                        <input
                                            type="radio"
                                            name={`q-${currentQuestion.id}`}
                                            value={opt.value}
                                            checked={isSelected}
                                            onChange={() =>
                                                setAnswer(
                                                    currentQuestion.id,
                                                    opt.value,
                                                )
                                            }
                                            className="hidden"
                                        />
                                        <span
                                            className={`text-sm ${isSelected ? "font-medium text-primary" : "text-foreground"}`}
                                        >
                                            {opt.label}
                                        </span>
                                    </label>
                                );
                            })
                        ) : (
                            <div className="mt-4">
                                <input
                                    type="text"
                                    value={answers[currentQuestion.id] ?? ""}
                                    onChange={(e) =>
                                        setAnswer(
                                            currentQuestion.id,
                                            e.target.value,
                                        )
                                    }
                                    className="w-full rounded-xl border-input px-4 py-3 text-sm focus:border-primary focus:ring-primary bg-input"
                                    placeholder="Nhập câu trả lời tại đây..."
                                />
                            </div>
                        )}
                    </div>
                </div>
            ) : null}

            {/* Navigation */}
            <div className="mt-8 flex items-center justify-between">
                <button
                    onClick={handlePrev}
                    disabled={currentQuestionIndex === 0}
                    className={`rounded-lg px-6 py-2.5 text-sm font-medium transition-colors ${
                        currentQuestionIndex === 0
                            ? "cursor-not-allowed text-muted"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    }`}
                >
                    ← Câu trước
                </button>

                {currentQuestionIndex === (quiz?.questions?.length ?? 0) - 1 ? (
                    <button
                        onClick={handleSubmit}
                        disabled={submitting}
                        className={`rounded-lg px-8 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition-all ${
                            submitting
                                ? "cursor-wait bg-primary/50"
                                : "bg-primary hover:bg-primary/90 hover:shadow"
                        }`}
                    >
                        {submitting ? "Đang nộp..." : "Nộp bài"}
                    </button>
                ) : (
                    <button
                        onClick={handleNext}
                        className="rounded-lg bg-primary px-8 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition-all hover:bg-primary/90 hover:shadow"
                    >
                        Câu tiếp →
                    </button>
                )}
            </div>

            <div className="mt-8 text-center text-xs text-muted-foreground">
                Dùng phím mũi tên để điều hướng · Điểm đậu:{" "}
                <span className="font-display tabular-nums">
                    {quiz?.pass_percent ?? "—"}
                </span>
                %
            </div>
        </main>
    );
}
