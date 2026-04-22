"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";

import { ApiError, getUrnDetail, getUrnExam, submitUrnExam } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

const STORAGE_KEY_PREFIX = "luuniensuki:urn-exam";

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

export default function UrnExamPage() {
    const params = useParams();
    const router = useRouter();
    const urnSlug = useMemo(
        () => (typeof params?.urnSlug === "string" ? params.urnSlug : ""),
        [params],
    );

    const status = useAuthStore((s) => s.status);

    const [urn, setUrn] = useState(null);
    const [exam, setExam] = useState(null);
    const [answers, setAnswers] = useState({});
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [startedAt, setStartedAt] = useState(null);
    const [elapsedTime, setElapsedTime] = useState(0);

    const [loading, setLoading] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [eligibility, setEligibility] = useState(null);

    useEffect(() => {
        let cancelled = false;
        async function load() {
            if (!urnSlug) return;

            setLoading(true);
            setError(null);
            setEligibility(null);

            try {
                const urnRes = await getUrnDetail(urnSlug);
                if (cancelled) return;
                setUrn(urnRes?.urn ?? null);

                if (status === "authed") {
                    const examRes = await getUrnExam({ urnSlug });
                    if (cancelled) return;
                    setExam(examRes ?? null);
                } else {
                    setExam(null);
                }
            } catch (err) {
                if (cancelled) return;
                if (
                    err instanceof ApiError &&
                    err.status === 403 &&
                    err.data?.detail &&
                    typeof err.data.detail === "object"
                ) {
                    setEligibility(err.data.detail);
                    setError(err.data.detail.message || err.message);
                } else {
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
    }, [urnSlug, status]);

    useEffect(() => {
        if (!exam?.questions?.length) return;
        setAnswers({});
        setCurrentQuestionIndex(0);
        setStartedAt(Date.now());
        setElapsedTime(0);
    }, [exam]);

    useEffect(() => {
        if (!startedAt || submitting) return;
        const interval = setInterval(() => {
            setElapsedTime(Math.floor((Date.now() - startedAt) / 1000));
        }, 1000);
        return () => clearInterval(interval);
    }, [startedAt, submitting]);

    useEffect(() => {
        if (loading || submitting || !exam?.questions?.length) return;

        function handleKeyDown(e) {
            if (e.key === "ArrowRight") {
                if (currentQuestionIndex < exam.questions.length - 1) {
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
    }, [currentQuestionIndex, exam, loading, submitting]);

    function setAnswer(questionId, answer) {
        setAnswers((prev) => ({ ...prev, [questionId]: answer }));
    }

    const currentQuestion = exam?.questions?.[currentQuestionIndex];
    const questionCount = exam?.questions?.length ?? 0;
    const progressPercent = questionCount
        ? ((currentQuestionIndex + 1) / questionCount) * 100
        : 0;

    const handleNext = useCallback(() => {
        if (!exam?.questions?.length) return;
        if (currentQuestionIndex < exam.questions.length - 1) {
            setCurrentQuestionIndex((prev) => prev + 1);
        }
    }, [exam, currentQuestionIndex]);

    const handlePrev = useCallback(() => {
        if (currentQuestionIndex > 0) {
            setCurrentQuestionIndex((prev) => prev - 1);
        }
    }, [currentQuestionIndex]);

    const handleSubmit = useCallback(async () => {
        if (status !== "authed") return;
        if (!exam?.questions?.length) return;

        setSubmitting(true);
        setError(null);

        try {
            const timeTakenSeconds = startedAt
                ? Math.max(0, Math.round((Date.now() - startedAt) / 1000))
                : undefined;
            const payloadAnswers = {};
            for (const q of exam.questions) {
                payloadAnswers[String(q.id)] = answers[q.id] ?? "";
            }

            const result = await submitUrnExam({
                urnSlug,
                answers: payloadAnswers,
                timeTakenSeconds,
            });

            const storageKey = `${STORAGE_KEY_PREFIX}:${urnSlug}`;
            const payload = {
                urn: { slug: urnSlug, name: urn?.name ?? urnSlug },
                exam: {
                    pass_percent: exam?.pass_percent ?? 80,
                    questions: exam?.questions ?? [],
                },
                answers,
                started_at: startedAt,
                time_taken_seconds: timeTakenSeconds ?? null,
                submitted_at: Date.now(),
                result,
            };

            try {
                sessionStorage.setItem(storageKey, JSON.stringify(payload));
            } catch {}

            if (result?.passed) {
                toast.success(
                    `✅ Chúc mừng! Bạn đã đạt ${result.score}/${result.max_score} điểm!`,
                );
            } else {
                toast.error("Bạn chưa đạt điểm đậu. Hãy thử lại!");
            }

            router.push(`/urns/${urnSlug}/exam/result`);
        } catch (err) {
            if (
                err instanceof ApiError &&
                err.status === 403 &&
                err.data?.detail &&
                typeof err.data.detail === "object"
            ) {
                const msg = err.data.detail.message || err.message;
                setEligibility(err.data.detail);
                setError(msg);
                toast.error(`❌ Lỗi: ${msg}`);
            } else {
                const msg = err instanceof Error ? err.message : String(err);
                setError(msg);
                toast.error(`❌ Lỗi: ${msg}`);
            }
        } finally {
            setSubmitting(false);
        }
    }, [status, exam, answers, startedAt, router, urnSlug, urn]);

    if (loading) {
        return (
            <main className="mx-auto max-w-4xl px-6 py-10">
                <div className="text-center text-sm text-muted-foreground">
                    Đang tải bài kiểm tra...
                </div>
            </main>
        );
    }

    if (error) {
        const missingMotifs = Array.isArray(eligibility?.missing_motifs)
            ? eligibility.missing_motifs
            : [];
        return (
            <main className="mx-auto max-w-4xl px-6 py-10">
                <div className="rounded-lg bg-destructive/10 p-4 text-sm text-destructive">
                    {error}
                </div>
                {missingMotifs.length ? (
                    <div className="mt-4 rounded-lg border border-border bg-card p-4 text-sm text-foreground">
                        <div className="font-semibold">
                            Họa tiết chưa hoàn thành
                        </div>
                        <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-muted-foreground">
                            {missingMotifs.slice(0, 6).map((motif) => (
                                <li key={motif?.id || motif?.name}>
                                    {motif?.name || "Họa tiết"}
                                </li>
                            ))}
                        </ul>
                        {missingMotifs.length > 6 ? (
                            <div className="mt-2 text-xs text-muted-foreground">
                                +{missingMotifs.length - 6} họa tiết khác
                            </div>
                        ) : null}
                    </div>
                ) : null}
                <div className="mt-4 flex flex-wrap gap-3">
                    <button
                        onClick={() => window.location.reload()}
                        className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
                    >
                        Thử lại
                    </button>
                    <Link
                        href={`/urns/${urnSlug}`}
                        className="rounded-lg border px-4 py-2 text-sm font-medium"
                    >
                        Quay lại đỉnh
                    </Link>
                </div>
            </main>
        );
    }

    if (status !== "authed") {
        return (
            <main className="mx-auto max-w-4xl px-6 py-10">
                <div className="rounded-xl border bg-card p-6">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                            <h1 className="text-xl font-display font-semibold">
                                {urn?.name
                                    ? `${urn.name} · Bài kiểm tra`
                                    : "Bài kiểm tra"}
                            </h1>
                            <p className="mt-1 text-sm text-muted-foreground">
                                Vui lòng đăng nhập để làm bài kiểm tra.
                            </p>
                        </div>
                        <Link
                            href={`/urns/${urnSlug}`}
                            className="text-sm font-medium text-primary hover:text-primary/80"
                        >
                            Quay lại đỉnh →
                        </Link>
                    </div>
                    <div className="mt-4 flex gap-3">
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

    if (!exam?.questions?.length) {
        return (
            <main className="mx-auto max-w-4xl px-6 py-10">
                <div className="rounded-xl border bg-card p-6">
                    <h1 className="text-xl font-display font-semibold">
                        {urn?.name
                            ? `${urn.name} · Bài kiểm tra`
                            : "Bài kiểm tra"}
                    </h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Hiện chưa có đề kiểm tra cho đỉnh này.
                    </p>
                    <div className="mt-4">
                        <Link
                            href={`/urns/${urnSlug}`}
                            className="text-sm font-medium text-primary hover:text-primary/80"
                        >
                            Quay lại đỉnh →
                        </Link>
                    </div>
                </div>
            </main>
        );
    }

    return (
        <main className="mx-auto max-w-3xl px-6 py-10">
            <div className="mb-8">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-display font-bold text-foreground">
                            {urn?.name
                                ? `${urn.name} · Bài kiểm tra`
                                : "Bài kiểm tra"}
                        </h1>
                        <p className="text-sm text-muted-foreground">
                            Câu hỏi{" "}
                            <span className="font-display tabular-nums">
                                {currentQuestionIndex + 1}
                            </span>{" "}
                            /{" "}
                            <span className="font-display tabular-nums">
                                {questionCount}
                            </span>
                        </p>
                        <div className="mt-2">
                            <Link
                                href={`/urns/${urnSlug}`}
                                className="text-xs font-medium text-primary hover:text-primary/80"
                            >
                                ← Quay lại đỉnh
                            </Link>
                        </div>
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

                <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-muted">
                    <div
                        className="h-full bg-primary transition-all duration-300 ease-out"
                        style={{ width: `${progressPercent}%` }}
                    />
                </div>
            </div>

            {currentQuestion ? (
                <div className="rounded-2xl border bg-card p-8 shadow-sm">
                    <h2 className="text-lg font-display font-medium text-foreground">
                        {currentQuestion.question_text}
                    </h2>

                    <div className="mt-6 space-y-3">
                        {Array.isArray(currentQuestion.options) &&
                        currentQuestion.options.length ? (
                            currentQuestion.options.map((opt) => {
                                const isSelected =
                                    (answers[currentQuestion.id] ?? "") === opt;
                                return (
                                    <label
                                        key={opt}
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
                                            value={opt}
                                            checked={isSelected}
                                            onChange={() =>
                                                setAnswer(
                                                    currentQuestion.id,
                                                    opt,
                                                )
                                            }
                                            className="hidden"
                                        />
                                        <span
                                            className={`text-sm ${isSelected ? "font-medium text-primary" : "text-foreground"}`}
                                        >
                                            {opt}
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
                                    className="w-full rounded-xl border-input bg-input px-4 py-3 text-sm focus:border-primary focus:ring-primary"
                                    placeholder="Nhập câu trả lời tại đây..."
                                />
                            </div>
                        )}
                    </div>
                </div>
            ) : null}

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

                {currentQuestionIndex === questionCount - 1 ? (
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
                    {exam?.pass_percent ?? 80}
                </span>
                %
            </div>
        </main>
    );
}
