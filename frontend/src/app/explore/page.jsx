"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowUpRight, Layers, Trophy } from "lucide-react";

import { getUrns } from "@/lib/api";
import Skeleton from "@/components/Skeleton";

export default function ExplorePage() {
  const [urns, setUrns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await getUrns();
        if (!cancelled) setUrns(res || []);
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
  }, []);

  const summary = urns.reduce(
    (acc, urn) => {
      acc.totalMotifs += urn.motif_count ?? 0;
      if (urn.is_demo) acc.demoCount += 1;
      return acc;
    },
    { totalMotifs: 0, demoCount: 0 },
  );

  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl px-5 pb-28 pt-8 md:px-7 md:pt-10">
      <section
        data-testid="explore-hero"
        className="relative overflow-hidden rounded-3xl border border-border/60 bg-card/70 p-6 shadow-[0_18px_50px_-22px_hsl(0_0%_0%_/_0.45)] backdrop-blur-xl md:p-8"
      >
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_80%_10%,hsl(var(--primary)/0.16),transparent_45%)]" />
        <div className="relative flex flex-wrap items-start justify-between gap-5">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-primary">
              Hành Trình Di Sản
            </div>
            <h1
              data-testid="explore-title"
              className="mt-4 font-display text-3xl font-bold tracking-tight text-foreground md:text-4xl"
            >
              Khám Phá Cửu Đỉnh
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground md:text-base">
              Chọn một đỉnh để bước vào lớp học 3D, theo dõi tiến độ họa tiết,
              và tiếp tục hành trình học theo nhịp cá nhân.
            </p>
          </div>

          <div className="grid w-full max-w-md grid-cols-3 gap-2 text-xs sm:text-sm">
            <div className="rounded-2xl border border-border/60 bg-background/80 px-3 py-3">
              <div className="text-muted-foreground">Số Đỉnh</div>
              <div className="mt-1 font-display text-lg font-semibold text-foreground">
                {loading ? "…" : urns.length}
              </div>
            </div>
            <div className="rounded-2xl border border-border/60 bg-background/80 px-3 py-3">
              <div className="text-muted-foreground">Họa Tiết</div>
              <div className="mt-1 font-display text-lg font-semibold text-foreground">
                {loading ? "…" : summary.totalMotifs}
              </div>
            </div>
            <div className="rounded-2xl border border-border/60 bg-background/80 px-3 py-3">
              <div className="text-muted-foreground">Bản Mẫu</div>
              <div className="mt-1 font-display text-lg font-semibold text-foreground">
                {loading ? "…" : summary.demoCount}
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="mt-4 flex flex-wrap gap-2 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1 rounded-full border border-border/60 bg-background/70 px-3 py-1.5">
          <Layers className="h-3.5 w-3.5 text-info" />
          Khám phá, học, thành thạo theo từng đỉnh
        </span>
        <span className="inline-flex items-center gap-1 rounded-full border border-border/60 bg-background/70 px-3 py-1.5">
          <Trophy className="h-3.5 w-3.5 text-primary" />
          Ưu tiên đỉnh đang có tiến độ
        </span>
      </div>

      {error ? (
        <div className="mt-6 rounded-2xl border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      {loading ? (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(9)].map((_, i) => (
            <div
              key={i}
              data-testid="urn-skeleton"
              className="rounded-3xl border border-border/70 bg-card/70 p-5 shadow-sm backdrop-blur-xl"
            >
              <div className="flex justify-between gap-3">
                <div className="w-2/3">
                  <Skeleton className="h-6 w-3/4" />
                  <Skeleton className="mt-2 h-3 w-1/2" />
                </div>
                <Skeleton className="h-6 w-12 rounded-full" />
              </div>
              <Skeleton className="mt-4 h-40 w-full rounded-xl" />
              <Skeleton className="mt-4 h-4 w-1/3" />
            </div>
          ))}
        </div>
      ) : (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {urns.map((urn) => (
            <Link
              key={urn.id}
              href={`/urns/${urn.slug}`}
              data-testid="urn-card"
              className="group relative overflow-hidden rounded-3xl border border-border/70 bg-card/65 p-4 shadow-[0_10px_24px_-14px_rgba(0,0,0,0.6)] backdrop-blur-xl transition duration-300 hover:-translate-y-1 hover:border-primary/45 hover:shadow-[0_14px_28px_-12px_hsl(var(--primary)/0.35)]"
            >
              <div className="pointer-events-none absolute inset-0 opacity-0 transition group-hover:opacity-100">
                <div className="absolute -right-10 -top-10 h-28 w-28 rounded-full bg-primary/15 blur-2xl" />
              </div>

              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="truncate text-lg font-display font-semibold text-foreground">{urn.name}</div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    Họa Tiết: <span className="font-display tabular-nums">{urn.motif_count ?? 0}</span> · Thứ Tự:{" "}
                    <span className="font-display tabular-nums">{urn.display_order ?? "—"}</span>
                  </div>
                </div>
                {urn.is_demo ? (
                  <span className="shrink-0 rounded-full bg-success/20 px-2 py-1 text-xs font-medium text-success">
                    Bản Mẫu
                  </span>
                ) : null}
              </div>

              <div className="mt-4 overflow-hidden rounded-2xl border border-border/50 bg-muted/70">
                {urn.thumbnail_url ? (
                  <img src={urn.thumbnail_url} alt={urn.name} className="h-40 w-full object-cover" />
                ) : (
                  <div className="flex h-40 items-center justify-center text-xs text-muted-foreground">
                    Chưa có ảnh thu nhỏ
                  </div>
                )}
              </div>

              <div className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-primary group-hover:text-primary/85">
                Mở Trình Xem
                <ArrowUpRight className="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
              </div>
            </Link>
          ))}
        </div>
      )}

      {!loading && urns.length === 0 && !error ? (
        <div className="mt-6 rounded-2xl border border-border/60 bg-card/60 p-4 text-sm text-muted-foreground">
          Không tìm thấy đỉnh nào. Hãy chạy tập lệnh seed dữ liệu.
        </div>
      ) : null}
    </main>
  );
}
