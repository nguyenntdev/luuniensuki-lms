"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  MapPin,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  List,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { setPageMeta } from "@/lib/seo";

interface MapItem {
  entity_id: string;
  entity_type: string;
  slug: string;
  name: string;
  lat: number | null;
  lng: number | null;
  geo_precision: string | null;
  mapping_status: string | null;
  related_reliefs: string[];
  urns: string[];
}

const PRECISION_LABELS: Record<string, string> = {
  exact: "Vị trí chính xác",
  approximate: "Vị trí gần đúng",
  settlement: "Cấp điểm dân cư",
  region: "Cấp vùng",
  water_body: "Thủy vực",
  historical_boundary: "Ranh giới lịch sử",
  modern_correspondence: "Tương ứng hiện đại",
  unknown: "Chưa xác định",
};

const STATUS_LABELS: Record<string, string> = {
  verified: "Đã kiểm chứng",
  probable: "Có thể",
  disputed: "Có tranh luận",
  unknown: "Chưa rõ",
};

function precisionIcon(precision: string | null) {
  switch (precision) {
    case "exact":
      return CheckCircle2;
    case "approximate":
    case "settlement":
    case "region":
    case "water_body":
      return AlertCircle;
    default:
      return HelpCircle;
  }
}

function MapView({
  items,
  selectedId,
  onSelect,
}: {
  items: MapItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const [L, setL] = useState<typeof import("leaflet") | null>(null);
  const [container, setContainer] = useState<HTMLDivElement | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    import("leaflet").then((mod) => {
      setL(mod.default ?? mod);
    }).catch(() => setFailed(true));
  }, []);

  useEffect(() => {
    if (!L || !container || items.length === 0) return;
    const map = L.map(container, {
      center: [16.4, 107.5],
      zoom: 6,
      scrollWheelZoom: true,
    });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 18,
    }).addTo(map);

    const markers: Array<import("leaflet").CircleMarker> = [];
    for (const item of items) {
      if (item.lat == null || item.lng == null) continue;
      const exact = item.geo_precision === "exact";
      const radius = exact ? undefined : 24000;
      if (radius) {
        L.circle([item.lat, item.lng], {
          radius,
          color: "#b8860b",
          weight: 1,
          fillOpacity: 0.12,
        }).addTo(map);
      }
      const marker = L.circleMarker([item.lat, item.lng], {
        radius: exact ? 7 : 5,
        color: exact ? "#2f6f4f" : "#b8860b",
        fillColor: exact ? "#318265" : "#d9a521",
        fillOpacity: 0.9,
        weight: 1.5,
      })
        .addTo(map)
        .bindTooltip(
          `${item.name}${exact ? "" : " (vị trí gần đúng)"}`,
          { direction: "top" },
        )
        .on("click", () => onSelect(item.entity_id));
      markers.push(marker);
    }
    if (markers.length > 0) {
      const group = L.featureGroup(markers);
      map.fitBounds(group.getBounds().pad(0.25));
    }
    return () => {
      map.remove();
    };
  }, [L, container, items, onSelect]);

  if (failed) {
    return (
      <div className="flex h-[420px] items-center justify-center rounded-xl border border-border bg-secondary/30 text-sm text-muted-foreground">
        Không tải được bản đồ. Vui lòng dùng danh sách bên dưới.
      </div>
    );
  }

  return (
    <div
      ref={setContainer}
      className="h-[420px] w-full overflow-hidden rounded-xl border border-border md:h-[560px]"
      role="application"
      aria-label="Bản đồ di sản Cửu Đỉnh"
    />
  );
}

