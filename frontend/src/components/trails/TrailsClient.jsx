"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listTrails } from "@/lib/api";

export default function TrailsClient() {
  const [trails, setTrails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    listTrails({ page: 1, perPage: 20 })
      .then((data) => {
        if (!mounted) return;
        setTrails(Array.isArray(data?.trails) ? data.trails : []);
        setLoading(false);
      })
      .catch((err) => {
        if (!mounted) return;
        setError(err?.message || "Không tải được danh sách lộ trình");
        setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="px-6 py-12 text-sm text-muted-foreground" role="status">
        Đang tải lộ trình…
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="px-6 py-12 text-sm text-destructive"
        role="alert"
        aria-live="assertive"
      >
        {error}
      </div>
    );
  }

  if (trails.length === 0) {
    return (
      <div className="px-6 py-12 text-sm text-muted-foreground">
        Chưa có lộ trình nào được công bố.
      </div>
    );
  }

  return (
    <ul className="grid grid-cols-1 gap-4 px-6 py-8 sm:grid-cols-2 lg:grid-cols-3">
      {trails.map((t) => (
        <li
          key={t.id}
          className="rounded-lg border border-border bg-card p-5 shadow-sm transition hover:shadow-md"
        >
          <Link
            href={`/trails/${encodeURIComponent(t.slug)}`}
            className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <h2 className="text-lg font-semibold">{t.title_vi}</h2>
            <p className="mt-1 text-xs uppercase tracking-wide text-muted-foreground">
              {t.difficulty} · {t.estimated_minutes} phút · {t.step_count} bước
            </p>
            {t.description_vi ? (
              <p className="mt-3 line-clamp-3 text-sm text-muted-foreground">
                {t.description_vi}
              </p>
            ) : null}
          </Link>
        </li>
      ))}
    </ul>
  );
}
