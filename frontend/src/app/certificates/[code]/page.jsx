"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { getCertificate } from "@/lib/api";

function formatDate(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return date.toLocaleDateString();
}

export default function CertificateVerifyPage() {
    const params = useParams();
    const code = useMemo(
        () => (typeof params?.code === "string" ? params.code : ""),
        [params],
    );

    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!code) return;
        let cancelled = false;

        async function load() {
            setLoading(true);
            setError(null);
            try {
                const res = await getCertificate({ code });
                if (!cancelled) setData(res);
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
    }, [code]);

    if (loading) {
        return (
            <main className="site-shell">
                <div className="rounded-lg border bg-card p-6 text-sm text-muted-foreground">
                    Đang xác minh chứng chỉ...
                </div>
            </main>
        );
    }

    if (error) {
        return (
            <main className="site-shell">
                <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-6 text-sm text-destructive">
                    {error}
                </div>
                <div className="mt-4">
                    <Link
                        href="/"
                        className="text-sm font-medium text-primary hover:text-primary/80"
                    >
                        Về trang chủ →
                    </Link>
                </div>
            </main>
        );
    }

    if (!data) {
        return (
            <main className="site-shell">
                <div className="rounded-lg border bg-card p-6 text-sm text-muted-foreground">
                    Không tìm thấy chứng chỉ.
                </div>
            </main>
        );
    }

    return (
        <main className="site-shell">
            <div className="rounded-lg border border-border bg-card p-8">
                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Xác minh chứng chỉ
                </div>
                <h1 className="mt-2 text-2xl font-display font-bold text-foreground">
                    Lưu Niên Sử Kí
                </h1>
                <p className="mt-1 text-sm text-muted-foreground">
                    Chứng chỉ xác thực cho hành trình học tập.
                </p>

                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                    <div className="rounded-lg border border-border bg-muted/40 p-4">
                        <div className="text-xs text-muted-foreground">Học viên</div>
                        <div className="mt-1 font-medium text-foreground">
                            {data.display_name}
                        </div>
                    </div>
                    <div className="rounded-lg border border-border bg-muted/40 p-4">
                        <div className="text-xs text-muted-foreground">Trạng thái</div>
                        <div className="mt-1 font-medium text-foreground">
                            {data.status === "issued" ? "Hợp lệ" : data.status}
                        </div>
                    </div>
                    <div className="rounded-lg border border-border bg-muted/40 p-4">
                        <div className="text-xs text-muted-foreground">Ngày cấp</div>
                        <div className="mt-1 font-medium text-foreground">
                            {formatDate(data.issued_at)}
                        </div>
                    </div>
                    <div className="rounded-lg border border-border bg-muted/40 p-4">
                        <div className="text-xs text-muted-foreground">Mã chứng chỉ</div>
                        <div className="mt-1 font-mono text-sm text-foreground">
                            {data.code}
                        </div>
                    </div>
                </div>

                <div className="mt-6 text-sm text-muted-foreground">
                    Nhà phát hành: <span className="font-medium">{data.issuer_name}</span>
                </div>
            </div>
        </main>
    );
}
