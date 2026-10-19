"use client";

import * as React from "react";
import {
  Box,
  Image as ImageIcon,
  FileText,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  X,
  Sparkles,
  Landmark,
  ShieldCheck,
  Maximize2,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { HeritageMediaAsset, AccuracyGrade } from "@/types/heritage";
import type { RbpcLocale } from "@/lib/rbpc/copy";
import { getRbpcCopy } from "@/lib/rbpc/copy";
import { SketchfabExhibit } from "@/components/media/SketchfabExhibit";
import { LicenseBadge } from "@/components/media/LicenseBadge";

export type MediaTabKey = "3d" | "photos" | "documents";

export interface HeritageMediaTabsProps extends React.HTMLAttributes<HTMLDivElement> {
  /** List of multimedia assets associated with the heritage place */
  media: HeritageMediaAsset[];
  /** Primary name of the heritage place in Vietnamese */
  placeName?: string;
  /** English translated name of the heritage place */
  placeNameEn?: string;
  /** Active UI locale ("vi" | "en", defaults to "vi") */
  locale?: RbpcLocale;
  /** Initial selected tab key */
  defaultTab?: MediaTabKey;
  /** Additional container classes */
  className?: string;
  /** Callback fired when user switches active tab */
  onTabChange?: (tab: MediaTabKey) => void;
  /** Callback fired when user selects a media asset */
  onAssetClick?: (asset: HeritageMediaAsset) => void;
}

/**
 * Epistemic label mapping for 3D photogrammetry accuracy grades
 */
export const ACCURACY_GRADE_LABELS: Record<
  AccuracyGrade,
  { vi: string; en: string; badgeClass: string }
> = {
  survey_grade: {
    vi: "Khảo sát chuẩn xác (LiDAR)",
    en: "Survey Grade (LiDAR)",
    badgeClass: "bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-300",
  },
  measured_photogrammetry: {
    vi: "Quang trắc chuẩn hóa (CyArk)",
    en: "Measured Photogrammetry",
    badgeClass: "bg-teal-50 text-teal-800 border-teal-300 dark:bg-teal-950/40 dark:text-teal-300",
  },
  historian_reviewed: {
    vi: "Chuyên gia sử học thẩm định",
    en: "Historian Reviewed",
    badgeClass: "bg-blue-50 text-blue-800 border-blue-300 dark:bg-blue-950/40 dark:text-blue-300",
  },
  illustrative_only: {
    vi: "Minh họa mỹ thuật (Không đo vẽ)",
    en: "Illustrative Only",
    badgeClass: "bg-amber-50 text-amber-800 border-amber-300 dark:bg-amber-950/40 dark:text-amber-300",
  },
  unreviewed: {
    vi: "Chờ kiểm định độ chính xác",
    en: "Accuracy Unreviewed",
    badgeClass: "bg-stone-100 text-stone-700 border-stone-300 dark:bg-stone-800 dark:text-stone-300",
  },
  rejected_accuracy: {
    vi: "Bác bỏ do sai lệch lịch sử",
    en: "Rejected / Speculative",
    badgeClass: "bg-rose-50 text-rose-800 border-rose-300 dark:bg-rose-950/40 dark:text-rose-300",
  },
};

/**
 * HeritageMediaTabs Component
 *
 * Tabbed media viewer for Place Detail:
 * 1. 3D Sketchfab Exhibit with WebGL viewer, photogrammetry provenance, and accuracy grade
 * 2. High-resolution documentary Photo Gallery with accessible Lightbox
 * 3. Archival Documents & historic blueprints with bibliographic source references
 */
export function HeritageMediaTabs({
  media = [],
  placeName = "Di tích Huế",
  placeNameEn,
  locale = "vi",
  defaultTab,
  className,
  onTabChange,
  onAssetClick,
  ...restProps
}: HeritageMediaTabsProps) {
  const dict = getRbpcCopy(locale);
  const isEn = locale === "en";
  const displayName = isEn && placeNameEn ? placeNameEn : placeName;

  // Partition media assets by type
  const models3D = React.useMemo(
    () =>
      media.filter(
        (m) =>
          m.media_type === "sketchfab_embed" ||
          m.media_type === "glb" ||
          Boolean(m.model_uid)
      ),
    [media]
  );

  const photos = React.useMemo(
    () =>
      media.filter(
        (m) => m.media_type === "photo" || m.media_type === "video"
      ),
    [media]
  );

  const documents = React.useMemo(
    () => media.filter((m) => m.media_type === "document"),
    [media]
  );

  // Compute default tab based on availability
  const computedInitialTab: MediaTabKey = React.useMemo(() => {
    if (defaultTab) return defaultTab;
    if (models3D.length > 0) return "3d";
    if (photos.length > 0) return "photos";
    if (documents.length > 0) return "documents";
    return "photos";
  }, [defaultTab, models3D.length, photos.length, documents.length]);

  const [activeTab, setActiveTab] = React.useState<MediaTabKey>(computedInitialTab);
  const [selected3DIndex, setSelected3DIndex] = React.useState<number>(0);
  const [lightboxPhoto, setLightboxPhoto] = React.useState<HeritageMediaAsset | null>(null);

  // Synchronize initial tab if props change
  React.useEffect(() => {
    if (defaultTab) {
      setActiveTab(defaultTab);
    }
  }, [defaultTab]);

  const handleTabSelect = (tab: MediaTabKey) => {
    setActiveTab(tab);
    onTabChange?.(tab);
  };

  const active3DModel = models3D[selected3DIndex] || models3D[0];

  return (
    <div
      className={cn(
        "rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-4 sm:p-6 shadow-sm",
        className
      )}
      {...restProps}
    >
      {/* Tab Navigation Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-[var(--rbpc-divider-subtle)] pb-4">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--rbpc-highlight)]">
            {isEn ? "Heritage Media & Evidence" : "Không gian tư liệu & Hình ảnh"}
          </span>
          <h3 className="font-serif text-xl sm:text-2xl font-bold text-[var(--rbpc-ink)]">
            {displayName}
          </h3>
        </div>

        {/* Tab Buttons */}
        <div
          role="tablist"
          aria-label={isEn ? "Heritage media tabs" : "Chuyển đổi phương tiện di sản"}
          className="inline-flex rounded-xl bg-[var(--rbpc-surface-muted)] p-1 gap-1"
        >
          {/* 3D Tab */}
          <button
            type="button"
            role="tab"
            id="tab-3d"
            aria-selected={activeTab === "3d"}
            aria-controls="panel-3d"
            onClick={() => handleTabSelect("3d")}
            className={cn(
              "inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs sm:text-sm font-medium transition-all min-h-[44px]",
              activeTab === "3d"
                ? "bg-[var(--rbpc-surface-elevated)] text-[var(--rbpc-primary)] shadow-sm font-semibold"
                : "text-[var(--rbpc-muted)] hover:text-[var(--rbpc-ink)]"
            )}
          >
            <Box className="h-4 w-4" aria-hidden="true" />
            <span>{isEn ? "3D Exhibit" : "Mô hình 3D"}</span>
            <span
              className={cn(
                "rounded-full px-1.5 py-0.5 text-[10px] font-bold",
                activeTab === "3d"
                  ? "bg-[var(--rbpc-primary-subtle)] text-[var(--rbpc-primary)]"
                  : "bg-black/5 text-[var(--rbpc-muted)] dark:bg-white/10"
              )}
            >
              {models3D.length}
            </span>
          </button>

          {/* Photo Gallery Tab */}
          <button
            type="button"
            role="tab"
            id="tab-photos"
            aria-selected={activeTab === "photos"}
            aria-controls="panel-photos"
            onClick={() => handleTabSelect("photos")}
            className={cn(
              "inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs sm:text-sm font-medium transition-all min-h-[44px]",
              activeTab === "photos"
                ? "bg-[var(--rbpc-surface-elevated)] text-[var(--rbpc-primary)] shadow-sm font-semibold"
                : "text-[var(--rbpc-muted)] hover:text-[var(--rbpc-ink)]"
            )}
          >
            <ImageIcon className="h-4 w-4" aria-hidden="true" />
            <span>{isEn ? "Photo Gallery" : "Thư viện ảnh"}</span>
            <span
              className={cn(
                "rounded-full px-1.5 py-0.5 text-[10px] font-bold",
                activeTab === "photos"
                  ? "bg-[var(--rbpc-primary-subtle)] text-[var(--rbpc-primary)]"
                  : "bg-black/5 text-[var(--rbpc-muted)] dark:bg-white/10"
              )}
            >
              {photos.length}
            </span>
          </button>

          {/* Archival Documents Tab */}
          <button
            type="button"
            role="tab"
            id="tab-documents"
            aria-selected={activeTab === "documents"}
            aria-controls="panel-documents"
            onClick={() => handleTabSelect("documents")}
            className={cn(
              "inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs sm:text-sm font-medium transition-all min-h-[44px]",
              activeTab === "documents"
                ? "bg-[var(--rbpc-surface-elevated)] text-[var(--rbpc-primary)] shadow-sm font-semibold"
                : "text-[var(--rbpc-muted)] hover:text-[var(--rbpc-ink)]"
            )}
          >
            <FileText className="h-4 w-4" aria-hidden="true" />
            <span>{isEn ? "Archival Documents" : "Tư liệu lưu trữ"}</span>
            <span
              className={cn(
                "rounded-full px-1.5 py-0.5 text-[10px] font-bold",
                activeTab === "documents"
                  ? "bg-[var(--rbpc-primary-subtle)] text-[var(--rbpc-primary)]"
                  : "bg-black/5 text-[var(--rbpc-muted)] dark:bg-white/10"
              )}
            >
              {documents.length}
            </span>
          </button>
        </div>
      </div>

      {/* Tab Panels */}
      <div className="mt-5">
        {/* ================================================================ */}
        {/* PANEL 1: 3D SKETCHFAB EXHIBIT                                    */}
        {/* ================================================================ */}
        {activeTab === "3d" && (
          <div
            id="panel-3d"
            role="tabpanel"
            aria-labelledby="tab-3d"
            className="space-y-4 focus:outline-none"
          >
            {models3D.length > 0 && active3DModel ? (
              <>
                {/* Multi-model switcher pill list if > 1 3D model */}
                {models3D.length > 1 && (
                  <div className="flex flex-wrap items-center gap-2 pb-2">
                    <span className="text-xs font-medium text-[var(--rbpc-muted)]">
                      {isEn ? "Select 3D model:" : "Chọn mô hình 3D:"}
                    </span>
                    {models3D.map((m, idx) => (
                      <button
                        key={m.id || idx}
                        type="button"
                        onClick={() => setSelected3DIndex(idx)}
                        className={cn(
                          "rounded-lg px-3.5 py-2 text-xs font-medium border transition-colors min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2",
                          selected3DIndex === idx
                            ? "bg-[var(--rbpc-primary)] text-white border-[var(--rbpc-primary)] font-semibold"
                            : "bg-[var(--rbpc-surface)] text-[var(--rbpc-ink)] border-[var(--rbpc-divider)] hover:bg-[var(--rbpc-surface-muted)]"
                        )}
                      >
                        {m.title || `${isEn ? "Model" : "Mô hình"} ${idx + 1}`}
                      </button>
                    ))}
                  </div>
                )}

                {/* Embedded Sketchfab Exhibit */}
                <SketchfabExhibit
                  modelUid={active3DModel.model_uid || undefined}
                  modelTitle={active3DModel.title || displayName}
                  siteName={displayName}
                  creatorName={active3DModel.creator_name || undefined}
                  creatorUrl={active3DModel.creator_url || undefined}
                  thumbnailUrl={active3DModel.original_url}
                  licenseText={active3DModel.license_label || undefined}
                  noai={active3DModel.noai}
                  modelUrl={active3DModel.embed_url || active3DModel.original_url}
                  onActivate={() => onAssetClick?.(active3DModel)}
                  className="w-full"
                />

                {/* Epistemic Metadata Bar */}
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-[var(--rbpc-surface-muted)] p-3 text-xs">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-[var(--rbpc-ink)]">
                      {isEn ? "Accuracy Grade:" : "Độ chuẩn xác quang trắc:"}
                    </span>
                    {active3DModel.accuracy_grade && (
                      <span
                        className={cn(
                          "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 font-medium",
                          ACCURACY_GRADE_LABELS[active3DModel.accuracy_grade]?.badgeClass ||
                            "bg-gray-100 text-gray-800"
                        )}
                      >
                        <ShieldCheck className="h-3 w-3" aria-hidden="true" />
                        {isEn
                          ? ACCURACY_GRADE_LABELS[active3DModel.accuracy_grade]?.en
                          : ACCURACY_GRADE_LABELS[active3DModel.accuracy_grade]?.vi}
                      </span>
                    )}
                  </div>

                  {active3DModel.provenance_notes && (
                    <div className="text-[var(--rbpc-muted)] max-w-md truncate">
                      <span className="font-medium text-[var(--rbpc-ink)]">
                        {isEn ? "Provenance: " : "Xuất xứ dữ liệu: "}
                      </span>
                      {active3DModel.provenance_notes}
                    </div>
                  )}
                </div>
              </>
            ) : (
              /* Empty state for 3D */
              <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-muted)]/50 p-12 text-center">
                <Box className="h-12 w-12 text-[var(--rbpc-muted)]/60 mb-3" aria-hidden="true" />
                <h4 className="font-serif text-base font-semibold text-[var(--rbpc-ink)]">
                  {isEn ? "No 3D Model Currently Available" : "Chưa có mô hình 3D đo đạc"}
                </h4>
                <p className="mt-1 text-xs text-[var(--rbpc-muted)] max-w-md">
                  {isEn
                    ? "Photogrammetric survey data for this site is currently being indexed and verified under open heritage standards."
                    : "Dữ liệu quang trắc đo đạc cho địa điểm này đang được số hóa và kiểm định theo tiêu chuẩn dữ liệu mở."}
                </p>
                {photos.length > 0 && (
                  <button
                    type="button"
                    onClick={() => handleTabSelect("photos")}
                    className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-[var(--rbpc-primary)] px-4 py-2 text-xs font-semibold text-white hover:bg-[var(--rbpc-primary-hover)] transition-colors min-h-[44px]"
                  >
                    <ImageIcon className="h-3.5 w-3.5" aria-hidden="true" />
                    <span>{isEn ? "View Photo Gallery" : "Xem thư viện ảnh"}</span>
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* ================================================================ */}
        {/* PANEL 2: PHOTO GALLERY                                           */}
        {/* ================================================================ */}
        {activeTab === "photos" && (
          <div
            id="panel-photos"
            role="tabpanel"
            aria-labelledby="tab-photos"
            className="space-y-4 focus:outline-none"
          >
            {photos.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {photos.map((item, idx) => (
                  <div
                    key={item.id || idx}
                    className="group relative flex flex-col overflow-hidden rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] shadow-xs transition-all hover:border-[var(--rbpc-primary)] hover:shadow-md"
                  >
                    {/* Image container */}
                    <div className="relative aspect-[16/10] w-full overflow-hidden bg-stone-100 dark:bg-stone-900">
                      <img
                        src={item.original_url}
                        alt={item.title || `${displayName} - ${idx + 1}`}
                        loading="lazy"
                        className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                        onError={(e) => {
                          const target = e.currentTarget;
                          target.onerror = null;
                          target.src =
                            "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Khiem_Tomb_Hue_Vietnam.jpg/640px-Khiem_Tomb_Hue_Vietnam.jpg";
                        }}
                      />
                      {/* Zoom overlay trigger */}
                      <button
                        type="button"
                        aria-label={isEn ? `Enlarge image: ${item.title || "Photo"}` : `Phóng to ảnh: ${item.title || "Ảnh"}`}
                        onClick={() => {
                          setLightboxPhoto(item);
                          onAssetClick?.(item);
                        }}
                        className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity focus:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
                      >
                        <span className="inline-flex items-center gap-1.5 rounded-lg bg-black/85 px-3.5 py-2 text-xs font-medium text-white shadow-xs">
                          <Maximize2 className="h-3.5 w-3.5" aria-hidden="true" />
                          {isEn ? "View Fullscreen" : "Xem chi tiết"}
                        </span>
                      </button>

                      {/* License Badge on image corner */}
                      {item.license_label && (
                        <div className="absolute bottom-2 left-2 pointer-events-none">
                          <span className="rounded bg-black/75 px-2 py-0.5 text-[10px] font-semibold text-white">
                            {item.license_label}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Metadata & Caption */}
                    <div className="flex flex-1 flex-col justify-between p-3.5">
                      <div>
                        <h4 className="font-serif text-sm font-semibold text-[var(--rbpc-ink)] line-clamp-1">
                          {item.title || `${displayName} — ${isEn ? "Historical View" : "Tư liệu thực địa"}`}
                        </h4>
                        {item.provenance_notes && (
                          <p className="mt-1 text-xs text-[var(--rbpc-muted)] line-clamp-2">
                            {item.provenance_notes}
                          </p>
                        )}
                      </div>

                      <div className="mt-3 flex items-center justify-between border-t border-[var(--rbpc-divider-subtle)] pt-2 text-[11px] text-[var(--rbpc-muted)]">
                        <span className="truncate max-w-[150px]">
                          {item.creator_name ? `© ${item.creator_name}` : "Tư liệu cộng đồng"}
                        </span>
                        {item.creator_url ? (
                          <a
                            href={item.creator_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 hover:text-[var(--rbpc-primary)] underline min-h-[30px]"
                          >
                            <span>{isEn ? "Source" : "Nguồn"}</span>
                            <ExternalLink className="h-3 w-3" aria-hidden="true" />
                          </a>
                        ) : null}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              /* Empty state for photos */
              <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-muted)]/50 p-12 text-center">
                <ImageIcon className="h-12 w-12 text-[var(--rbpc-muted)]/60 mb-3" aria-hidden="true" />
                <h4 className="font-serif text-base font-semibold text-[var(--rbpc-ink)]">
                  {isEn ? "No Photos Available" : "Chưa có hình ảnh tư liệu"}
                </h4>
                <p className="mt-1 text-xs text-[var(--rbpc-muted)] max-w-md">
                  {isEn
                    ? "Historical photos and survey imagery are currently being curated for this monument."
                    : "Hình ảnh khảo sát thực địa và tư liệu lịch sử cho di tích này đang được tổng hợp."}
                </p>
              </div>
            )}
          </div>
        )}

        {/* ================================================================ */}
        {/* PANEL 3: ARCHIVAL DOCUMENTS                                      */}
        {/* ================================================================ */}
        {activeTab === "documents" && (
          <div
            id="panel-documents"
            role="tabpanel"
            aria-labelledby="tab-documents"
            className="space-y-4 focus:outline-none"
          >
            {documents.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {documents.map((doc, idx) => (
                  <div
                    key={doc.id || idx}
                    className="flex flex-col justify-between rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-4 shadow-xs hover:border-[var(--rbpc-primary)] transition-all"
                  >
                    <div className="flex items-start gap-3">
                      <div className="rounded-lg bg-[var(--rbpc-primary-subtle)] p-2.5 text-[var(--rbpc-primary)] shrink-0">
                        <FileText className="h-5 w-5" aria-hidden="true" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="rounded bg-amber-100 text-amber-900 dark:bg-amber-950/40 dark:text-amber-300 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider">
                            {isEn ? "Archival Scan" : "Hồ sơ lưu trữ"}
                          </span>
                          {doc.license_label && (
                            <span className="text-[11px] text-[var(--rbpc-muted)]">
                              • {doc.license_label}
                            </span>
                          )}
                        </div>
                        <h4 className="font-serif text-base font-semibold text-[var(--rbpc-ink)] mt-1">
                          {doc.title || `${isEn ? "Archival Record" : "Hồ sơ tư liệu"} #${idx + 1}`}
                        </h4>
                        {doc.provenance_notes && (
                          <p className="mt-1.5 text-xs text-[var(--rbpc-muted)] leading-relaxed">
                            {doc.provenance_notes}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="mt-4 flex items-center justify-between border-t border-[var(--rbpc-divider-subtle)] pt-3 text-xs">
                      <span className="text-[var(--rbpc-muted)] truncate max-w-[200px]">
                        {doc.creator_name ? `Lưu trữ: ${doc.creator_name}` : "Hồ sơ bảo tồn Cố đô Huế"}
                      </span>
                      {doc.original_url && (
                        <a
                          href={doc.original_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 font-semibold text-[var(--rbpc-primary)] hover:underline min-h-[36px]"
                        >
                          <span>{isEn ? "View Document" : "Xem văn bản gốc"}</span>
                          <ExternalLink className="h-3 w-3" aria-hidden="true" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              /* Empty state for documents */
              <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--rbpc-divider)] bg-[var(--rbpc-surface-muted)]/50 p-12 text-center">
                <FileText className="h-12 w-12 text-[var(--rbpc-muted)]/60 mb-3" aria-hidden="true" />
                <h4 className="font-serif text-base font-semibold text-[var(--rbpc-ink)]">
                  {isEn ? "No Archival Documents Catalogued" : "Chưa có bản quét tư liệu lưu trữ"}
                </h4>
                <p className="mt-1 text-xs text-[var(--rbpc-muted)] max-w-md">
                  {isEn
                    ? "Châu Bản, imperial decrees, and architectural blueprints for this monument are undergoing archival digitisation."
                    : "Châu bản triều Nguyễn, bản vẽ kỹ thuật và văn bản lưu trữ đang trong tiến trình đối chiếu số hóa."}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Accessible Fullscreen Lightbox Modal (Zero heavy backdrop-blur) */}
      {lightboxPhoto && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={lightboxPhoto.title || "Photo viewer"}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
        >
          <div className="relative max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden rounded-2xl bg-[var(--rbpc-surface-elevated)] shadow-2xl">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-[var(--rbpc-divider)] px-4 py-3 bg-[var(--rbpc-surface)]">
              <div className="flex items-center gap-2">
                <ImageIcon className="h-4 w-4 text-[var(--rbpc-primary)]" aria-hidden="true" />
                <h4 className="font-serif text-sm sm:text-base font-bold text-[var(--rbpc-ink)] truncate max-w-md">
                  {lightboxPhoto.title || displayName}
                </h4>
              </div>
              <button
                type="button"
                onClick={() => setLightboxPhoto(null)}
                aria-label={isEn ? "Close photo" : "Đóng hình ảnh"}
                className="rounded-lg p-2 text-[var(--rbpc-muted)] hover:bg-[var(--rbpc-surface-muted)] hover:text-[var(--rbpc-ink)] min-h-[44px] min-w-[44px] flex items-center justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>

            {/* Modal Image Area */}
            <div className="relative flex-1 overflow-auto bg-black flex items-center justify-center min-h-[300px] max-h-[60vh]">
              <img
                src={lightboxPhoto.original_url}
                alt={lightboxPhoto.title || displayName}
                className="max-h-[60vh] w-auto max-w-full object-contain"
              />
            </div>

            {/* Modal Caption & Provenance Footer */}
            <div className="p-4 bg-[var(--rbpc-surface)] border-t border-[var(--rbpc-divider)] text-xs text-[var(--rbpc-ink)]">
              {lightboxPhoto.provenance_notes && (
                <p className="leading-relaxed text-[var(--rbpc-muted)]">
                  {lightboxPhoto.provenance_notes}
                </p>
              )}
              <div className="mt-2 flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[var(--rbpc-divider-subtle)] text-[11px] text-[var(--rbpc-muted)]">
                <span>
                  {lightboxPhoto.creator_name
                    ? `Bản quyền: ${lightboxPhoto.creator_name}`
                    : "Tư liệu lưu trữ số"}
                  {lightboxPhoto.license_label ? ` • ${lightboxPhoto.license_label}` : ""}
                </span>
                {lightboxPhoto.creator_url && (
                  <a
                    href={lightboxPhoto.creator_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex min-h-[44px] items-center gap-1 text-[var(--rbpc-primary)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2 rounded-sm"
                  >
                    <span>{isEn ? "Visit Source Repository" : "Đến trang tư liệu gốc"}</span>
                    <ExternalLink className="h-3 w-3" aria-hidden="true" />
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

HeritageMediaTabs.displayName = "HeritageMediaTabs";

export default HeritageMediaTabs;
