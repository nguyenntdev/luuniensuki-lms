"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  Check,
  Filter,
  GitCompare,
  Plus,
  Search,
  Trash2,
  X,
} from "lucide-react";

import {
  getHistoryEntityById,
  getHistoryEntityBySlug,
  listHistoryEntities,
} from "@/lib/api";
import { setPageMeta } from "@/lib/seo";
import {
  asEntityList,
  deburr,
  entityName,
  entityTypeLabel,
  KNOWN_URNS,
  RELIEF_IMAGE_MAP,
  reliefNumberFromSlug,
  reliefThumbnailUrl,
  urnNameFromSlug,
  urnSlugFromReliefSlug,
} from "@/lib/history";
import Skeleton from "@/components/Skeleton";
import VerificationNote from "@/components/history/VerificationNote";

function isUuid(value) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
    String(value || ""),
  );
}

function entityHref(e) {
  if (!e) return "#";
  if (e.entity_type === "urn") return `/cuu-dinh/${e.slug}`;
  if (e.entity_type === "relief") {
    const urn = e.slug?.split("-").slice(0, 2).join("-");
    return `/atlas/${urn}/${e.slug}`;
  }
  if (e.entity_type === "source") return `/sources/${e.slug}`;
  return `/explore/connections?entity=${e.id}`;
}

function buildFallbackEntities() {
  const urns = KNOWN_URNS.map((u) => ({
    id: u.slug,
    slug: u.slug,
    entity_type: "urn",
    name_vi: u.nameVi,
    thumbnail_url: reliefThumbnailUrl(u.slug),
    summary_vi: `Đỉnh đồng bảo vật hoàng cung triều Nguyễn đặt tại Thế Miếu, đúc năm 1835-1837.`,
  }));

  const reliefs = Object.keys(RELIEF_IMAGE_MAP)
    .filter((k) => k.includes("-"))
    .map((slug) => {
      const urnSlug = urnSlugFromReliefSlug(slug);
      const urnName = urnNameFromSlug(urnSlug);
      const num = reliefNumberFromSlug(slug);
      return {
        id: slug,
        slug,
        urn_slug: urnSlug,
        entity_type: "relief",
        name_vi: `${urnName} — #${num}`,
        thumbnail_url: reliefThumbnailUrl(slug),
        summary_vi: `Phù điêu bản đúc nổi trên ${urnName} thuộc Cửu Đỉnh triều Nguyễn.`,
      };
    });

  return [...urns, ...reliefs];
}

function CompareContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Available candidate entities for in-page search / picker
  const [candidates, setCandidates] = useState([]);
  const [loadingCandidates, setLoadingCandidates] = useState(true);

  // Picker search & filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all"); // 'all' | 'urn' | 'relief'
  const [displayCount, setDisplayCount] = useState(18);
  const [showPickerWhenFull, setShowPickerWhenFull] = useState(false);

  const ids = useMemo(() => {
    const raw = searchParams?.get("entities") || "";
    return raw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
      .slice(0, 4);
  }, [searchParams]);

  useEffect(() => {
    setPageMeta({
      title: "So sánh — Lưu Niên Sử Kí",
      description: "So sánh các đỉnh và phù điêu trên Cửu Đỉnh.",
      path: "/compare",
    });
  }, []);

  // Fetch all available entities for the picker
  useEffect(() => {
    let cancelled = false;
    async function loadCandidates() {
      setLoadingCandidates(true);
      try {
        const res = await listHistoryEntities({ limit: 200 });
        if (cancelled) return;
        const list = asEntityList(res);
        if (list.length > 0) {
          setCandidates(list);
        } else {
          setCandidates(buildFallbackEntities());
        }
      } catch {
        if (!cancelled) setCandidates(buildFallbackEntities());
      } finally {
        if (!cancelled) setLoadingCandidates(false);
      }
    }
    loadCandidates();
    return () => {
      cancelled = true;
    };
  }, []);

  // Load selected entities from URL query params
  useEffect(() => {
    let cancelled = false;
    async function loadSelected() {
      setLoading(true);
      setError(null);
      try {
        const results = await Promise.all(
          ids.map(async (idOrSlug) => {
            // Check candidates first for zero-latency lookup
            const foundInCandidates = candidates.find(
              (c) =>
                c.slug === idOrSlug ||
                String(c.id) === idOrSlug,
            );
            if (foundInCandidates) return foundInCandidates;

            try {
              if (isUuid(idOrSlug)) {
                return await getHistoryEntityById(idOrSlug);
              }
              return await getHistoryEntityBySlug(idOrSlug);
            } catch {
              try {
                return await getHistoryEntityById(idOrSlug);
              } catch {
                return null;
              }
            }
          }),
        );
        if (cancelled) return;
        setEntities(results.filter(Boolean));
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    if (ids.length > 0) {
      loadSelected();
    } else {
      setEntities([]);
      setLoading(false);
    }

    return () => {
      cancelled = true;
    };
  }, [ids, candidates]);

  function updateUrl(newEntities) {
    const newKeys = newEntities
      .map((e) => e.slug || String(e.id))
      .filter(Boolean)
      .slice(0, 4);
    if (newKeys.length > 0) {
      router.replace(`/compare?entities=${encodeURIComponent(newKeys.join(","))}`, {
        scroll: false,
      });
    } else {
      router.replace("/compare", { scroll: false });
    }
  }

  function handleSelect(entity) {
    const key = entity.slug || String(entity.id);
    const exists = entities.some(
      (e) => e.slug === key || String(e.id) === key,
    );

    if (exists) {
      const next = entities.filter(
        (e) => e.slug !== key && String(e.id) !== key,
      );
      setEntities(next);
      updateUrl(next);
    } else {
      if (entities.length >= 4) return;
      const next = [...entities, entity];
      setEntities(next);
      updateUrl(next);
    }
  }

  function handleRemove(key) {
    const next = entities.filter(
      (e) => e.slug !== key && String(e.id) !== key,
    );
    setEntities(next);
    updateUrl(next);
  }

  function handleClearAll() {
    setEntities([]);
    updateUrl([]);
  }

  // Filtered candidate entities for the in-page search / picker
  const filteredCandidates = useMemo(() => {
    return candidates.filter((item) => {
      if (typeFilter !== "all" && item.entity_type !== typeFilter) {
        return false;
      }

      if (searchQuery.trim()) {
        const q = deburr(searchQuery.trim().toLowerCase());
        const name = deburr(
          String(entityName(item) || item.name_vi || item.name || "").toLowerCase(),
        );
        const han = String(item.name_han_nom || item.han_nom || "").toLowerCase();
        const slug = String(item.slug || "").toLowerCase();
        const summary = deburr(
          String(item.summary_vi || item.summary || "").toLowerCase(),
        );

        if (
          !name.includes(q) &&
          !han.includes(q) &&
          !slug.includes(q) &&
          !summary.includes(q)
        ) {
          return false;
        }
      }

      return true;
    });
  }, [candidates, typeFilter, searchQuery]);

  const displayedCandidates = useMemo(() => {
    return filteredCandidates.slice(0, displayCount);
  }, [filteredCandidates, displayCount]);

  const selectedKeys = useMemo(() => {
    return new Set(entities.map((e) => e.slug || String(e.id)));
  }, [entities]);

  return (
    <main className="site-shell">
      {/* Hero Header */}
      <section className="heritage-hero p-6 md:p-9">
        <div className="relative max-w-4xl">
          <div className="heritage-chip">
            <GitCompare className="h-4 w-4" aria-hidden="true" />
            So sánh thực thể
          </div>
          <h1 className="mt-5 font-display text-3xl font-bold tracking-tight text-foreground md:text-5xl">
            So sánh các thực thể
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
            Đối chiếu từ 2 đến 4 đỉnh đồng hoặc phù điêu bản đúc nổi cạnh nhau
            dựa trên sử liệu được kiểm chứng. Chọn các thực thể trực tiếp từ công cụ
            tìm kiếm bên dưới để bắt đầu so sánh.
          </p>

          {/* Active selection tray */}
          {entities.length > 0 && (
            <div className="mt-6 flex flex-wrap items-center gap-2 rounded-xl border border-primary/20 bg-background/50 p-3 backdrop-blur-sm">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Đã chọn ({entities.length}/4):
              </span>
              {entities.map((e) => {
                const key = e.slug || String(e.id);
                return (
                  <span
                    key={key}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-primary/30 bg-primary/10 px-2.5 py-1 text-xs font-medium text-foreground"
                  >
                    {entityName(e)}
                    <button
                      type="button"
                      onClick={() => handleRemove(key)}
                      className="text-muted-foreground hover:text-foreground"
                      title="Gỡ bỏ"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                );
              })}
              <button
                type="button"
                onClick={handleClearAll}
                className="ml-auto inline-flex items-center gap-1 text-xs text-destructive hover:underline"
              >
                <Trash2 className="h-3.5 w-3.5" />
                Xóa tất cả
              </button>
            </div>
          )}
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
          Không tải được dữ liệu so sánh: {error}
        </div>
      ) : null}

      {/* Loading Skeleton */}
      {loading ? (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="heritage-card p-6">
              <Skeleton className="h-6 w-1/2" />
              <Skeleton className="mt-4 h-24 w-full" />
            </div>
          ))}
        </div>
      ) : entities.length >= 2 ? (
        /* Full Side-by-Side Comparison View (2-4 entities) */
        <section className="mt-6">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-display text-xl font-bold text-foreground">
              Bảng đối chiếu ({entities.length} thực thể)
            </h2>
            <div className="flex items-center gap-2">
              {entities.length < 4 && (
                <button
                  type="button"
                  onClick={() => setShowPickerWhenFull(!showPickerWhenFull)}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-primary/30 bg-primary/10 px-3 py-1.5 text-xs font-semibold text-primary hover:bg-primary/20"
                >
                  <Plus className="h-3.5 w-3.5" />
                  {showPickerWhenFull ? "Đóng bộ chọn" : "Thêm thực thể (+)"}
                </button>
              )}
            </div>
          </div>

          <div
            className={`grid gap-4 ${
              entities.length === 2
                ? "md:grid-cols-2"
                : entities.length === 3
                  ? "md:grid-cols-3"
                  : "sm:grid-cols-2 lg:grid-cols-4"
            }`}
          >
            {entities.map((e) => {
              const key = e.slug || String(e.id);
              const thumb = e.thumbnail_url || reliefThumbnailUrl(e.slug);
              const hanNom = e.name_han_nom || e.han_nom;
              const urnSlug = e.urn_slug || urnSlugFromReliefSlug(e.slug);
              const urnName = urnNameFromSlug(urnSlug);

              return (
                <div
                  key={key}
                  className="heritage-card flex flex-col justify-between p-5"
                >
                  <div>
                    {/* Card Header */}
                    <div className="flex items-start justify-between gap-2">
                      <span className="rounded-full border border-border bg-secondary/50 px-2.5 py-0.5 text-[11px] uppercase tracking-wide text-muted-foreground">
                        {entityTypeLabel(e.entity_type)}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleRemove(key)}
                        className="rounded p-1 text-muted-foreground transition hover:bg-muted hover:text-foreground"
                        title="Gỡ bỏ khỏi so sánh"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>

                    {/* Image Preview */}
                    <div className="relative mt-3 aspect-[16/10] w-full overflow-hidden rounded-lg bg-black">
                      <img
                        src={thumb}
                        alt={entityName(e)}
                        loading="lazy"
                        decoding="async"
                        className="h-full w-full object-cover"
                      />
                      {hanNom && (
                        <span className="absolute bottom-2 right-2 rounded bg-black/80 px-2 py-0.5 font-serif text-xs font-bold text-amber-300 backdrop-blur-sm">
                          {hanNom}
                        </span>
                      )}
                    </div>

                    {/* Title */}
                    <h3 className="mt-3 font-display text-lg font-bold text-foreground">
                      {entityName(e)}
                    </h3>
                    {e.name_en && (
                      <div className="text-xs italic text-muted-foreground">
                        {e.name_en}
                      </div>
                    )}

                    {/* Affiliated Urn if relief */}
                    {e.entity_type === "relief" && urnName && (
                      <div className="mt-2 text-xs text-primary">
                        Thuộc đỉnh: <span className="font-semibold">{urnName}</span>
                      </div>
                    )}

                    {/* Summary */}
                    {e.summary_vi ? (
                      <p className="mt-3 text-sm leading-6 text-muted-foreground">
                        {e.summary_vi}
                      </p>
                    ) : (
                      <p className="mt-3 text-sm italic text-muted-foreground/70">
                        Chưa có tóm tắt đã kiểm chứng.
                      </p>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="mt-5 border-t border-border/50 pt-3">
                    <Link
                      href={entityHref(e)}
                      className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
                    >
                      Xem chi tiết hồ sơ
                      <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      ) : entities.length === 1 ? (
        /* 1 entity selected - show it and invite to pick a 2nd entity */
        <section className="mt-6">
          <div className="rounded-xl border border-primary/25 bg-primary/5 p-4 text-sm text-foreground">
            Bạn đã chọn <strong>1 thực thể ({entityName(entities[0])})</strong>. Hãy chọn thêm ít nhất 1 thực thể nữa từ danh sách bên dưới để bắt đầu đối chiếu so sánh.
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            {/* Selected Slot 1 */}
            {entities.map((e) => {
              const key = e.slug || String(e.id);
              const thumb = e.thumbnail_url || reliefThumbnailUrl(e.slug);
              const hanNom = e.name_han_nom || e.han_nom;

              return (
                <div key={key} className="heritage-card p-5">
                  <div className="flex items-start justify-between gap-2">
                    <span className="rounded-full border border-primary/30 bg-primary/10 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-primary">
                      Thực thể 1: {entityTypeLabel(e.entity_type)}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemove(key)}
                      className="rounded p-1 text-muted-foreground transition hover:bg-muted hover:text-foreground"
                      title="Gỡ bỏ"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>

                  <div className="relative mt-3 aspect-[16/10] w-full overflow-hidden rounded-lg bg-black">
                    <img
                      src={thumb}
                      alt={entityName(e)}
                      loading="lazy"
                      decoding="async"
                      className="h-full w-full object-cover"
                    />
                    {hanNom && (
                      <span className="absolute bottom-2 right-2 rounded bg-black/80 px-2 py-0.5 font-serif text-xs font-bold text-amber-300 backdrop-blur-sm">
                        {hanNom}
                      </span>
                    )}
                  </div>

                  <h3 className="mt-3 font-display text-lg font-bold text-foreground">
                    {entityName(e)}
                  </h3>
                  {e.summary_vi ? (
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">
                      {e.summary_vi}
                    </p>
                  ) : null}
                </div>
              );
            })}

            {/* Empty Slot 2 */}
            <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-primary/30 bg-card/40 p-8 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Plus className="h-6 w-6" />
              </div>
              <h3 className="mt-3 font-display text-base font-semibold text-foreground">
                Chọn thực thể thứ hai
              </h3>
              <p className="mt-1 text-xs text-muted-foreground">
                Chọn bất kỳ đỉnh đồng hoặc phù điêu nào từ danh sách tìm kiếm bên dưới để so sánh cạnh nhau.
              </p>
            </div>
          </div>
        </section>
      ) : (
        /* 0 entities selected */
        <div className="mt-6 rounded-xl border border-dashed border-border/80 bg-card/45 p-6 text-center text-sm text-muted-foreground">
          Chưa có thực thể nào được chọn để so sánh. Hãy tìm kiếm và chọn ít nhất 2 thực thể từ danh sách bên dưới để bắt đầu.
        </div>
      )}

      {/* In-Page Entity Search & Picker (Always shown when fewer than 2 entities, or toggled when 2-3) */}
      {(entities.length < 2 || showPickerWhenFull) && (
        <section className="mt-10 rounded-2xl border border-border bg-card/60 p-6 md:p-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="font-display text-xl font-bold tracking-tight text-foreground md:text-2xl">
                Chọn thực thể để so sánh
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Tìm kiếm trong 9 đỉnh đồng và 153 phù điêu họa tiết Cửu Đỉnh. Bấm vào thực thể để thêm hoặc gỡ bỏ.
              </p>
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center gap-1 rounded-lg border border-border bg-secondary/40 p-1 text-xs">
              <button
                type="button"
                onClick={() => {
                  setTypeFilter("all");
                  setDisplayCount(18);
                }}
                className={`rounded-md px-3 py-1.5 font-medium transition ${
                  typeFilter === "all"
                    ? "bg-primary text-primary-foreground shadow"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Tất cả ({candidates.length})
              </button>
              <button
                type="button"
                onClick={() => {
                  setTypeFilter("urn");
                  setDisplayCount(18);
                }}
                className={`rounded-md px-3 py-1.5 font-medium transition ${
                  typeFilter === "urn"
                    ? "bg-primary text-primary-foreground shadow"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Đỉnh đồng (9)
              </button>
              <button
                type="button"
                onClick={() => {
                  setTypeFilter("relief");
                  setDisplayCount(18);
                }}
                className={`rounded-md px-3 py-1.5 font-medium transition ${
                  typeFilter === "relief"
                    ? "bg-primary text-primary-foreground shadow"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Phù điêu (153)
              </button>
            </div>
          </div>

          {/* Search Bar */}
          <div className="relative mt-5">
            <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Tìm theo tên, chữ Hán, số hiệu (vd: Cao Đỉnh, Long, Ba La Mật, #02)..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setDisplayCount(18);
              }}
              className="w-full rounded-xl border border-input bg-background/80 py-2.5 pl-10 pr-10 text-sm text-foreground shadow-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Results count */}
          <div className="mt-3 text-xs text-muted-foreground">
            Hiển thị {displayedCandidates.length} / {filteredCandidates.length} thực thể phù hợp
          </div>

          {/* Entity Grid */}
          {loadingCandidates ? (
            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="heritage-card aspect-[4/5] p-3">
                  <Skeleton className="h-[75%] w-full rounded-lg" />
                  <Skeleton className="mt-2 h-4 w-2/3" />
                </div>
              ))}
            </div>
          ) : filteredCandidates.length === 0 ? (
            <div className="mt-6 rounded-xl border border-dashed border-border py-10 text-center text-sm text-muted-foreground">
              Không tìm thấy thực thể nào phù hợp với từ khóa &ldquo;{searchQuery}&rdquo;.
            </div>
          ) : (
            <>
              <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
                {displayedCandidates.map((item) => {
                  const key = item.slug || String(item.id);
                  const isSelected = selectedKeys.has(key);
                  const thumb =
                    item.thumbnail_url || reliefThumbnailUrl(item.slug);
                  const hanNom = item.name_han_nom || item.han_nom;
                  const name = entityName(item) || item.name_vi || item.slug;
                  const isUrn = item.entity_type === "urn";

                  return (
                    <button
                      type="button"
                      key={key}
                      onClick={() => handleSelect(item)}
                      className={`group relative flex aspect-[4/5] flex-col overflow-hidden rounded-xl border text-left transition duration-200 ${
                        isSelected
                          ? "border-primary bg-primary/10 shadow-md ring-2 ring-primary"
                          : "border-border/70 bg-card/75 hover:border-primary/50 hover:-translate-y-0.5"
                      }`}
                    >
                      <div className="relative flex-1 overflow-hidden bg-black">
                        <img
                          src={thumb}
                          alt={name}
                          loading="lazy"
                          decoding="async"
                          className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
                        />
                        {/* Selection checkmark or plus */}
                        <div className="absolute right-2 top-2">
                          {isSelected ? (
                            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground shadow">
                              <Check className="h-3 w-3" />
                            </span>
                          ) : (
                            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-black/60 text-white backdrop-blur-sm transition group-hover:bg-primary group-hover:text-primary-foreground">
                              <Plus className="h-3 w-3" />
                            </span>
                          )}
                        </div>

                        {/* Type badge */}
                        <span className="absolute left-2 top-2 rounded bg-black/70 px-1.5 py-0.5 text-[9px] font-semibold uppercase text-white backdrop-blur-sm">
                          {isUrn ? "Đỉnh" : "Phù điêu"}
                        </span>

                        {hanNom && (
                          <span className="absolute bottom-1.5 right-1.5 rounded bg-black/80 px-1.5 py-0.5 font-serif text-[10px] font-bold text-amber-300 backdrop-blur-sm">
                            {hanNom}
                          </span>
                        )}
                      </div>

                      <div className="p-2.5">
                        <div
                          className="truncate text-xs font-semibold text-foreground"
                          title={name}
                        >
                          {name}
                        </div>
                        <div className="mt-1 flex items-center justify-between text-[10px] text-muted-foreground">
                          <span>
                            {isSelected ? "Đã chọn" : "Bấm để chọn"}
                          </span>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Load More Button */}
              {displayedCandidates.length < filteredCandidates.length && (
                <div className="mt-6 text-center">
                  <button
                    type="button"
                    onClick={() => setDisplayCount((prev) => prev + 18)}
                    className="rounded-lg border border-border bg-secondary/50 px-4 py-2 text-xs font-medium text-foreground hover:bg-secondary"
                  >
                    Xem thêm ({filteredCandidates.length - displayedCandidates.length} thực thể)
                  </button>
                </div>
              )}
            </>
          )}
        </section>
      )}
    </main>
  );
}

export default function ComparePage() {
  return (
    <Suspense
      fallback={
        <main className="site-shell p-6">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="mt-4 h-32 w-full" />
        </main>
      }
    >
      <CompareContent />
    </Suspense>
  );
}
