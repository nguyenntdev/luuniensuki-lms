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
    <main className="site-shell">
      <section
        data-testid="explore-hero"
        className="heritage-hero md:p-6"
      >
        <div className="relative flex flex-wrap items-start justify-between gap-5">
          <div className="max-w-2xl">
            <div className="heritage-chip">
              Hành trình di sản
            </div>
            <h1
              data-testid="explore-title"
              className="mt-4 font-display text-3xl font-bold tracking-tight text-foreground md:text-4xl"
            >
              Khám phá Cửu Đỉnh
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground md:text-base">
              Chọn một đỉnh để bước vào lớp học 3D, theo dõi tiến độ họa tiết,
              và tiếp tục hành trình học theo nhịp cá nhân.
            </p>
          </div>

          <div className="grid w-full max-w-lg grid-cols-3 gap-2 text-xs sm:text-sm">
            <div className="heritage-stat px-3 py-3">
              <div className="text-muted-foreground">Số đỉnh</div>
              <div className="mt-1 font-display text-lg font-semibold text-foreground">
                {loading ? "…" : urns.length}
              </div>
            </div>
            <div className="heritage-stat px-3 py-3">
              <div className="text-muted-foreground">Họa tiết</div>
              <div className="mt-1 font-display text-lg font-semibold text-foreground">
                {loading ? "…" : summary.totalMotifs}
              </div>
            </div>
            <div className="heritage-stat px-3 py-3">
              <div className="text-muted-foreground">Bản mẫu</div>
              <div className="mt-1 font-display text-lg font-semibold text-foreground">
                {loading ? "…" : summary.demoCount}
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="mt-4 flex flex-wrap gap-2 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1 rounded-lg border border-border/60 bg-background/70 px-3 py-1.5">
          <Layers className="h-3.5 w-3.5 text-info" />
          Khám phá, học, thành thạo theo từng đỉnh
        </span>
        <span className="inline-flex items-center gap-1 rounded-lg border border-border/60 bg-background/70 px-3 py-1.5">
          <Trophy className="h-3.5 w-3.5 text-primary" />
          Ưu tiên đỉnh đang có tiến độ
        </span>
      </div>

      {error ? (
        <div className="mt-6 rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      {loading ? (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {[...Array(9)].map((_, i) => (
            <div
              key={i}
              data-testid="urn-skeleton"
              className="heritage-card p-5"
            >
              <div className="relative">
              <div className="flex justify-between gap-3">
                <div className="w-2/3">
                  <Skeleton className="h-6 w-3/4" />
                  <Skeleton className="mt-2 h-3 w-1/2" />
                </div>
                <Skeleton className="h-6 w-12 rounded-full" />
              </div>
              <Skeleton className="mt-4 h-36 w-full rounded-lg" />
              <Skeleton className="mt-4 h-4 w-1/3" />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {urns.map((urn) => {
            const total = urn.motif_count ?? 0;
            const mastered = urn.mastered_count ?? 0;
            const learned = urn.learned_count ?? 0;
            const discovered = urn.discovered_count ?? 0;
            const pct = total ? Math.round((mastered / total) * 100) : 0;
            const has3d = Boolean(urn.model_url);
            const started = discovered + learned + mastered > 0;
            return (
              <Link
                key={urn.id}
                href={`/urns/${urn.slug}`}
                data-testid="urn-card"
                className="heritage-card group hover-lift p-4 outline-none transition duration-200 hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-primary"
              >
                <div className="relative">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="truncate text-lg font-display font-semibold text-foreground">{urn.name}</div>
                      <div className="mt-1 text-xs text-muted-foreground">
                        Họa tiết: <span className="font-display tabular-nums">{total}</span>
                        {started ? (
                          <> · <span className="font-display tabular-nums">{pct}%</span> thành thạo</>
                        ) : (
                          <> · Chưa bắt đầu</>
                        )}
                      </div>
                    </div>
                    <div className="flex shrink-0 flex-col items-end gap-1">
                      {has3d ? (
                        <span className="rounded-md bg-primary/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-primary ring-1 ring-primary/30">
                          3D
                        </span>
                      ) : null}
                      {urn.is_demo ? (
                        <span className="rounded-md bg-success/20 px-2 py-0.5 text-[10px] font-medium text-success">
                          Bản mẫu
                        </span>
                      ) : null}
                    </div>
                  </div>

                  <div className="mt-4 overflow-hidden rounded-lg border border-border/50 bg-muted/70">
                    {urn.thumbnail_url ? (
                      <img
                        src={urn.thumbnail_url}
                        alt={urn.name}
                        loading="lazy"
                        decoding="async"
                        className="h-36 w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
                      />
                    ) : (
                      <div className="flex h-36 items-center justify-center text-xs text-muted-foreground">
                        Chưa có ảnh thu nhỏ
                      </div>
                    )}
                  </div>

                  {/* Progress */}
                  <div className="mt-4">
                    <div className="progress-track">
                      <div className="progress-fill" style={{ width: `${pct}%` }} />
                    </div>
                    <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
                      <span className="inline-flex items-center gap-1">
                        <span className="h-1.5 w-1.5 rounded-full bg-info" /> {discovered} khám phá
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <span className="h-1.5 w-1.5 rounded-full bg-warning" /> {learned} đã học
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <span className="h-1.5 w-1.5 rounded-full bg-success" /> {mastered} thành thạo
                      </span>
                    </div>
                  </div>

                  <div className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-primary group-hover:text-primary/85">
                    {started ? "Tiếp tục học" : "Mở trình xem"}
                    <ArrowUpRight className="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}

      {!loading && urns.length === 0 && !error ? (
        <div className="mt-6 rounded-lg border border-border/60 bg-card/60 p-4 text-sm text-muted-foreground">
          Không tìm thấy đỉnh nào. Hãy chạy tập lệnh seed dữ liệu.
        </div>
      ) : null}
    </main>
  );
}
