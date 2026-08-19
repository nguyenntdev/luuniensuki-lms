"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  ChevronDown,
  Fish,
  Flower2,
  Layers,
  Mountain,
  RotateCcw,
  Sailboat,
  Search,
  Ship,
  SlidersHorizontal,
  TreePine,
  Waves,
} from "lucide-react";

import { listHistoryEntities } from "@/lib/api";
import {
  asEntityList,
  deburr,
  entityName,
  reliefNumberFromSlug,
  urnNameFromSlug,
  urnSlugFromReliefSlug,
  publicationStatusLabel,
  KNOWN_URNS,
} from "@/lib/history";
import { cn } from "@/lib/utils";
import Skeleton from "@/components/Skeleton";
import EntityCard from "@/components/history/EntityCard";
import VerificationNote from "@/components/history/VerificationNote";
import { Input } from "@/components/ui/input";

const SORT_OPTIONS = [
  { value: "name", label: "Theo tên" },
  { value: "number", label: "Theo số phù điêu" },
  { value: "urn", label: "Theo đỉnh" },
];

const SORT_VALUES = SORT_OPTIONS.map((o) => o.value);

const THEMES = [
  { id: "mountains", label: "Núi non", query: "sơn", icon: Mountain },
  { id: "rivers", label: "Sông ngòi", query: "giang", icon: Waves },
  { id: "seas", label: "Cửa biển", query: "hải", icon: Sailboat },
  { id: "trees", label: "Cây gỗ", query: "mộc", icon: TreePine },
  { id: "flowers", label: "Hoa cỏ", query: "hoa", icon: Flower2 },
  { id: "waterlife", label: "Thủy tộc", query: "ngư", icon: Fish },
  { id: "ships", label: "Thuyền bè", query: "thuyền", icon: Ship },
];

function readParams() {
  if (typeof window === "undefined") {
    return { q: "", urn: "", status: "", sort: "urn" };
  }
  const p = new URLSearchParams(window.location.search);
  const sort = p.get("sort") || "urn";
  return {
    q: p.get("q") || "",
    urn: p.get("urn") || "",
    status: p.get("status") || "",
    sort: SORT_VALUES.includes(sort) ? sort : "urn",
  };
}

function searchableText(r) {
  return deburr(
    `${entityName(r)} ${r.name_en || ""} ${r.slug || ""} ${
      r.summary_vi || r.summary || ""
    }`,
  );
}

function matchesQuery(r, rawQuery) {
  const tokens = deburr(rawQuery).split(/\s+/).filter(Boolean);
  if (tokens.length === 0) return true;
  const text = searchableText(r);
  return tokens.every((token) => text.includes(token));
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
    case "urn":
    default:
      return arr.sort((a, b) => {
        const urnA = a.urn_slug || urnSlugFromReliefSlug(a.slug);
        const urnB = b.urn_slug || urnSlugFromReliefSlug(b.slug);
        if (urnA !== urnB) return String(urnA).localeCompare(String(urnB));
        return (
          parseInt(reliefNumberFromSlug(a.slug), 10) -
          parseInt(reliefNumberFromSlug(b.slug), 10)
        );
      });
  }
}

