"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { ApiError, getShareById } from "@/lib/api";

const SHARE_TYPE_LABELS = {
    achievement: "Thành tích",
    badge: "Huy hiệu",
    streak: "Streak",
    level_up: "Lên hạng",
    certificate: "Chứng nhận",
};

function shareTypeLabel(shareType) {
    return SHARE_TYPE_LABELS[shareType] || shareType || "Bài chia sẻ";
}

function formatDate(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    return date.toLocaleString("vi-VN");
}

function renderContentData(share) {
    const data = share?.content_data;
    if (!data || typeof data !== "object") return null;

    if (share.share_type === "badge") {
        return (
            <div className="mt-4 rounded-xl border border-border bg-background p-4">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">
                    Huy hiệu
                </p>
                <p className="mt-1 text-base font-semibold text-foreground">
                    {data.badge_name || "Badge"}
                </p>
                {data.badge_description ? (
                    <p className="mt-1 text-sm text-muted-foreground">
                        {data.badge_description}
                    </p>
                ) : null}
            </div>
        );
    }

    if (share.share_type === "certificate") {
        return (
            <div className="mt-4 rounded-xl border border-border bg-background p-4 text-sm text-muted-foreground">
                <p>
                    Mã chứng nhận: <span className="font-semibold text-foreground">{data.certificate_code || "-"}</span>
                </p>
                <p className="mt-1">
                    Đơn vị cấp: <span className="font-semibold text-foreground">{data.issuer_name || "-"}</span>
                </p>
            </div>
        );
    }

    if (share.share_type === "streak") {
        return (
            <div className="mt-4 rounded-xl border border-border bg-background p-4 text-sm text-muted-foreground">
                <p>
                    Streak hiện tại: <span className="font-semibold text-foreground">{data.current_streak ?? 0}</span>
                </p>
                <p className="mt-1">
                    Streak dài nhất: <span className="font-semibold text-foreground">{data.longest_streak ?? 0}</span>
                </p>
            </div>
        );
    }

    return null;
}

export default function ShareDetailPage() {
    const params = useParams();
    const shareId = useMemo(() => {
        const raw = params?.shareId;
        return Array.isArray(raw) ? raw[0] : raw;
    }, [params]);

    const [share, setShare] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        if (!shareId) return;

        let cancelled = false;
        async function load() {
            setLoading(true);
            setError(null);
            try {
                const result = await getShareById({ shareId });
                if (!cancelled) setShare(result);
            } catch (err) {
                if (!cancelled) {
                    if (err instanceof ApiError && err.status === 404) {
                        setError("Bài chia sẻ không tồn tại hoặc bạn không có quyền xem.");
                    } else {
                        setError(err instanceof Error ? err.message : String(err));
                    }
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        load();
        return () => {
            cancelled = true;
        };
    }, [shareId]);

    async function copyShareLink() {
        if (!shareId || typeof window === "undefined") return;
        const url = `${window.location.origin}/share/${shareId}`;
        try {
            await navigator.clipboard.writeText(url);
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
        } catch {
            setCopied(false);
        }
    }

    if (loading) {
        return (
            <main className="mx-auto max-w-3xl px-4 py-10 sm:px-6 lg:px-8">
                <div className="rounded-2xl border border-border bg-card p-6 text-sm text-muted-foreground">
                    Đang tải bài chia sẻ...
                </div>
            </main>
        );
    }

    if (error || !share) {
        return (
            <main className="mx-auto max-w-3xl px-4 py-10 sm:px-6 lg:px-8">
                <div className="rounded-2xl border border-border bg-card p-6">
                    <p className="text-sm text-destructive">{error || "Không tìm thấy bài chia sẻ."}</p>
                    <div className="mt-4">
                        <Link
                            href="/achievements"
                            className="text-sm font-semibold text-primary hover:text-primary/80"
                        >
                            Quay lại thành tích
                        </Link>
                    </div>
                </div>
            </main>
        );
    }

    return (
        <main className="mx-auto max-w-3xl px-4 py-10 sm:px-6 lg:px-8">
            <article className="rounded-2xl border border-border bg-card p-6">
                <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                        <p className="text-xs uppercase tracking-wide text-muted-foreground">
                            {shareTypeLabel(share.share_type)}
                        </p>
                        <h1 className="mt-1 text-2xl font-display font-semibold text-foreground">
                            {share.user_display_name}
                        </h1>
                        <p className="mt-1 text-sm text-muted-foreground">
                            {formatDate(share.created_at)}
                        </p>
                    </div>

                    <div className="flex items-center gap-2">
                        <button
                            type="button"
                            onClick={copyShareLink}
                            className="rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground"
                        >
                            {copied ? "Đã sao chép" : "Sao chép link"}
                        </button>
                        <Link
                            href={`/u/${share.user_id}`}
                            className="rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground"
                        >
                            Xem hồ sơ
                        </Link>
                    </div>
                </div>

                {share.caption ? (
                    <p className="mt-4 rounded-xl border border-border bg-background p-4 text-sm text-foreground">
                        {share.caption}
                    </p>
                ) : null}

                {renderContentData(share)}

                <div className="mt-4 text-xs text-muted-foreground">
                    {share.view_count || 0} lượt xem
                </div>
            </article>
        </main>
    );
}
