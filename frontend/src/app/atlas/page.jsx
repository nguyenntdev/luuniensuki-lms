"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Layers, Search, SlidersHorizontal } from "lucide-react";

import { listHistoryEntities } from "@/lib/api";
import {
  asEntityList,
  deburr,
  entityName,
  listTotal,
  reliefNumberFromSlug,
  urnNameFromSlug,
  urnSlugFromReliefSlug,
  publicationStatusLabel,
  KNOWN_URNS,
} from "@/lib/history";
import Skeleton from "@/components/Skeleton";
import EntityCard from "@/components/history/EntityCard";
import SectionHeading from "@/components/history/SectionHeading";
import VerificationNote from "@/components/history/VerificationNote";
import { Input } from "@/components/ui/input";

const SORT_OPTIONS = [
  { value: "slug", label: "Theo slug" },
  { value: "number", label: "Theo số phù điêu" },
  { value: "name", label: "Tên A–Z" },
  { value: "name_desc", label: "Tên Z–A" },
];

function readParams() {
  if (typeof window === "undefined") {
    return { q: "", urn: "", status: "", sort: "slug" };
  }
  const p = new URLSearchParams(window.location.search);
  return {
    q: p.get("q") || "",
    urn: p.get("urn") || "",
    status: p.get("status") || "",
    sort: p.get("sort") || "slug",
  };
}

function sortReliefs(list, sort) {
  const arr = [...list];
  switch (sort) {
    case "number":
      return arr.sort(
        (a, b) =>
          parseInt(reliefNumberFromSlug(a.slug), 10) -
          parseInt(reliefNumberFromSlug(b.slug), 10),
      );
    case "name":
      return arr.sort((a, b) =>
        entityName(a).localeCompare(entityName(b), "vi"),
      );
    case "name_desc":
      return arr.sort((a, b) =>
        entityName(b).localeCompare(entityName(a), "vi"),
      );
    default:
      return arr.sort((a, b) =>
        String(a.slug || "").localeCompare(String(b.slug || "")),
      );
  }
}

