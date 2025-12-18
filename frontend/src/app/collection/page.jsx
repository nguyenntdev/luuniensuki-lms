"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { getMyCollection } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import Skeleton from "@/components/Skeleton";

const CATEGORIES = [
  { value: "", label: "Tất Cả Danh Mục" },
  { value: "linh_thu", label: "Linh Thú" },
  { value: "dong_vat", label: "Động Vật" },
  { value: "thao_moc", label: "Thảo Mộc" },
  { value: "dia_ly", label: "Địa Lý" },
  { value: "nong_nghiep", label: "Nông Nghiệp" },
  { value: "vo_bi", label: "Võ Bị" },
  { value: "giao_thuong", label: "Giao Thương" },
  { value: "thien_van", label: "Thiên Văn" },
  { value: "kien_truc", label: "Kiến Trúc" },
];

const RARITIES = [
  { value: "", label: "Tất Cả Độ Hiếm" },
  { value: "common", label: "Phổ Thông" },
  { value: "uncommon", label: "Không Phổ Biến" },
  { value: "rare", label: "Hiếm" },
  { value: "epic", label: "Sử Thi" },
  { value: "legendary", label: "Huyền Thoại" },
];

const STATUSES = [
  { value: "", label: "Tất Cả Trạng Thái" },
  { value: "discovered", label: "Đã Khám Phá" },
  { value: "learned", label: "Đã Học" },
  { value: "mastered", label: "Đã Thành Thạo" },
  { value: "hidden", label: "Đã Khóa" },
];

