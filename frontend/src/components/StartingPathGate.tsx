"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname } from "next/navigation";

import { getUrns, logAnalyticsEvent, setStartingPath } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import { isPublicPath } from "@/lib/publicPaths";

interface Urn {
    id: string | number;
    name?: string;
    motif_count?: number;
    thumbnail_url?: string | null;
    [key: string]: unknown;
}

interface StartingPathResponse {
    starting_urn_id?: string | number;
    starting_urn_slug?: string;
    [key: string]: unknown;
}

export default function StartingPathGate() {    const pathname = usePathname();
    const status = useAuthStore((s) => s.status);
    const user = useAuthStore((s) => s.user);
    const fetchMe = useAuthStore((s) => s.fetchMe);

    const [urns, setUrns] = useState<Urn[]>([]);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedUrnId, setSelectedUrnId] = useState<string | number | null>(null);

    const shouldShow = useMemo(() => {
        if (status !== "authed" || !user) return false;
        if (isPublicPath(pathname)) return false;
        return !user.starting_urn_id;
    }, [pathname, status, user]);

    useEffect(() => {
        if (status === "authed" && !user) fetchMe();
    }, [status, user, fetchMe]);

    useEffect(() => {
        if (!shouldShow) return;
        let cancelled = false;

        async function load() {
            setLoading(true);
            setError(null);
            try {
                const res = (await getUrns()) as Urn[] | null;
                if (!cancelled) {
                    setUrns(res || []);
                    if (!selectedUrnId && res?.length)
                        setSelectedUrnId(res[0].id);
                }
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
    }, [shouldShow, selectedUrnId]);

    useEffect(() => {
        if (!shouldShow) return;
        const prevOverflow = document.body.style.overflow;
        document.body.style.overflow = "hidden";
        return () => {
            document.body.style.overflow = prevOverflow;
        };
    }, [shouldShow]);

    async function handleConfirm() {
        if (status !== "authed" || !selectedUrnId) return;
        setSaving(true);
        setError(null);
        try {
            const res = (await setStartingPath({ urnId: selectedUrnId })) as StartingPathResponse;
            useAuthStore.setState((state) => ({
                user: {
                    ...(state.user || {}),
                    starting_urn_id: res.starting_urn_id,
                } as unknown as typeof state.user,
            }));
            await logAnalyticsEvent({
                name: "starting_path_selected",
                payload: {
                    urn_id: res.starting_urn_id,
                    urn_slug: res.starting_urn_slug,
                    source: "client",
                },
                path: pathname || "/",
            }).catch(() => null);
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err));
        } finally {
            setSaving(false);
        }
    }

    if (!shouldShow) return null;

    return (
        <div className="fixed inset-0 z-[90] flex min-h-dvh items-center justify-center bg-background/90 px-4 py-8 backdrop-blur-sm">
            <div className="w-full max-w-5xl rounded-3xl border border-border bg-card p-6 shadow-elegant">
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                        <h1 className="text-2xl font-display font-bold text-foreground">
                            Chọn lộ trình bắt đầu
                        </h1>
                        <p className="mt-1 text-sm text-muted-foreground">
                            Chọn một Cửu Đỉnh để hệ thống cá nhân hóa hành trình
                            học tập của bạn.
                        </p>
                    </div>
                    <button
                        type="button"
                        onClick={handleConfirm}
                        disabled={!selectedUrnId || saving}
                        className="rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
                    >
                        {saving ? "Đang lưu..." : "Bắt đầu lộ trình"}
                    </button>
                </div>

                {error ? (
                    <div className="mt-4 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                        {error}
                    </div>
                ) : null}

                {loading ? (
                    <div className="mt-6 text-sm text-muted-foreground">
                        Đang tải danh sách Cửu Đỉnh...
                    </div>
                ) : (
                    <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        {urns.map((urn) => {
                            const isSelected = urn.id === selectedUrnId;
                            return (
                                <button
                                    key={urn.id}
                                    type="button"
                                    onClick={() => setSelectedUrnId(urn.id)}
                                    className={[
                                        "group rounded-2xl border p-4 text-left transition",
                                        isSelected
                                            ? "border-primary bg-primary/10"
                                            : "border-border bg-card hover:border-primary/50",
                                    ].join(" ")}
                                >
                                    <div className="flex items-start justify-between gap-3">
                                        <div className="min-w-0">
                                            <div className="truncate text-lg font-display font-semibold text-foreground">
                                                {urn.name}
                                            </div>
                                            <div className="mt-1 text-xs text-muted-foreground">
                                                Họa tiết:{" "}
                                                <span className="font-display tabular-nums">
                                                    {urn.motif_count ?? 0}
                                                </span>
                                            </div>
                                        </div>
                                        {isSelected ? (
                                            <span className="rounded-full bg-primary px-2 py-1 text-[10px] font-semibold text-primary-foreground">
                                                Đã chọn
                                            </span>
                                        ) : null}
                                    </div>

                                    <div className="mt-4 overflow-hidden rounded-xl bg-muted">
                                        {urn.thumbnail_url ? (
                                            <img
                                                src={urn.thumbnail_url}
                                                alt={urn.name}
                                                loading="lazy"
                                                decoding="async"
                                                className="h-36 w-full object-cover"
                                            />
                                        ) : (
                                            <div className="flex h-36 items-center justify-center text-xs text-muted-foreground">
                                                Chưa có ảnh thu nhỏ
                                            </div>
                                        )}
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
