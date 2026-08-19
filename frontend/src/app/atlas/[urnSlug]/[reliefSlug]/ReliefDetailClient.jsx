"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  Boxes,
  Crosshair,
  GitCompareArrows,
  Landmark,
  Library,
  Link2,
  Map as MapIcon,
  Network,
  ScrollText,
  BookOpen,
} from "lucide-react";

import {
  getHistoryEntityBySlug,
  getHistoryEntityGeography,
  getReliefHotspot,
  listHistoryClaimSources,
  listHistoryEntityClaims,
  listHistoryEntityRelations,
} from "@/lib/api";
import {
  asClaimList,
  asGeographies,
  asRelations,
  asSourceList,
  entityName,
  meshNameFromReliefSlug,
  publicationStatusLabel,
  relationObjectName,
  reliefNumberFromSlug,
  reliefThumbnailUrl,
  urnNameFromSlug,
  urnSlugFromReliefSlug,
} from "@/lib/history";
import { useAuthStore } from "@/stores/authStore";
import { useMotifStore } from "@/stores/motifStore";
import Skeleton from "@/components/Skeleton";
import ClaimItem from "@/components/history/ClaimItem";
import SectionHeading from "@/components/history/SectionHeading";
import VerificationNote from "@/components/history/VerificationNote";
import { Badge } from "@/components/ui/badge";

const DOCUMENTED_STATUSES = new Set(["editor_reviewed", "expert_verified"]);

const INTERPRETATION_TYPES = new Set([
  "symbolism",
  "interpretation",
  "modern_interpretation",
  "traditional_account",
]);

