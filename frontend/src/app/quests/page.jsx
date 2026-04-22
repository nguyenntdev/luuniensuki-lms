"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import Skeleton from "@/components/Skeleton";
import { getQuests } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

const STATUS_LABELS = {
    locked: "Đã khóa",
    not_started: "Chưa bắt đầu",
    in_progress: "Đang thực hiện",
    completed: "Hoàn thành",
};

export default function QuestsPage() {
    const status = useAuthStore((s) => s.status);
    const [quests, setQuests] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (status !== "authed") return;
        let cancelled = false;

        async function load() {
            setLoading(true);
            setError(null);
            try {
                const res = await getQuests();
                if (!cancelled) setQuests(Array.isArray(res) ? res : []);
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

    if (status !== "authed") {
        return (
            <main className="mx-auto max-w-5xl px-6 py-10">
                <div className="rounded-xl border border-border bg-card p-6">
                    <h1 className="text-xl font-display font-semibold">
                        Quest Map
                    </h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Vui lòng đăng nhập để xem hành trình học tập.
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
                        Quest Map
                    </h1>
                    <p className="mt-1 text-sm text-muted-foreground">
                        Chọn hành trình và theo dõi tiến trình qua từng thử
                        thách.
                    </p>
                </div>
                <Link
                    href="/dashboard"
                    className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted"
                >
                    Về Learning Hub
                </Link>
            </div>

            {error ? (
                <div className="mt-6 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
                    {error}
                </div>
            ) : null}

            <div className="mt-8 grid gap-4 md:grid-cols-2">
                {loading
                    ? Array.from({ length: 4 }).map((_, idx) => (
                          <div
                              key={`quest-skeleton-${idx}`}
                              className="rounded-2xl border border-border bg-card p-5"
                          >
                              <Skeleton className="h-5 w-40" />
                              <Skeleton className="mt-3 h-4 w-56" />
                              <Skeleton className="mt-4 h-2 w-full" />
                              <Skeleton className="mt-4 h-8 w-28" />
                          </div>
                      ))
                    : quests.map((quest) => {
                          const statusLabel =
                              STATUS_LABELS[quest.status] || quest.status;
                          const isLocked = quest.is_locked;
                          const progress = Math.round(
                              Number(quest.progress_percent || 0),
                          );
                          return (
                              <div
                                  key={quest.id}
                                  className={[
                                      "rounded-2xl border border-border bg-card p-5 shadow-sm",
                                      isLocked ? "opacity-80" : "",
                                  ].join(" ")}
                              >
                                  <div className="flex items-start justify-between gap-3">
                                      <div>
                                          <h2 className="text-lg font-display font-semibold text-foreground">
                                              {quest.name}
                                          </h2>
                                          <p className="mt-1 text-sm text-muted-foreground">
                                              {quest.description ||
                                                  "Hành trình khám phá Cửu Đỉnh."}
                                          </p>
                                      </div>
                                      <span className="rounded-full border border-border px-3 py-1 text-xs font-semibold text-muted-foreground">
                                          {statusLabel}
                                      </span>
                                  </div>

                                  <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-muted">
                                      <div
                                          className="h-full bg-primary transition-all"
                                          style={{ width: `${progress}%` }}
                                      />
                                  </div>
                                  <div className="mt-2 text-xs text-muted-foreground">
                                      Tiến trình:{" "}
                                      <span className="font-display tabular-nums text-foreground">
                                          {progress}%
                                      </span>
                                  </div>

                                  {isLocked ? (
                                      <div className="mt-3 rounded-lg bg-muted/60 p-3 text-xs text-muted-foreground">
                                          {quest.lock_reason ||
                                              "Hoàn thành quest trước để mở khóa."}
                                      </div>
                                  ) : null}

                                  <div className="mt-4 flex items-center justify-between">
                                      <div className="text-xs text-muted-foreground">
                                          {quest.rewards?.length
                                              ? `Thưởng: ${quest.rewards
                                                    .map((r) =>
                                                        r.reward_type === "xp"
                                                            ? `${r.amount} XP`
                                                            : r.reward_type,
                                                    )
                                                    .join(", ")}`
                                              : "Thưởng: chứng nhận + XP"}
                                      </div>
                                      <Link
                                          href={`/quests/${quest.slug}`}
                                          className="text-sm font-semibold text-primary hover:text-primary/80"
                                      >
                                          Xem chi tiết →
                                      </Link>
                                  </div>
                              </div>
                          );
                      })}
            </div>
        </main>
    );
}
