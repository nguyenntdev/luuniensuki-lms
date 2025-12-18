"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getLeaderboard } from "@/lib/api";
import Skeleton from "@/components/Skeleton";

export default function LeaderboardPage() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await getLeaderboard({ limit: 50 });
        if (!cancelled) setEntries(res || []);
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
    <main className="mx-auto max-w-4xl px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-display font-semibold text-foreground">Bảng Xếp Hạng</h1>
          <p className="mt-1 text-sm text-muted-foreground">Những nhà khám phá hàng đầu theo XP.</p>
        </div>
      </div>

      {error ? <div className="mt-6 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}

      <div className="mt-8 overflow-hidden rounded-2xl border border-border bg-card">
        <table className="w-full text-left text-sm">
          <thead className="bg-muted text-xs text-muted-foreground">
            <tr>
              <th className="px-4 py-3">Hạng</th>
              <th className="px-4 py-3">Nhà Khám Phá</th>
              <th className="px-4 py-3">Danh Hiệu</th>
              <th className="px-4 py-3 text-right">XP</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              [...Array(10)].map((_, i) => (
                <tr key={i} className="border-t border-border">
                  <td className="px-4 py-3">
                    <Skeleton className="h-4 w-6" />
                  </td>
                  <td className="px-4 py-3">
                    <Skeleton className="h-4 w-32" />
                  </td>
                  <td className="px-4 py-3">
                    <Skeleton className="h-4 w-24" />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Skeleton className="ml-auto h-4 w-12" />
                  </td>
                </tr>
              ))
            ) : (
              <>
                {entries.map((e) => (
                  <tr key={e.user_id} className="border-t border-border">
                    <td className="px-4 py-3 font-display tabular-nums text-xs text-muted-foreground">{e.rank}</td>
                    <td className="px-4 py-3 font-medium text-foreground">{e.display_name}</td>
                    <td className="px-4 py-3 text-muted-foreground">{e.title}</td>
                    <td className="px-4 py-3 text-right font-display tabular-nums font-semibold text-primary">{e.total_xp}</td>
                  </tr>
                ))}
                {entries.length === 0 ? (
                  <tr>
                    <td className="px-4 py-6 text-center text-sm text-muted-foreground" colSpan={4}>
                      Chưa có dữ liệu.
                    </td>
                  </tr>
                ) : null}
              </>
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}