export default function CollectionPage() {
  const token = useAuthStore((s) => s.accessToken);
  const fetchMe = useAuthStore((s) => s.fetchMe);

  const [collection, setCollection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter states
  const [searchQuery, setSearchQuery] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterRarity, setFilterRarity] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  useEffect(() => {
    if (token) fetchMe();
  }, [token, fetchMe]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!token) return;
      setLoading(true);
      setError(null);
      try {
        const res = await getMyCollection({ token });
        if (!cancelled) setCollection(res);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [token]);

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
      if (filterCategory && item.category !== filterCategory) return false;

      // Rarity filter
      if (filterRarity && item.rarity !== filterRarity) return false;

      // Status filter
      if (filterStatus && item.status !== filterStatus) return false;

      return true;
    });
  }, [collection, searchQuery, filterCategory, filterRarity, filterStatus]);

  if (!token) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-10">
        <div className="rounded-xl border bg-card p-6">
          <h1 className="text-xl font-display font-semibold">Bộ Sưu Tập</h1>
          <p className="mt-2 text-sm text-muted-foreground">Vui lòng đăng nhập để xem bộ sưu tập của bạn.</p>
          <div className="mt-4">
            <Link href="/login" className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">
              Đăng Nhập
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold tracking-tight text-foreground">Bộ Sưu Tập Của Bạn</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Theo dõi tiến trình khám phá, học tập và thành thạo các họa tiết từ Hoàng Thành.
          </p>
        </div>
      </div>

      {/* Stats Overview */}
      {loading && !collection ? (
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="rounded-xl border bg-card p-4 shadow-sm">
              <Skeleton className="mx-auto h-8 w-12" />
              <Skeleton className="mx-auto mt-2 h-3 w-20" />
            </div>
          ))}
        </div>
      ) : collection?.stats ? (
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-xl border bg-card p-4 text-center shadow-sm">
            <div className="font-display tabular-nums text-2xl font-bold text-foreground">{collection.stats.total}</div>
            <div className="text-xs font-medium text-muted-foreground">Tổng Họa Tiết</div>
          </div>
          <div className="rounded-xl border bg-card p-4 text-center shadow-sm">
            <div className="font-display tabular-nums text-2xl font-bold text-primary">{collection.stats.discovered}</div>
            <div className="text-xs font-medium text-muted-foreground">Đã Khám Phá</div>
          </div>
          <div className="rounded-xl border bg-card p-4 text-center shadow-sm">
            <div className="font-display tabular-nums text-2xl font-bold text-success">{collection.stats.learned}</div>
            <div className="text-xs font-medium text-muted-foreground">Đã Học</div>
          </div>
          <div className="rounded-xl border bg-card p-4 text-center shadow-sm">
            <div className="font-display tabular-nums text-2xl font-bold text-bronze">{collection.stats.mastered}</div>
            <div className="text-xs font-medium text-muted-foreground">Đã Thành Thạo</div>
          </div>
        </div>
      ) : null}

      {/* Filters */}
      <div className="mt-8 rounded-xl border bg-card p-4 shadow-sm">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Search */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground">Tìm Kiếm</label>
            <input
              type="text"
              placeholder="Lọc theo tên..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="mt-1 block w-full rounded-md border-input bg-background shadow-sm focus:border-primary focus:ring-primary sm:text-sm text-foreground"
            />
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground">Trạng Thái</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="mt-1 block w-full rounded-md border-input bg-background shadow-sm focus:border-primary focus:ring-primary sm:text-sm text-foreground"
            >
              {STATUSES.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {/* Category Filter */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground">Danh Mục</label>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="mt-1 block w-full rounded-md border-input bg-background shadow-sm focus:border-primary focus:ring-primary sm:text-sm text-foreground"
            >
              {CATEGORIES.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {/* Rarity Filter */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground">Độ Hiếm</label>
            <select
              value={filterRarity}
              onChange={(e) => setFilterRarity(e.target.value)}
              className="mt-1 block w-full rounded-md border-input bg-background shadow-sm focus:border-primary focus:ring-primary sm:text-sm text-foreground"
            >
              {RARITIES.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error ? <div className="mt-6 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}
      
      {/* Grid */}
      <div className="mt-6">
        <div className="mb-4 text-sm text-muted-foreground">
          {loading && !collection ? (
            <Skeleton className="h-4 w-32" />
          ) : (
            <span>
              Hiển thị <span className="font-display tabular-nums">{items.length}</span>{" "}
              {items.length === 1 ? "mục" : "mục"}
            </span>
          )}
        </div>
        
	        {loading && !collection ? (
	           <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
	             {[...Array(12)].map((_, i) => (
	               <div key={i} className="aspect-[4/5] rounded-xl border bg-card p-3 shadow-sm">
	                 <Skeleton className="h-[75%] w-full rounded-lg" />
	                 <div className="mt-3">
                    <Skeleton className="h-4 w-2/3" />
                    <Skeleton className="mt-1 h-3 w-1/2" />
                 </div>
               </div>
             ))}
           </div>
        ) : items.length === 0 && !loading ? (
          <div className="rounded-xl border border-dashed border-input py-12 text-center">
            <p className="text-muted-foreground">Không tìm thấy họa tiết nào phù hợp với bộ lọc của bạn.</p>
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
	          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
	            {items.map((item) => {
	              const unlocked = item.status !== "hidden";
	              let statusColor = "bg-muted text-muted-foreground";
	              if (item.status === "discovered") statusColor = "bg-info/20 text-info";
              if (item.status === "learned") statusColor = "bg-success/20 text-success";
              if (item.status === "mastered") statusColor = "bg-bronze/20 text-bronze";

              return (
                <Link
                  key={item.motif_id}
                  href={`/motif/${item.motif_id}`}
                  className={[
                    "group relative flex aspect-[4/5] flex-col overflow-hidden rounded-xl border bg-card shadow-sm transition hover:shadow-md",
                    unlocked ? "" : "opacity-75",
                  ].join(" ")}
                >
                  {/* Image Area */}
                  <div className="relative flex-1 overflow-hidden bg-muted">
                    {item.thumbnail_url ? (
                      <img
                        src={item.thumbnail_url}
                        alt={item.name}
                        className={["h-full w-full object-cover transition duration-300 group-hover:scale-105", unlocked ? "" : "grayscale"].join(" ")}
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center text-2xl text-muted-foreground">
                        ?
                      </div>
                    )}
                    
                    {/* Status Badge */}
                    <div className="absolute right-2 top-2">
                      {unlocked ? (
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${statusColor}`}>
                          {item.status}
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded-full bg-black/60 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-white backdrop-blur-sm">
                          Locked
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Info Area */}
                  <div className="border-t p-3">
                    <h3 className="truncate text-sm font-display font-semibold text-foreground" title={item.name}>
                      {unlocked ? item.name : "???"}
                    </h3>
                    <div className="mt-1 flex items-center justify-between text-xs text-muted-foreground">
                      <span className="truncate">{item.category}</span>
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
