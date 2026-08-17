"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  Boxes,
  GitCompareArrows,
  Landmark,
  Library,
  Link2,
  Map as MapIcon,
  ScrollText,
} from "lucide-react";

import {
  getHistoryEntityBySlug,
  getHistoryEntityGeography,
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
  publicationStatusLabel,
  relationObjectName,
  urnNameFromSlug,
  urnSlugFromReliefSlug,
} from "@/lib/history";
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

export default function ReliefDetailPage() {
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
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
  const effectiveUrnSlug = entity.urn_slug || urnSlug || urnSlugFromReliefSlug(entity.slug);
  const urnName = urnNameFromSlug(effectiveUrnSlug);
  const compareIds = [entity.id, ...relatedIds.slice(0, 2)].filter(Boolean);
  const compareHref = `/compare?entities=${compareIds.join(",")}`;

  return (
    <main className="site-shell">
      {/* Identity header */}
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

          <div className="mt-5 flex flex-wrap gap-2">
            <Badge variant="outline">Đỉnh: {urnName}</Badge>
            {reliefSlug ? (
              <Badge variant="secondary">Vị trí: {reliefSlug}</Badge>
            ) : null}
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href={`/cuu-dinh/${effectiveUrnSlug}`}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
            >
              <Boxes className="h-4 w-4" aria-hidden="true" />
              Xem trên đỉnh {urnName} (3D)
            </Link>
            <Link
              href={compareHref}
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary"
            >
              <GitCompareArrows className="h-4 w-4 text-primary" aria-hidden="true" />
              So sánh
            </Link>
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

      {/* Timeline relationship */}
      <section className="mt-10">
        <SectionHeading
          kicker="Dòng thời gian"
          title="Kết nối thời gian"
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
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-card/60 px-3 py-2 text-sm transition hover:border-primary/40"
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

      {/* Practice CTA */}
      <section className="mt-10">
        <div className="heritage-hero flex flex-col items-center gap-5 p-6 text-center md:p-9">
          <h2 className="font-display text-2xl font-bold tracking-tight text-foreground md:text-3xl">
            Củng cố hiểu biết về phù điêu này
          </h2>
          <p className="max-w-2xl text-sm leading-7 text-muted-foreground md:text-base">
            Thử sức với bài tập ngắn hoặc quay lại trình xem 3D để quan sát phù
            điêu trong ngữ cảnh thực tế trên đỉnh.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link
              href="/practice"
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
            >
              Vào luyện tập
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
            <Link
              href={`/cuu-dinh/${effectiveUrnSlug}`}
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary"
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