export default function AtlasClient() {
  const router = useRouter();
  const [reliefs, setReliefs] = useState([]);
  const [total, setTotal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [displayLimit, setDisplayLimit] = useState(36);
  const [params, setParams] = useState({
    q: "",
    urn: "",
    status: "",
    sort: "urn",
  });
  const [qInput, setQInput] = useState("");
  const debounceRef = useRef(null);

  useEffect(() => {
    setParams(readParams());
  }, []);

  useEffect(() => {
    setQInput(params.q);
  }, [params.q]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await listHistoryEntities({
          limit: 200,
        });
        if (cancelled) return;
        const items = asEntityList(res);
        setReliefs(items);
        setTotal(items.length);
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

  useEffect(
    () => () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    },
    [],
  );

  const commitParams = (next) => {
    setParams(next);
    setDisplayLimit(36);
    const p = new URLSearchParams();
    if (next.q) p.set("q", next.q);
    if (next.urn) p.set("urn", next.urn);
    if (next.status) p.set("status", next.status);
    if (next.sort && next.sort !== "urn") p.set("sort", next.sort);
    const qs = p.toString();
    router.replace(`/atlas${qs ? `?${qs}` : ""}`, { scroll: false });
  };

  const onSearchChange = (value) => {
    setQInput(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      commitParams({ ...params, q: value });
    }, 250);
  };

  const toggleTheme = (theme) => {
    const active = deburr(params.q) === deburr(theme.query);
    const nextQ = active ? "" : theme.query;
    setQInput(nextQ);
    commitParams({ ...params, q: nextQ });
  };

  const clearFilters = () => {
    setQInput("");
    commitParams({ q: "", urn: "", status: "", sort: "urn" });
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

  const themeCounts = useMemo(() => {
    const counts = {};
    for (const theme of THEMES) {
      counts[theme.id] = reliefs.filter((r) =>
        matchesQuery(r, theme.query),
      ).length;
    }
    return counts;
  }, [reliefs]);

  const filtered = useMemo(() => {
    let list = reliefs;
    if (params.urn) {
      list = list.filter(
        (r) => (r.urn_slug || urnSlugFromReliefSlug(r.slug)) === params.urn,
      );
    }
    if (params.status) {
      list = list.filter((r) => r.publication_status === params.status);
    }
    if (params.q) {
      list = list.filter((r) => matchesQuery(r, params.q));
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
            Bộ sưu tập 162 bản đúc nổi
          </div>
          <h1 className="mt-5 font-display text-3xl font-bold tracking-tight text-foreground md:text-5xl">
            Atlas — {total ?? 162} bản đúc nổi
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
            Toàn bộ 162 bản đúc nổi trên chín chiếc đỉnh đồng (gồm 9 đồ án chữ thụy hiệu mang tên đỉnh và 153 phù điêu họa tiết cảnh vật). Tìm kiếm theo tên, lọc theo đỉnh hoặc mở từng bản đúc để xem hồ sơ và nguồn sử liệu.
          </p>

          <div className="relative mt-6 max-w-2xl">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              type="search"
              value={qInput}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Tìm theo tên, slug, mô tả… (không phân biệt dấu)"
              aria-label="Tìm phù điêu trong Atlas"
              className="pl-9"
            />
          </div>

          <div className="mt-5">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Khám phá theo chủ đề
            </p>
            <div
              className="mt-3 flex flex-wrap gap-2"
              role="group"
              aria-label="Khám phá theo chủ đề"
            >
              {THEMES.map((theme) => {
                const Icon = theme.icon;
                const active = deburr(params.q) === deburr(theme.query);
                return (
                  <button
                    key={theme.id}
                    type="button"
                    onClick={() => toggleTheme(theme)}
                    aria-pressed={active}
                    className={cn(
                      "inline-flex items-center gap-2 rounded-full border px-3.5 py-2 text-sm font-medium transition focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                      active
                        ? "border-primary/50 bg-primary/15 text-primary"
                        : "border-border bg-background/45 text-muted-foreground hover:border-primary/40 hover:text-foreground",
                    )}
                  >
                    <Icon className="h-4 w-4" aria-hidden="true" />
                    {theme.label}
                    <span
                      className="font-display tabular-nums text-xs text-muted-foreground"
                      aria-label={`${themeCounts[theme.id]} phù điêu`}
                    >
                      {themeCounts[theme.id]}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
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
          <label className="flex flex-1 items-center gap-2 text-sm text-muted-foreground">
            <span className="sr-only">Lọc theo đỉnh</span>
            <select
              value={params.urn}
              onChange={(e) => commitParams({ ...params, urn: e.target.value })}
              className="h-11 w-full min-w-[180px] rounded-xl border border-border bg-background/45 px-3 text-sm text-foreground outline-none transition focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/25"
            >
              <option value="">Tất cả đỉnh</option>
              {urnOptions.map((u) => (
                <option key={u.slug} value={u.slug}>
                  {u.nameVi}
                </option>
              ))}
            </select>
          </label>

          <details className="group/advanced min-w-[220px] flex-1 rounded-xl border border-border bg-background/30">
            <summary className="flex cursor-pointer list-none items-center gap-2 rounded-xl px-3 py-3 text-sm font-semibold text-muted-foreground transition hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring [&::-webkit-details-marker]:hidden">
              <SlidersHorizontal className="h-4 w-4" aria-hidden="true" />
              Bộ lọc nâng cao
              <ChevronDown
                className="ml-auto h-4 w-4 transition-transform group-open/advanced:rotate-180"
                aria-hidden="true"
              />
            </summary>
            <div className="mt-2 grid gap-3 sm:grid-cols-2">
              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <span className="sr-only">Lọc theo trạng thái xuất bản</span>
                <select
                  value={params.status}
                  onChange={(e) =>
                    commitParams({ ...params, status: e.target.value })
                  }
                  className="h-11 w-full rounded-xl border border-border bg-background/45 px-3 text-sm text-foreground outline-none transition focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/25"
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
                  onChange={(e) =>
                    commitParams({ ...params, sort: e.target.value })
                  }
                  className="h-11 w-full rounded-xl border border-border bg-background/45 px-3 text-sm text-foreground outline-none transition focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/25"
                >
                  {SORT_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </details>

          {hasFilters ? (
            <button
              type="button"
              onClick={clearFilters}
              className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2.5 text-sm font-semibold text-muted-foreground transition hover:bg-secondary hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
            >
              <RotateCcw className="h-4 w-4" aria-hidden="true" />
              Xóa bộ lọc
            </button>
          ) : null}
        </div>
        <p className="mt-3 text-xs text-muted-foreground" aria-live="polite">
          {loading
            ? "Đang tải dữ liệu…"
            : `Hiển thị ${filtered.length} bản đúc nổi${
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
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filtered.slice(0, displayLimit).map((relief) => {
              const urnSlug =
                relief.urn_slug || urnSlugFromReliefSlug(relief.slug);
              const isUrn = relief.entity_type === "urn";
              const href = isUrn ? `/cuu-dinh/${urnSlug}` : `/atlas/${urnSlug}/${relief.slug}`;
              return (
                <EntityCard
                  key={relief.slug || relief.id}
                  entity={relief}
                  href={href}
                  badge={urnNameFromSlug(urnSlug)}
                />
              );
            })}
          </div>

          {filtered.length > displayLimit ? (
            <div className="mt-10 flex flex-col items-center justify-center gap-3">
              <button
                type="button"
                onClick={() => setDisplayLimit((prev) => prev + 36)}
                className="inline-flex items-center gap-2 rounded-xl border border-primary/40 bg-card/80 px-6 py-3 text-sm font-bold text-primary shadow-sm transition hover:bg-primary hover:text-primary-foreground focus-visible:ring-2 focus-visible:ring-primary"
              >
                <Layers className="h-4 w-4" aria-hidden="true" />
                Xem thêm {Math.min(36, filtered.length - displayLimit)} bản đúc ({Math.min(displayLimit, filtered.length)}/{filtered.length})
              </button>
              <button
                type="button"
                onClick={() => setDisplayLimit(filtered.length)}
                className="text-xs text-muted-foreground hover:text-foreground hover:underline"
              >
                Hiển thị tất cả ({filtered.length})
              </button>
            </div>
          ) : null}
        </>
      ) : (
        <div className="mt-6">
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-14 text-center">
            <Layers
              className="mb-3 h-8 w-8 text-muted-foreground"
              aria-hidden="true"
            />
            <h2 className="font-display text-base font-semibold text-foreground">
              Không tìm thấy bản đúc nổi nào
            </h2>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">
              {hasFilters
                ? "Thử điều chỉnh từ khóa hoặc bộ lọc."
                : "Chưa có dữ liệu bản đúc nào được nạp từ máy chủ lịch sử."}
            </p>
            {hasFilters ? (
              <button
                type="button"
                onClick={clearFilters}
                className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground focus-visible:ring-2 focus-visible:ring-ring"
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
