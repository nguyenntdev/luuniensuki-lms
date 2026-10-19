"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import React, { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  Award,
  Box,
  Compass,
  Landmark,
  Layers,
  MapPin,
  RotateCcw,
  Search,
  Sparkles,
  Trophy,
} from "lucide-react";

import HeritageCard from "@/components/explore/HeritageCard";
import HeritageFilters, {
  FILTER_CATEGORY_TABS,
} from "@/components/explore/HeritageFilters";
import Skeleton from "@/components/Skeleton";
import EmptyState from "@/components/ui/EmptyState";
import { listHeritagePlaces } from "@/lib/api";
import {
  DEFAULT_HERITAGE_PLACES,
  filterHeritagePlaces,
} from "@/lib/rbpc/heritageData";

function ExploreContent() {
  const searchParams = useSearchParams();

  // Read initial query parameters from URL if present
  const initialCategory = searchParams?.get("category") || "all";
  const initialQuery = searchParams?.get("q") || "";
  const initialUnesco = searchParams?.get("unesco") === "true";
  const initial3d = searchParams?.get("has_3d") === "true";
  const initialView = searchParams?.get("view") === "map" ? "map" : "grid";

  const [places, setPlaces] = useState(DEFAULT_HERITAGE_PLACES);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [filterValues, setFilterValues] = useState({
    q: initialQuery,
    category: initialCategory,
    unescoOnly: initialUnesco,
    has3dOnly: initial3d,
    accessStatus: "all",
  });

  const [viewMode, setViewMode] = useState(initialView);

  // Synchronize when searchParams change externally (e.g. from header nav links)
  useEffect(() => {
    if (!searchParams) return;
    const cat = searchParams.get("category");
    const q = searchParams.get("q");
    const unesco = searchParams.get("unesco");
    const has3d = searchParams.get("has_3d");
    const view = searchParams.get("view");

    setFilterValues((prev) => ({
      ...prev,
      category: cat || prev.category,
      q: q !== null ? q : prev.q,
      unescoOnly: unesco !== null ? unesco === "true" : prev.unescoOnly,
      has3dOnly: has3d !== null ? has3d === "true" : prev.has3dOnly,
    }));

    if (view === "map" || view === "grid") {
      setViewMode(view);
    }
  }, [searchParams]);

  // Attempt to fetch fresh data from backend API with fallback to verified seed data
  useEffect(() => {
    let cancelled = false;

    async function loadPlaces() {
      try {
        const data = await listHeritagePlaces({ limit: 100 });
        if (!cancelled && data?.items && Array.isArray(data.items) && data.items.length > 0) {
          setPlaces(data.items);
        }
      } catch (err) {
        // Silently preserve DEFAULT_HERITAGE_PLACES fallback
      }
    }

    loadPlaces();
    return () => {
      cancelled = true;
    };
  }, []);

  // Diacritic-tolerant, accent-insensitive filtered places
  const filteredPlaces = useMemo(() => {
    return filterHeritagePlaces(places, filterValues);
  }, [places, filterValues]);

  const handleResetFilters = useCallback(() => {
    setFilterValues({
      q: "",
      category: "all",
      unescoOnly: false,
      has3dOnly: false,
      accessStatus: "all",
    });
  }, []);

  // Compute live statistics for summary chips
  const totalUnescoCount = useMemo(() => {
    return places.filter(
      (p) =>
        p.official_reference_id?.startsWith("678") ||
        p.official_designation?.toLowerCase().includes("unesco")
    ).length;
  }, [places]);

  const total3dCount = useMemo(() => {
    return places.filter((p) => p.has_3d).length;
  }, [places]);

  return (
    <main className="site-shell">
      {/* 1. Hero Showcase Section */}
      <section data-testid="explore-hero" className="heritage-hero md:p-6">
        <div className="relative flex flex-wrap items-start justify-between gap-5">
          <div className="max-w-2xl">
            <div className="heritage-chip">LƯU NIÊN · KHÔNG GIAN KHẢO CỨU</div>
            <h1
              data-testid="explore-title"
              className="mt-4 font-display text-3xl font-bold tracking-tight text-foreground md:text-4xl"
            >
              Khám phá Di sản Cố đô Huế
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground md:text-base">
              Hệ thống khảo cứu tri thức di sản Cố đô Huế: 14 cấu phần Quần thể Di
              tích Cố đô Huế (UNESCO 678), lăng tẩm hoàng gia, làng nghề thủ công và
              nghệ thuật diễn xướng truyền thống được bảo chứng bằng thư tịch chính sử.
            </p>
          </div>

          <div className="grid w-full max-w-lg grid-cols-3 gap-2 text-xs sm:text-sm">
            <div className="heritage-stat px-3 py-3">
              <div className="text-muted-foreground">Cấu phần UNESCO</div>
              <div className="mt-1 font-display text-lg font-semibold text-foreground">
                {totalUnescoCount || 14}
              </div>
            </div>
            <div className="heritage-stat px-3 py-3">
              <div className="text-muted-foreground">Thực thể khảo cứu</div>
              <div className="mt-1 font-display text-lg font-semibold text-foreground">
                {places.length}
              </div>
            </div>
            <div className="heritage-stat px-3 py-3">
              <div className="text-muted-foreground">Mô hình 3D đo đạc</div>
              <div className="mt-1 font-display text-lg font-semibold text-foreground">
                {total3dCount}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. Prominent Legacy Nine Dynastic Urns (Cửu Đỉnh) Collection Showcase */}
      <section
        data-testid="legacy-cuu-dinh-banner"
        className="mt-6 overflow-hidden rounded-2xl border border-amber-500/30 bg-gradient-to-r from-amber-950/20 via-background to-secondary/30 p-5 shadow-xs transition-all hover:border-amber-500/50 sm:p-6"
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-amber-600/30 bg-amber-500/10 text-amber-700 dark:text-amber-400">
              <Landmark className="h-6 w-6" aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-1 rounded-full border border-amber-600/30 bg-amber-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-amber-900 dark:text-amber-300">
                  <Award className="h-3 w-3" />
                  Bảo vật Quốc gia · UNESCO MOWCAP
                </span>
                <span className="text-xs text-muted-foreground font-mono">1835–1837</span>
              </div>
              <h2 className="mt-1.5 font-display text-xl font-bold tracking-tight text-foreground sm:text-2xl">
                Bộ sưu tập Cửu Đỉnh & 162 Bản đúc nổi
              </h2>
              <p className="mt-1 max-w-3xl text-xs sm:text-sm text-muted-foreground leading-relaxed">
                Chín chiếc đỉnh đồng uy nghiêm đặt trước sân Thế Miếu biểu trưng cho
                sự trường tồn của vương triều và non sông Đại Nam. Khám phá từng bản
                đúc nổi, mô hình xoay lật 3D và hành trình học tập tương tác.
              </p>
            </div>
          </div>

          <div className="flex shrink-0 flex-wrap items-center gap-3 pt-2 lg:pt-0">
            <Link
              href="/cuu-dinh"
              className="inline-flex min-h-[44px] items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-xs sm:text-sm font-semibold text-primary-foreground shadow-xs transition-all hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <span>Xem Bộ sưu tập Cửu Đỉnh</span>
              <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
            </Link>

            {/* Testid link ensuring backward compatibility with urns e2e navigation */}
            <Link
              href="/urns/cao-dinh"
              data-testid="urn-card"
              className="inline-flex min-h-[44px] items-center gap-1.5 rounded-xl border border-border/80 bg-background/80 px-3.5 py-2.5 text-xs sm:text-sm font-semibold text-foreground transition-all hover:bg-secondary/60 hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <span>Vào xem Cao Đỉnh 3D</span>
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>

      {/* 3. HeritageFilters: Categories, Diacritic-Tolerant Search, View Toggle, Facet Pills */}
      <section className="mt-8">
        <HeritageFilters
          values={filterValues}
          onChange={setFilterValues}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          totalCount={filteredPlaces.length}
          isLoading={loading}
          locale="vi"
          onReset={handleResetFilters}
        />
      </section>

      {/* 4. Error Feedback Display */}
      {error ? (
        <div className="mt-6 rounded-xl border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      {/* 5. Main Content Grid or Map View Transition */}
      {viewMode === "map" ? (
        /* Map View Bridge & Interactive Showcase */
        <section className="mt-6 overflow-hidden rounded-2xl border border-border/80 bg-card p-6 text-center sm:p-10">
          <div className="mx-auto flex max-w-lg flex-col items-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-primary/20 bg-primary/10 text-primary shadow-xs">
              <MapPin className="h-8 w-8" aria-hidden="true" />
            </div>

            <h3 className="mt-4 font-display text-2xl font-bold text-foreground">
              Bản đồ Di sản Cố đô Huế
            </h3>

            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
              Trải nghiệm định vị không gian địa lý của 14 cấu phần di sản thế giới
              dọc sông Hương, khu vực Kinh thành và các cụm lăng tẩm hoàng gia ở phía Nam.
            </p>

            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <Link
                href="/map"
                className="inline-flex min-h-[44px] items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow-xs transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              >
                <span>Mở Bản đồ Không gian Đầy đủ</span>
                <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
              </Link>

              <button
                type="button"
                onClick={() => setViewMode("grid")}
                className="inline-flex min-h-[44px] items-center gap-1.5 rounded-xl border border-border/80 bg-background px-4 py-2.5 text-sm font-semibold text-foreground transition-colors hover:bg-secondary/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              >
                <span>Quay lại dạng lưới</span>
              </button>
            </div>
          </div>
        </section>
      ) : loading && places.length === 0 ? (
        /* Loading Skeletons */
        <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              data-testid="heritage-card-skeleton"
              className="flex flex-col overflow-hidden rounded-2xl border border-border/70 bg-card p-4 shadow-xs"
            >
              <Skeleton className="aspect-[16/10] w-full rounded-xl" />
              <div className="mt-4 flex-1">
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="mt-2 h-4 w-1/2" />
                <Skeleton className="mt-4 h-12 w-full" />
              </div>
              <Skeleton className="mt-4 h-10 w-full rounded-xl" />
            </div>
          ))}
        </div>
      ) : filteredPlaces.length > 0 ? (
        /* HeritageCard Grid with Aspect Ratio & Fallback Management */
        <section aria-label="Danh sách di sản Huế" className="mt-6">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filteredPlaces.map((place, index) => (
              <HeritageCard
                key={place.id}
                place={place}
                priority={index < 3}
                locale="vi"
              />
            ))}
          </div>
        </section>
      ) : (
        /* Empty State */
        <div className="mt-6">
          <EmptyState
            icon={Search}
            title="Không tìm thấy di sản phù hợp"
            description={
              filterValues.q
                ? `Không có địa danh nào khớp với từ khóa "${filterValues.q}". Hãy thử tìm kiếm với các tên như "Ngọ Môn", "Lăng Tự Đức", "Phường Đúc", "Thiên Mụ" hoặc xóa bộ lọc.`
                : "Không có di sản nào thỏa mãn tất cả tiêu chí đang chọn. Vui lòng thử nới lỏng bộ lọc."
            }
            actionLabel="Xóa toàn bộ bộ lọc"
            onAction={handleResetFilters}
          />
        </div>
      )}
    </main>
  );
}

export default function ExplorePage() {
  return (
    <Suspense
      fallback={
        <main className="site-shell">
          <div className="heritage-hero p-6">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="mt-3 h-4 w-96" />
          </div>
          <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="overflow-hidden rounded-2xl border border-border/70 bg-card p-4"
              >
                <Skeleton className="aspect-[16/10] w-full rounded-xl" />
                <Skeleton className="mt-4 h-6 w-3/4" />
                <Skeleton className="mt-2 h-4 w-1/2" />
              </div>
            ))}
          </div>
        </main>
      }
    >
      <ExploreContent />
    </Suspense>
  );
}
