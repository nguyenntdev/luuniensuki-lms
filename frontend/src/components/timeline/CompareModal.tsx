"use client";

import { useEffect, useRef, useState } from "react";
import { compareMotifs, logAnalyticsEvent } from "@/lib/api";

/** A lightweight motif reference (id may be null when prompting for a pick). */
export interface CompareMotifRef {
  id: string | number | null;
  name: string;
  [key: string]: unknown;
}

interface CompareEra {
  id: string | number;
  name_vi?: string;
  color_hex?: string | null;
}

/** Full motif record returned by the compare endpoint. */
interface CompareMotifFull {
  id: string | number;
  name: string;
  name_en?: string | null;
  description?: string | null;
  thumbnail_url?: string | null;
  category?: string | null;
  rarity?: string | null;
  eras?: CompareEra[];
  urn?: { name?: string } | null;
}

/** Response payload of `GET /api/v1/motifs/compare`. */
interface CompareData {
  motifs?: CompareMotifFull[];
  comparison_axes?: string[];
}

interface CompareModalProps {
  motifA: CompareMotifRef;
  motifB: CompareMotifRef;
  onClose: () => void;
}

/**
 * Side-by-side motif comparison modal.
 *
 * Props:
 * - `motifA` / `motifB`: objects with at least `{ id, name }`.
 * - `onClose`: callback to dismiss the modal.
 *
 * Fetches full comparison data from `GET /api/v1/motifs/compare?ids=A,B`.
 * Accessible: focus trap, Escape to close, aria-modal.
 */
export default function CompareModal({ motifA, motifB, onClose }: CompareModalProps) {
  const [data, setData] = useState<CompareData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const closeRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (!motifA?.id || !motifB?.id) return;
    let mounted = true;
    setLoading(true);
    compareMotifs(motifA.id, motifB.id)
      .then((res) => {
        if (!mounted) return;
        setData(res as CompareData);
        setLoading(false);
        try {
          logAnalyticsEvent({
            name: "compare_opened",
            payload: { motif_ids: [motifA.id, motifB.id] },
          });
        } catch {
          // best-effort
        }
      })
      .catch((err) => {
        if (!mounted) return;
        setError((err as { message?: string })?.message || "Không tải được so sánh");
        setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [motifA?.id, motifB?.id]);

  // Focus trap + Escape
  useEffect(() => {
    closeRef.current?.focus();
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="compare-heading"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="relative max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-xl border border-border bg-card p-6 shadow-xl">
        <div className="flex items-center justify-between">
          <h2
            id="compare-heading"
            className="text-xl font-bold tracking-tight"
          >
            So sánh hoạ tiết
          </h2>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            aria-label="Đóng"
            className="rounded-md border border-border px-3 py-1 text-sm hover:bg-muted focus-visible:ring-2 focus-visible:ring-primary"
          >
            Đóng
          </button>
        </div>

        {loading ? (
          <p className="mt-6 text-sm text-muted-foreground" role="status">
            Đang tải…
          </p>
        ) : error ? (
          <p className="mt-6 text-sm text-destructive" role="alert">
            {error}
          </p>
        ) : data ? (
          <CompareContent data={data} />
        ) : null}
      </div>
    </div>
  );
}

function CompareContent({ data }: { data: CompareData }) {
  const { motifs, comparison_axes } = data;
  if (!motifs || motifs.length < 2) return null;
  const [a, b] = motifs;

  return (
    <div className="mt-6">
      {/* Axes summary */}
      {(comparison_axes?.length ?? 0) > 0 ? (
        <p className="mb-4 text-xs text-muted-foreground">
          Trục so sánh: {comparison_axes?.join(", ")}
        </p>
      ) : null}

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <MotifCard motif={a} />
        <MotifCard motif={b} />
      </div>

      {/* Comparison table */}
      <table className="mt-6 w-full text-sm" aria-label="Bảng so sánh">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase text-muted-foreground">
            <th className="py-2 pr-4">Thuộc tính</th>
            <th className="py-2 pr-4">{a.name}</th>
            <th className="py-2">{b.name}</th>
          </tr>
        </thead>
        <tbody>
          {(comparison_axes || []).map((axis: string) => (
            <tr key={axis} className="border-b border-border/50">
              <td className="py-2 pr-4 font-medium capitalize">{axis}</td>
              <td className="py-2 pr-4">{renderAxis(a, axis)}</td>
              <td className="py-2">{renderAxis(b, axis)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MotifCard({ motif }: { motif: CompareMotifFull }) {
  return (
    <div className="rounded-lg border border-border p-4">
      {motif.thumbnail_url ? (
        <img
          src={motif.thumbnail_url}
          alt={motif.name}
          className="mb-3 h-32 w-full rounded-md object-cover"
        />
      ) : (
        <div className="mb-3 flex h-32 items-center justify-center rounded-md bg-muted text-xs text-muted-foreground">
          Không có ảnh
        </div>
      )}
      <h3 className="text-lg font-semibold">{motif.name}</h3>
      {motif.name_en ? (
        <p className="text-xs text-muted-foreground">{motif.name_en}</p>
      ) : null}
      {motif.description ? (
        <p className="mt-2 line-clamp-3 text-sm text-muted-foreground">
          {motif.description}
        </p>
      ) : null}
      {(motif.eras?.length ?? 0) > 0 ? (
        <div className="mt-2 flex flex-wrap gap-1">
          {motif.eras?.map((era) => (
            <span
              key={era.id}
              className="rounded-full px-2 py-0.5 text-[10px] font-medium text-white"
              style={{ backgroundColor: era.color_hex || "#666" }}
            >
              {era.name_vi}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function renderAxis(motif: CompareMotifFull, axis: string) {
  switch (axis) {
    case "category":
      return motif.category || "—";
    case "rarity":
      return motif.rarity || "—";
    case "era":
      return motif.eras?.map((e) => e.name_vi).join(", ") || "—";
    case "urn":
      return motif.urn?.name || "—";
    default:
      return "—";
  }
}
