"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { getMyCollection } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import Skeleton from "@/components/Skeleton";

const CATEGORIES = [
    { value: "", label: "Tất cả danh mục" },
    { value: "linh_thu", label: "Linh thú" },
    { value: "dong_vat", label: "Động vật" },
    { value: "thao_moc", label: "Thảo mộc" },
    { value: "dia_ly", label: "Địa lý" },
    { value: "nong_nghiep", label: "Nông nghiệp" },
    { value: "vo_bi", label: "Võ bị" },
    { value: "giao_thuong", label: "Giao thương" },
    { value: "thien_van", label: "Thiên văn" },
    { value: "kien_truc", label: "Kiến trúc" },
];

const RARITIES = [
    { value: "", label: "Tất cả độ hiếm" },
    { value: "common", label: "Phổ thông" },
    { value: "uncommon", label: "Không phổ biến" },
    { value: "rare", label: "Hiếm" },
    { value: "epic", label: "Sử thi" },
    { value: "legendary", label: "Huyền thoại" },
];

const STATUSES = [
    { value: "", label: "Tất cả trạng thái" },
    { value: "discovered", label: "Đã khám phá" },
    { value: "learned", label: "Đã học" },
    { value: "mastered", label: "Đã thành thạo" },
    { value: "hidden", label: "Đã khóa" },
];

// Quick lookup: category enum -> Vietnamese label (cards showed the raw enum before).
const CATEGORY_LABEL = Object.fromEntries(
    CATEGORIES.filter((c) => c.value).map((c) => [c.value, c.label]),
);