export default function AtlasPage() {
  const router = useRouter();
  const [reliefs, setReliefs] = useState([]);
  const [total, setTotal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [params, setParams] = useState({
    q: "",
    urn: "",
    status: "",
    sort: "slug",
  });

  useEffect(() => {
    setParams(readParams());
  }, []);

  useEffect(() => {
    document.title = "Atlas — 162 hình đúc · Lưu Niên Sử Kí";
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await listHistoryEntities({
          entityType: "relief",
          limit: 200,
        });
        if (cancelled) return;
        setReliefs(asEntityList(res));
        setTotal(listTotal(res) ?? asEntityList(res).length);
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

  const updateParam = (key, value) => {
    const next = { ...params, [key]: value };
    setParams(next);
    const p = new URLSearchParams();
    if (next.q) p.set("q", next.q);
    if (next.urn) p.set("urn", next.urn);
    if (next.status) p.set("status", next.status);
    if (next.sort && next.sort !== "slug") p.set("sort", next.sort);
    const qs = p.toString();
    router.replace(`/atlas${qs ? `?${qs}` : ""}`, { scroll: false });
  };

  const clearFilters = () => {
    const next = { q: "", urn: "", status: "", sort: "slug" };
    setParams(next);
    router.replace("/atlas", { scroll: false });
  };

  const urnOptions = useMemo(() => {
    const present = new Set(
      reliefs
        .map((r) => r.urn_slug || urnSlugFromReliefSlug(r.slug))
        .filter(Boolean),
    );
    const known = KNOWN_URNS.filter((u) => present.has(u.slug));
    const extra = [...present]
      .filter((slug) => !KNOWN_URNS.some((u) => u.slug === slug))
      .map((slug) => ({ slug, nameVi: urnNameFromSlug(slug) }));
    return known.length > 0 || extra.length > 0
      ? [...known, ...extra]
      : KNOWN_URNS;
  }, [reliefs]);

  const statusOptions = useMemo(() => {
    const set = new Set(
      reliefs.map((r) => r.publication_status).filter(Boolean),
    );
    return [...set].sort();
  }, [reliefs]);

  const filtered = useMemo(() => {
    const q = deburr(params.q.trim());
    let list = reliefs;
    if (params.urn) {
      list = list.filter(
        (r) => (r.urn_slug || urnSlugFromReliefSlug(r.slug)) === params.urn,
      );
    }
    if (params.status) {
      list = list.filter((r) => r.publication_status === params.status);
    }
    if (q) {
      list = list.filter((r) =>
        deburr(
          `${entityName(r)} ${r.name_en || ""} ${r.slug || ""} ${
            r.summary_vi || r.summary || ""
          }`,
        ).includes(q),
      );
    }
    return sortReliefs(list, params.sort);
  }, [reliefs, params]);

  const hasFilters = Boolean(params.q || params.urn || params.status);

  return (
    <main className="site-shell">
      <section className="heritage-hero p-6 md:p-9">
        <div className="relative max-w-4xl">
          <div className="heritage-chip">
            <Layers className="h-4 w-4" aria-hidden="true" />
            Bộ sưu tập phù điêu
          </div>
          <h1 className="mt-5 font-display text-3xl font-bold tracking-tight text-foreground md:text-5xl">
            Atlas — {total ?? "..."} hình đúc
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
            Toàn bộ hình tượng khắc nổi trên chín chiếc đỉnh đồng. Tìm kiếm theo
            tên, lọc theo đỉnh hoặc trạng thái xuất bản, và mở từng phù điêu để
            xem mô tả cùng nguồn sử liệu.
          </p>
        </div>
      </section>

      <div className="mt-5">
        <VerificationNote />
      </div>

      {error ? (
        <div
          role="alert"
          className="mt-5 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive"
        >
          Không tải được dữ liệu Atlas: {error}
        </div>
      ) : null}

      {/* Filters */}
      <section
        className="mt-6 rounded-lg border border-border bg-card/60 p-4"
        aria-label="Bộ lọc Atlas"
      >
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative min-w-[220px] flex-1">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              type="search"
              value={params.q}
              onChange={(e) => updateParam("q", e.target.value)}
              placeholder="Tìm theo tên, slug, mô tả… (không phân biệt dấu)"
              aria-label="Tìm phù điêu"
              className="pl-9"
            />
          </div>

          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="sr-only">Lọc theo đỉnh</span>
            <select
              value={params.urn}
              onChange={(e) => updateParam("urn", e.target.value)}
              className="h-11 rounded-xl border border-border bg-background/45 px-3 text-sm text-foreground outline-none transition focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/25"
            >
              <option value="">Tất cả đỉnh</option>
              {urnOptions.map((u) => (
                <option key={u.slug} value={u.slug}>
                  {u.nameVi}
                </option>
              ))}
            </select>
          </label>

          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="sr-only">Lọc theo trạng thái</span>
            <select
              value={params.status}
              onChange={(e) => updateParam("status", e.target.value)}
              className="h-11 rounded-xl border border-border bg-background/45 px-3 text-sm text-foreground outline-none transition focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/25"
            >
              <option value="">Mọi trạng thái</option>
              {statusOptions.map((s) => (
                <option key={s} value={s}>
                  {publicationStatusLabel(s)}
                </option>
              ))}
            </select>
          </label>

          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="sr-only">Sắp xếp</span>
            <select
              value={params.sort}
              onChange={(e) => updateParam("sort", e.target.value)}
              className="h-11 rounded-xl border border-border bg-background/45 px-3 text-sm text-foreground outline-none transition focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/25"
            >
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          {hasFilters ? (
            <button
              type="button"
              onClick={clearFilters}
              className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-semibold text-muted-foreground transition hover:bg-secondary hover:text-foreground"
            >
              <SlidersHorizontal className="h-4 w-4" aria-hidden="true" />
              Xóa bộ lọc
            </button>
          ) : null}
        </div>
        <p className="mt-3 text-xs text-muted-foreground" aria-live="polite">
          {loading
            ? "Đang tải dữ liệu…"
            : `Hiển thị ${filtered.length} phù điêu${
                hasFilters ? " sau khi lọc" : ""
              }.`}
        </p>
      </section>

      {/* Grid */}
      {loading ? (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {[...Array(12)].map((_, i) => (
            <div key={i} className="heritage-card p-5">
              <Skeleton className="h-5 w-2/3" />
              <Skeleton className="mt-3 h-4 w-full" />
              <Skeleton className="mt-2 h-4 w-1/2" />
            </div>
          ))}
        </div>
      ) : filtered.length > 0 ? (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((relief) => {
            const urnSlug = relief.urn_slug || urnSlugFromReliefSlug(relief.slug);
            return (
              <EntityCard
                key={relief.slug || relief.id}
                entity={relief}
                href={`/atlas/${urnSlug}/${relief.slug}`}
                badge={urnNameFromSlug(urnSlug)}
              />
            );
          })}
        </div>
      ) : (
        <div className="mt-6">
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-14 text-center">
            <Layers className="mb-3 h-8 w-8 text-muted-foreground" aria-hidden="true" />
            <h3 className="font-display text-base font-semibold text-foreground">
              Không tìm thấy phù điêu nào
            </h3>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">
              {hasFilters
                ? "Thử điều chỉnh từ khóa hoặc bộ lọc."
                : "Chưa có dữ liệu phù điêu nào được nạp từ máy chủ lịch sử."}
            </p>
            {hasFilters ? (
              <button
                type="button"
                onClick={clearFilters}
                className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
              >
                Xóa bộ lọc
              </button>
            ) : (
              <Link
                href="/cuu-dinh"
                className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
              >
                Về trang Cửu Đỉnh
              </Link>
            )}
          </div>
        </div>
      )}
    </main>
  );
}