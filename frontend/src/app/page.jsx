"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
    Eye,
    Trophy,
    Flame,
    Star,
    Medal,
    ArrowRight,
    BookOpen,
    Sparkles,
} from "lucide-react";

import { useAuthStore } from "@/stores/authStore";
import { getDashboardSummary } from "@/lib/api";
import Skeleton from "@/components/Skeleton";

// Landing page for guests
function GuestLanding() {
    return (
        <main className="min-h-screen bg-gradient-to-b from-background to-muted/30">
            {/* Hero Section */}
            <section className="relative px-6 py-20 md:py-32">
                <div className="mx-auto max-w-5xl text-center">
                    <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
                        <Sparkles className="h-4 w-4" />
                        Nền tảng học tập tương tác
                    </div>

                    <h1 className="font-display text-4xl font-bold tracking-tight text-foreground md:text-6xl">
                        Khám Phá Di Sản
                        <br />
                        <span className="text-primary">Cửu Đỉnh</span>
                    </h1>

                    <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
                        Trải nghiệm học tập gamified về 9 chiếc đỉnh đồng của
                        triều Nguyễn. Khám phá mô hình 3D, tìm hiểu họa tiết, và
                        chinh phục các thử thách.
                    </p>

                    <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
                        <Link
                            href="/login"
                            className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 font-medium text-primary-foreground shadow-lg transition hover:bg-primary/90"
                        >
                            Bắt Đầu Ngay
                            <ArrowRight className="h-4 w-4" />
                        </Link>
                        <Link
                            href="/explore"
                            className="inline-flex items-center gap-2 rounded-full border border-border bg-background px-6 py-3 font-medium text-foreground transition hover:bg-muted"
                        >
                            <Eye className="h-4 w-4" />
                            Xem Trước
                        </Link>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="border-t border-border bg-card/50 px-6 py-20">
                <div className="mx-auto max-w-5xl">
                    <h2 className="text-center font-display text-2xl font-semibold text-foreground md:text-3xl">
                        Tại sao chọn Lưu Niên Sử Kí?
                    </h2>

                    <div className="mt-12 grid gap-6 md:grid-cols-3">
                        <div className="rounded-2xl border border-border bg-background p-6 text-center">
                            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
                                <Eye className="h-7 w-7 text-primary" />
                            </div>
                            <h3 className="font-display font-semibold text-foreground">
                                Mô Hình 3D
                            </h3>
                            <p className="mt-2 text-sm text-muted-foreground">
                                Khám phá các đỉnh đồng với mô hình 3D chi tiết,
                                tương tác trực tiếp với từng họa tiết.
                            </p>
                        </div>

                        <div className="rounded-2xl border border-border bg-background p-6 text-center">
                            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
                                <BookOpen className="h-7 w-7 text-primary" />
                            </div>
                            <h3 className="font-display font-semibold text-foreground">
                                Bài Học Chi Tiết
                            </h3>
                            <p className="mt-2 text-sm text-muted-foreground">
                                Nội dung giáo dục phong phú về lịch sử, ý nghĩa
                                biểu tượng của từng họa tiết.
                            </p>
                        </div>

                        <div className="rounded-2xl border border-border bg-background p-6 text-center">
                            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
                                <Trophy className="h-7 w-7 text-primary" />
                            </div>
                            <h3 className="font-display font-semibold text-foreground">
                                Gamification
                            </h3>
                            <p className="mt-2 text-sm text-muted-foreground">
                                Tích lũy XP, nhận huy hiệu, leo bảng xếp hạng và
                                duy trì streak hàng ngày.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="px-6 py-20">
                <div className="mx-auto max-w-3xl rounded-3xl bg-primary/5 p-8 text-center md:p-12">
                    <h2 className="font-display text-2xl font-semibold text-foreground">
                        Sẵn sàng khám phá?
                    </h2>
                    <p className="mt-3 text-muted-foreground">
                        Tạo tài khoản miễn phí và bắt đầu hành trình học tập của
                        bạn ngay hôm nay.
                    </p>
                    <Link
                        href="/login"
                        className="mt-6 inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 font-medium text-primary-foreground shadow-lg transition hover:bg-primary/90"
                    >
                        Đăng Ký Ngay
                        <ArrowRight className="h-4 w-4" />
                    </Link>
                </div>
            </section>
        </main>
    );
}

