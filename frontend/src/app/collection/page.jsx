"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Lock, LogIn, Sparkles, UserPlus } from "lucide-react";

import { getMyCollection, listHistoryEntities } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import Skeleton from "@/components/Skeleton";
import {
    asEntityList,
    deburr,
    entityName,
    KNOWN_URNS,
    RELIEF_IMAGE_MAP,
    reliefThumbnailUrl,
    urnNameFromSlug,
    urnSlugFromReliefSlug,
} from "@/lib/history";

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

function buildFallbackMotifs() {
    return Object.keys(RELIEF_IMAGE_MAP).map((slug) => {
        const urnSlug = urnSlugFromReliefSlug(slug);
        const urnName = urnNameFromSlug(urnSlug);
        return {
            id: slug,
            slug,
            urn_slug: urnSlug,
            name_vi: slug.includes("-") ? `${urnName} — ${slug}` : urnName,
            thumbnail_url: reliefThumbnailUrl(slug),
        };
    });
}

function GuestCollectionPreview() {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedUrn, setSelectedUrn] = useState("");

    useEffect(() => {
        let cancelled = false;
        async function load() {
            setLoading(true);
            try {
                const res = await listHistoryEntities({ limit: 200 });
                if (cancelled) return;
                const list = asEntityList(res);
                const reliefs = list.filter(
                    (e) => e.entity_type === "relief" || !e.entity_type,
                );
                if (reliefs.length > 0) {
                    setItems(reliefs);
                } else {
                    setItems(buildFallbackMotifs());
                }
            } catch {
                if (!cancelled) setItems(buildFallbackMotifs());
            } finally {
                if (!cancelled) setLoading(false);
            }
        }
        load();
        return () => {
            cancelled = true;
        };
    }, []);

    const filteredItems = useMemo(() => {
        return items.filter((item) => {
            if (selectedUrn) {
                const itemUrn =
                    item.urn_slug || urnSlugFromReliefSlug(item.slug);
                if (itemUrn !== selectedUrn) return false;
            }
            if (searchQuery.trim()) {
                const q = deburr(searchQuery.trim().toLowerCase());
                const name = deburr(
                    String(
                        entityName(item) || item.name_vi || item.name || "",
                    ).toLowerCase(),
                );
                const han = String(
                    item.name_han_nom || item.han_nom || "",
                ).toLowerCase();
                const slug = String(item.slug || "").toLowerCase();
                if (
                    !name.includes(q) &&
                    !han.includes(q) &&
                    !slug.includes(q)
                )
                    return false;
            }
            return true;
        });
    }, [items, selectedUrn, searchQuery]);

    return (
        <main className="site-shell">
            {/* Guest Hero */}
            <section className="heritage-hero p-5 md:p-8">
                <div className="relative flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
                    <div className="max-w-2xl">
                        <div className="heritage-chip">
                            <Sparkles className="h-3.5 w-3.5" />
                            Kho báu 162 bản đúc nổi
                        </div>
                        <h1 className="mt-3 text-3xl font-display font-bold tracking-tight text-foreground md:text-4xl">
                            Bộ sưu tập 162 bản đúc nổi Cửu Đỉnh
                        </h1>
                        <p className="mt-3 text-sm leading-relaxed text-muted-foreground md:text-base">
                            Toàn bộ 162 phù điêu và đồ án đúc nổi trên chín đỉnh đồng Hoàng cung Huế (Di sản Tư liệu Ký ức Thế giới UNESCO). Bạn đang xem ở chế độ Khách xem trước — đăng nhập để lưu trữ bộ sưu tập cá nhân, làm bài kiểm tra và mở khóa danh hiệu!
                        </p>
                        <div className="mt-5 flex flex-wrap items-center gap-3">
                            <Link
                                href="/login"
                                className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-md transition hover:bg-primary/90"
                            >
                                <LogIn className="h-4 w-4" />
                                Đăng nhập để lưu tiến trình
                            </Link>
                            <Link
                                href="/register"
                                className="inline-flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/10 px-4 py-2.5 text-sm font-semibold text-primary transition hover:bg-primary/20"
                            >
                                <UserPlus className="h-4 w-4" />
                                Tạo tài khoản mới
                            </Link>
                        </div>
                    </div>

                    <div className="rounded-xl border border-primary/20 bg-background/50 p-5 backdrop-blur-sm lg:max-w-xs">
                        <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                            Chế độ khách
                        </div>
                        <div className="mt-2 text-sm font-medium text-foreground">
                            Đăng nhập để nhận các quyền lợi:
                        </div>
                        <ul className="mt-2.5 space-y-1.5 text-xs text-muted-foreground">
                            <li className="flex items-center gap-1.5">
                                <span className="text-success">✓</span> Theo dõi tiến độ mở khóa 162 họa tiết
                            </li>
                            <li className="flex items-center gap-1.5">
                                <span className="text-success">✓</span> Làm bài kiểm tra và ôn tập FSRS
                            </li>
                            <li className="flex items-center gap-1.5">
                                <span className="text-success">✓</span> Tích lũy XP, duy trì chuỗi học và nhận chứng chỉ
                            </li>
                        </ul>
                    </div>
                </div>
            </section>

            {/* Quick Stats Overview */}
            <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div className="heritage-card p-4 text-center">
                    <div className="relative">
                        <div className="font-display tabular-nums text-2xl font-bold text-foreground">
                            162
                        </div>
                        <div className="text-xs font-medium text-muted-foreground">
                            Tổng họa tiết
                        </div>
                    </div>
                </div>
                <div className="heritage-card p-4 text-center">
                    <div className="relative">
                        <div className="font-display tabular-nums text-2xl font-bold text-primary">
                            9
                        </div>
                        <div className="text-xs font-medium text-muted-foreground">
                            Đỉnh đồng
                        </div>
                    </div>
                </div>
                <div className="heritage-card p-4 text-center">
                    <div className="relative">
                        <div className="font-display tabular-nums text-2xl font-bold text-success">
                            18
                        </div>
                        <div className="text-xs font-medium text-muted-foreground">
                            Bản đúc mỗi đỉnh
                        </div>
                    </div>
                </div>
                <div className="heritage-card p-4 text-center">
                    <div className="relative">
                        <div className="font-display tabular-nums text-2xl font-bold text-bronze">
                            0 / 162
                        </div>
                        <div className="text-xs font-medium text-muted-foreground">
                            Đã mở khóa (Khách)
                        </div>
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="heritage-surface mt-5 p-4">
                <div className="relative grid gap-4 sm:grid-cols-2">
                    <div>
                        <label className="block text-xs font-medium text-muted-foreground">
                            Tìm kiếm họa tiết
                        </label>
                        <input
                            type="text"
                            placeholder="Lọc theo tên, chữ Hán, chủ đề..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="mt-1 block w-full rounded-lg border border-input bg-background/60 px-3 py-2 text-foreground shadow-sm focus:border-primary focus:ring-primary sm:text-sm"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-muted-foreground">
                            Lọc theo Đỉnh đồng
                        </label>
                        <select
                            value={selectedUrn}
                            onChange={(e) => setSelectedUrn(e.target.value)}
                            className="mt-1 block w-full rounded-lg border border-input bg-background/60 px-3 py-2 text-foreground shadow-sm focus:border-primary focus:ring-primary sm:text-sm"
                        >
                            <option value="">Tất cả 9 đỉnh đồng</option>
                            {KNOWN_URNS.map((u) => (
                                <option key={u.slug} value={u.slug}>
                                    {u.name} ({u.slug})
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            {/* Count & Grid */}
            <div className="mt-6">
                <div className="mb-4 flex items-center justify-between text-sm text-muted-foreground">
                    <span>
                        Hiển thị <span className="font-display font-semibold tabular-nums text-foreground">{filteredItems.length}</span> / 162 bản đúc nổi (Bản xem trước)
                    </span>
                    {(searchQuery || selectedUrn) && (
                        <button
                            type="button"
                            onClick={() => {
                                setSearchQuery("");
                                setSelectedUrn("");
                            }}
                            className="text-xs text-primary hover:underline"
                        >
                            Đặt lại bộ lọc
                        </button>
                    )}
                </div>

                {loading ? (
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
                        {[...Array(12)].map((_, i) => (
                            <div key={i} className="heritage-card aspect-[4/5] p-3">
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
                ) : filteredItems.length === 0 ? (
                    <div className="rounded-lg border border-dashed border-input bg-card/45 py-12 text-center">
                        <p className="text-muted-foreground">
                            Không tìm thấy họa tiết nào phù hợp với từ khóa của bạn.
                        </p>
                        <button
                            type="button"
                            onClick={() => {
                                setSearchQuery("");
                                setSelectedUrn("");
                            }}
                            className="mt-2 text-sm font-medium text-primary hover:underline"
                        >
                            Xóa bộ lọc
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
                        {filteredItems.map((item) => {
                            const urnSlug =
                                item.urn_slug || urnSlugFromReliefSlug(item.slug);
                            const urnName = urnNameFromSlug(urnSlug);
                            const name =
                                entityName(item) ||
                                item.name_vi ||
                                item.name ||
                                item.slug;
                            const hanNom = item.name_han_nom || item.han_nom;
                            const thumb =
                                item.thumbnail_url ||
                                reliefThumbnailUrl(item.slug);
                            const href =
                                urnSlug && item.slug
                                    ? `/atlas/${urnSlug}/${item.slug}`
                                    : `/cuu-dinh/${urnSlug || "cao-dinh"}`;

                            return (
                                <Link
                                    key={item.id || item.slug}
                                    href={href}
                                    className="group relative flex aspect-[4/5] flex-col overflow-hidden rounded-lg border border-primary/15 bg-card/75 shadow-[0_12px_30px_-26px_rgba(0,0,0,0.8)] transition duration-200 hover:border-primary/40 hover:-translate-y-0.5"
                                >
                                    <div className="relative flex-1 overflow-hidden bg-muted">
                                        {thumb ? (
                                            <img
                                                src={thumb}
                                                alt={name}
                                                loading="lazy"
                                                decoding="async"
                                                className="h-full w-full object-cover transition duration-200 group-hover:scale-[1.03]"
                                            />
                                        ) : (
                                            <div className="flex h-full w-full items-center justify-center text-sm text-muted-foreground">
                                                Chưa có ảnh
                                            </div>
                                        )}
                                        <div className="absolute right-2 top-2">
                                            <span className="inline-flex items-center gap-1 rounded-md bg-black/70 px-2 py-0.5 text-[10px] font-medium text-white backdrop-blur-sm">
                                                <Lock className="h-2.5 w-2.5" />
                                                Xem trước
                                            </span>
                                        </div>
                                        {hanNom ? (
                                            <span className="absolute bottom-2 left-2 rounded-md bg-black/70 px-1.5 py-0.5 font-serif text-[11px] font-bold text-amber-300 backdrop-blur-sm">
                                                {hanNom}
                                            </span>
                                        ) : null}
                                    </div>

                                    <div className="border-t p-2.5">
                                        <h3
                                            className="truncate text-xs font-display font-semibold text-foreground"
                                            title={name}
                                        >
                                            {name}
                                        </h3>
                                        <div className="mt-1 flex items-center justify-between text-[11px] text-muted-foreground">
                                            <span className="truncate">
                                                {urnName}
                                            </span>
                                        </div>
                                    </div>
                                </Link>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Bottom CTA Banner */}
            <div className="heritage-surface mt-8 p-6 text-center">
                <div className="relative mx-auto max-w-xl">
                    <h2 className="text-xl font-display font-bold text-foreground">
                        Bắt đầu hành trình chinh phục di sản Cửu Đỉnh
                    </h2>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Đăng ký tài khoản để ghi nhận từng họa tiết bạn khám phá, làm bài kiểm tra trắc nghiệm và nhận huy hiệu danh giá.
                    </p>
                    <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
                        <Link
                            href="/register"
                            className="rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow transition hover:bg-primary/90"
                        >
                            Đăng ký tài khoản
                        </Link>
                        <Link
                            href="/login"
                            className="rounded-lg border border-border px-5 py-2.5 text-sm font-medium text-foreground hover:bg-muted"
                        >
                            Đăng nhập
                        </Link>
                    </div>
                </div>
            </div>
        </main>
    );
}

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
        return <GuestCollectionPreview />;
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
