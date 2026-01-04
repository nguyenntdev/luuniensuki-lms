"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState, useCallback } from "react";

import { getLatestUrnExamAttempt, getMyBadges } from "@/lib/api";

const STORAGE_KEY_PREFIX = "luuniensuki:urn-exam";

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

export default function UrnExamResultPage() {
    const params = useParams();
    const router = useRouter();
    const urnSlug = useMemo(
        () => (typeof params?.urnSlug === "string" ? params.urnSlug : ""),
        [params],
    );

    const [payload, setPayload] = useState(null);
    const [loading, setLoading] = useState(false);
    const [loadError, setLoadError] = useState(null);
    const [badges, setBadges] = useState([]);
    const [badgeError, setBadgeError] = useState(null);

    useEffect(() => {
        if (!urnSlug) return;
        const storageKey = `${STORAGE_KEY_PREFIX}:${urnSlug}`;
        let cancelled = false;

        async function load() {
            setLoading(true);
            setLoadError(null);
            let storedPayload = null;
            try {
                const raw = sessionStorage.getItem(storageKey);
                if (raw) {
                    const parsed = JSON.parse(raw);
                    storedPayload = parsed;
                    if (!cancelled) setPayload(parsed);
                }
            } catch {
                if (!cancelled) setPayload(null);
            }

            try {
                const latest = await getLatestUrnExamAttempt({ urnSlug });
                if (cancelled) return;
                if (!latest) {
                    if (!storedPayload) setPayload(null);
                    return;
                }
                const normalized = {
                    urn: latest.urn,
                    exam: latest.exam,
                    answers: latest.answers,
                    time_taken_seconds: latest.time_taken_seconds ?? null,
                    submitted_at: latest.submitted_at
                        ? new Date(latest.submitted_at).getTime()
                        : null,
                    result: latest.result,
                };
                setPayload(normalized);
                try {
                    sessionStorage.setItem(
                        storageKey,
                        JSON.stringify(normalized),
                    );
                } catch {}
            } catch (err) {
                if (!cancelled) {
                    setLoadError(
                        err instanceof Error ? err.message : String(err),
                    );
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        load();
        return () => {
            cancelled = true;
        };
    }, [urnSlug]);

    useEffect(() => {
        let cancelled = false;
        async function loadBadges() {
            try {
                const res = await getMyBadges();
                if (!cancelled) setBadges(Array.isArray(res) ? res : []);
            } catch (err) {
                if (!cancelled) {
                    setBadgeError(
                        err instanceof Error ? err.message : String(err),
                    );
                }
            }
        }
        loadBadges();
        return () => {
            cancelled = true;
        };
    }, []);

    const handleRetry = useCallback(() => {
        if (!urnSlug) return;
        const storageKey = `${STORAGE_KEY_PREFIX}:${urnSlug}`;
        try {
            sessionStorage.removeItem(storageKey);
        } catch {}
        router.push(`/urns/${urnSlug}/exam`);
    }, [router, urnSlug]);

    if (!payload?.result) {
        return (
            <main className="mx-auto max-w-4xl px-6 py-10">
                <div className="rounded-xl border bg-card p-6">
                    <h1 className="text-xl font-display font-semibold">
                        Kết quả bài kiểm tra
                    </h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        {loading
                            ? "Đang tải kết quả..."
                            : loadError
                              ? loadError
                              : "Chưa có kết quả. Hãy làm bài kiểm tra trước."}
                    </p>
                    <div className="mt-4 flex gap-3">
                        <Link
                            href={`/urns/${urnSlug}/exam`}
                            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
                        >
                            Bắt đầu bài kiểm tra
                        </Link>
                        <Link
                            href={`/urns/${urnSlug}`}
                            className="rounded-lg border px-4 py-2 text-sm font-medium"
                        >
                            Quay lại đỉnh
                        </Link>
                    </div>
                </div>
            </main>
        );
    }

    const urnName = payload?.urn?.name || urnSlug;
    const exam = payload?.exam || {};
    const questions = Array.isArray(exam?.questions) ? exam.questions : [];
    const answers =
        payload?.answers && typeof payload.answers === "object"
            ? payload.answers
            : {};

    const result = payload.result;
    const passPercent = exam?.pass_percent ?? result?.pass_percent ?? 80;
    const submittedAtMs =
        typeof payload?.submitted_at === "number"
            ? payload.submitted_at
            : payload?.submitted_at
              ? new Date(payload.submitted_at).getTime()
              : null;
    const badgeCutoffMs =
        typeof submittedAtMs === "number"
            ? submittedAtMs - 5 * 60 * 1000
            : null;
    const badgesByExam =
        Array.isArray(badges) && badgeCutoffMs
            ? badges.filter((entry) => {
                  const earnedAt = entry?.earned_at
                      ? new Date(entry.earned_at).getTime()
                      : null;
                  return (
                      typeof earnedAt === "number" &&
                      !Number.isNaN(earnedAt) &&
                      earnedAt >= badgeCutoffMs
                  );
              })
            : [];
    const recentBadges = badgesByExam.length
        ? badgesByExam
        : Array.isArray(badges)
          ? badges.slice(0, 4)
          : [];
    const badgeHeading = badgesByExam.length
        ? "Huy hiệu vừa nhận"
        : "Huy hiệu gần đây";

    const timeTakenSeconds = (() => {
        if (typeof payload?.time_taken_seconds === "number")
            return payload.time_taken_seconds;
        if (typeof result?.time_taken_seconds === "number")
            return result.time_taken_seconds;
        if (
            typeof payload?.started_at === "number" &&
            typeof payload?.submitted_at === "number"
        ) {
            return Math.max(
                0,
                Math.round((payload.submitted_at - payload.started_at) / 1000),
            );
        }
        return null;
    })();

    const resultByQuestionId = (() => {
        const map = {};
        const list = Array.isArray(result?.results) ? result.results : [];
        for (const r of list) {
            const id = r?.question_id ?? r?.questionId ?? r?.id;
            if (!id) continue;
            map[String(id)] = r;
        }
        return map;
    })();

    return (
        <main className="mx-auto max-w-4xl px-6 py-10">
            <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-display font-bold text-foreground">
                        {urnName} · Kết quả bài kiểm tra
                    </h1>
                    <div className="mt-1 text-sm text-muted-foreground">
                        Điểm đậu:{" "}
                        <span className="font-display tabular-nums">
                            {passPercent}
                        </span>
                        %
                        {typeof timeTakenSeconds === "number" ? (
                            <>
                                {" "}
                                · Thời gian:{" "}
                                <span className="font-display tabular-nums">
                                    {formatTime(timeTakenSeconds)}
                                </span>
                            </>
                        ) : null}
                    </div>
                </div>
                <Link
                    href={`/urns/${urnSlug}`}
                    className="text-sm font-medium text-primary hover:text-primary/80"
                >
                    Quay lại đỉnh →
                </Link>
            </div>

            <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">
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
                        </span>
                    </div>
                    {result.certificate?.code ? (
                        <div className="mt-4 inline-flex flex-col items-center gap-2">
                            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                Chứng chỉ
                            </div>
                            <Link
                                href={`/certificates/${result.certificate.code}`}
                                className="rounded-full bg-primary px-4 py-1.5 text-xs font-semibold text-primary-foreground"
                            >
                                Xem chứng chỉ Lưu Niên Sử Kí
                            </Link>
                        </div>
                    ) : null}
                    {badgeError ? (
                        <div className="mt-4 text-xs text-muted-foreground">
                            {badgeError}
                        </div>
                    ) : null}
                    {recentBadges.length ? (
                        <div className="mt-4 flex flex-col items-center gap-2">
                            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                {badgeHeading}
                            </div>
                            <div className="flex flex-wrap justify-center gap-3">
                                {recentBadges.map((entry) => (
                                    <div
                                        key={
                                            entry?.badge?.slug ||
                                            entry?.badge?.name
                                        }
                                        className="flex items-center gap-2 rounded-full bg-muted/40 px-3 py-1.5"
                                    >
                                        {entry?.badge?.icon_url ? (
                                            <img
                                                src={entry.badge.icon_url}
                                                alt={entry.badge.name}
                                                className="h-5 w-5 rounded-full object-cover"
                                                loading="lazy"
                                            />
                                        ) : (
                                            <span className="text-sm">🏅</span>
                                        )}
                                        <span className="text-xs font-medium text-foreground">
                                            {entry?.badge?.name || "Huy hiệu"}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : null}
                </div>

                <div className="bg-card p-6">
                    <h3 className="mb-4 font-display font-semibold text-foreground">
                        Xem lại câu trả lời
                    </h3>
                    <div className="space-y-6">
                        {questions.map((q, idx) => {
                            const qId = String(q.id);
                            const qResult = resultByQuestionId[qId];
                            const isCorrect = Boolean(qResult?.correct);
                            const userAnswer =
                                qResult?.user_answer ?? answers[qId] ?? "";
                            const correctAnswer =
                                qResult?.correct_answer ??
                                q?.correct_answer ??
                                null;
                            const explanation =
                                qResult?.explanation ?? q?.explanation ?? null;

                            return (
                                <div
                                    key={qId}
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
                                            {userAnswer ? (
                                                userAnswer
                                            ) : (
                                                <span className="italic text-muted">
                                                    Bỏ qua
                                                </span>
                                            )}
                                        </span>
                                        {!isCorrect && correctAnswer ? (
                                            <span className="ml-2 text-muted-foreground">
                                                (Đáp án đúng:{" "}
                                                <span className="font-medium text-success">
                                                    {correctAnswer}
                                                </span>
                                                )
                                            </span>
                                        ) : null}
                                    </div>

                                    {explanation ? (
                                        <div
                                            className={`mt-3 rounded-lg border p-3 text-sm ${
                                                isCorrect
                                                    ? "border-success/20 bg-success/10 text-success"
                                                    : "border-destructive/20 bg-destructive/10 text-destructive"
                                            }`}
                                        >
                                            <span className="mb-1 block font-semibold">
                                                Giải thích:
                                            </span>
                                            {explanation}
                                        </div>
                                    ) : null}
                                </div>
                            );
                        })}
                    </div>
                </div>

                <div className="flex flex-wrap justify-center gap-3 border-t border-border bg-muted/50 p-6">
                    <button
                        onClick={handleRetry}
                        className="rounded-lg bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                    >
                        Làm lại bài kiểm tra
                    </button>
                    <Link
                        href={`/urns/${urnSlug}/exam`}
                        className="rounded-lg border px-6 py-2.5 text-sm font-semibold"
                    >
                        Xem lại đề
                    </Link>
                </div>
            </div>
        </main>
    );
}
