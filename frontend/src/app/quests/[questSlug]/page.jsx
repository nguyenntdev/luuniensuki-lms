"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import Skeleton from "@/components/Skeleton";
import { getQuestDetail, startQuest } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

const STATUS_LABELS = {
    locked: "Đã khóa",
    not_started: "Chưa bắt đầu",
    in_progress: "Đang thực hiện",
    completed: "Hoàn thành",
};

export default function QuestDetailPage() {
    const params = useParams();
    const questSlug = useMemo(
        () => (typeof params?.questSlug === "string" ? params.questSlug : ""),
        [params],
    );

    const status = useAuthStore((s) => s.status);
    const [quest, setQuest] = useState(null);
    const [loading, setLoading] = useState(false);
    const [starting, setStarting] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (status !== "authed" || !questSlug) return;
        let cancelled = false;

        async function load() {
            setLoading(true);
            setError(null);
            try {
                const res = await getQuestDetail({ questSlug });
                if (!cancelled) setQuest(res || null);
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
    }, [status, questSlug]);

    async function handleStartQuest() {
        if (!questSlug) return;
        setStarting(true);
        setError(null);
        try {
            const res = await startQuest({ questSlug });
            setQuest(res || null);
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err));
        } finally {
            setStarting(false);
        }
    }

    const progress = Math.round(Number(quest?.progress_percent || 0));
    const statusLabel = STATUS_LABELS[quest?.status] || quest?.status;
    const isLocked = quest?.is_locked;
    const canStart = quest?.status === "not_started" && !isLocked;

    return (
        <main className="mx-auto max-w-5xl px-6 py-10 pb-24">
            <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                    <Link
                        href="/quests"
                        className="text-sm font-medium text-primary hover:text-primary/80"
                    >
                        ← Quay lại Quest Map
                    </Link>
                    <h1 className="mt-2 text-3xl font-display font-bold text-foreground">
                        {loading ? <Skeleton className="h-7 w-48" /> : quest?.name}
                    </h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        {loading ? (
                            <Skeleton className="h-4 w-72" />
                        ) : (
                            quest?.description ||
                            "Hành trình khám phá văn hóa Cửu Đỉnh."
                        )}
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <span className="rounded-full border border-border px-3 py-1 text-xs font-semibold text-muted-foreground">
                        {statusLabel || "—"}
                    </span>
                    {canStart ? (
                        <button
                            type="button"
                            onClick={handleStartQuest}
                            disabled={starting}
                            className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
                        >
                            {starting ? "Đang bắt đầu..." : "Bắt đầu quest"}
                        </button>
                    ) : null}
                </div>
            </div>

            {error ? (
                <div className="mt-6 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
                    {error}
                </div>
            ) : null}

            {loading ? (
                <div className="mt-8 space-y-4">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-2/3" />
                </div>
            ) : (
                <>
                    <div className="mt-8 rounded-2xl border border-border bg-card p-6 shadow-sm">
                        <div className="flex items-center justify-between">
                            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                Tiến trình
                            </div>
                            <div className="text-xs text-muted-foreground">
                                {progress}%
                            </div>
                        </div>
                        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-muted">
                            <div
                                className="h-full bg-primary transition-all"
                                style={{ width: `${progress}%` }}
                            />
                        </div>

                        {quest?.lock_reason ? (
                            <div className="mt-4 rounded-lg bg-muted/60 p-3 text-xs text-muted-foreground">
                                {quest.lock_reason}
                            </div>
                        ) : null}

                        {quest?.certificate?.code ? (
                            <div className="mt-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-700">
                                Chứng nhận đã sẵn sàng:{" "}
                                <Link
                                    href={`/certificates/${quest.certificate.code}`}
                                    className="font-semibold underline underline-offset-2"
                                >
                                    Xem chứng nhận
                                </Link>
                            </div>
                        ) : null}
                    </div>

                    <div className="mt-6 space-y-4">
                        {quest?.steps?.length ? (
                            quest.steps.map((step) => (
                                <div
                                    key={step.id}
                                    className="rounded-2xl border border-border bg-card p-6 shadow-sm"
                                >
                                    <div className="flex items-start justify-between gap-4">
                                        <div>
                                            <h2 className="text-lg font-display font-semibold text-foreground">
                                                {step.title}
                                            </h2>
                                            {step.description ? (
                                                <p className="mt-1 text-sm text-muted-foreground">
                                                    {step.description}
                                                </p>
                                            ) : null}
                                        </div>
                                        <span className="rounded-full border border-border px-3 py-1 text-xs font-semibold text-muted-foreground">
                                            {Math.round(step.completion_percent)}%
                                        </span>
                                    </div>

                                    <div className="mt-4 space-y-2">
                                        {step.objectives.map((objective) => {
                                            const objProgress =
                                                objective.target_value > 0
                                                    ? Math.round(
                                                          (objective.current_value /
                                                              objective.target_value) *
                                                              100,
                                                      )
                                                    : 0;
                                            return (
                                                <div
                                                    key={objective.id}
                                                    className="rounded-xl border border-border/70 bg-secondary/30 p-3"
                                                >
                                                    <div className="flex items-center justify-between text-sm text-foreground">
                                                        <span className="font-semibold">
                                                            {objective.objective_type}
                                                        </span>
                                                        <span className="text-xs text-muted-foreground">
                                                            {objective.current_value}/
                                                            {objective.target_value}
                                                        </span>
                                                    </div>
                                                    <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-muted">
                                                        <div
                                                            className="h-full bg-primary transition-all"
                                                            style={{
                                                                width: `${objProgress}%`,
                                                            }}
                                                        />
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="rounded-xl border border-border bg-card p-6 text-sm text-muted-foreground">
                                Chưa có bước quest nào được định nghĩa.
                            </div>
                        )}
                    </div>
                </>
            )}
        </main>
    );
}