export default function MapPage() {
  const [items, setItems] = useState<MapItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [entityType, setEntityType] = useState<string>("");
  const [showList, setShowList] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const params = new URLSearchParams();
    if (entityType) params.set("entity_type", entityType);
    fetch(`/api/v1/history/map?${params.toString()}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: { items: MapItem[] }) => {
        if (cancelled) return;
        setItems(data.items ?? []);
        setError(null);
      })
      .catch(() => {
        if (!cancelled) setError("Không tải được dữ liệu bản đồ.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [entityType]);

  useEffect(() => {
    setPageMeta({
      title: "Bản đồ di sản — Lưu Niên Sử Kí",
      description: "Khám phá các địa danh và mối liên hệ địa lý của Cửu Đỉnh với độ chính xác được nêu rõ.",
      path: "/map",
    });
  }, []);

  const selected = useMemo(
    () => items.find((i) => i.entity_id === selectedId) ?? null,
    [items, selectedId],
  );

  const unmappedNote =
    "Hiện chỉ các thực thể đã có dữ liệu địa lý (kèm độ chính xác) được hiển thị. Vị trí gần đúng được vẽ bằng vòng tròn lớn thay vì ghim chính xác.";

  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-24 pt-20 md:pt-24">
      <header className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-widest text-primary/80">
          Địa lý lịch sử
        </p>
        <h1 className="mt-1 font-serif text-3xl font-bold text-foreground md:text-4xl">
          Bản đồ di sản
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
          Địa lý được khắc họa trên Cửu Đỉnh và các thực thể lịch sử có liên
          quan. {unmappedNote}
        </p>
      </header>

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <label className="text-xs font-semibold text-muted-foreground" htmlFor="map-type">
          Loại thực thể
        </label>
        <select
          id="map-type"
          value={entityType}
          onChange={(e) => setEntityType(e.target.value)}
          className="rounded-lg border border-border bg-secondary/40 px-3 py-1.5 text-sm"
        >
          <option value="">Tất cả</option>
          <option value="place">Địa danh</option>
          <option value="mountain">Núi</option>
          <option value="water_body">Sông / biển</option>
          <option value="island">Đảo</option>
          <option value="settlement">Điểm dân cư</option>
          <option value="region">Vùng</option>
        </select>
        <button
          type="button"
          onClick={() => setShowList((v) => !v)}
          className="ml-auto inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-muted-foreground hover:bg-secondary"
        >
          <List className="h-3.5 w-3.5" />
          {showList ? "Ẩn danh sách" : "Xem danh sách"}
        </button>
      </div>

      {error ? (
        <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      ) : loading ? (
        <div className="h-[420px] animate-pulse rounded-xl border border-border bg-secondary/30 md:h-[560px]" />
      ) : items.length === 0 ? (
        <div className="rounded-xl border border-border bg-secondary/30 p-8 text-center text-sm text-muted-foreground">
          Chưa có thực thể nào được gắn tọa độ đã kiểm chứng. Dữ liệu địa lý sẽ
          được bổ sung trong quá trình kiểm chứng nguồn.
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
          <MapView
            items={items}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
          <aside
            className={cn(
              "rounded-xl border border-border bg-secondary/30 p-4",
              !showList && "hidden lg:block",
            )}
            aria-label="Danh sách thực thể trên bản đồ"
          >
            <h2 className="mb-3 text-sm font-bold text-foreground">
              Thực thể ({items.length})
            </h2>
            <ul className="max-h-[480px] space-y-1.5 overflow-y-auto">
              {items.map((item) => {
                const Icon = precisionIcon(item.geo_precision);
                const active = item.entity_id === selectedId;
                return (
                  <li key={item.entity_id}>
                    <button
                      type="button"
                      onClick={() => setSelectedId(item.entity_id)}
                      className={cn(
                        "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm",
                        active
                          ? "bg-primary/15 text-foreground"
                          : "text-muted-foreground hover:bg-secondary",
                      )}
                    >
                      <Icon
                        className={cn(
                          "h-4 w-4 shrink-0",
                          item.geo_precision === "exact"
                            ? "text-emerald-600"
                            : "text-amber-600",
                        )}
                      />
                      <span className="min-w-0 flex-1 truncate">{item.name}</span>
                      <span className="text-[10px] uppercase text-muted-foreground/70">
                        {item.entity_type}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </aside>
        </div>
      )}

      {selected ? (
        <div className="mt-4 rounded-xl border border-border bg-popover p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="font-serif text-lg font-bold text-foreground">
                {selected.name}
              </h3>
              <p className="text-xs text-muted-foreground">
                {selected.entity_type} · {selected.slug}
              </p>
            </div>
            <Link
              href={
                selected.entity_type === "relief"
                  ? `/atlas/${selected.slug.split("-").slice(0, 2).join("-")}/${selected.slug}`
                  : `/cuu-dinh/${selected.slug}`
              }
              className="rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground"
            >
              Xem chi tiết
            </Link>
          </div>
          <dl className="mt-3 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2">
            <div className="flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5" />
              {PRECISION_LABELS[selected.geo_precision ?? "unknown"] ??
                "Chưa xác định"}
            </div>
            <div>
              Trạng thái:{" "}
              {STATUS_LABELS[selected.mapping_status ?? "unknown"] ?? "Chưa rõ"}
            </div>
          </dl>
        </div>
      ) : null}

      <p className="mt-6 text-xs leading-relaxed text-muted-foreground">
        Bản đồ không áp ranh giới hành chính lịch sử chính xác nếu chưa có
        nguồn xác minh. Thông tin địa lý sẽ được kiểm chứng theo{" "}
        <Link href="/sources" className="underline">
          nguồn tư liệu
        </Link>
        .
      </p>
    </main>
  );
}
