"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { useEffect, useMemo } from "react";

import { useAuthStore } from "@/stores/authStore";
import { useMotifStore } from "@/stores/motifStore";

const UrnViewer = dynamic(() => import("@/components/UrnViewer"), {
  ssr: false,
  loading: () => (
    <div className="absolute inset-0 flex items-center justify-center bg-black text-sm text-white/70">
      Đang Tải Trình Xem 3D…
    </div>
  ),
});

export default function UrnExperience({ urnSlug }) {
  const token = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const fetchMe = useAuthStore((s) => s.fetchMe);

  const ensureMotifsLoaded = useMotifStore((s) => s.ensureMotifsLoaded);
  const motifsById = useMotifStore((s) => s.motifsById);
  const loadingMotifs = useMotifStore((s) => s.loadingMotifs);

  useEffect(() => {
    if (token) fetchMe();
  }, [token, fetchMe]);

  useEffect(() => {
    if (!urnSlug) return;
    ensureMotifsLoaded(urnSlug);
  }, [urnSlug, ensureMotifsLoaded]);

  const discoveredCount = useMotifStore((s) => {
    const motifs = s.motifsById || {};
    const found = s.foundByMotifId || {};
    let count = 0;
    for (const motifId of Object.keys(motifs)) {
      if (found[motifId]) count += 1;
    }
    return count;
  });

  const urnMotifProgress = useMemo(() => {
    const total = Object.keys(motifsById || {}).length;
    const discovered = Math.min(discoveredCount, total);
    const percent = total ? Math.max(0, Math.min(100, (discovered / total) * 100)) : 0;

    return { discovered, total, percent };
  }, [discoveredCount, motifsById]);

  const totalLabel =
    urnMotifProgress.total > 0 ? String(urnMotifProgress.total) : loadingMotifs ? "…" : "0";
  const barWidth = urnMotifProgress.total
    ? `${urnMotifProgress.percent}%`
    : loadingMotifs
      ? "35%"
      : "0%";

  return (
    <div className="fixed inset-0 w-full overflow-hidden bg-black">
      <div className="pointer-events-none absolute left-0 top-0 z-10 w-full px-4 py-3 text-white">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="pointer-events-auto flex items-center gap-3">
            <Link href="/" className="rounded-md bg-white/10 px-3 py-2 text-sm hover:bg-white/15">
              Trang Chủ
            </Link>
            <Link href="/profile" className="rounded-md bg-white/10 px-3 py-2 text-sm hover:bg-white/15">
              Bảng Điều Khiển
            </Link>
          </div>

          <div className="flex flex-wrap items-center justify-end gap-3 text-sm">
            <div className="rounded-md bg-white/10 px-3 py-2">
              Đỉnh: <span className="font-mono">{urnSlug}</span>
            </div>
            <div className="rounded-md bg-white/10 px-3 py-2">
              {user?.display_name || (token ? "Đang Tải…" : "Khách")}
            </div>
          </div>
        </div>

        <div className="mt-3 flex w-full justify-center">
          <div className="pointer-events-none w-full max-w-md rounded-xl border border-white/10 bg-black/30 px-4 py-3 backdrop-blur-sm">
            <div className="text-sm text-white/90">
              Đã khám phá:{" "}
              <span className="font-display tabular-nums">{urnMotifProgress.discovered}</span>/
              <span className="font-display tabular-nums">{totalLabel}</span> họa tiết
            </div>
            <div className="mt-2 h-2.5 w-full overflow-hidden rounded-full bg-white/15">
              <div
                className={[
                  "h-full rounded-full bg-primary transition-[width] duration-500 ease-out",
                  "shadow-[0_0_10px_rgba(var(--primary),0.35)]",
                  loadingMotifs && urnMotifProgress.total === 0 ? "animate-pulse" : "",
                ].join(" ")}
                style={{ width: barWidth }}
                role="progressbar"
                aria-label="Tiến độ khám phá họa tiết"
                aria-valuenow={urnMotifProgress.discovered}
                aria-valuemin={0}
                aria-valuemax={urnMotifProgress.total || undefined}
              />
            </div>
          </div>
        </div>
      </div>

      <UrnViewer urnSlug={urnSlug} userId={user?.id || null} className="absolute inset-0" />
    </div>
  );
}