function relationTarget(rel) {
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

export default function ReliefDetailClient() {
  const params = useParams();
  const reliefSlug = useMemo(
    () => (typeof params?.reliefSlug === "string" ? params.reliefSlug : ""),
    [params],
  );
  const urnSlug = useMemo(
    () => (typeof params?.urnSlug === "string" ? params.urnSlug : ""),
    [params],
  );

  const [entity, setEntity] = useState(null);
  const [claims, setClaims] = useState([]);
  const [relations, setRelations] = useState([]);
  const [geographies, setGeographies] = useState([]);
  const [sources, setSources] = useState([]);
  const [hotspot, setHotspot] = useState(null);
  const [hotspotLoading, setHotspotLoading] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const authStatus = useAuthStore((s) => s.status);
  const motifByMesh = useMotifStore((s) => s.motifsByMesh);

  useEffect(() => {
    if (!reliefSlug) return;
    document.title = `Phù điêu ${reliefSlug} — Atlas · Lưu Niên Sử Kí`;
  }, [reliefSlug]);

  useEffect(() => {
    if (!reliefSlug) return;
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      setNotFound(false);
      try {
        let entityRes;
        try {
          entityRes = await getHistoryEntityBySlug(reliefSlug);
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

        const [claimsRes, relRes, geoRes] = await Promise.all([
          listHistoryEntityClaims(entityId).catch(() => null),
          listHistoryEntityRelations(entityId).catch(() => null),
          getHistoryEntityGeography(entityId).catch(() => null),
        ]);
        if (cancelled) return;
        const claimList = asClaimList(claimsRes);
        setClaims(claimList);
        setRelations(asRelations(relRes));
        setGeographies(asGeographies(geoRes));

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
  }, [reliefSlug]);

  const effectiveUrnSlug = useMemo(
    () =>
      entity?.urn_slug ||
      urnSlug ||
      urnSlugFromReliefSlug(entity?.slug || reliefSlug),
    [entity, urnSlug, reliefSlug],
  );

  useEffect(() => {
    if (!entity || !effectiveUrnSlug || !reliefSlug) return;
    let cancelled = false;
    setHotspotLoading(true);
    getReliefHotspot(effectiveUrnSlug, reliefSlug)
      .then((res) => {
        if (!cancelled) setHotspot(res);
      })
      .catch(() => {
        if (!cancelled) setHotspot(null);
      })
      .finally(() => {
        if (!cancelled) setHotspotLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [entity?.id, effectiveUrnSlug, reliefSlug]);

  const documentedClaims = useMemo(
    () =>
      claims.filter((c) =>
        DOCUMENTED_STATUSES.has(
          String(c.verification_status || "").toLowerCase(),
        ),
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
      documentedClaims.map((c) => String(c.id)).concat(
        interpretationClaims.map((c) => String(c.id)),
      ),
    );
    return claims.filter((c) => !seen.has(String(c.id)));
  }, [claims, documentedClaims, interpretationClaims]);

  const relatedIds = useMemo(
    () =>
      relations
        .map((r) => r.object_entity_id)
        .filter((id) => id != null),
    [relations],
  );

  const learnedMotif = useMemo(() => {
    const mesh = entity?.slug ? meshNameFromReliefSlug(entity.slug) : null;
    return mesh ? motifByMesh[mesh] : null;
  }, [entity, motifByMesh]);
  const learningHref = learnedMotif?.id
    ? `/motif/${learnedMotif.id}`
    : "/practice";
  const isAuthed = authStatus === "authed";
  const learningTarget = isAuthed
    ? learningHref
    : `/login?returnUrl=${encodeURIComponent(learningHref)}`;

  if (!reliefSlug) return null;

  if (loading) {
    return (
      <main className="site-shell" aria-busy="true">
        <div className="heritage-hero p-6 md:p-8">
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="mt-3 h-4 w-2/3" />
          <Skeleton className="mt-3 h-4 w-1/3" />
        </div>
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {[...Array(4)].map((_, i) => (
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
            Không tìm thấy phù điêu này
          </h1>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            Không có dữ liệu nào cho phù điêu “{reliefSlug}” trên máy chủ lịch
            sử.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Link
              href="/atlas"
              className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
            >
              Về Atlas
            </Link>
            <Link
              href="/cuu-dinh"
              className="rounded-lg border border-border px-4 py-2 text-sm font-semibold text-foreground"
            >
              Về trang Cửu Đỉnh
            </Link>
          </div>
        </section>
      </main>
    );
  }

  const pubLabel = publicationStatusLabel(entity.publication_status);
  const hanNom = entity.name_han_nom || entity.han_nom;
  const urnName = urnNameFromSlug(effectiveUrnSlug);
  const positionNumber =
    reliefNumberFromSlug(reliefSlug || entity.slug) || reliefSlug || "";
  const relief3dHref = `/urns/${effectiveUrnSlug}?relief=${encodeURIComponent(
    reliefSlug,
  )}`;
  const compareIds = [entity.id, ...relatedIds.slice(0, 2)].filter(Boolean);
  const compareHref = `/compare?entities=${compareIds.join(",")}`;
  const hasHotspot = Boolean(
    hotspot?.hotspot?.pos && Array.isArray(hotspot.hotspot.pos),
  );
  const thumbnailUrl =
    entity.thumbnail_url ||
    entity.thumbnailUrl ||
    reliefThumbnailUrl(reliefSlug || entity.slug);

  return (
    <main className="site-shell">
      {/* Identity header + relief visual */}
      <section className="heritage-hero p-6 md:p-8">
        <div className="relative">
          <div className="flex flex-wrap items-center gap-2">
            <span className="heritage-chip">
              <Landmark className="h-4 w-4" aria-hidden="true" />
              Phù điêu · {urnName}
            </span>
            {pubLabel ? (
              <span className="rounded-md border border-border/60 bg-background/70 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                {pubLabel}
              </span>
            ) : null}
          </div>

          <div className="mt-6 grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,360px)] lg:items-start">
            <div>
              <h1 className="font-serif text-3xl font-bold tracking-tight text-foreground md:text-5xl">
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
              <p className="mt-1 text-xs text-muted-foreground">
                {entity.slug}
              </p>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                <Link
                  href={`/cuu-dinh/${effectiveUrnSlug}`}
                  className="inline-flex items-center gap-1.5 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary transition hover:bg-primary/15 focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <Landmark className="h-3.5 w-3.5" aria-hidden="true" />
                  Đỉnh: {urnName}
                </Link>
                {positionNumber ? (
                  <Badge variant="secondary">Vị trí: {positionNumber}</Badge>
                ) : null}
              </div>

              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href={relief3dHref}
                  className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <Boxes className="h-4 w-4" aria-hidden="true" />
                  Xem trên đỉnh (3D)
                </Link>
                <Link
                  href={`/cuu-dinh/${effectiveUrnSlug}`}
                  className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <Landmark className="h-4 w-4" aria-hidden="true" />
                  Đỉnh chứa phù điêu
                </Link>
                {entity.id != null ? (
                  <Link
                    href={`/explore/connections?entity=${encodeURIComponent(
                      entity.id,
                    )}`}
                    className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <Network className="h-4 w-4 text-primary" aria-hidden="true" />
                    Mạng lưới
                  </Link>
                ) : null}
                <Link
                  href={compareHref}
                  className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <GitCompareArrows
                    className="h-4 w-4 text-primary"
                    aria-hidden="true"
                  />
                  So sánh
                </Link>
              </div>
            </div>

            <div className="relative overflow-hidden rounded-xl border border-border bg-paper-elevated p-3">
              {thumbnailUrl ? (
                <div className="aspect-[4/3] w-full overflow-hidden rounded-lg border border-border bg-muted">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={thumbnailUrl}
                    alt={entityName(entity)}
                    className="h-full w-full object-cover"
                  />
                </div>
              ) : (
                <div className="relative flex aspect-[4/3] w-full items-center justify-center overflow-hidden rounded-lg border border-border/70 bg-gradient-to-br from-bronze-accent/10 via-paper-elevated to-jade-accent/5 p-6">
                  <div
                    className="pointer-events-none absolute inset-2 rounded-md border border-bronze-accent/25"
                    aria-hidden="true"
                  />
                  <div className="relative flex flex-col items-center gap-3 text-center">
                    <Landmark
                      className="h-10 w-10 text-bronze-accent/70"
                      aria-hidden="true"
                    />
                    <p className="font-serif text-2xl leading-snug text-ink">
                      {entityName(entity)}
                    </p>
                    <p className="text-xs text-ink-muted">
                      Hình ảnh tư liệu đang được bổ sung
                    </p>
                  </div>
                </div>
              )}
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
          Có lỗi khi tải dữ liệu: {error}
        </div>
      ) : null}

      {/* What you are seeing */}
      <section className="mt-10">
        <SectionHeading
          kicker="Bạn đang nhìn thấy gì"
          title="Mô tả hình tượng"
          lead="Mô tả phù điêu này trên thân đỉnh, được nạp từ máy chủ lịch sử."
        />
        <div className="heritage-surface mt-6 p-6 md:p-8">
          <p className="text-base leading-8 text-foreground/90">
            {entity.summary_vi ||
              entity.summary ||
              entity.summary_en ||
              "Chưa có mô tả cho phù điêu này — nội dung đang được soạn thảo."}
          </p>
        </div>
      </section>

      {/* Location on the urn (hotspot) */}
      <section className="mt-10">
        <SectionHeading
          kicker="Vị trí trên đỉnh"
          title="Định vị phù điêu"
          lead="Tọa độ của hình đúc trên mô hình 3D, được nạp từ máy chủ lịch sử khi có."
        />
        <div className="mt-6 rounded-lg border border-border bg-card/60 p-5">
          {hotspotLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-4 w-2/3" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          ) : hasHotspot ? (
            <div className="flex flex-wrap items-center gap-4">
              <div className="min-w-0 flex-1">
                <p className="text-sm text-foreground/90">
                  Phù điêu này có tọa độ trên mô hình{" "}
                  <span className="font-medium text-foreground">{urnName}</span>.
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {hotspot?.hotspot?.mesh_name || "mesh"}
                  {hotspot?.hotspot?.pos
                    ? ` · tọa độ ${hotspot.hotspot.pos
                        .map((n) => Number(n).toFixed(2))
                        .join(", ")}`
                    : ""}
                </p>
              </div>
              <Link
                href={relief3dHref}
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-ring"
              >
                <Crosshair className="h-4 w-4" aria-hidden="true" />
                Định vị trên đỉnh
              </Link>
            </div>
          ) : (
            <div className="flex flex-wrap items-center gap-4">
              <p className="min-w-0 flex-1 text-sm text-muted-foreground">
                Chưa có tọa độ hotspot cho hình đúc này trên mô hình 3D. Bạn vẫn
                có thể mở trình xem 3D và tìm phù điêu bằng tên.
              </p>
              <Link
                href={relief3dHref}
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-4 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary focus-visible:ring-2 focus-visible:ring-ring"
              >
                <Boxes className="h-4 w-4 text-primary" aria-hidden="true" />
                Mở trình xem 3D
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* Documented facts */}
      <section className="mt-10">
        <SectionHeading
          kicker="Dữ kiện đã xác nhận"
          title="Dữ kiện được nguồn xác nhận"
          lead="Các nhận định đã qua biên tập hoặc chuyên gia xác nhận. Hiện tại có thể chưa có mục nào."
        />
        {documentedClaims.length > 0 ? (
          <div className="mt-6 grid gap-3 lg:grid-cols-2">
            {documentedClaims.map((claim) => (
              <ClaimItem key={String(claim.id)} claim={claim} />
            ))}
          </div>
        ) : (
          <div className="mt-6 rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-10 text-center text-sm text-muted-foreground">
            Chưa có dữ kiện nào được xác nhận cho phù điêu này. Toàn bộ nội dung
            hiện đang trong quá trình rà soát và kiểm chứng nguồn.
          </div>
        )}
      </section>

      {/* Interpretations */}
      <section className="mt-10">
        <SectionHeading
          kicker="Diễn giải / Interpretation"
          title="Diễn giải và ý nghĩa biểu tượng"
          lead="Các diễn giải dưới đây thể hiện cách đọc của các nhà nghiên cứu và truyền thống — chưa được xác nhận là kết luận cuối cùng."
        />
        {interpretationClaims.length > 0 ? (
          <div className="mt-6 grid gap-3 lg:grid-cols-2">
            {interpretationClaims.map((claim) => (
              <ClaimItem key={String(claim.id)} claim={claim} />
            ))}
          </div>
        ) : (
          <div className="mt-6 rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-10 text-center text-sm text-muted-foreground">
            Chưa có diễn giải nào được ghi nhận. Khi có, chúng sẽ xuất hiện tại
            đây cùng với nhãn mức độ kiểm chứng.
          </div>
        )}
      </section>

      {/* Other claims */}
      {otherClaims.length > 0 ? (
        <section className="mt-10">
          <SectionHeading kicker="Nhận định khác" title="Các nhận định còn lại" />
          <div className="mt-6 grid gap-3 lg:grid-cols-2">
            {otherClaims.map((claim) => (
              <ClaimItem key={String(claim.id)} claim={claim} />
            ))}
          </div>
        </section>
      ) : null}

      {/* Geographic relationship */}
      <section className="mt-10">
        <SectionHeading
          kicker="Địa lý"
          title="Mối liên hệ địa lý"
          lead="Các địa danh gắn với phù điêu này trên bản đồ."
        />
        {geographies.length > 0 ? (
          <div className="mt-6 space-y-2">
            {geographies.map((geo) => (
              <div
                key={String(geo.id || geo.entity_id || geo.name)}
                className="flex flex-wrap items-center gap-3 rounded-lg border border-border bg-card/60 px-4 py-3 text-sm"
              >
                <MapIcon className="h-4 w-4 text-primary" aria-hidden="true" />
                <span className="font-medium text-foreground">
                  {geo.name_vi || geo.name || "Địa danh"}
                </span>
                {geo.latitude != null && geo.longitude != null ? (
                  <span className="text-xs text-muted-foreground">
                    {Number(geo.latitude).toFixed(3)},{" "}
                    {Number(geo.longitude).toFixed(3)}
                  </span>
                ) : null}
                <Link
                  href={`/map?entity=${entity.id}`}
                  className="ml-auto inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
                >
                  Xem trên bản đồ
                  <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                </Link>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-6 rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-8 text-center text-sm text-muted-foreground">
            Chưa có dữ liệu địa lý cho phù điêu này.{" "}
            <Link href="/map" className="font-medium text-primary hover:underline">
              Mở bản đồ
            </Link>
            .
          </div>
        )}
      </section>

      {/* Related entities + timeline */}
      <section className="mt-10">
        <SectionHeading
          kicker="Thực thể liên quan"
          title="Kết nối thời gian và thực thể"
          lead="Quan hệ với các thực thể và giai đoạn lịch sử liên quan."
        />
        {relations.length > 0 ? (
          <ul className="mt-6 space-y-2">
            {relations.map((rel) => {
              const href = relationTarget(rel);
              const name = relationObjectName(rel);
              return (
                <li
                  key={String(rel.id || rel.object_entity_id || `${rel.predicate}-${name}`)}
                  className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-card/60 px-4 py-3 text-sm"
                >
                  <Link2 className="h-4 w-4 text-primary" aria-hidden="true" />
                  <span className="text-muted-foreground">
                    {rel.predicate || "Liên quan"}
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
                </li>
              );
            })}
          </ul>
        ) : (
          <div className="mt-6 rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-8 text-center text-sm text-muted-foreground">
            Chưa có kết nối thời gian nào được ghi nhận.
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

      {/* Evidence / sources */}
      <section className="mt-10">
        <SectionHeading
          kicker="Nguồn sử liệu"
          title="Bằng chứng và nguồn"
          lead="Các nguồn gắn với nhận định của phù điêu này."
        />
        {sources.length > 0 ? (
          <div className="mt-6 flex flex-wrap gap-2">
            {sources.map((src) => (
              <Link
                key={String(src.id)}
                href={`/sources/${src.id}`}
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-card/60 px-3 py-2 text-sm transition hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-ring"
              >
                <Library className="h-4 w-4 text-primary" aria-hidden="true" />
                <span className="max-w-[240px] truncate font-medium text-foreground">
                  {src.title || `Nguồn #${src.id}`}
                </span>
              </Link>
            ))}
          </div>
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

      {/* Learning card */}
      <section className="mt-10">
        <div className="heritage-hero flex flex-col items-center gap-5 p-6 text-center md:p-9">
          <BookOpen className="h-8 w-8 text-primary" aria-hidden="true" />
          <h2 className="font-display text-2xl font-bold tracking-tight text-foreground md:text-3xl">
            Học về phù điêu này
          </h2>
          <p className="max-w-2xl text-sm leading-7 text-muted-foreground md:text-base">
            {learnedMotif?.id
              ? "Phù điêu này có bài học tương tác kèm câu hỏi trắc nghiệm."
              : "Tìm hiểu sâu hơn qua bài tập ngắn hoặc quay lại trình xem 3D để quan sát phù điêu trong ngữ cảnh thực tế trên đỉnh."}
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link
              href={learningTarget}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-ring"
            >
              {isAuthed ? "Vào bài học" : "Đăng nhập để học"}
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
            <Link
              href={relief3dHref}
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Boxes className="h-4 w-4" aria-hidden="true" />
              Xem trên đỉnh (3D)
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
