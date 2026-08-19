"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  BadgeCheck,
  BookOpen,
  Boxes,
  Compass,
  Crown,
  GraduationCap,
  Landmark,
  Library,
  Link2,
  Map as MapIcon,
  Network,
  ScrollText,
} from "lucide-react";

import {
  getHistoryEntityBySlug,
  getHistoryEntityGeography,
  getReliefHotspot,
  listHistoryEntities,
  listHistoryClaimSources,
  listHistoryEntityClaims,
  listHistoryEntityRelations,
} from "@/lib/api";
import {
  asClaimList,
  asEntityList,
  asGeographies,
  asRelations,
  asSourceList,
  claimEpistemic,
  claimText,
  claimTypeLabel,
  entityName,
  publicationEpistemic,
  publicationStatusLabel,
  relationPredicateLabel,
  reliefNumberFromSlug,
  reliefThumbnailUrl,
  urnNameFromSlug,
  urnSlugFromReliefSlug,
} from "@/lib/history";
import { setPageMeta } from "@/lib/seo";
import { useAuthStore } from "@/stores/authStore";
import Skeleton from "@/components/Skeleton";
import EntityCard from "@/components/history/EntityCard";
import ClaimItem from "@/components/history/ClaimItem";
import EpistemicLabel from "@/components/history/EpistemicLabel";
import SectionHeading from "@/components/history/SectionHeading";
import VerificationNote from "@/components/history/VerificationNote";

const FACT_TYPES = new Set([
  "factual",
  "chronology",
  "geographic",
  "material",
  "measurement",
  "production",
]);

const CHRONOLOGY_TYPES = new Set(["chronology"]);

const INTERPRETATION_TYPES = new Set([
  "symbolism",
  "interpretation",
  "modern_interpretation",
  "traditional_account",
]);

const SECTION_TABS = [
  { id: "overview", label: "Tổng quan", icon: BookOpen },
  { id: "reliefs", label: "Phù điêu", icon: Landmark },
  { id: "threed", label: "3D", icon: Boxes },
  { id: "context", label: "Bối cảnh", icon: ScrollText },
  { id: "evidence", label: "Chứng cứ", icon: BadgeCheck },
  { id: "sources", label: "Nguồn", icon: Library },
  { id: "learning", label: "Học tập", icon: GraduationCap },
];

const ROMAN_NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"];

function relationObjectName(rel) {
  return (
    rel.object_name ||
    rel.object?.name_vi ||
    rel.object?.name_en ||
    rel.object?.slug ||
    (rel.object_entity_id != null ? `#${rel.object_entity_id}` : "")
  );
}

function relationHref(rel) {
  const obj = rel.object;
  if (obj?.slug) {
    if (obj.entity_type === "urn") return `/cuu-dinh/${obj.slug}`;
    if (obj.entity_type === "relief") {
      const urn = obj.urn_slug || urnSlugFromReliefSlug(obj.slug);
      return `/atlas/${urn}/${obj.slug}`;
    }
    if (obj.entity_type === "source") return `/sources/${obj.slug}`;
    return `/timeline`;
  }
  return null;
}

function firstSentence(text) {
  const t = String(text || "").trim();
  if (!t) return "";
  const idx = t.indexOf(".");
  return (idx > 0 ? t.slice(0, idx + 1) : t).trim();
}

function urnOrdinalLabel(slug) {
  const KNOWN = [
    "cao-dinh",
    "nhan-dinh",
    "chuong-dinh",
    "anh-dinh",
    "nghi-dinh",
    "thuan-dinh",
    "tuyen-dinh",
    "du-dinh",
    "huyen-dinh",
  ];
  const idx = KNOWN.indexOf(slug);
  if (idx === -1) return null;
  return `Đỉnh thứ ${ROMAN_NUMERALS[idx]} trong Cửu Đỉnh`;
}

