"use client";

/**
 * Render Performance Dashboard (Gap 4 — paper claim "+46% speedup").
 *
 * Aggregates `render_performance` analytics events emitted by `UrnViewer` and
 * compares the three LOD levels (512 / 1k / 2k) so admins can validate the
 * conference paper's "+46% speedup" claim against real production data.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";

import { apiRequest } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

const PAPER_CLAIM_PCT = 46;
const LOD_ORDER = ["512", "1k", "2k"];

function formatBytes(bytes) {
    if (bytes == null) return "—";
    if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(2)} MB`;
    if (bytes >= 1_000) return `${(bytes / 1_000).toFixed(1)} KB`;
    return `${Math.round(bytes)} B`;
}

function formatMs(value) {
    if (value == null) return "—";
    return `${Math.round(value)} ms`;
}

function formatFps(value) {
    if (value == null) return "—";
    return value.toFixed(1);
}

function formatPct(value) {
    if (value == null) return "—";
    const sign = value >= 0 ? "+" : "";
    return `${sign}${value.toFixed(1)}%`;
}

function isoDate(d) {
    return d.toISOString().slice(0, 10);
}

function defaultRange() {
    const to = new Date();
    const from = new Date(to.getTime() - 7 * 24 * 60 * 60 * 1000);
    return { from: isoDate(from), to: isoDate(to) };
}

function toCsv(byLod) {
    const header = [
        "lod_label",
        "sample_count",
        "avg_file_size_bytes",
        "ttf_p50_ms",
        "ttf_p95_ms",
        "ttf_p99_ms",
        "ttfi_p50_ms",
        "ttfi_p95_ms",
        "ttfi_p99_ms",
        "fps_p50",
        "fps_p95",
        "fps_p99",
    ].join(",");
    const rows = byLod.map((b) =>
        [
            b.lod_label,
            b.sample_count,
            b.avg_file_size_bytes ?? "",
            b.ttf_ms?.p50 ?? "",
            b.ttf_ms?.p95 ?? "",
            b.ttf_ms?.p99 ?? "",
            b.ttfi_ms?.p50 ?? "",
            b.ttfi_ms?.p95 ?? "",
            b.ttfi_ms?.p99 ?? "",
            b.avg_fps?.p50 ?? "",
            b.avg_fps?.p95 ?? "",
            b.avg_fps?.p99 ?? "",
        ].join(","),
    );
    return [header, ...rows].join("\n");
}

function downloadCsv(filename, content) {
    const blob = new Blob([content], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function PercentilesTable({ title, percentiles, formatter }) {
    return (
        <div className="rounded-md border border-border bg-background p-3">
            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {title}
            </div>
            <div className="mt-2 grid grid-cols-3 gap-2 text-sm">
                <div>
                    <div className="text-[10px] text-muted-foreground">p50</div>
                    <div className="font-display tabular-nums">
                        {formatter(percentiles?.p50)}
                    </div>
                </div>
                <div>
                    <div className="text-[10px] text-muted-foreground">p95</div>
                    <div className="font-display tabular-nums">
                        {formatter(percentiles?.p95)}
                    </div>
                </div>
                <div>
                    <div className="text-[10px] text-muted-foreground">p99</div>
                    <div className="font-display tabular-nums">
                        {formatter(percentiles?.p99)}
                    </div>
                </div>
            </div>
        </div>
    );
}

function LodCard({ bucket }) {
    if (!bucket) {
        return (
            <div className="rounded-lg border border-dashed border-border bg-card/50 p-5 text-sm text-muted-foreground">
                Chưa có dữ liệu cho LOD này.
            </div>
        );
    }
    return (
        <div className="rounded-lg border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between">
                <div>
                    <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        LOD
                    </div>
                    <div className="mt-1 text-2xl font-display font-bold text-foreground">
                        {bucket.lod_label}
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-xs text-muted-foreground">
                        Mẫu / File size
                    </div>
                    <div className="font-display tabular-nums">
                        {bucket.sample_count} ·{" "}
                        {formatBytes(bucket.avg_file_size_bytes)}
                    </div>
                </div>
            </div>

            <div className="mt-4 space-y-3">
                <PercentilesTable
                    title="Time to first frame"
                    percentiles={bucket.ttf_ms}
                    formatter={formatMs}
                />
                <PercentilesTable
                    title="Time to first interaction"
                    percentiles={bucket.ttfi_ms}
                    formatter={formatMs}
                />
                <PercentilesTable
                    title="Average FPS (5s window)"
                    percentiles={bucket.avg_fps}
                    formatter={formatFps}
                />
            </div>
        </div>
    );
}

export default function RenderPerfDashboardPage() {
    const status = useAuthStore((s) => s.status);
    const user = useAuthStore((s) => s.user);
    const isAdmin = user?.role === "admin" || user?.role === "super_admin";

    const initial = useMemo(() => defaultRange(), []);
    const [from, setFrom] = useState(initial.from);
    const [to, setTo] = useState(initial.to);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const params = new URLSearchParams();
            if (from) params.set("from", new Date(from).toISOString());
            if (to) {
                // include the entire "to" day
                const toDate = new Date(to);
                toDate.setHours(23, 59, 59, 999);
                params.set("to", toDate.toISOString());
            }
            const res = await apiRequest(
                `/api/v1/admin/analytics/render-performance?${params.toString()}`,
            );
            setData(res);
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err));
        } finally {
            setLoading(false);
        }
    }, [from, to]);

    useEffect(() => {
        if (status !== "authed" || !isAdmin) return;
        fetchData();
    }, [fetchData, isAdmin, status]);

    const bucketByLabel = useMemo(() => {
        const map = {};
        for (const b of data?.by_lod || []) {
            map[b.lod_label.toLowerCase()] = b;
        }
        return map;
    }, [data]);

    const speedup512 = data?.speedup_vs_2k?.["512_vs_2k_ttf_pct"] ?? null;
    const speedup1k = data?.speedup_vs_2k?.["1k_vs_2k_ttf_pct"] ?? null;

    const claimDelta =
        speedup512 != null ? speedup512 - PAPER_CLAIM_PCT : null;
    const meetsClaim = speedup512 != null && speedup512 >= PAPER_CLAIM_PCT;

    if (status !== "authed") {
        return (
            <main className="site-shell">
                <div className="rounded-lg border border-border bg-card p-6">
                    <h1 className="text-xl font-display font-semibold">
                        Render Performance
                    </h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Vui lòng đăng nhập để tiếp tục.
                    </p>
                </div>
            </main>
        );
    }

    if (!isAdmin) {
        return (
            <main className="site-shell">
                <div className="rounded-lg border border-border bg-card p-6">
                    <h1 className="text-xl font-display font-semibold">
                        Render Performance
                    </h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Bạn không có quyền truy cập trang này.
                    </p>
                    <Link
                        href="/admin"
                        className="mt-3 inline-block text-sm text-primary underline"
                    >
                        ← Về Admin Studio
                    </Link>
                </div>
            </main>
        );
    }

    return (
        <main className="site-shell">
            <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                    <Link
                        href="/admin"
                        className="text-xs text-muted-foreground hover:text-foreground"
                    >
                        ← Admin Studio
                    </Link>
                    <h1 className="mt-1 text-3xl font-display font-bold text-foreground">
                        Render Performance Dashboard
                    </h1>
                    <p className="mt-1 text-sm text-muted-foreground">
                        Đối chiếu tốc độ render 3 LOD với tuyên bố{" "}
                        <strong>+{PAPER_CLAIM_PCT}%</strong> trong bài báo hội
                        thảo.
                    </p>
                </div>
                <div className="flex flex-wrap items-end gap-3">
                    <div>
                        <label className="block text-xs font-semibold text-muted-foreground">
                            Từ ngày
                        </label>
                        <input
                            type="date"
                            value={from}
                            onChange={(e) => setFrom(e.target.value)}
                            className="mt-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-semibold text-muted-foreground">
                            Đến ngày
                        </label>
                        <input
                            type="date"
                            value={to}
                            onChange={(e) => setTo(e.target.value)}
                            className="mt-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
                        />
                    </div>
                    <button
                        type="button"
                        onClick={fetchData}
                        disabled={loading}
                        className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                    >
                        {loading ? "Đang tải..." : "Tải lại"}
                    </button>
                    <button
                        type="button"
                        disabled={!data?.by_lod?.length}
                        onClick={() =>
                            downloadCsv(
                                `render-perf-${from}-to-${to}.csv`,
                                toCsv(data.by_lod),
                            )
                        }
                        className="rounded-md border border-border bg-card px-4 py-2 text-sm font-semibold hover:bg-muted disabled:opacity-50"
                    >
                        Xuất CSV
                    </button>
                </div>
            </div>

            {error ? (
                <div className="mt-6 rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
                    Lỗi: {error}
                </div>
            ) : null}

            <section className="mt-8">
                <div className="rounded-lg border border-border bg-card p-5 shadow-sm">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-display font-semibold">
                            Speedup vs 2k baseline (p50 ttf_ms)
                        </h2>
                        <div className="text-xs text-muted-foreground">
                            Tuyên bố bài báo: +{PAPER_CLAIM_PCT}%
                        </div>
                    </div>
                    <div className="mt-4 grid gap-4 md:grid-cols-2">
                        <div className="rounded-md border border-border bg-background p-4">
                            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                512 vs 2k
                            </div>
                            <div
                                className={[
                                    "mt-2 text-4xl font-display font-bold tabular-nums",
                                    speedup512 == null
                                        ? "text-muted-foreground"
                                        : meetsClaim
                                          ? "text-emerald-600 dark:text-emerald-400"
                                          : "text-amber-600 dark:text-amber-400",
                                ].join(" ")}
                            >
                                {formatPct(speedup512)}
                            </div>
                            {claimDelta != null ? (
                                <div className="mt-1 text-xs text-muted-foreground">
                                    Δ vs +{PAPER_CLAIM_PCT}%:{" "}
                                    <span className="font-semibold">
                                        {formatPct(claimDelta)}
                                    </span>
                                </div>
                            ) : null}
                        </div>
                        <div className="rounded-md border border-border bg-background p-4">
                            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                1k vs 2k
                            </div>
                            <div className="mt-2 text-4xl font-display font-bold tabular-nums">
                                {formatPct(speedup1k)}
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section className="mt-8 grid gap-4 md:grid-cols-3">
                {LOD_ORDER.map((label) => (
                    <LodCard
                        key={label}
                        bucket={bucketByLabel[label.toLowerCase()] || null}
                    />
                ))}
            </section>

            {data?.by_lod?.length === 0 ? (
                <div className="mt-8 rounded-lg border border-dashed border-border bg-card/50 p-6 text-center text-sm text-muted-foreground">
                    Chưa có sự kiện <code>render_performance</code> nào trong
                    khoảng thời gian này. Mở một trang chi tiết đỉnh để bắt đầu
                    thu thập dữ liệu.
                </div>
            ) : null}
        </main>
    );
}
