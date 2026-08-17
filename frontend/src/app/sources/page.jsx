"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { BookOpen, Library, SlidersHorizontal } from "lucide-react";

import { listHistorySources } from "@/lib/api";
import {
  asSourceList,
  listTotal,
  sourceTypeLabel,
} from "@/lib/history";
import Skeleton from "@/components/Skeleton";
import SectionHeading from "@/components/history/SectionHeading";
import VerificationNote from "@/components/history/VerificationNote";
import { Badge } from "@/components/ui/badge";
import { setPageMeta } from "@/lib/seo";

export default function SourcesPage() {
  const [sources, setSources] = useState([]);
  const [total, setTotal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [typeFilter, setTypeFilter] = useState("");

  useEffect(() => {
    setPageMeta({
      title: "Thư viện nguồn — Lưu Niên Sử Kí",
      description: "Thư viện nguồn tư liệu và bằng chứng liên quan đến Cửu Đỉnh.",
      path: "/sources",
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await listHistorySources({ limit: 100 });
        if (cancelled) return;
        setSources(asSourceList(res));
        setTotal(listTotal(res) ?? asSourceList(res).length);
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

  const typeOptions = useMemo(() => {
    const set = new Set(
      sources.map((s) => s.source_type).filter(Boolean),
    );
    return [...set].sort();
  }, [sources]);

  const filtered = useMemo(
    () =>
      typeFilter
        ? sources.filter((s) => s.source_type === typeFilter)
        : sources,
    [sources, typeFilter],
  );

  return (
    <main className="site-shell">
      <section className="heritage-hero p-6 md:p-9">
        <div className="relative max-w-4xl">
          <div className="heritage-chip">
            <Library className="h-4 w-4" aria-hidden="true" />
            Nguồn sử liệu
          </div>
          <h1 className="mt-5 font-display text-3xl font-bold tracking-tight text-foreground md:text-5xl">
            Thư viện nguồn
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
            Các sách, châu bản, văn khắc và công trình nghiên cứu được dùng làm
            nguồn cho nội dung trên trang. Chúng tôi không bịa thêm bất kỳ mục
            thư mục nào — thông tin nào chưa xác minh sẽ được dán nhãn rõ ràng.
          </p>
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
          Không tải được danh sách nguồn: {error}
        </div>
      ) : null}

      <section className="mt-6 flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="sr-only">Lọc theo loại nguồn</span>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="h-11 rounded-xl border border-border bg-background/45 px-3 text-sm text-foreground outline-none transition focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/25"
          >
            <option value="">Mọi loại nguồn</option>
            {typeOptions.map((t) => (
              <option key={t} value={t}>
                {sourceTypeLabel(t)}
              </option>
            ))}
          </select>
        </label>
        {typeFilter ? (
          <button
            type="button"
            onClick={() => setTypeFilter("")}
            className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-semibold text-muted-foreground transition hover:bg-secondary hover:text-foreground"
          >
            <SlidersHorizontal className="h-4 w-4" aria-hidden="true" />
            Xóa bộ lọc
          </button>
        ) : null}
        <p className="text-xs text-muted-foreground" aria-live="polite">
          {loading
            ? "Đang tải…"
            : `${filtered.length} nguồn${total != null ? ` / ${total} tổng cộng` : ""}.`}
        </p>
      </section>

      {loading ? (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(9)].map((_, i) => (
            <div key={i} className="heritage-card p-5">
              <Skeleton className="h-5 w-2/3" />
              <Skeleton className="mt-3 h-4 w-1/2" />
              <Skeleton className="mt-2 h-4 w-1/3" />
            </div>
          ))}
        </div>
      ) : filtered.length > 0 ? (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((src) => (
            <Link
              key={String(src.id)}
              href={`/sources/${src.id}`}
              className="heritage-card group flex flex-col gap-3 p-5 outline-none transition duration-200 hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-primary"
            >
              <div className="flex items-start justify-between gap-3">
                <h2 className="font-display text-base font-semibold text-foreground">
                  {src.title || `Nguồn #${src.id}`}
                </h2>
                <BookOpen
                  className="h-4 w-4 shrink-0 text-muted-foreground transition group-hover:text-primary"
                  aria-hidden="true"
                />
              </div>
              {src.subtitle ? (
                <p className="text-sm text-muted-foreground">{src.subtitle}</p>
              ) : null}
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">
                  {sourceTypeLabel(src.source_type)}
                </Badge>
                {src.author_text ? (
                  <span className="text-xs text-muted-foreground">
                    {src.author_text}
                  </span>
                ) : null}
                {src.publication_year ? (
                  <span className="text-xs text-muted-foreground">
                    · {String(src.publication_year)}
                  </span>
                ) : null}
              </div>
              <p className="mt-auto line-clamp-2 text-sm leading-6 text-muted-foreground">
                {src.title
                  ? `Nguồn: ${src.title}`
                  : "Thông tin thư mục đang được hoàn thiện."}
              </p>
            </Link>
          ))}
        </div>
      ) : (
        <div className="mt-6">
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-14 text-center">
            <Library className="mb-3 h-8 w-8 text-muted-foreground" aria-hidden="true" />
            <h2 className="font-display text-base font-semibold text-foreground">
              Chưa có nguồn nào
            </h2>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">
              {typeFilter
                ? "Không có nguồn nào thuộc loại này. Thử chọn loại khác."
                : "Chưa có nguồn nào được nạp từ máy chủ lịch sử."}
            </p>
          </div>
        </div>
      )}
    </main>
  );
}
