"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { QRCodeCanvas } from "qrcode.react";

import Skeleton from "@/components/Skeleton";
import {
    ApiError,
    getUserPublicProfile,
    getUserPublicProfileByUsername,
} from "@/lib/api";

function isUuid(value) {
    return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
        String(value || ""),
    );
}

function Avatar({ src, name }) {
    const initial = (name || "U").trim().slice(0, 1).toUpperCase();
    return (
        <div className="h-20 w-20 overflow-hidden rounded-full border border-border bg-secondary">
            {src ? (
                <img
                    src={src}
                    alt={name || "Avatar"}
                    className="h-full w-full object-cover"
                />
            ) : (
                <div className="flex h-full w-full items-center justify-center font-display text-2xl font-semibold text-muted-foreground">
                    {initial}
                </div>
            )}
        </div>
    );
}

function StatCard({ label, value }) {
    return (
        <div className="rounded-lg border border-border bg-card p-5">
            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {label}
            </div>
            <div className="mt-2 font-display text-3xl font-bold tabular-nums text-foreground">
                {value}
            </div>
        </div>
    );
}

const STATUS_LABELS = {
    discovered: "Đã Khám Phá",
    learned: "Đã Học",
    mastered: "Đã Thành Thạo",
};

export default function PublicUserPage() {
    const params = useParams();
    const userId = params?.userId;

    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [apiStatus, setApiStatus] = useState(null);
    const [error, setError] = useState(null);
    const [shareUrl, setShareUrl] = useState("");

    useEffect(() => {
        if (!userId) return;
        let cancelled = false;

        async function load() {
            setLoading(true);
            setError(null);
            setApiStatus(null);
            try {
                let data;
                try {
                    data = await getUserPublicProfileByUsername({
                        usernameOrId: userId,
                    });
                } catch (err) {
                    if (
                        err instanceof ApiError &&
                        err.status === 404 &&
                        isUuid(userId)
                    ) {
                        data = await getUserPublicProfile({ userId });
                    } else {
                        throw err;
                    }
                }
                if (!cancelled) setProfile(data);
            } catch (err) {
                if (cancelled) return;
                if (err instanceof ApiError) {
                    setApiStatus(err.status ?? null);
                    setError(err.message);
                    return;
                }
                setError(err instanceof Error ? err.message : String(err));
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        load();
        return () => {
            cancelled = true;
        };
    }, [userId]);

    useEffect(() => {
        if (!userId) return;
        if (typeof window === "undefined") return;
        const identifier = profile?.username || userId;
        setShareUrl(`${window.location.origin}/u/${identifier}`);
    }, [profile, userId]);

    const motifsDiscovered = useMemo(() => {
        const s = profile?.stats;
        return (
            (s?.discovered_count || 0) +
            (s?.learned_count || 0) +
            (s?.mastered_count || 0)
        );
    }, [profile]);

    const lessonsCompleted = useMemo(() => {
        const s = profile?.stats;
        return (s?.learned_count || 0) + (s?.mastered_count || 0);
    }, [profile]);

    const quizzesPassed = profile?.stats?.quizzes_passed || 0;

    async function copyShareLink() {
        if (!shareUrl) return;
        try {
            await navigator.clipboard.writeText(shareUrl);
        } catch {
            // ignore
        }
    }

    if (loading) {
        return (
            <main className="site-shell">
                <div className="rounded-lg border border-border bg-card p-6">
                    <div className="flex items-center gap-4">
                        <Skeleton className="h-20 w-20 rounded-full" />
                        <div className="flex-1">
                            <Skeleton className="h-6 w-48" />
                            <Skeleton className="mt-2 h-4 w-80" />
                        </div>
                    </div>
                </div>
                <div className="mt-6 grid gap-4 sm:grid-cols-3">
                    <Skeleton className="h-24 rounded-lg" />
                    <Skeleton className="h-24 rounded-lg" />
                    <Skeleton className="h-24 rounded-lg" />
                </div>
                <div className="mt-6 grid gap-6 lg:grid-cols-2">
                    <Skeleton className="h-64 rounded-lg" />
                    <Skeleton className="h-64 rounded-lg" />
                </div>
            </main>
        );
    }

    if (apiStatus === 403) {
        return (
            <main className="site-shell">
                <div className="rounded-lg border border-border bg-card p-8">
                    <div className="font-display text-2xl font-semibold text-foreground">
                        403 — Không thể truy cập
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Hồ sơ này đang ở chế độ riêng tư. Bạn không có quyền xem
                        thông tin công khai của người dùng này.
                    </p>
                    <div className="mt-6">
                        <Link
                            className="text-sm font-medium text-primary hover:underline"
                            href="/achievements"
                        >
                            Quay lại Bảng Xếp Hạng
                        </Link>
                    </div>
                </div>
            </main>
        );
    }

    if (apiStatus === 404) {
        return (
            <main className="site-shell">
                <div className="rounded-lg border border-border bg-card p-8">
                    <div className="font-display text-2xl font-semibold text-foreground">
                        Không tìm thấy người dùng
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Người dùng không tồn tại hoặc đã bị xóa.
                    </p>
                    <div className="mt-6">
                        <Link
                            className="text-sm font-medium text-primary hover:underline"
                            href="/achievements"
                        >
                            Quay lại Bảng Xếp Hạng
                        </Link>
                    </div>
                </div>
            </main>
        );
    }

    if (!profile) {
        return (
            <main className="site-shell">
                <div className="rounded-lg border border-border bg-card p-8">
                    <div className="font-display text-2xl font-semibold text-foreground">
                        Không tải được hồ sơ
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">
                        {error || "Vui lòng thử lại sau."}
                    </p>
                </div>
            </main>
        );
    }

    return (
        <main className="site-shell">
            <div className="flex items-baseline justify-between gap-4">
                <div>
                    <h1 className="font-display text-2xl font-semibold text-foreground">
                        Hồ Sơ Công Khai
                    </h1>
                    <p className="mt-1 text-sm text-muted-foreground">
                        Chia sẻ hành trình khám phá di sản.
                    </p>
                </div>
            </div>

            {error ? (
                <div className="mt-6 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
                    {error}
                </div>
            ) : null}

            <section className="mt-6 rounded-lg border border-border bg-card p-6">
                <div className="flex flex-wrap items-start justify-between gap-6">
                    <div className="flex items-start gap-4">
                        <Avatar
                            src={profile.avatar_url}
                            name={profile.display_name}
                        />
                        <div>
                            <div className="font-display text-xl font-semibold text-foreground">
                                {profile.display_name}
                            </div>
                            <div className="mt-1 text-sm text-muted-foreground">
                                @{profile.username}
                            </div>
                            {profile.bio ? (
                                <p className="mt-3 max-w-xl text-sm text-foreground/90">
                                    {profile.bio}
                                </p>
                            ) : null}
                        </div>
                    </div>

                    <div className="rounded-lg border border-border bg-secondary/40 p-4">
                        <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                            XP
                        </div>
                        <div className="mt-1 font-display text-2xl font-bold tabular-nums text-primary">
                            {profile.total_xp}
                        </div>
                        <div className="mt-2 text-xs text-muted-foreground">
                            Hạng:{" "}
                            <span className="font-medium text-foreground">
                                {profile.rank?.name || "—"}
                            </span>
                        </div>
                    </div>
                </div>
            </section>

            <section className="mt-6 grid gap-4 sm:grid-cols-3">
                <StatCard
                    label="Họa tiết đã khám phá"
                    value={motifsDiscovered}
                />
                <StatCard
                    label="Bài học đã hoàn thành"
                    value={lessonsCompleted}
                />
                <StatCard
                    label="Bài kiểm tra đã vượt qua"
                    value={quizzesPassed}
                />
            </section>

            <section className="mt-6 grid gap-6 lg:grid-cols-2">
                <div className="rounded-lg border border-border bg-card p-6">
                    <div className="flex items-baseline justify-between">
                        <h2 className="font-display text-lg font-semibold text-foreground">
                            Huy Hiệu
                        </h2>
                        <div className="text-xs text-muted-foreground">
                            {profile.badges?.length || 0} huy hiệu
                        </div>
                    </div>

                    {profile.badges?.length ? (
                        <div className="mt-5 grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-5">
                            {profile.badges.map((b, idx) => (
                                <div
                                    key={`${b.name}-${idx}`}
                                    title={b.description || b.name}
                                    className="rounded-lg border border-border bg-secondary/30 p-3 text-center"
                                >
                                    {b.icon ? (
                                        <img
                                            src={b.icon}
                                            alt={b.name}
                                            className="mx-auto h-10 w-10"
                                        />
                                    ) : (
                                        <div className="mx-auto h-10 w-10 rounded-lg bg-muted" />
                                    )}
                                    <div className="mt-2 text-xs font-medium leading-snug text-foreground">
                                        {b.name}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="mt-5 rounded-lg bg-secondary/30 p-4 text-sm text-muted-foreground">
                            Chưa có huy hiệu.
                        </div>
                    )}
                </div>

                <div className="rounded-lg border border-border bg-card p-6">
                    <div className="flex items-baseline justify-between">
                        <h2 className="font-display text-lg font-semibold text-foreground">
                            Chứng Chỉ
                        </h2>
                        <div className="text-xs text-muted-foreground">
                            {profile.certificates?.length || 0} chứng chỉ
                        </div>
                    </div>

                    {profile.certificates?.length ? (
                        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
                            {profile.certificates.map((c, idx) => (
                                <a
                                    key={c.id || idx}
                                    href={c.certificate_url || "#"}
                                    className="rounded-lg border border-border bg-secondary/30 p-4 hover:bg-secondary/40"
                                >
                                    <div className="text-sm font-medium text-foreground">
                                        {c.title || c.name || "Chứng chỉ"}
                                    </div>
                                    {c.issued_at ? (
                                        <div className="mt-1 text-xs text-muted-foreground">
                                            Cấp ngày:{" "}
                                            {new Date(
                                                c.issued_at,
                                            ).toLocaleDateString("vi-VN")}
                                        </div>
                                    ) : null}
                                </a>
                            ))}
                        </div>
                    ) : (
                        <div className="mt-5 rounded-lg bg-secondary/30 p-4 text-sm text-muted-foreground">
                            Chưa có chứng chỉ.
                        </div>
                    )}
                </div>
            </section>

            <section className="mt-6 rounded-lg border border-border bg-card p-6">
                <div className="flex items-baseline justify-between">
                    <h2 className="font-display text-lg font-semibold text-foreground">
                        Họa tiết đã mở khóa
                    </h2>
                    <div className="text-xs text-muted-foreground">
                        {profile.motifs?.length || 0} họa tiết
                    </div>
                </div>

                {profile.motifs?.length ? (
                    <div className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
                        {profile.motifs.map((m) => (
                            <div
                                key={m.id}
                                className="group overflow-hidden rounded-lg border border-border bg-secondary/20"
                            >
                                <div className="relative aspect-square w-full overflow-hidden bg-muted">
                                    {m.thumbnail_url ? (
                                        <img
                                            src={m.thumbnail_url}
                                            alt={m.name}
                                            loading="lazy"
                                            decoding="async"
                                            className="h-full w-full object-cover transition-transform duration-200 group-hover:scale-[1.025]"
                                        />
                                    ) : (
                                        <div className="flex h-full w-full items-center justify-center text-sm text-muted-foreground">
                                            —
                                        </div>
                                    )}
                                    <div className="absolute bottom-2 left-2 rounded-full bg-black/60 px-2 py-1 text-[10px] uppercase tracking-wider text-white">
                                        {STATUS_LABELS[m.status] || m.status}
                                    </div>
                                </div>
                                <div className="p-3">
                                    <div className="truncate text-xs font-semibold text-foreground">
                                        {m.name}
                                    </div>
                                    <div className="mt-1 truncate text-[10px] text-muted-foreground">
                                        {m.urn_name}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="mt-5 rounded-lg bg-secondary/30 p-4 text-sm text-muted-foreground">
                        Chưa có họa tiết nào được mở khóa.
                    </div>
                )}
            </section>

            <section className="mt-6 rounded-lg border border-border bg-card p-6">
                <h2 className="font-display text-lg font-semibold text-foreground">
                    Chia Sẻ Hồ Sơ
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                    Gửi link hoặc quét mã QR để mở nhanh.
                </p>

                <div className="mt-5 flex flex-wrap items-center gap-4">
                    <div className="rounded-lg border border-border bg-secondary/30 p-4">
                        {shareUrl ? (
                            <div className="rounded-lg bg-white p-2">
                                <QRCodeCanvas
                                    value={shareUrl}
                                    size={160}
                                    includeMargin
                                />
                            </div>
                        ) : (
                            <div className="h-40 w-40 rounded-lg bg-muted" />
                        )}
                    </div>

                    <div className="min-w-[240px] flex-1">
                        <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                            Link chia sẻ
                        </div>
                        <div className="mt-2 break-all rounded-lg border border-border bg-secondary/30 p-3 text-sm text-foreground">
                            {shareUrl || `.../u/${userId}`}
                        </div>
                        <div className="mt-3 flex flex-wrap gap-3">
                            <button
                                type="button"
                                onClick={copyShareLink}
                                className="rounded-lg border border-border bg-secondary px-4 py-2 text-sm font-medium text-foreground hover:bg-secondary/80"
                            >
                                Sao chép link
                            </button>
                            <Link
                                href="/achievements"
                                className="rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-secondary/30"
                            >
                                Xem Bảng Xếp Hạng
                            </Link>
                        </div>
                    </div>
                </div>
            </section>
        </main>
    );
}
