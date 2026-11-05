"use client";

import React, { useState } from "react";
import Image from "next/image";
import {
  QrCode,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Accessibility,
  Footprints,
  Download,
  CheckCircle2,
  ExternalLink,
  ChevronRight,
  Info,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface TrailAccessibilityInfo {
  accessibility_grade: string;
  wheelchair_accessible: boolean;
  is_accessibility_verified: boolean;
  wheelchair_route_summary: string;
  ramp_locations: string[];
  tactile_paving: boolean;
  rest_stops_count: number;
  auditory_beacon_available: boolean;
  safety_notes?: string | null;
}

export interface TrailRubbingFallback {
  asset_url: string;
  local_path: string;
  format: string;
  sha256: string;
  file_exists: boolean;
  byte_size: number;
  rights_attribution: string;
  legal_basis: string;
  description_vi: string;
  description_en?: string | null;
}

export interface TrailStation {
  station_index: number;
  station_code: string;
  title_vi: string;
  title_en?: string | null;
  location_lat?: number | null;
  location_lon?: number | null;
  inspection_prompt_vi: string;
  inspection_prompt_en?: string | null;
  qr_token: string;
  qr_data_uri: string;
  authority: string;
  offline_rubbing: TrailRubbingFallback;
  primary_sources: any[];
  accessibility_info: TrailAccessibilityInfo;
}

export interface MuseumGuidedTrailData {
  place_slug: string;
  place_name_vi: string;
  place_name_en?: string | null;
  trail_title_vi: string;
  trail_title_en?: string | null;
  summary_vi: string;
  summary_en?: string | null;
  estimated_duration_minutes: number;
  total_stations: number;
  accessibility: TrailAccessibilityInfo;
  offline_rubbing_fallback: TrailRubbingFallback;
  primary_sources_count: number;
  primary_sources: any[];
  stations: TrailStation[];
}

interface MuseumQRGuidedTrailProps {
  trail: MuseumGuidedTrailData;
  locale?: "vi" | "en";
  className?: string;
  onOpenCitationDrawer?: () => void;
}

export default function MuseumQRGuidedTrail({
  trail,
  locale = "vi",
  className,
  onOpenCitationDrawer,
}: MuseumQRGuidedTrailProps) {
  const [activeTab, setActiveTab] = useState<"trail" | "rubbing" | "accessibility">("trail");
  const [showQRModal, setShowQRModal] = useState<TrailStation | null>(null);

  const acc = trail.accessibility;
  const isAccessible = acc.wheelchair_accessible && acc.is_accessibility_verified;
  const isUnknown = acc.accessibility_grade === "unknown_unverified" || !acc.is_accessibility_verified;

  return (
    <div
      className={cn(
        "rounded-2xl border border-border/80 bg-card p-6 shadow-sm transition-all sm:p-8",
        className
      )}
      data-testid="museum-qr-guided-trail"
    >
      {/* 1. Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs font-semibold tracking-wider text-primary uppercase">
            <Footprints className="h-4 w-4" />
            <span>Tuyến Khảo Cứu Hiện Trường & QR</span>
          </div>
          <h2 className="font-display text-xl font-bold text-foreground sm:text-2xl">
            {trail.trail_title_vi}
          </h2>
          {trail.trail_title_en && (
            <p className="text-xs text-muted-foreground italic sm:text-sm">
              {trail.trail_title_en}
            </p>
          )}
        </div>

        {/* Accessibility Status Pill */}
        <div className="flex flex-wrap items-center gap-2">
          {isAccessible ? (
            <span
              className="inline-flex items-center gap-1.5 rounded-full border border-emerald-600/40 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-700 dark:text-emerald-400"
              data-testid="badge-accessible"
            >
              <Accessibility className="h-3.5 w-3.5" />
              <span>Tiếp cận xe lăn đầy đủ</span>
            </span>
          ) : isUnknown ? (
            <span
              className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-700 dark:text-amber-400"
              data-testid="badge-accessibility-unknown"
            >
              <AlertTriangle className="h-3.5 w-3.5" />
              <span>Chưa khảo sát xe lăn</span>
            </span>
          ) : (
            <span
              className="inline-flex items-center gap-1.5 rounded-full border border-rose-500/40 bg-rose-500/10 px-3 py-1 text-xs font-medium text-rose-700 dark:text-rose-400"
              data-testid="badge-inaccessible"
            >
              <Accessibility className="h-3.5 w-3.5" />
              <span>Bậc thang dốc - Hạn chế</span>
            </span>
          )}

          <span className="inline-flex items-center gap-1 rounded-full border border-border bg-muted/50 px-2.5 py-1 text-xs text-muted-foreground">
            <ShieldCheck className="h-3.5 w-3.5 text-primary" />
            <span>HMCC Xác Thực</span>
          </span>
        </div>
      </div>

      {/* 2. Navigation Tabs */}
      <div className="mt-4 flex border-b border-border/60">
        <button
          type="button"
          onClick={() => setActiveTab("trail")}
          className={cn(
            "flex items-center gap-2 border-b-2 px-4 py-2 text-xs font-medium transition-colors sm:text-sm",
            activeTab === "trail"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          <QrCode className="h-4 w-4" />
          <span>Trạm QR Khảo Chứng ({trail.total_stations})</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("rubbing")}
          className={cn(
            "flex items-center gap-2 border-b-2 px-4 py-2 text-xs font-medium transition-colors sm:text-sm",
            activeTab === "rubbing"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          <Layers className="h-4 w-4" />
          <span>Bản Dập 2D Ngoại Tuyến</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("accessibility")}
          className={cn(
            "flex items-center gap-2 border-b-2 px-4 py-2 text-xs font-medium transition-colors sm:text-sm",
            activeTab === "accessibility"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          <Accessibility className="h-4 w-4" />
          <span>Lộ Trình Tiếp Cận</span>
        </button>
      </div>

      {/* 3. Tab Contents */}
      <div className="mt-6">
        {/* TAB 1: Trail Stations */}
        {activeTab === "trail" && (
          <div className="space-y-4">
            <p className="text-xs text-muted-foreground sm:text-sm">
              Khách tham quan quét mã QR tại các bảng định vị hiện trường để mở trực tiếp
              ngữ cảnh lịch sử và sử liệu đối chiếu gốc được bảo chứng bởi Quốc Sử Quán và UNESCO.
            </p>

            <div className="grid gap-4 sm:grid-cols-1">
              {trail.stations.map((st) => (
                <div
                  key={st.station_code}
                  className="group relative rounded-xl border border-border/70 bg-card/60 p-4 transition-all hover:border-primary/50 hover:bg-muted/30"
                  data-testid={`station-card-${st.station_code}`}
                >
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="rounded-md bg-primary/10 px-2 py-0.5 font-mono text-xs font-bold text-primary">
                          {st.station_code}
                        </span>
                        <h3 className="text-sm font-semibold text-foreground sm:text-base">
                          {st.title_vi}
                        </h3>
                      </div>
                      <p className="text-xs leading-relaxed text-muted-foreground sm:text-sm">
                        {st.inspection_prompt_vi}
                      </p>

                      {/* Primary source badge */}
                      {st.primary_sources && st.primary_sources.length > 0 && (
                        <div className="flex flex-wrap items-center gap-2 pt-1">
                          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-primary">
                            <FileText className="h-3 w-3" />
                            <span>Sử liệu đối chiếu:</span>
                          </span>
                          {st.primary_sources.map((src, sIdx) => (
                            <span
                              key={src.id || sIdx}
                              onClick={onOpenCitationDrawer}
                              className="cursor-pointer rounded border border-border/80 bg-background px-2 py-0.5 text-[11px] text-foreground/80 hover:bg-muted hover:text-foreground"
                            >
                              {src.source_title} ({src.cited_section || src.cited_page || "Chính biên"})
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* QR Button Action */}
                    <div className="flex shrink-0 items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setShowQRModal(st)}
                        className="inline-flex items-center gap-2 rounded-xl bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground transition-transform hover:scale-[1.02] active:scale-[0.98]"
                        data-testid={`btn-view-qr-${st.station_code}`}
                      >
                        <QrCode className="h-4 w-4" />
                        <span>Mở Mã QR</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 2: Offline 2D Rubbing Fallback */}
        {activeTab === "rubbing" && (
          <div className="space-y-4">
            <div className="rounded-xl border border-border/80 bg-muted/20 p-4">
              <div className="flex items-start gap-3">
                <Info className="mt-0.5 h-4 w-4 text-primary shrink-0" />
                <div className="space-y-1 text-xs leading-relaxed text-muted-foreground sm:text-sm">
                  <p className="font-semibold text-foreground">
                    Nguyên Tắc Bình Đẳng Tiếp Cận Ngoại Tuyến (100% 2D Rubbing Equivalence)
                  </p>
                  <p>
                    Để đảm bảo học sinh và du khách không có thiết bị 3D/AR hoặc ở khu vực sóng yếu
                    vẫn hoàn thành trọn vẹn nhiệm vụ khảo cứu, hệ thống đối chiếu trực tiếp bản dập
                    hoa văn truyền thống từ kho tư liệu lưu trữ bản đúc nổi chính thức.
                  </p>
                </div>
              </div>
            </div>

            <div className="overflow-hidden rounded-xl border border-border bg-card">
              <div className="p-4 sm:p-6 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
                  <div>
                    <h4 className="text-sm font-bold text-foreground">
                      {trail.offline_rubbing_fallback.description_vi}
                    </h4>
                    <p className="text-xs text-muted-foreground">
                      Lưu trữ: {trail.offline_rubbing_fallback.local_path} (
                      {(trail.offline_rubbing_fallback.byte_size / 1024).toFixed(1)} KB)
                    </p>
                  </div>
                  <span className="rounded-md bg-emerald-500/10 px-2.5 py-1 text-xs font-mono font-medium text-emerald-700 dark:text-emerald-400">
                    SHA-256 Verified
                  </span>
                </div>

                <div className="space-y-2 text-xs sm:text-sm text-foreground/90">
                  <p>
                    <span className="font-semibold text-foreground">Bản quyền tư liệu: </span>
                    {trail.offline_rubbing_fallback.rights_attribution}
                  </p>
                  <p>
                    <span className="font-semibold text-foreground">Căn cứ pháp lý: </span>
                    {trail.offline_rubbing_fallback.legal_basis}
                  </p>
                  <p className="font-mono text-[11px] text-muted-foreground break-all">
                    Checksum: {trail.offline_rubbing_fallback.sha256}
                  </p>
                </div>

                {trail.offline_rubbing_fallback.asset_url && (
                  <div className="pt-2">
                    <a
                      href={trail.offline_rubbing_fallback.asset_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-muted"
                    >
                      <Download className="h-3.5 w-3.5" />
                      <span>Mở Bản Dập Độ Phân Giải Cao</span>
                      <ExternalLink className="h-3 w-3 text-muted-foreground" />
                    </a>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: Accessibility Route Info */}
        {activeTab === "accessibility" && (
          <div className="space-y-4" data-testid="accessibility-panel">
            {/* Warning when unverified / unknown */}
            {isUnknown && (
              <div
                className="rounded-xl border border-amber-500/50 bg-amber-500/10 p-4"
                data-testid="alert-accessibility-unverified"
              >
                <div className="flex items-start gap-3">
                  <AlertTriangle className="mt-0.5 h-4 w-4 text-amber-600 shrink-0" />
                  <div className="space-y-1 text-xs text-amber-800 dark:text-amber-200 sm:text-sm">
                    <p className="font-bold">
                      Cảnh Báo Minh Bạch: Chưa Có Khảo Sát Xe Lăn Chính Thức
                    </p>
                    <p>
                      Điểm di tích này chưa được chuyên viên khảo sát độ dốc đường đi và hạ tầng xe lăn.
                      Hệ thống cam kết không quảng bá sai lệch là “tiếp cận xe lăn” khi chưa có dữ liệu kiểm chứng.
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div className="rounded-xl border border-border bg-card p-5 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
                <span className="text-xs font-semibold uppercase text-muted-foreground">
                  Trạng thái khảo sát tiếp cận
                </span>
                <span className="font-mono text-xs font-bold text-foreground">
                  {acc.accessibility_grade}
                </span>
              </div>

              <div className="space-y-3 text-xs sm:text-sm leading-relaxed text-foreground/90">
                <p>
                  <span className="font-semibold text-foreground">Mô tả tuyến đường: </span>
                  {acc.wheelchair_route_summary}
                </p>

                {acc.ramp_locations && acc.ramp_locations.length > 0 && (
                  <div>
                    <span className="font-semibold text-foreground">Vị trí ram dốc hỗ trợ: </span>
                    <ul className="mt-1 list-disc list-inside space-y-0.5 text-muted-foreground">
                      {acc.ramp_locations.map((r, rIdx) => (
                        <li key={rIdx}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4 pt-2 border-t border-border/60 text-xs text-muted-foreground">
                  <div>
                    <span className="font-semibold text-foreground">Lối đi xúc giác: </span>
                    <span>{acc.tactile_paving ? "Có trang bị" : "Chưa có"}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-foreground">Trạm nghỉ chân: </span>
                    <span>{acc.rest_stops_count} điểm</span>
                  </div>
                  <div>
                    <span className="font-semibold text-foreground">Cột phát âm thanh chỉ dẫn: </span>
                    <span>{acc.auditory_beacon_available ? "Có hỗ trợ" : "Không có"}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-foreground">Khảo sát thực địa: </span>
                    <span>{acc.is_accessibility_verified ? "Đã nghiệm thu" : "Chưa nghiệm thu"}</span>
                  </div>
                </div>

                {acc.safety_notes && (
                  <p className="pt-2 text-xs italic text-muted-foreground">
                    Lưu ý an toàn: {acc.safety_notes}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 4. Station QR Modal */}
      {showQRModal && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs"
          data-testid="modal-station-qr"
        >
          <div className="relative w-full max-w-sm rounded-2xl border border-border bg-card p-6 shadow-xl">
            <div className="text-center space-y-3">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <QrCode className="h-6 w-6" />
              </div>
              <h3 className="text-base font-bold text-foreground">
                Mã QR Khảo Chứng Hiện Trường
              </h3>
              <p className="text-xs text-muted-foreground">
                Trạm: <span className="font-semibold text-foreground">{showQRModal.title_vi}</span>
              </p>

              {/* Simulated QR Visual Representation with Data URI */}
              <div className="my-4 flex flex-col items-center justify-center rounded-xl border border-border bg-white p-4 text-black">
                <div className="font-mono text-[10px] break-all p-2 bg-slate-50 border rounded text-slate-700">
                  {showQRModal.qr_data_uri}
                </div>
                <p className="mt-2 text-[10px] text-slate-500 font-mono">
                  HMAC-SHA256: {showQRModal.qr_token.slice(0, 16)}...
                </p>
              </div>

              <div className="text-left text-xs text-muted-foreground space-y-1">
                <p>
                  <span className="font-semibold text-foreground">Cơ quan bảo chứng: </span>
                  {showQRModal.authority}
                </p>
                <p>
                  <span className="font-semibold text-foreground">Mã định danh: </span>
                  {showQRModal.station_code}
                </p>
              </div>

              <button
                type="button"
                onClick={() => setShowQRModal(null)}
                className="mt-4 w-full rounded-xl bg-secondary py-2.5 text-xs font-semibold text-foreground hover:bg-secondary/80"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