export default function CollectionPage() {
    const status = useAuthStore((s) => s.status);

    const [collection, setCollection] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Filter states
    const [searchQuery, setSearchQuery] = useState("");
    const [filterCategory, setFilterCategory] = useState("");
    const [filterRarity, setFilterRarity] = useState("");
    const [filterStatus, setFilterStatus] = useState("");

    useEffect(() => {
        let cancelled = false;
        async function load() {
            if (status !== "authed") return;
            setLoading(true);
            setError(null);
            try {
                const res = await getMyCollection();
                if (!cancelled) setCollection(res);
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

    const items = useMemo(() => {
        if (!collection?.items) return [];

        return collection.items.filter((item) => {
            // Search filter
            if (searchQuery) {
                const q = searchQuery.toLowerCase();
                const matchName = item.name.toLowerCase().includes(q);
                const matchEn = item.name_en?.toLowerCase().includes(q);
                if (!matchName && !matchEn) return false;
            }

            // Category filter
            if (filterCategory && item.category !== filterCategory)
                return false;

            // Rarity filter
            if (filterRarity && item.rarity !== filterRarity) return false;

            // Status filter
            if (filterStatus && item.status !== filterStatus) return false;

            return true;
        });
    }, [collection, searchQuery, filterCategory, filterRarity, filterStatus]);

    if (status !== "authed") {
        return (
            <main className="site-shell">
                <div className="heritage-surface p-6">
                  <div className="relative">
                    <h1 className="text-xl font-display font-semibold">
                        Bộ sưu tập
                    </h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Vui lòng đăng nhập để xem bộ sưu tập của bạn.
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
                </div>
            </main>
        );
    }

    return (
        <main className="site-shell">
            {/* Header */}
            <section className="heritage-hero md:p-6">
              <div className="relative flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div className="max-w-2xl">
                    <div className="heritage-chip">Kho họa tiết</div>
                    <h1 className="text-3xl font-display font-bold tracking-tight text-foreground">
                        Bộ sưu tập của bạn
                    </h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Theo dõi tiến trình khám phá, học tập và thành thạo các
                        họa tiết từ Hoàng Thành.
                    </p>
                </div>
              </div>
            </section>

            {/* Stats Overview */}
            {loading && !collection ? (
                <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {[...Array(4)].map((_, i) => (
                        <div
                            key={i}
                            className="heritage-card p-4"
                        >
                            <div className="relative">
                            <Skeleton className="mx-auto h-8 w-12" />
                            <Skeleton className="mx-auto mt-2 h-3 w-20" />
                            </div>
                        </div>
                    ))}
                </div>
            ) : collection?.stats ? (
                <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
                    <div className="heritage-card p-4 text-center">
                      <div className="relative">
                        <div className="font-display tabular-nums text-2xl font-bold text-foreground">
                            {collection.stats.total}
                        </div>
                        <div className="text-xs font-medium text-muted-foreground">
                            Tổng họa tiết
                        </div>
                      </div>
                    </div>
                    <div className="heritage-card p-4 text-center">
                      <div className="relative">
                        <div className="font-display tabular-nums text-2xl font-bold text-primary">
                            {collection.stats.discovered}
                        </div>
                        <div className="text-xs font-medium text-muted-foreground">
                            Đã khám phá
                        </div>
                      </div>
                    </div>
                    <div className="heritage-card p-4 text-center">
                      <div className="relative">
                        <div className="font-display tabular-nums text-2xl font-bold text-success">
                            {collection.stats.learned}
                        </div>
                        <div className="text-xs font-medium text-muted-foreground">
                            Đã học
                        </div>
                      </div>
                    </div>
                    <div className="heritage-card p-4 text-center">
                      <div className="relative">
                        <div className="font-display tabular-nums text-2xl font-bold text-bronze">
                            {collection.stats.mastered}
                        </div>
                        <div className="text-xs font-medium text-muted-foreground">
                            Đã thành thạo
                        </div>
                      </div>
                    </div>
                </div>
            ) : null}

            {/* Overall mastery progress */}
            {collection?.stats && collection.stats.total > 0 ? (
                <div className="heritage-surface mt-3 p-4">
                  <div className="relative">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span className="font-semibold uppercase tracking-wider">Tiến độ thành thạo</span>
                        <span className="font-display tabular-nums text-foreground">
                            {Math.round((collection.stats.mastered / collection.stats.total) * 100)}%
                        </span>
                    </div>
                    <div className="progress-track mt-2">
                        <div
                            className="progress-fill"
                            style={{ width: `${Math.round((collection.stats.mastered / collection.stats.total) * 100)}%` }}
                        />
                    </div>
                    <div className="mt-2 text-[11px] text-muted-foreground">
                        {collection.stats.mastered}/{collection.stats.total} họa tiết đã thành thạo ·{" "}
                        {collection.stats.discovered + collection.stats.learned + collection.stats.mastered} đã mở khóa
                    </div>
                  </div>
                </div>
            ) : null}

            {/* Filters */}
            <div className="heritage-surface mt-5 p-4">
              <div className="relative">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    {/* Search */}
                    <div>
                        <label className="block text-xs font-medium text-muted-foreground">
                            Tìm kiếm
                        </label>
                        <input
                            type="text"
                            placeholder="Lọc theo tên..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="mt-1 block w-full rounded-lg border border-input bg-background/60 px-3 py-2 text-foreground shadow-sm focus:border-primary focus:ring-primary sm:text-sm"
                        />
                    </div>

                    {/* Status Filter */}
                    <div>
                        <label className="block text-xs font-medium text-muted-foreground">
                            Trạng thái
                        </label>
                        <select
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                            className="mt-1 block w-full rounded-lg border border-input bg-background/60 px-3 py-2 text-foreground shadow-sm focus:border-primary focus:ring-primary sm:text-sm"
                        >
                            {STATUSES.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                    {opt.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Category Filter */}
                    <div>
                        <label className="block text-xs font-medium text-muted-foreground">
                            Danh mục
                        </label>
                        <select
                            value={filterCategory}
                            onChange={(e) => setFilterCategory(e.target.value)}
                            className="mt-1 block w-full rounded-lg border border-input bg-background/60 px-3 py-2 text-foreground shadow-sm focus:border-primary focus:ring-primary sm:text-sm"
                        >
                            {CATEGORIES.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                    {opt.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Rarity Filter */}
                    <div>
                        <label className="block text-xs font-medium text-muted-foreground">
                            Độ hiếm
                        </label>
                        <select
                            value={filterRarity}
                            onChange={(e) => setFilterRarity(e.target.value)}
                            className="mt-1 block w-full rounded-lg border border-input bg-background/60 px-3 py-2 text-foreground shadow-sm focus:border-primary focus:ring-primary sm:text-sm"
                        >
                            {RARITIES.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                    {opt.label}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
              </div>
            </div>

            {error ? (
                <div className="mt-6 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
                    {error}
                </div>
            ) : null}

            {/* Grid */}
            <div className="mt-6">
                <div className="mb-4 text-sm text-muted-foreground">
                    {loading && !collection ? (
                        <Skeleton className="h-4 w-32" />
                    ) : (
                        <span>
                            Hiển thị{" "}
                            <span className="font-display tabular-nums">
                                {items.length}
                            </span>{" "}
                            {items.length === 1 ? "mục" : "mục"}
                        </span>
                    )}
                </div>

                {loading && !collection ? (
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
                        {[...Array(12)].map((_, i) => (
                            <div
                                key={i}
                                className="heritage-card aspect-[4/5] p-3"
                            >
                                <div className="relative h-full">
                                <Skeleton className="h-[75%] w-full rounded-lg" />
                                <div className="mt-3">
                                    <Skeleton className="h-4 w-2/3" />
                                    <Skeleton className="mt-1 h-3 w-1/2" />
                                </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : items.length === 0 && !loading ? (
                    <div className="rounded-lg border border-dashed border-input bg-card/45 py-12 text-center">
                        <p className="text-muted-foreground">
                            Không tìm thấy họa tiết nào phù hợp với bộ lọc của
                            bạn.
                        </p>
                        <button
                            onClick={() => {
                                setSearchQuery("");
                                setFilterCategory("");
                                setFilterRarity("");
                                setFilterStatus("");
                            }}
                            className="mt-2 text-sm font-medium text-primary hover:text-primary/80"
                        >
                            Xóa tất cả bộ lọc
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
                        {items.map((item) => {
                            const unlocked = item.status !== "hidden";
                            let statusColor = "bg-muted text-muted-foreground";
                            if (item.status === "discovered")
                                statusColor = "bg-info/20 text-info";
                            if (item.status === "learned")
                                statusColor = "bg-success/20 text-success";
                            if (item.status === "mastered")
                                statusColor = "bg-bronze/20 text-bronze";

                            return (
                                <Link
                                    key={item.motif_id}
                                    href={`/motif/${item.motif_id}`}
                                    className={[
                                        "group relative flex aspect-[4/5] flex-col overflow-hidden rounded-lg border border-primary/15 bg-card/75 shadow-[0_12px_30px_-26px_rgba(0,0,0,0.8)] transition duration-200 hover:border-primary/35",
                                        unlocked ? "" : "opacity-75",
                                    ].join(" ")}
                                >
                                    {/* Image Area */}
                                    <div className="relative flex-1 overflow-hidden bg-muted">
                                        {item.thumbnail_url ? (
                                            <img
                                                src={item.thumbnail_url}
                                                alt={item.name}
                                                loading="lazy"
                                                decoding="async"
                                                className={[
                                                    "h-full w-full object-cover transition duration-200 group-hover:scale-[1.025]",
                                                    unlocked ? "" : "grayscale",
                                                ].join(" ")}
                                            />
                                        ) : (
                                            <div className="flex h-full w-full items-center justify-center text-2xl text-muted-foreground">
                                                Chưa có ảnh
                                            </div>
                                        )}

                                        {/* Status Badge */}
                                        <div className="absolute right-2 top-2">
                                            {unlocked ? (
                                                <span
                                                    className={`inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${statusColor}`}
                                                >
                                                    {STATUSES.find((statusItem) => statusItem.value === item.status)?.label || item.status}
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center rounded-md bg-black/60 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-white backdrop-blur-sm">
                                                    Đã khóa
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    {/* Info Area */}
                                    <div className="border-t p-3">
                                        <h3
                                            className="truncate text-sm font-display font-semibold text-foreground"
                                            title={item.name}
                                        >
                                            {unlocked ? item.name : "???"}
                                        </h3>
                                        <div className="mt-1 flex items-center justify-between text-xs text-muted-foreground">
                                            <span className="truncate">
                                                {CATEGORY_LABEL[item.category] || item.category}
                                            </span>
                                        </div>
                                    </div>
                                </Link>
                            );
                        })}
                    </div>
                )}
            </div>
        </main>
    );
}