// Dashboard for authenticated users
function AuthenticatedDashboard() {
    const user = useAuthStore((s) => s.user);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        let cancelled = false;

        async function load() {
            setLoading(true);
            try {
                const summary = await getDashboardSummary();
                if (!cancelled) setData(summary);
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
    }, []);

    const displayName = user?.display_name || user?.email?.split("@")[0] || "Nhà Khám Phá";
    const streak = data?.streak || { current_streak: 0, longest_streak: 0 };
    const stats = data?.collection_stats || { total: 0, discovered: 0, learned: 0, mastered: 0 };
    const urns = data?.urns || [];

    // Find continue learning target
    const startingUrn = urns.find((u) => u.id === user?.starting_urn_id) || urns[0];
    const progressPercent = stats.total > 0
        ? Math.round(((stats.discovered + stats.learned + stats.mastered) / (stats.total * 3)) * 100)
        : 0;

    return (
        <main className="min-h-screen bg-gradient-to-b from-background to-muted/30 px-4 py-8 md:px-6">
            <div className="mx-auto max-w-5xl">
                {/* Welcome Header */}
                <div className="mb-8">
                    <h1 className="font-display text-2xl font-bold text-foreground md:text-3xl">
                        Xin chào, {displayName}! 👋
                    </h1>
                    <p className="mt-1 text-muted-foreground">
                        Tiếp tục hành trình khám phá Cửu Đỉnh của bạn
                    </p>
                </div>

                {error && (
                    <div className="mb-6 rounded-lg bg-destructive/10 p-4 text-sm text-destructive">
                        {error}
                    </div>
                )}

                {/* Stats Row */}
                <div className="mb-8 grid grid-cols-3 gap-4">
                    {/* Streak */}
                    <div className="rounded-2xl border border-border bg-card p-4 text-center">
                        <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-orange-500/10">
                            <Flame className="h-5 w-5 text-orange-500" />
                        </div>
                        {loading ? (
                            <Skeleton className="mx-auto h-8 w-12" />
                        ) : (
                            <div className="text-2xl font-bold text-foreground">
                                {streak.current_streak}
                            </div>
                        )}
                        <div className="text-xs text-muted-foreground">Streak</div>
                    </div>

                    {/* XP */}
                    <div className="rounded-2xl border border-border bg-card p-4 text-center">
                        <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-yellow-500/10">
                            <Star className="h-5 w-5 text-yellow-500" />
                        </div>
                        {loading ? (
                            <Skeleton className="mx-auto h-8 w-16" />
                        ) : (
                            <div className="text-2xl font-bold text-foreground">
                                {user?.total_xp || 0}
                            </div>
                        )}
                        <div className="text-xs text-muted-foreground">Tổng XP</div>
                    </div>

                    {/* Badges */}
                    <div className="rounded-2xl border border-border bg-card p-4 text-center">
                        <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                            <Medal className="h-5 w-5 text-primary" />
                        </div>
                        {loading ? (
                            <Skeleton className="mx-auto h-8 w-12" />
                        ) : (
                            <div className="text-2xl font-bold text-foreground">
                                {stats.mastered}
                            </div>
                        )}
                        <div className="text-xs text-muted-foreground">Thành Thạo</div>
                    </div>
                </div>

                {/* Continue Learning Card */}
                <div className="mb-8 overflow-hidden rounded-2xl border border-border bg-card">
                    <div className="p-6">
                        <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                                <h2 className="font-display text-lg font-semibold text-foreground">
                                    Tiếp Tục Học
                                </h2>
                                {loading ? (
                                    <Skeleton className="mt-2 h-5 w-48" />
                                ) : startingUrn ? (
                                    <p className="mt-1 text-sm text-muted-foreground">
                                        {startingUrn.name} • {stats.discovered + stats.learned + stats.mastered}/{stats.total * 3} bước hoàn thành
                                    </p>
                                ) : (
                                    <p className="mt-1 text-sm text-muted-foreground">
                                        Chọn một đỉnh để bắt đầu khám phá
                                    </p>
                                )}

                                {/* Progress Bar */}
                                <div className="mt-4">
                                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                                        <span>Tiến độ</span>
                                        <span>{progressPercent}%</span>
                                    </div>
                                    <div className="mt-1 h-2 overflow-hidden rounded-full bg-muted">
                                        <div
                                            className="h-full rounded-full bg-primary transition-all"
                                            style={{ width: `${progressPercent}%` }}
                                        />
                                    </div>
                                </div>
                            </div>

                            <Link
                                href={startingUrn ? `/urns/${startingUrn.slug}` : "/explore"}
                                className="shrink-0 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition hover:bg-primary/90"
                            >
                                Tiếp Tục
                            </Link>
                        </div>
                    </div>
                </div>

                {/* Quick Links */}
                <div className="grid gap-4 md:grid-cols-2">
                    <Link
                        href="/explore"
                        className="group flex items-center gap-4 rounded-2xl border border-border bg-card p-4 transition hover:border-primary/30 hover:bg-primary/5"
                    >
                        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                            <Eye className="h-6 w-6 text-primary" />
                        </div>
                        <div className="flex-1">
                            <h3 className="font-semibold text-foreground">Khám Phá</h3>
                            <p className="text-sm text-muted-foreground">
                                Xem tất cả các đỉnh và họa tiết
                            </p>
                        </div>
                        <ArrowRight className="h-5 w-5 text-muted-foreground transition group-hover:text-primary" />
                    </Link>

                    <Link
                        href="/collection"
                        className="group flex items-center gap-4 rounded-2xl border border-border bg-card p-4 transition hover:border-primary/30 hover:bg-primary/5"
                    >
                        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                            <BookOpen className="h-6 w-6 text-primary" />
                        </div>
                        <div className="flex-1">
                            <h3 className="font-semibold text-foreground">Bộ Sưu Tập</h3>
                            <p className="text-sm text-muted-foreground">
                                {loading ? "..." : `${stats.discovered + stats.learned + stats.mastered} họa tiết đã khám phá`}
                            </p>
                        </div>
                        <ArrowRight className="h-5 w-5 text-muted-foreground transition group-hover:text-primary" />
                    </Link>

                    <Link
                        href="/achievements"
                        className="group flex items-center gap-4 rounded-2xl border border-border bg-card p-4 transition hover:border-primary/30 hover:bg-primary/5"
                    >
                        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                            <Trophy className="h-6 w-6 text-primary" />
                        </div>
                        <div className="flex-1">
                            <h3 className="font-semibold text-foreground">Thành Tích</h3>
                            <p className="text-sm text-muted-foreground">
                                Huy hiệu và bảng xếp hạng
                            </p>
                        </div>
                        <ArrowRight className="h-5 w-5 text-muted-foreground transition group-hover:text-primary" />
                    </Link>

                    <Link
                        href="/profile"
                        className="group flex items-center gap-4 rounded-2xl border border-border bg-card p-4 transition hover:border-primary/30 hover:bg-primary/5"
                    >
                        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                            <Star className="h-6 w-6 text-primary" />
                        </div>
                        <div className="flex-1">
                            <h3 className="font-semibold text-foreground">Hồ Sơ</h3>
                            <p className="text-sm text-muted-foreground">
                                Cài đặt và thông tin cá nhân
                            </p>
                        </div>
                        <ArrowRight className="h-5 w-5 text-muted-foreground transition group-hover:text-primary" />
                    </Link>
                </div>
            </div>
        </main>
    );
}

export default function HomePage() {
    const status = useAuthStore((s) => s.status);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    // Prevent hydration mismatch
    if (!mounted) {
        return (
            <main className="flex min-h-screen items-center justify-center">
                <div className="text-muted-foreground">Đang tải...</div>
            </main>
        );
    }

    if (status === "authed") {
        return <AuthenticatedDashboard />;
    }

    return <GuestLanding />;
}
