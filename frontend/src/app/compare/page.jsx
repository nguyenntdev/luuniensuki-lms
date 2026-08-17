"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { ArrowRight, GitCompare } from "lucide-react";

import { getHistoryEntityById } from "@/lib/api";
import { setPageMeta } from "@/lib/seo";
import { entityName, entityTypeLabel } from "@/lib/history";
import Skeleton from "@/components/Skeleton";
import SectionHeading from "@/components/history/SectionHeading";
import VerificationNote from "@/components/history/VerificationNote";

function entityHref(e) {
  if (!e) return "#";
  if (e.entity_type === "urn") return `/cuu-dinh/${e.slug}`;
  if (e.entity_type === "relief") {
    const urn = e.slug.split("-").slice(0, 2).join("-");
    return `/atlas/${urn}/${e.slug}`;
  }
  if (e.entity_type === "source") return `/sources/${e.slug}`;
  return `/explore/connections?entity=${e.id}`;
}

export default function ComparePage() {
  const searchParams = useSearchParams();
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const ids = useMemo(() => {
    const raw = searchParams?.get("entities") || "";
    return raw.split(",").map((s) => s.trim()).filter(Boolean).slice(0, 4);
  }, [searchParams]);

  useEffect(() => {
    setPageMeta({
      title: "So sánh — Lưu Niên Sử Kí",
      description: "So sánh các đỉnh và phù điêu trên Cửu Đỉnh.",
      path: "/compare",
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      setEntities([]);
      try {
        const results = await Promise.all(
          ids.map((id) => getHistoryEntityById(id).catch(() => null)),
        );
        if (cancelled) return;
        setEntities(results.filter(Boolean));
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    if (ids.length >= 2) load();
    else {
      setLoading(false);
      setEntities([]);
    }
    return () => {
      cancelled = true;
    };
  }, [ids]);

  return (
    <main className="site-shell">
      <section className="heritage-hero p-6 md:p-9">
        <div className="relative max-w-4xl">
          <div className="heritage-chip">
            <GitCompare className="h-4 w-4" aria-hidden="true" />
            So sánh
          </div>
          <h1 className="mt-5 font-display text-3xl font-bold tracking-tight text-foreground md:text-5xl">
            So sánh các thực thể
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
            Đối chiếu hai đến bốn đỉnh hoặc phù điêu cạnh nhau dựa trên dữ liệu
            được kiểm chứng. Truy cập qua “So sánh” trên trang phù điêu hoặc dùng
            đường dẫn <code className="rounded bg-secondary px-1">/compare?entities=id1,id2</code>.
          </p>
        </div>
      </section>

      <div className="mt-5">
        <VerificationNote />
      </div>

      {error ? (
        <div role="alert" className="mt-5 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          Không tải được dữ liệu so sánh: {error}
        </div>
      ) : null}

      {loading ? (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="heritage-card p-6">
              <Skeleton className="h-6 w-1/2" />
              <Skeleton className="mt-4 h-24 w-full" />
            </div>
          ))}
        </div>
      ) : entities.length < 2 ? (
        <div className="mt-6 rounded-xl border border-dashed border-border/70 bg-card/45 p-10 text-center text-sm text-muted-foreground">
          Chọn ít nhất hai thực thể để so sánh (bằng cách dùng nút “So sánh” trên
          các trang phù điêu, hoặc đường dẫn <code>/compare?entities=id1,id2</code>).
          <div className="mt-4">
            <Link href="/atlas" className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground">
              Mở Atlas
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>
        </div>
      ) : (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {entities.map((e) => (
            <div key={e.id} className="heritage-card p-6">
              <div className="flex items-center justify-between gap-2">
                <h2 className="font-display text-lg font-semibold text-foreground">
                  {entityName(e)}
                </h2>
                <span className="rounded-full border border-border bg-secondary/50 px-2.5 py-0.5 text-[11px] uppercase tracking-wide text-muted-foreground">
                  {entityTypeLabel(e.entity_type)}
                </span>
              </div>
              {e.summary_vi ? (
                <p className="mt-3 text-sm leading-6 text-muted-foreground">{e.summary_vi}</p>
              ) : (
                <p className="mt-3 text-sm text-muted-foreground/70">
                  Chưa có tóm tắt đã kiểm chứng.
                </p>
              )}
              <div className="mt-4">
                <Link href={entityHref(e)} className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline">
                  Xem chi tiết
                  <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
