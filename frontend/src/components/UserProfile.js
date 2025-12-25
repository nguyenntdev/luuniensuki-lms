"use client";

import { useEffect, useMemo, useState } from "react";
import { getMyBadges, getMyCollection, getMyStreak } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import Skeleton from "@/components/Skeleton";

function ProgressBar({ value }) {
    const clamped = Math.max(0, Math.min(100, value || 0));
    return (
        <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
            <div
                className="h-full bg-primary transition-all duration-500 ease-out shadow-[0_0_10px_rgba(var(--primary),0.5)]"
                style={{ width: `${clamped}%` }}
            />
        </div>
    );
}

export default function UserProfile() {
    const status = useAuthStore((s) => s.status);
    const user = useAuthStore((s) => s.user);
    const stats = useAuthStore((s) => s.stats);
    const logout = useAuthStore((s) => s.logout);

    const [collection, setCollection] = useState(null);
    const [streak, setStreak] = useState(null);
    const [badges, setBadges] = useState([]);
    const [loadingCollection, setLoadingCollection] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        let cancelled = false;
        async function load() {
            if (status !== "authed") return;
            setLoadingCollection(true);
            setError(null);
            try {
                const [collectionRes, streakRes, badgesRes] = await Promise.all(
                    [getMyCollection(), getMyStreak(), getMyBadges()],
                );
                if (!cancelled) {
                    setCollection(collectionRes);
                    setStreak(streakRes);
                    setBadges(badgesRes || []);
                }
            } catch (err) {
                if (!cancelled)
                    setError(err instanceof Error ? err.message : String(err));
            } finally {
                if (!cancelled) setLoadingCollection(false);
            }
        }
        load();
        return () => {
            cancelled = true;
        };
    }, [status]);

    const gridItems = useMemo(() => collection?.items || [], [collection]);
    const quest = collection?.stats?.quest;
    const unlockedCount = useMemo(() => {
        const s = collection?.stats;
        if (!s) return 0;
        return (s.discovered || 0) + (s.learned || 0) + (s.mastered || 0);
    }, [collection]);

    if (status !== "authed") {
        return (
            <div className="mx-auto max-w-5xl p-6">
                <div className="rounded-xl border border-border bg-card p-8 shadow-elegant">
                    <h1 className="text-3xl font-display font-bold text-primary">
                        Hồ sơ cá nhân
                    </h1>
                    <p className="mt-4 text-muted-foreground">
                        Vui lòng đăng nhập để xem hồ sơ và bộ sưu tập di sản của
                        bạn.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="mx-auto max-w-6xl p-6 space-y-8 animate-fade-in-up">
            {/* Header Section */}
            <div className="rounded-xl border border-border bg-card/80 backdrop-blur-sm p-8 shadow-elegant relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />

                <div className="relative flex flex-wrap items-center justify-between gap-6">
                    <div>
                        <h1 className="text-4xl font-display font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary to-amber-300">
                            Chào mừng, {user?.display_name || "Nhà thám hiểm"}
                        </h1>
                        <p className="mt-2 text-muted-foreground font-sans">
                            {user?.email}
                        </p>
                    </div>
                    <button
                        onClick={logout}
                        className="px-6 py-2.5 rounded-lg border border-primary/30 text-primary hover:bg-primary hover:text-primary-foreground transition-all duration-300 font-medium tracking-wide uppercase text-sm hover:shadow-[0_0_20px_rgba(var(--primary),0.3)]"
                    >
                        Đăng xuất
                    </button>
                </div>

                {/* Stats Grid */}
                <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                    {/* Rank Card */}
                    <div className="rounded-lg bg-secondary/50 p-5 border border-white/5 hover:border-primary/20 transition-all duration-300 hover:transform hover:-translate-y-1">
                        <div className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                            Cấp bậc
                        </div>
                        <div className="mt-2 text-xl font-display font-bold text-foreground">
                            {stats?.rank?.name || "—"}
                        </div>
                        <div className="mt-2 text-xs text-muted-foreground">
                            XP:{" "}
                            <span className="font-display tabular-nums text-primary">
                                {stats?.total_xp ?? 0}
                            </span>{" "}
                            · Cần thêm:{" "}
                            <span className="font-display tabular-nums">
                                {stats?.xp_to_next_rank ?? 0}
                            </span>
                        </div>
                    </div>

                    {/* Quest Card */}
                    {loadingCollection ? (
                        <div className="rounded-lg bg-secondary/50 p-5 border border-white/5">
                            <Skeleton className="h-3 w-12 bg-muted" />
                            <Skeleton className="mt-3 h-5 w-32 bg-muted" />
                            <Skeleton className="mt-4 h-2 w-full rounded-full bg-muted" />
                            <Skeleton className="mt-3 h-3 w-24 bg-muted" />
                        </div>
                    ) : (
                        <div className="rounded-lg bg-secondary/50 p-5 border border-white/5 hover:border-primary/20 transition-all duration-300 hover:transform hover:-translate-y-1">
                            <div className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                                Nhiệm vụ
                            </div>
                            <div
                                className="mt-2 text-sm font-medium text-foreground truncate"
                                title={quest?.quest_name}
                            >
                                {quest?.quest_name || "Chưa có nhiệm vụ"}
                            </div>
                            <div className="mt-4">
                                <ProgressBar
                                    value={quest?.progress_percent || 0}
                                />
                            </div>
                            <div className="mt-2 text-xs text-muted-foreground flex justify-between">
                                <span>
                                    <span className="font-display tabular-nums">
                                        {quest?.discovered ?? 0}
                                    </span>
                                    /
                                    <span className="font-display tabular-nums">
                                        {quest?.total ?? 0}
                                    </span>{" "}
                                    đã khám phá
                                </span>
                                <span className="font-display tabular-nums text-primary font-bold">
                                    {Math.round(quest?.progress_percent || 0)}%
                                </span>
                            </div>
                        </div>
                    )}

                    {/* Collection Count Card */}
                    {loadingCollection ? (
                        <div className="rounded-lg bg-secondary/50 p-5 border border-white/5">
                            <Skeleton className="h-3 w-16 bg-muted" />
                            <Skeleton className="mt-3 h-8 w-12 bg-muted" />
                            <Skeleton className="mt-3 h-3 w-24 bg-muted" />
                        </div>
                    ) : (
                        <div className="rounded-lg bg-secondary/50 p-5 border border-white/5 hover:border-primary/20 transition-all duration-300 hover:transform hover:-translate-y-1">
                            <div className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                                Bộ sưu tập
                            </div>
                            <div className="mt-2 text-3xl font-display font-bold text-primary">
                                {unlockedCount}
                            </div>
                            <div className="mt-2 text-xs text-muted-foreground">
                                Tổng số đã mở khóa (trên{" "}
                                <span className="font-display tabular-nums">
                                    {collection?.stats?.total ?? 0}
                                </span>
                                )
                            </div>
                        </div>
                    )}

                    {/* Streak Card */}
                    {loadingCollection ? (
                        <div className="rounded-lg bg-secondary/50 p-5 border border-white/5">
                            <Skeleton className="h-3 w-12 bg-muted" />
                            <Skeleton className="mt-3 h-8 w-12 bg-muted" />
                            <Skeleton className="mt-3 h-3 w-24 bg-muted" />
                        </div>
                    ) : (
                        <div className="rounded-lg bg-secondary/50 p-5 border border-white/5 hover:border-primary/20 transition-all duration-300 hover:transform hover:-translate-y-1">
                            <div className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                                Chuỗi ngày
                            </div>
                            <div className="mt-2 text-3xl font-display font-bold text-orange-400">
                                {streak?.current_streak ?? "—"}
                            </div>
                            <div className="mt-2 text-xs text-muted-foreground">
                                Dài nhất:{" "}
                                <span className="font-display tabular-nums text-foreground">
                                    {streak?.longest_streak ?? 0}
                                </span>{" "}
                                · Huy hiệu:{" "}
                                <span className="font-display tabular-nums text-foreground">
                                    {badges?.length ?? 0}
                                </span>
                            </div>
                        </div>
                    )}
                </div>

                {error ? (
                    <div className="mt-6 rounded-lg bg-destructive/10 border border-destructive/20 p-4 text-sm text-destructive font-medium">
                        Không tải được dữ liệu: {error}
                    </div>
                ) : null}
            </div>

            {/* Collection Grid Section */}
            <div className="rounded-xl border border-border bg-card/80 backdrop-blur-sm p-8 shadow-elegant relative">
                <div className="flex items-baseline justify-between mb-6">
                    <h2 className="text-2xl font-display font-bold text-foreground flex items-center gap-3">
                        <span className="w-8 h-[2px] bg-primary block"></span>
                        Kho Tàng Di Sản
                    </h2>
                </div>

                {loadingCollection ? (
                    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
                        {[...Array(16)].map((_, i) => (
                            <Skeleton
                                key={i}
                                className="aspect-square w-full rounded-lg bg-secondary/50"
                            />
                        ))}
                    </div>
                ) : (
                    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
                        {gridItems.map((item) => {
                            const unlocked = item.status !== "hidden";
                            return (
                                <div
                                    key={item.motif_id}
                                    title={`${item.name} (${item.status})`}
                                    className={[
                                        "group relative aspect-square overflow-hidden rounded-lg border transition-all duration-500",
                                        unlocked
                                            ? "bg-secondary border-primary/30 shadow-[0_0_15px_rgba(var(--primary),0.1)] hover:shadow-[0_0_20px_rgba(var(--primary),0.3)] hover:border-primary"
                                            : "bg-secondary/30 border-white/5 opacity-60 grayscale",
                                    ].join(" ")}
                                >
                                    {item.thumbnail_url ? (
                                        <div className="h-full w-full overflow-hidden">
                                            <img
                                                src={item.thumbnail_url}
                                                alt={item.name}
                                                className={[
                                                    "h-full w-full object-cover transition-transform duration-700 ease-out group-hover:scale-110",
                                                    unlocked
                                                        ? ""
                                                        : "opacity-40",
                                                ].join(" ")}
                                            />
                                        </div>
                                    ) : (
                                        <div
                                            className={[
                                                "flex h-full w-full items-center justify-center text-lg font-serif",
                                                unlocked
                                                    ? "text-primary"
                                                    : "text-muted-foreground",
                                            ].join(" ")}
                                        >
                                            {unlocked ? "✓" : "?"}
                                        </div>
                                    )}

                                    {/* Hover Overlay */}
                                    <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100 flex items-end p-2">
                                        <div className="w-full text-center">
                                            <div className="truncate text-[10px] font-medium text-white uppercase tracking-wider">
                                                {item.name}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Status Indicator Dot */}
                                    {unlocked && (
                                        <div className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_5px_rgba(var(--primary),1)]" />
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}

                <div className="mt-8 pt-6 border-t border-white/5 flex items-start gap-3">
                    <div className="p-1.5 rounded-full bg-primary/10 text-primary mt-0.5">
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="14"
                            height="14"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <circle cx="12" cy="12" r="10" />
                            <path d="M12 16v-4" />
                            <path d="M12 8h.01" />
                        </svg>
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                        <span className="text-primary font-semibold">
                            Mách nhỏ:
                        </span>{" "}
                        Việc mở khóa các họa tiết trong trình xem bình 3D sẽ cập
                        nhật bộ sưu tập này ngay lập tức. Hãy khám phá từng chi
                        tiết hoa văn để làm giàu kho tàng của bạn.
                    </p>
                </div>
            </div>
        </div>
    );
}