function ReliefMuseumCard({ relief, urnSlug }) {
  const name = entityName(relief);
  const isUrn = relief.entity_type === "urn";
  const atlasHref = isUrn ? `/cuu-dinh/${urnSlug}` : `/atlas/${urnSlug}/${relief.slug}`;
  const deepLinkHref = isUrn
    ? `/urns/${urnSlug}`
    : `/urns/${urnSlug}?relief=${encodeURIComponent(relief.slug)}`;
  const num = reliefNumberFromSlug(relief.slug);
  const thumbnail = relief.thumbnail_url || reliefThumbnailUrl(relief.slug);
  const summary = firstSentence(
    relief.summary_vi || relief.summary || relief.summary_en,
  );

  return (
    <article className="group flex flex-col gap-2 [content-visibility:auto] [contain-intrinsic-size:1px_320px]">
      <Link
        href={atlasHref}
        prefetch={false}
        aria-label={`Mở bản đúc ${name} trong Atlas`}
        className="focus-ring block rounded-lg"
      >
        <div className="relative flex aspect-[16/10] w-full items-center justify-center overflow-hidden rounded-lg border border-border/70 bg-gradient-to-br from-secondary via-card to-secondary/40 transition duration-200 group-hover:border-primary/40">
          {thumbnail ? (
            <img
              src={thumbnail}
              alt={name}
              loading="lazy"
              decoding="async"
              className="h-full w-full object-cover"
            />
          ) : (
            <span
              className="select-none font-serif text-6xl text-primary/35"
              aria-hidden="true"
            >
              {num || "鼎"}
            </span>
          )}
          <span className="heritage-chip absolute left-3 top-3 text-[10px]">
            {isUrn ? "Bản đúc #01" : `Phù điêu ${num}`}
          </span>
        </div>
      </Link>
      <EntityCard entity={relief} href={atlasHref} className="flex-1" />
      <Link
        href={deepLinkHref}
        prefetch={false}
        className="inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-card/60 px-3 py-2 text-xs font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary"
      >
        <Boxes className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
        Định vị trên đỉnh (3D)
      </Link>
    </article>
  );
}

