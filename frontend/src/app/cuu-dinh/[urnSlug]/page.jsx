"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  Boxes,
  Landmark,
  Library,
  Link2,
  Network,
  ScrollText,
} from "lucide-react";

import {
  getHistoryEntityBySlug,
  listHistoryEntities,
  listHistoryClaimSources,
  listHistoryEntityClaims,
  listHistoryEntityRelations,
} from "@/lib/api";
import {
  asClaimList,
  asEntityList,
  asRelations,
  asSourceList,
  claimTypeLabel,
  entityName,
  publicationStatusLabel,
  relationPredicateLabel,
  urnSlugFromReliefSlug,
} from "@/lib/history";
import Skeleton from "@/components/Skeleton";
import EntityCard from "@/components/history/EntityCard";
import ClaimItem from "@/components/history/ClaimItem";
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

const INTERPRETATION_TYPES = new Set([
  "symbolism",
  "interpretation",
  "modern_interpretation",
  "traditional_account",
]);

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

export default function UrnDetailPage() {
  const params = useParams();
  const urnSlug = useMemo(
    () =>
      typeof params?.urnSlug === "string" ? params.urnSlug : "",
    [params],
  );

  const [entity, setEntity] = useState(null);
  const [reliefs, setReliefs] = useState([]);
  const [claims, setClaims] = useState([]);
  const [relations, setRelations] = useState([]);
  const [sources, setSources] = useState([]);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!urnSlug) return;
    document.title = `${urnSlug
      .split("-")
      .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
      .join(" ")} — Cửu Đỉnh · Lưu Niên Sử Kí`;
  }, [urnSlug]);

  useEffect(() => {
    if (!urnSlug) return;
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      setNotFound(false);
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
        const mine = allReliefs.filter(
          (r) =>
            (r.urn_slug || urnSlugFromReliefSlug(r.slug)) === urnSlug,
        );
        if (cancelled) return;
        setReliefs(mine);

        const claimsRes = await listHistoryEntityClaims(entityId).catch(
          () => null,
        );
        const claimList = asClaimList(claimsRes);
        if (cancelled) return;
        setClaims(claimList);

        const relRes = await listHistoryEntityRelations(entityId).catch(
          () => null,
        );
        if (!cancelled) setRelations(asRelations(relRes));

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
    () => claims.filter((c) => FACT_TYPES.has(String(c.claim_type || "").toLowerCase())),
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

  const pubLabel = publicationStatusLabel(entity.publication_status);
  const hanNom = entity.name_han_nom || entity.han_nom;

  return (
    <main className="site-shell">
      {/* Identity header */}
      <section className="heritage-hero p-6 md:p-8">
        <div className="relative">
          <div className="flex flex-wrap items-center gap-2">
            <span className="heritage-chip">
              <Landmark className="h-4 w-4" aria-hidden="true" />
              Chiếc đỉnh · Cửu Đỉnh
            </span>
            {pubLabel ? (
              <span className="rounded-md border border-border/60 bg-background/70 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                {pubLabel}
              </span>
            ) : null}
          </div>
          <h1 className="mt-5 font-display text-3xl font-bold tracking-tight text-foreground md:text-5xl">
            {entityName(entity)}
          </h1>
          {entity.name_en ? (
            <p className="mt-2 text-lg text-muted-foreground">
              {entity.name_en}
            </p>
          ) : null}
          {hanNom ? (
            <p className="mt-2 font-serif text-2xl text-foreground/80">
              {hanNom}
            </p>
          ) : null}
          <p className="mt-1 text-xs text-muted-foreground">{entity.slug}</p>

          <p className="mt-6 max-w-3xl text-base leading-7 text-muted-foreground">
            {entity.summary_vi ||
              entity.summary ||
              entity.summary_en ||
              "Chưa có tóm tắt cho chiếc đỉnh này — nội dung đang được soạn thảo."}
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href={`/urns/${entity.slug || urnSlug}`}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
            >
              <Boxes className="h-4 w-4" aria-hidden="true" />
              Xem 3D và luyện tập
            </Link>
            <Link
              href="/atlas"
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary"
            >
              Mở Atlas
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
            {entity.id != null ? (
              <Link
                href={`/explore/connections?entity=${encodeURIComponent(entity.id)}`}
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary"
              >
                <Network className="h-4 w-4 text-primary" aria-hidden="true" />
                Xem mạng lưới liên kết
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

      {/* Basic verified facts */}
      <section className="mt-10">
        <SectionHeading
          kicker="Dữ kiện cơ bản"
          title="Các dữ kiện đã được ghi nhận"
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
      </section>

      {/* Reliefs */}
      <section className="mt-10">
        <SectionHeading
          kicker="Phù điêu"
          title={`${reliefs.length} phù điêu trên ${entityName(entity)}`}
          lead="Mỗi phù điêu là một mục tra cứu riêng trong Atlas. Mở từng phù điêu để xem mô tả, diễn giải và nguồn sử liệu."
        />
        {reliefs.length > 0 ? (
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {reliefs.map((relief) => (
              <EntityCard
                key={relief.slug || relief.id}
                entity={relief}
                href={`/atlas/${urnSlug}/${relief.slug}`}
                badge="Phù điêu"
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

      {/* Category / claim-type distribution */}
      <section className="mt-10">
        <SectionHeading
          kicker="Phân bố"
          title="Phân bố theo nhóm nhận định"
          lead="Dữ liệu phân loại theo chủ đề (thảo mộc, linh thú, địa lý…) đang được xây dựng. Dưới đây là phân bố theo loại nhận định hiện có."
        />
        {claimTypeCounts.length > 0 ? (
          <div className="mt-6 flex flex-wrap gap-2">
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
        ) : (
          <div className="mt-6 rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-8 text-center text-sm text-muted-foreground">
            Chưa có dữ liệu phân bố.
          </div>
        )}
      </section>

      {/* Timeline connections / relations */}
      <section className="mt-10">
        <SectionHeading
          kicker="Liên hệ"
          title="Kết nối thời gian và thực thể"
          lead="Các quan hệ được nạp từ máy chủ lịch sử, liên kết đỉnh này với các thực thể khác."
        />
        {relations.length > 0 ? (
          <ul className="mt-6 space-y-2">
            {relations.map((rel) => {
              const href = relationHref(rel);
              const name = relationObjectName(rel);
              return (
                <li
                  key={String(rel.id || rel.object_entity_id || `${rel.predicate}-${name}`)}
                  className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-card/60 px-4 py-3 text-sm"
                >
                  <Link2 className="h-4 w-4 text-primary" aria-hidden="true" />
                  <span className="text-muted-foreground">
                    {relationPredicateLabel(rel.predicate)}
                  </span>
                  {href ? (
                    <Link
                      href={href}
                      className="font-medium text-primary hover:underline"
                    >
                      {name || "Chi tiết"}
                    </Link>
                  ) : (
                    <span className="font-medium text-foreground">
                      {name || "Thực thể liên quan"}
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
          <div className="mt-6 rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-8 text-center text-sm text-muted-foreground">
            Chưa có quan hệ nào được ghi nhận.
          </div>
        )}
        <Link
          href="/timeline"
          className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
        >
          <ScrollText className="h-4 w-4" aria-hidden="true" />
          Xem dòng thời gian đầy đủ
        </Link>
      </section>

      {/* Sources */}
      <section className="mt-10">
        <SectionHeading
          kicker="Nguồn sử liệu"
          title="Nguồn liên quan"
          lead="Các nguồn gắn với nhận định của chiếc đỉnh này (lấy từ các nhận định hiện có)."
        />
        {sources.length > 0 ? (
          <ul className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {sources.map((src) => (
              <li key={String(src.id)}>
                <Link
                  href={`/sources/${src.id}`}
                  className="flex items-start gap-3 rounded-lg border border-border bg-card/60 px-4 py-3 text-sm transition hover:border-primary/40"
                >
                  <Library className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
                  <span className="min-w-0">
                    <span className="block font-medium text-foreground">
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
          className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
        >
          <Library className="h-4 w-4" aria-hidden="true" />
          Mở thư viện nguồn
        </Link>
      </section>

      {/* Interpretations */}
      {interpretationClaims.length > 0 ? (
        <section className="mt-10">
          <SectionHeading
            kicker="Diễn giải"
            title="Diễn giải và biểu tượng"
            lead="Các diễn giải được dán nhãn rõ ràng và đang trong quá trình kiểm chứng nguồn."
          />
          <div className="mt-6 grid gap-3 lg:grid-cols-2">
            {interpretationClaims.map((claim) => (
              <ClaimItem key={String(claim.id)} claim={claim} />
            ))}
          </div>
        </section>
      ) : null}

      {/* Other claims */}
      {otherClaims.length > 0 ? (
        <section className="mt-10">
          <SectionHeading
            kicker="Nhận định khác"
            title="Các nhận định còn lại"
          />
          <div className="mt-6 grid gap-3 lg:grid-cols-2">
            {otherClaims.map((claim) => (
              <ClaimItem key={String(claim.id)} claim={claim} />
            ))}
          </div>
        </section>
      ) : null}

      {/* Practice CTA */}
      <section className="mt-10">
        <div className="heritage-hero flex flex-col items-center gap-5 p-6 text-center md:p-9">
          <h2 className="font-display text-2xl font-bold tracking-tight text-foreground md:text-3xl">
            Tìm hiểu {entityName(entity)} trong 3D
          </h2>
          <p className="max-w-2xl text-sm leading-7 text-muted-foreground md:text-base">
            Xoay quanh đỉnh, phóng to các phù điêu và thử sức với bài tập trên
            trình xem 3D.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link
              href={`/urns/${entity.slug || urnSlug}`}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
            >
              <Boxes className="h-4 w-4" aria-hidden="true" />
              Vào trình xem 3D
            </Link>
            <Link
              href="/practice"
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary"
            >
              Ôn tập
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}