"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

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

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-display font-semibold text-foreground">Khám Phá Cửu Đỉnh</h1>
          <p className="mt-1 text-sm text-muted-foreground">Chọn một Cửu Đỉnh để bắt đầu khám phá họa tiết.</p>
        </div>
      </div>

      {error ? <div className="mt-6 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}

      {loading ? (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(9)].map((_, i) => (
            <div key={i} className="rounded-2xl border bg-card p-5 shadow-sm">
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
              className="group rounded-2xl border bg-card p-5 shadow-sm transition hover:shadow-md"
            >
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

              <div className="mt-4 overflow-hidden rounded-xl bg-muted">
                {urn.thumbnail_url ? (
                  <img src={urn.thumbnail_url} alt={urn.name} className="h-40 w-full object-cover" />
                ) : (
                  <div className="flex h-40 items-center justify-center text-xs text-muted-foreground">
                    Chưa có ảnh thu nhỏ
                  </div>
                )}
              </div>

              <div className="mt-4 text-sm font-medium text-primary group-hover:text-primary/80">Mở Trình Xem →</div>
            </Link>
          ))}
        </div>
      )}

      {!loading && urns.length === 0 && !error ? (
        <div className="mt-6 text-sm text-muted-foreground">Không tìm thấy đỉnh nào. Hãy chạy tập lệnh seed dữ liệu.</div>
      ) : null}
    </main>
  );
}