export default function UrnDetailClient() {
  const params = useParams();
  const authStatus = useAuthStore((s) => s.status);
  const urnSlug = useMemo(
    () => (typeof params?.urnSlug === "string" ? params.urnSlug : ""),
    [params],
  );

  const [entity, setEntity] = useState(null);
  const [reliefs, setReliefs] = useState([]);
  const [claims, setClaims] = useState([]);
  const [relations, setRelations] = useState([]);
  const [sources, setSources] = useState([]);
  const [geographies, setGeographies] = useState([]);
  const [firstReliefHotspot, setFirstReliefHotspot] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeSection, setActiveSection] = useState("overview");

  useEffect(() => {
    if (!urnSlug) return;
    setPageMeta({
      title: `${urnNameFromSlug(urnSlug)} — Cửu Đỉnh · Lưu Niên Sử Kí`,
      description: `Chiếc đỉnh ${urnNameFromSlug(urnSlug)} trong Cửu Đỉnh triều Nguyễn.`,
      path: `/cuu-dinh/${urnSlug}`,
    });
  }, [urnSlug]);

  useEffect(() => {
    if (!urnSlug) return;
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      setNotFound(false);
      setActiveSection("overview");
      try {
        let entityRes;
        try {
          entityRes = await getHistoryEntityBySlug(urnSlug);
        } catch (err) {
          if (cancelled) return;
          if (
            err?.status === 404 ||
            (err instanceof Error && /404|not found/i.test(err.message))
          ) {
            setNotFound(true);
            return;
          }
          throw err;
        }
        if (cancelled || !entityRes) return;
        setEntity(entityRes);
        const entityId = entityRes.id;

        const reliefRes = await listHistoryEntities({
          entityType: "relief",
          limit: 200,
        });
        const allReliefs = asEntityList(reliefRes);
        const pictorialReliefs = allReliefs.filter(
          (r) =>
            (r.urn_slug || urnSlugFromReliefSlug(r.slug)) === urnSlug,
        );
        const urnItem = {
          ...entityRes,
          entity_type: "urn",
          slug: entityRes.slug,
          name_vi: entityRes.name_vi,
        };
        const mine = [urnItem, ...pictorialReliefs];
        if (cancelled) return;
        setReliefs(mine);

        const claimsRes = await listHistoryEntityClaims(entityId).catch(
          () => null,
        );
        const claimList = asClaimList(claimsRes);
        if (cancelled) return;
        setClaims(claimList);

        const [relRes, geoRes] = await Promise.all([
          listHistoryEntityRelations(entityId).catch(() => null),
          getHistoryEntityGeography(entityId).catch(() => null),
        ]);
        if (!cancelled) {
          setRelations(asRelations(relRes));
          setGeographies(asGeographies(geoRes));
        }

        const srcResults = await Promise.all(
          claimList.slice(0, 6).map((c) =>
            listHistoryClaimSources(c.id).catch(() => []),
          ),
        );
        const seen = new Set();
        const uniqueSources = srcResults
          .flatMap((r) => asSourceList(r))
          .filter((s) => {
            if (!s.id || seen.has(String(s.id))) return false;
            seen.add(String(s.id));
            return true;
          });
        if (!cancelled) setSources(uniqueSources);

        if (mine.length > 0) {
          const firstReliefSlug = mine[0].slug;
          getReliefHotspot(urnSlug, firstReliefSlug)
            .then((hotspotRes) => {
              if (!cancelled) {
                setFirstReliefHotspot(
                  hotspotRes?.hotspot ? { slug: firstReliefSlug, ...hotspotRes } : null,
                );
              }
            })
            .catch(() => {
              if (!cancelled) setFirstReliefHotspot(null);
            });
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
  }, [urnSlug]);

  const factClaims = useMemo(
    () =>
      claims.filter((c) =>
        FACT_TYPES.has(String(c.claim_type || "").toLowerCase()),
      ),
    [claims],
  );
  const chronologyClaims = useMemo(
    () =>
      claims.filter((c) =>
        CHRONOLOGY_TYPES.has(String(c.claim_type || "").toLowerCase()),
      ),
    [claims],
  );
  const interpretationClaims = useMemo(
    () =>
      claims.filter((c) =>
        INTERPRETATION_TYPES.has(String(c.claim_type || "").toLowerCase()),
      ),
    [claims],
  );
  const otherClaims = useMemo(() => {
    const seen = new Set(
      factClaims.map((c) => String(c.id)).concat(
        interpretationClaims.map((c) => String(c.id)),
      ),
    );
    return claims.filter((c) => !seen.has(String(c.id)));
  }, [claims, factClaims, interpretationClaims]);

  const claimTypeCounts = useMemo(() => {
    const counts = {};
    for (const c of claims) {
      const key = String(c.claim_type || "other").toLowerCase();
      counts[key] = (counts[key] || 0) + 1;
    }
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [claims]);

  useEffect(() => {
    if (loading || notFound || !entity) return;
    const sections = SECTION_TABS.map((t) =>
      document.getElementById(t.id),
    ).filter(Boolean);
    if (sections.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        }
      },
      { rootMargin: "-15% 0px -70% 0px", threshold: 0 },
    );
    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, [loading, notFound, entity]);

  if (!urnSlug) return null;

  if (loading) {
    return (
      <main className="site-shell" aria-busy="true">
        <div className="heritage-hero p-6 md:p-8">
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="mt-3 h-4 w-2/3" />
          <Skeleton className="mt-3 h-4 w-1/3" />
        </div>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="heritage-card p-5">
              <Skeleton className="h-5 w-2/3" />
              <Skeleton className="mt-3 h-4 w-full" />
            </div>
          ))}
        </div>
      </main>
    );
  }

  if (notFound || !entity) {
    return (
      <main className="site-shell">
        <section className="heritage-surface mx-auto max-w-xl p-8 text-center">
          <h1 className="font-display text-2xl font-bold text-foreground">
            Không tìm thấy chiếc đỉnh này
          </h1>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            Không có dữ liệu nào cho địa chỉ “{urnSlug}” trên máy chủ lịch sử.
            Có thể đỉnh này chưa được chuyển đổi hoặc địa chỉ không chính xác.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Link
              href="/cuu-dinh"
              className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
            >
              Về trang Cửu Đỉnh
            </Link>
            <Link
              href="/atlas"
              className="rounded-lg border border-border px-4 py-2 text-sm font-semibold text-foreground"
            >
              Mở Atlas
            </Link>
          </div>
        </section>
      </main>
    );
  }

  const name = entityName(entity);
  const pubEpistemic = publicationEpistemic(entity.publication_status);
  const pubLabel = publicationStatusLabel(entity.publication_status);
  const hanNom = entity.name_han_nom || entity.han_nom;
  const ordinalLabel = urnOrdinalLabel(urnSlug);
  const firstHotspotMesh = firstReliefHotspot?.hotspot?.mesh_name;
  const firstHotspotPos = firstReliefHotspot?.hotspot?.pos;

  return (
    <main className="site-shell">
      {/* Identity header */}
      <section className="heritage-hero p-6 md:p-10">
        <div className="relative max-w-4xl">
          <div className="flex flex-wrap items-center gap-2">
            <span className="heritage-chip">
              <Landmark className="h-4 w-4" aria-hidden="true" />
              Chiếc đỉnh · Cửu Đỉnh
            </span>
            <EpistemicLabel info={pubEpistemic} />
          </div>

          <h1 className="mt-6 font-serif text-4xl font-bold leading-tight tracking-tight text-foreground md:text-6xl">
            {name}
          </h1>
          {entity.name_en ? (
            <p className="mt-3 text-lg text-muted-foreground md:text-xl">
              {entity.name_en}
            </p>
          ) : null}
          {hanNom ? (
            <p className="mt-3 font-serif text-2xl text-foreground/80">
              {hanNom}
            </p>
          ) : null}
          {ordinalLabel ? (
            <p className="mt-3 inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/60 px-3 py-1 text-xs font-semibold text-muted-foreground">
              <Crown className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
              {ordinalLabel}
            </p>
          ) : null}

          <div className="mt-6 flex flex-wrap gap-6 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-2">
              <Landmark className="h-4 w-4 text-primary" aria-hidden="true" />
              {reliefs.length} bản đúc nổi trên đỉnh
            </span>
            {pubLabel ? (
              <span className="inline-flex items-center gap-2">
                <BadgeCheck className="h-4 w-4 text-primary" aria-hidden="true" />
                {pubLabel}
              </span>
            ) : null}
          </div>

          <p className="mt-6 max-w-3xl text-base leading-7 text-muted-foreground md:text-lg">
            {entity.summary_vi ||
              entity.summary ||
              entity.summary_en ||
              "Chưa có tóm tắt cho chiếc đỉnh này — nội dung đang được soạn thảo."}
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href={`/urns/${entity.slug || urnSlug}`}
              prefetch={false}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
            >
              <Boxes className="h-4 w-4" aria-hidden="true" />
              Xem trong 3D
            </Link>
            {entity.id != null ? (
              <Link
                href={`/explore/connections?entity=${encodeURIComponent(entity.id)}`}
                prefetch={false}
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary"
              >
                <Network className="h-4 w-4 text-primary" aria-hidden="true" />
                Khám phá mạng lưới
              </Link>
            ) : null}
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
          Có lỗi khi tải dữ liệu: {error}
        </div>
      ) : null}

      {/* Sectional navigation */}
      <nav
        aria-label="Điều hướng các phần của trang"
        className="sticky top-0 z-30 -mx-4 mt-6 border-b border-border/70 bg-background/95 px-4 backdrop-blur-md md:top-14 md:-mx-6 md:px-6"
      >
        <ul className="scrollbar-hide flex items-center gap-1 overflow-x-auto py-2">
          {SECTION_TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeSection === tab.id;
            return (
              <li key={tab.id} className="shrink-0">
                <a
                  href={`#${tab.id}`}
                  aria-current={isActive ? "true" : undefined}
                  className={[
                    "inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition",
                    isActive
                      ? "bg-primary/15 text-primary ring-1 ring-primary/30"
                      : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                  ].join(" ")}
                >
                  <Icon className="h-3.5 w-3.5" aria-hidden="true" />
                  {tab.label}
                </a>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Overview */}
      <section
        id="overview"
        className="mt-12 scroll-mt-28 md:scroll-mt-40"
      >
        <SectionHeading
          kicker="Tổng quan"
          title="Chiếc đỉnh này đại diện cho điều gì"
          lead="Tóm tắt biên tập về vị trí của chiếc đỉnh trong Cửu Đỉnh và ý nghĩa được ghi nhận."
        />
        <div className="mt-6 max-w-reading">
          <p className="font-serif text-base leading-8 text-foreground/90 md:text-lg md:leading-9">
            {entity.summary_vi ||
              entity.summary ||
              entity.summary_en ||
              "Chưa có tóm tắt cho chiếc đỉnh này — nội dung đang được soạn thảo."}
          </p>
        </div>
        {claimTypeCounts.length > 0 ? (
          <div className="mt-8">
            <h3 className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Phân bố theo nhóm nhận định
            </h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {claimTypeCounts.map(([type, count]) => (
                <span
                  key={type}
                  className="inline-flex items-center gap-2 rounded-lg border border-border/70 bg-card/60 px-3 py-2 text-sm"
                >
                  <span className="font-semibold text-foreground">
                    {claimTypeLabel(type)}
                  </span>
                  <span className="font-display tabular-nums text-muted-foreground">
                    {count}
                  </span>
                </span>
              ))}
            </div>
          </div>
        ) : null}
      </section>

      {/* Reliefs */}
      <section
        id="reliefs"
        className="mt-16 scroll-mt-28 md:scroll-mt-40"
      >
        <SectionHeading
          kicker="Bản đúc & Phù điêu"
          title={`${reliefs.length} bản đúc nổi trên ${name}`}
          lead="Mỗi đỉnh mang 18 bản đúc nổi gồm 1 đồ án chữ thụy hiệu mang tên đỉnh ở chính diện hàng trên và 17 phù điêu họa tiết cảnh vật. Mở từng bản đúc để xem mô tả, diễn giải và nguồn sử liệu."
        />
        {reliefs.length > 0 ? (
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {reliefs.map((relief) => (
              <ReliefMuseumCard
                key={relief.slug || relief.id}
                relief={relief}
                urnSlug={urnSlug}
              />
            ))}
          </div>
        ) : (
          <div className="mt-6 rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-10 text-center text-sm text-muted-foreground">
            Chưa có dữ liệu phù điêu nào cho chiếc đỉnh này trên máy chủ lịch
            sử.
          </div>
        )}
      </section>

      {/* 3D */}
      <section
        id="threed"
        className="mt-16 scroll-mt-28 md:scroll-mt-40"
      >
        <SectionHeading
          kicker="Không gian ba chiều"
          title="Khám phá đỉnh trong 3D"
          lead="Trình xem 3D toàn màn hình cho phép xoay quanh đỉnh, phóng to từng họa tiết và thực hành trực tiếp trên mô hình."
        />
        <div className="heritage-surface mt-6 p-6 md:p-9">
          <div className="grid gap-8 md:grid-cols-[1.4fr_1fr] md:items-center">
            <div>
              <h3 className="font-display text-xl font-bold tracking-tight text-foreground">
                Trình xem 3D tương tác
              </h3>
              <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
                Xoay và phóng to mô hình để soi từng phù điêu; bật chế độ quét
                để dò họa tiết, theo dõi tiến độ khám phá và hoàn thành bài học,
                trắc nghiệm cho từng họa tiết. Toàn bộ trải nghiệm chạy ở chế độ
                toàn màn hình.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href={`/urns/${entity.slug || urnSlug}`}
                  prefetch={false}
                  className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
                >
                  <Boxes className="h-4 w-4" aria-hidden="true" />
                  Mở trình xem 3D
                </Link>
                <Link
                  href={`/urns/${entity.slug || urnSlug}/exam`}
                  prefetch={false}
                  className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary"
                >
                  <GraduationCap className="h-4 w-4 text-primary" aria-hidden="true" />
                  Bài kiểm tra cuối đỉnh
                </Link>
              </div>
            </div>
            <div className="heritage-stat rounded-lg p-5">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <Compass className="h-4 w-4 text-primary" aria-hidden="true" />
                Hotspot 3D
              </div>
              {firstReliefHotspot && firstHotspotMesh ? (
                <div className="mt-3 space-y-2 text-sm">
                  <p className="font-medium text-foreground">
                    Phù điêu “{firstReliefHotspot.slug}”
                  </p>
                  <p className="font-mono text-xs text-muted-foreground">
                    Mesh: {firstHotspotMesh}
                  </p>
                  {Array.isArray(firstHotspotPos) ? (
                    <p className="font-mono text-xs text-muted-foreground">
                      Toạ độ: ({firstHotspotPos.map((n) => Number(n).toFixed(2)).join(", ")})
                    </p>
                  ) : null}
                </div>
              ) : (
                <p className="mt-3 text-sm leading-6 text-muted-foreground">
                  Mỗi phù điêu trên đỉnh đều được gắn một vị trí (hotspot) để
                  định vị trực tiếp trên mô hình 3D.
                </p>
              )}
              <p className="mt-3 text-[11px] text-muted-foreground">
                Định vị một phù điêu cụ thể:{" "}
                <Link
                  href={`/urns/${entity.slug || urnSlug}?relief=${
                    reliefs[0]?.slug || ""
                  }`}
                  prefetch={false}
                  className="font-semibold text-primary hover:underline"
                >
                  mở 3D tại phù điêu đầu tiên
                </Link>
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Context */}
      <section
        id="context"
        className="mt-16 scroll-mt-28 md:scroll-mt-40"
      >
        <SectionHeading
          kicker="Bối cảnh"
          title="Bối cảnh đúc và phụng tạo"
          lead="Niên đại và hoàn cảnh hình thành chiếc đỉnh, cùng các mối liên hệ thời gian với thực thể khác."
        />
        {chronologyClaims.length > 0 ? (
          <ol className="mt-6 space-y-3">
            {chronologyClaims.map((claim, i) => (
              <li
                key={String(claim.id)}
                className="flex gap-4 rounded-lg border border-border bg-card/60 px-4 py-3"
              >
                <span
                  className="select-none font-serif text-2xl leading-8 text-primary/40"
                  aria-hidden="true"
                >
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-md bg-muted/70 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                      {claimTypeLabel(claim.claim_type)}
                    </span>
                    <EpistemicLabel info={claimEpistemic(claim)} />
                  </div>
                  <p className="mt-2 text-sm leading-7 text-foreground/90">
                    {claimText(claim)}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        ) : (
          <div className="mt-6 rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-8 text-center text-sm text-muted-foreground">
            Chưa có nhận định niên đại nào được ghi nhận cho chiếc đỉnh này.
          </div>
        )}

        {/* Relations */}
        <div className="mt-10">
          <h3 className="font-display text-xl font-bold tracking-tight text-foreground">
            Kết nối thời gian và thực thể
          </h3>
          {relations.length > 0 ? (
            <ul className="mt-4 space-y-2">
              {relations.map((rel) => {
                const href = relationHref(rel);
                const relName = relationObjectName(rel);
                return (
                  <li
                    key={String(
                      rel.id ||
                        rel.object_entity_id ||
                        `${rel.predicate}-${relName}`,
                    )}
                    className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-card/60 px-4 py-3 text-sm"
                  >
                    <Link2 className="h-4 w-4 text-primary" aria-hidden="true" />
                    <span className="text-muted-foreground">
                      {relationPredicateLabel(rel.predicate)}
                    </span>
                    {href ? (
                      <Link
                        href={href}
                        prefetch={false}
                        className="font-medium text-primary hover:underline"
                      >
                        {relName || "Chi tiết"}
                      </Link>
                    ) : (
                      <span className="font-medium text-foreground">
                        {relName || "Thực thể liên quan"}
                      </span>
                    )}
                    {rel.verification_status ? (
                      <span className="text-[11px] text-muted-foreground">
                        {rel.verification_status}
                      </span>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          ) : (
            <div className="mt-4 rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-8 text-center text-sm text-muted-foreground">
              Chưa có quan hệ nào được ghi nhận.
            </div>
          )}
          <div className="mt-4 flex flex-wrap gap-4">
            <Link
              href={`/timeline?entity=${encodeURIComponent(urnSlug)}`}
              prefetch={false}
              className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
            >
              <ScrollText className="h-4 w-4" aria-hidden="true" />
              Xem trên dòng thời gian
            </Link>
            {entity.id != null ? (
              <Link
                href={`/explore/connections?entity=${encodeURIComponent(entity.id)}`}
                prefetch={false}
                className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
              >
                <Network className="h-4 w-4" aria-hidden="true" />
                Xem toàn bộ mạng lưới liên kết
              </Link>
            ) : null}
          </div>
        </div>
      </section>

      {/* Evidence */}
      <section
        id="evidence"
        className="mt-16 scroll-mt-28 md:scroll-mt-40"
      >
        <SectionHeading
          kicker="Chứng cứ"
          title="Dữ kiện đã được ghi nhận"
          lead="Các nhận định thuộc nhóm thực tế / niên đại / địa lý / chất liệu / chế tác. Trạng thái kiểm chứng của từng nhận định được dán nhãn."
        />
        {factClaims.length > 0 ? (
          <div className="mt-6 grid gap-3 lg:grid-cols-2">
            {factClaims.map((claim) => (
              <ClaimItem key={String(claim.id)} claim={claim} />
            ))}
          </div>
        ) : (
          <div className="mt-6 rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-10 text-center text-sm text-muted-foreground">
            Chưa có dữ kiện nào được ghi nhận cho chiếc đỉnh này. Các thông tin
            cơ bản đang được đối chiếu và sẽ xuất hiện ở đây khi sẵn sàng.
          </div>
        )}

        {interpretationClaims.length > 0 ? (
          <div className="mt-10">
            <h3 className="font-display text-xl font-bold tracking-tight text-foreground">
              Diễn giải và biểu tượng
            </h3>
            <p className="mt-2 max-w-3xl text-sm leading-7 text-muted-foreground">
              Các diễn giải được dán nhãn rõ ràng và đang trong quá trình kiểm
              chứng nguồn.
            </p>
            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              {interpretationClaims.map((claim) => (
                <ClaimItem key={String(claim.id)} claim={claim} />
              ))}
            </div>
          </div>
        ) : null}

        {otherClaims.length > 0 ? (
          <div className="mt-10">
            <h3 className="font-display text-xl font-bold tracking-tight text-foreground">
              Nhận định khác
            </h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              {otherClaims.map((claim) => (
                <ClaimItem key={String(claim.id)} claim={claim} />
              ))}
            </div>
          </div>
        ) : null}

        {/* Geography */}
        <div className="mt-10">
          <h3 className="font-display text-xl font-bold tracking-tight text-foreground">
            Định vị địa lý
          </h3>
          <div className="heritage-stat mt-4 flex flex-wrap items-center justify-between gap-4 rounded-lg p-5">
            <div className="min-w-0">
              {geographies.length > 0 ? (
                <p className="text-sm leading-6 text-muted-foreground">
                  {geographies
                    .map(
                      (g) => g.name_vi || g.name || "Vị trí lịch sử",
                    )
                    .join(" · ")}
                </p>
              ) : (
                <p className="text-sm leading-6 text-muted-foreground">
                  Xem vị trí lịch sử và không gian liên quan đến chiếc đỉnh trên
                  bản đồ.
                </p>
              )}
            </div>
            <Link
              href={`/map?entity=${encodeURIComponent(entity.id)}`}
              prefetch={false}
              className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-border bg-background/60 px-4 py-2 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary"
            >
              <MapIcon className="h-4 w-4 text-primary" aria-hidden="true" />
              Xem trên bản đồ
            </Link>
          </div>
        </div>
      </section>

      {/* Sources */}
      <section
        id="sources"
        className="mt-16 scroll-mt-28 md:scroll-mt-40"
      >
        <SectionHeading
          kicker="Nguồn sử liệu"
          title="Nguồn liên quan"
          lead="Các nguồn gắn với nhận định của chiếc đỉnh này (lấy từ các nhận định hiện có)."
        />
        {sources.length > 0 ? (
          <ul className="mt-6 flex flex-wrap gap-2">
            {sources.map((src) => (
              <li key={String(src.id)}>
                <Link
                  href={`/sources/${src.id}`}
                  prefetch={false}
                  className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-4 py-2 text-sm transition hover:border-primary/40 hover:bg-secondary"
                >
                  <Library className="h-3.5 w-3.5 shrink-0 text-primary" aria-hidden="true" />
                  <span className="min-w-0">
                    <span className="block max-w-[260px] truncate font-medium text-foreground">
                      {src.title || `Nguồn #${src.id}`}
                    </span>
                    <span className="block truncate text-xs text-muted-foreground">
                      {[src.author_text, src.publication_year]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <div className="mt-6 rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-10 text-center text-sm text-muted-foreground">
            Chưa có nguồn nào được liên kết. Các nguồn đang được gắn vào từng
            nhận định trong quá trình kiểm chứng.
          </div>
        )}
        <Link
          href="/sources"
          prefetch={false}
          className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
        >
          <Library className="h-4 w-4" aria-hidden="true" />
          Mở thư viện nguồn
        </Link>
      </section>

      {/* Learning */}
      <section
        id="learning"
        className="mt-16 scroll-mt-28 md:scroll-mt-40"
      >
        <div className="heritage-hero flex flex-col gap-5 p-6 md:p-9">
          <SectionHeading
            kicker="Học tập"
            title="Học về đỉnh này"
            lead="Biến trải nghiệm khám phá thành hành trình học có theo dõi tiến độ."
          />
          {authStatus === "authed" ? (
            <div className="flex flex-wrap items-center gap-3">
              <Link
                href={`/urns/${entity.slug || urnSlug}`}
                prefetch={false}
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
              >
                <Boxes className="h-4 w-4" aria-hidden="true" />
                Học trong trình xem 3D
              </Link>
              <Link
                href="/practice"
                prefetch={false}
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary"
              >
                Mở phần ôn tập
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
            </div>
          ) : (
            <div className="max-w-2xl">
              <p className="text-sm leading-7 text-muted-foreground md:text-base">
                Đăng nhập để lưu tiến độ khám phá, duy trì chuỗi ngày học, nhận
                nhiệm vụ và hoàn thành bài kiểm tra cuối đỉnh.
              </p>
              <Link
                href="/login"
                prefetch={false}
                className="mt-5 inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
              >
                <GraduationCap className="h-4 w-4" aria-hidden="true" />
                Đăng nhập để lưu tiến độ
              </Link>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
