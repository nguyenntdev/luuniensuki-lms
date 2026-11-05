"use client";

import React, { useState } from "react";
import {
  Download,
  FileCheck,
  FileSpreadsheet,
  FileText,
  Headphones,
  Layers,
  Printer,
  QrCode,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  ALL_16_PRINTABLE_STATIONS,
  STANDARD_4_STATIONS_SLUGS,
  STATION_CLUSTERS,
} from "./worksheetData";
import { PrintableStation } from "./types";
import PrintWorksheetModal from "./PrintWorksheetModal";
import { cn } from "@/lib/utils";

interface LowBandwidthOfflineKitProps {
  className?: string;
  defaultClusterId?: string;
}

export default function LowBandwidthOfflineKit({
  className,
  defaultClusterId = "standard_4",
}: LowBandwidthOfflineKitProps) {
  const [selectedCluster, setSelectedCluster] = useState<string>(defaultClusterId);
  const [isPrintModalOpen, setIsPrintModalOpen] = useState(false);
  const [highContrastMode, setHighContrastMode] = useState(true);

  // Filter stations based on chosen cluster
  const currentClusterObj = STATION_CLUSTERS.find((c) => c.id === selectedCluster) || STATION_CLUSTERS[0];
  const activeStations: PrintableStation[] = ALL_16_PRINTABLE_STATIONS.filter((s) =>
    currentClusterObj.slugs.includes(s.monument_slug)
  );

  const handleExportJson = () => {
    const bundle = {
      kit_id: `low-bandwidth-kit-${selectedCluster}`,
      version: "1.0.0",
      content_scope: "STTT_IMPERIAL_CITY",
      zero_ar_guarantee: true,
      paper_achievable_percent: 100,
      ar_or_smartphone_mandatory: false,
      cluster_title_vi: currentClusterObj.title_vi,
      exported_at: new Date().toISOString(),
      stations: activeStations.map((st) => ({
        station_index: st.station_index,
        monument_slug: st.monument_slug,
        monument_name_vi: st.monument_name_vi,
        zone_name_vi: st.zone_name_vi,
        reign: st.reign,
        construction_year: st.construction_year,
        primary_source: st.primary_source,
        rubbing_asset: st.rubbing_asset,
        offline_task: st.offline_task,
        audio_transcript: st.audio_transcript,
        qr_code_url: `https://luuniensuki.vn/dai-noi/cong-trinh/${st.monument_slug}`,
      })),
    };

    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(bundle, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `luu_nien_offline_kit_${selectedCluster}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className={cn("space-y-6 max-w-5xl mx-auto p-4 md:p-6", className)}>
      {/* 1. Header Banner & Strict Equity Guarantee */}
      <div className="rounded-3xl border border-primary/20 bg-gradient-to-br from-card via-card to-primary/5 p-6 md:p-8 space-y-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Badge variant="outline" className="gap-1.5 border-emerald-500/40 text-emerald-700 dark:text-emerald-300 bg-emerald-500/10 px-3 py-1 text-xs">
            <ShieldCheck className="size-3.5" />
            <span>100% Hoàn Thành Trên Giấy &amp; 2D • Không Bắt Buộc AR / Smartphone</span>
          </Badge>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportJson}
              className="gap-1.5 text-xs"
            >
              <Download className="size-3.5" />
              <span>Tải JSON ngoại tuyến</span>
            </Button>
            <Button
              size="sm"
              onClick={() => setIsPrintModalOpen(true)}
              className="gap-1.5 text-xs bg-primary text-primary-foreground hover:bg-primary/90"
            >
              <Printer className="size-3.5" />
              <span>In phiếu học tập</span>
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          <h1 className="font-serif font-black text-2xl md:text-3xl text-foreground tracking-tight">
            Gói Học Tập Ngoại Tuyến &amp; Bản In Thực Địa (Low-Bandwidth Kit)
          </h1>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-3xl">
            Thiết kế dành riêng cho các trường học vùng xa, môi trường mạng hạn chế hoặc không gian di tích không có sóng 4G. Toàn bộ trích lục chính sử, bản dập 2D độ tương phản cao, nhiệm vụ điền dã và toàn văn lời thoại âm thanh được chuẩn hóa sẵn sàng cho việc in ấn hoặc lưu trữ ngoại tuyến.
          </p>
        </div>

        {/* Core Invariant Guarantees */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs">
          <div className="p-3 rounded-2xl bg-background/80 border border-border/60 space-y-1">
            <span className="font-bold text-foreground block flex items-center gap-1.5">
              <FileSpreadsheet className="size-3.5 text-primary" />
              <span>Bản dập 2D tương phản cao</span>
            </span>
            <p className="text-muted-foreground text-[11px] leading-snug">
              Bản dập nổi di sản (ban-duc-noi) phục vụ mắt thường; không đòi hỏi màn hình đồ họa 3D/WebGL.
            </p>
          </div>
          <div className="p-3 rounded-2xl bg-background/80 border border-border/60 space-y-1">
            <span className="font-bold text-foreground block flex items-center gap-1.5">
              <Headphones className="size-3.5 text-primary" />
              <span>Toàn văn lời thoại thuyết minh</span>
            </span>
            <p className="text-muted-foreground text-[11px] leading-snug">
              Lời thoại hướng dẫn âm thanh được in thành văn bản; học sinh đọc trực tiếp, tiêu thụ 0 MB dữ liệu di động.
            </p>
          </div>
          <div className="p-3 rounded-2xl bg-background/80 border border-border/60 space-y-1">
            <span className="font-bold text-foreground block flex items-center gap-1.5">
              <ShieldCheck className="size-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Bình đẳng đánh giá sư phạm</span>
            </span>
            <p className="text-muted-foreground text-[11px] leading-snug">
              Học sinh không có điện thoại đạt trọn vẹn điểm Rubric S1–S4 (12/12) và 25 XP khám phá mà không bị phân biệt.
            </p>
          </div>
        </div>
      </div>

      {/* 2. Station Cluster Selection */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="font-serif font-bold text-sm text-foreground flex items-center gap-2">
            <Layers className="size-4 text-primary" />
            <span>Chọn cụm di tích điền dã</span>
          </span>
          <span className="text-xs text-muted-foreground">
            Hiển thị: <strong>{activeStations.length}</strong> trạm
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
          {STATION_CLUSTERS.map((cl) => {
            const isSelected = selectedCluster === cl.id;
            return (
              <button
                key={cl.id}
                type="button"
                onClick={() => setSelectedCluster(cl.id)}
                className={cn(
                  "p-3 rounded-2xl border text-left transition-all space-y-1",
                  isSelected
                    ? "border-primary bg-primary/10 shadow-sm ring-1 ring-primary/30"
                    : "border-border/70 bg-card hover:bg-secondary/40"
                )}
              >
                <div className="font-semibold text-xs text-foreground">{cl.title_vi}</div>
                <div className="text-[11px] text-muted-foreground line-clamp-1">{cl.description_vi}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Stations List Preview */}
      <div className="space-y-4">
        {activeStations.map((st, idx) => (
          <div
            key={st.monument_slug}
            className="rounded-3xl border border-border/80 bg-card p-5 space-y-4 hover:border-primary/40 transition-colors"
          >
            {/* Header info */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold px-2 py-0.5 rounded-lg bg-primary text-primary-foreground">
                  TRẠM {idx + 1}
                </span>
                <h3 className="font-serif font-bold text-base text-foreground">
                  {st.monument_name_vi}
                </h3>
                {st.reign && (
                  <span className="text-xs text-muted-foreground italic">
                    (Triều {st.reign})
                  </span>
                )}
              </div>
              <span className="text-xs text-muted-foreground font-mono">
                Khởi dựng: <strong>{st.construction_year || "1804-1833"}</strong>
              </span>
            </div>

            {/* 3-Column Content Preview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              {/* Col 1: 2D Rubbing & QR */}
              <div className="space-y-2 p-3 rounded-2xl bg-secondary/30 border border-border/40">
                <span className="font-semibold text-foreground flex items-center justify-between">
                  <span>Bản dập 2D tương phản cao</span>
                  <span className="font-mono text-[10px] text-muted-foreground">Tỉ lệ 1:1</span>
                </span>
                {st.rubbing_asset && (
                  <div className="border border-border/80 rounded-xl overflow-hidden bg-background p-1 flex items-center justify-center">
                    <img
                      src={st.rubbing_asset.asset_url}
                      alt={st.rubbing_asset.caption_vi}
                      className={cn(
                        "max-h-28 w-auto object-contain",
                        highContrastMode && "filter contrast-150 grayscale"
                      )}
                      loading="lazy"
                    />
                  </div>
                )}
                <div className="flex items-center gap-2 pt-1 border-t border-border/40">
                  <div className="p-1 rounded bg-white border border-neutral-300">
                    <QRCodeSVG
                      value={`https://luuniensuki.vn/dai-noi/cong-trinh/${st.monument_slug}`}
                      size={40}
                      level="M"
                    />
                  </div>
                  <div className="text-[10px] text-muted-foreground leading-tight">
                    <span className="font-semibold text-foreground block">Mã QR di tích:</span>
                    Quét khi có mạng để xem tọa độ không ảnh.
                  </div>
                </div>
              </div>

              {/* Col 2: Primary Source Excerpt */}
              <div className="space-y-2 p-3 rounded-2xl bg-secondary/30 border border-border/40">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <FileText className="size-3.5 text-primary" />
                  <span>Chính sử triều Nguyễn đối chiếu</span>
                </span>
                <div className="font-serif font-bold text-foreground text-[11px]">
                  📖 {st.primary_source.source_title}
                </div>
                <blockquote className="p-2 rounded-xl bg-background border-l-2 border-primary text-[11px] italic text-foreground leading-relaxed">
                  &ldquo;{st.primary_source.citation}&rdquo;
                </blockquote>
                <div className="text-[10px] text-muted-foreground font-mono">
                  Bản quyền: {st.primary_source.rights_owner || "HMCC & Quốc Sử Quán"} • {st.primary_source.license || "CC BY 4.0"}
                </div>
              </div>

              {/* Col 3: Offline Task & Audio Transcript */}
              <div className="space-y-2 p-3 rounded-2xl bg-secondary/30 border border-border/40">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <Sparkles className="size-3.5 text-primary" />
                  <span>Nhiệm vụ 100% trên giấy</span>
                </span>
                {st.offline_task && (
                  <div className="space-y-1 text-[11px]">
                    <p className="text-muted-foreground leading-snug">
                      {st.offline_task.instructions_vi}
                    </p>
                    <div className="space-y-0.5 text-[10px] text-foreground font-medium pt-1">
                      {st.offline_task.checkpoints.map((cp, cIdx) => (
                        <div key={cIdx} className="flex items-start gap-1">
                          <span className="font-mono text-primary font-bold">•</span>
                          <span>{cp}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {st.audio_transcript && (
                  <div className="pt-2 border-t border-border/40 text-[10px] text-muted-foreground space-y-0.5">
                    <div className="font-semibold text-foreground flex items-center justify-between">
                      <span>Lời thoại audio ({st.audio_transcript.duration_text})</span>
                      <span className="text-[9px] text-emerald-600 dark:text-emerald-400 font-mono">0 MB data</span>
                    </div>
                    <p className="italic line-clamp-2 leading-relaxed">
                      &ldquo;{st.audio_transcript.script_text}&rdquo;
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 4. Print Modal Dialog */}
      <PrintWorksheetModal
        open={isPrintModalOpen}
        onOpenChange={setIsPrintModalOpen}
      />
    </div>
  );
}
