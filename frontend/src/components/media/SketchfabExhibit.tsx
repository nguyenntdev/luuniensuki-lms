"use client";

import * as React from "react";
import {
  Box,
  ExternalLink,
  Square,
  ShieldCheck,
  AlertCircle,
  Sparkles,
  Maximize2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { LicenseBadge } from "./LicenseBadge";
import { ThreeDFallback } from "./ThreeDFallback";

/**
 * Approved Sketchfab models permitted for interactive WebGL iframe embedding under CC BY 4.0.
 * Specification: Master Execution Goal V2 (§V2-C.2) & ADR 05.
 */
export const APPROVED_SKETCHFAB_MODELS = ["SF-009", "SF-011", "SF-016"] as const;

/**
 * Restricted Sketchfab models blocked from commercial embedding or AI ingestion.
 */
export const BLOCKED_SKETCHFAB_MODELS = ["SF-010", "SF-017"] as const;

/**
 * Negative guardrail model: Permanently rejected due to imagined/speculative architecture.
 */
export const REJECTED_SKETCHFAB_MODEL = "SF-020" as const;

export const REJECTED_SKETCHFAB_UID = "84a8ab573293497ab0d4f97b4650bb55";

export interface CuratedModelRecord {
  id: string;
  title: string;
  siteName: string;
  creatorName: string;
  creatorUrl: string;
  modelUid: string;
  modelUrl: string;
  license: string;
  noai: boolean;
  doi: string;
  doiUrl: string;
  thumbnailUrl: string;
  description: string;
  provenanceNotes: string;
}

export const CURATED_MODELS: Record<string, CuratedModelRecord> = {
  "SF-009": {
    id: "SF-009",
    title: "Tomb of Tu Duc",
    siteName: "Lăng Tự Đức",
    creatorName: "matousekfoto",
    creatorUrl: "https://sketchfab.com/matousekfoto",
    modelUid: "77728a86ad1d4964824b63844d50bfe7",
    modelUrl: "https://sketchfab.com/3d-models/tomb-of-tu-duc-77728a86ad1d4964824b63844d50bfe7",
    license: "CC BY 4.0",
    noai: false,
    doi: "10.26301/n06n-qa49",
    doiUrl: "https://doi.org/10.26301/n06n-qa49",
    thumbnailUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Khiem_Tomb_Hue_Vietnam.jpg/1280px-Khiem_Tomb_Hue_Vietnam.jpg",
    description: "Mô hình quang trắc Lăng Tự Đức (Khiêm Lăng) được xử lý từ bộ dữ liệu khảo sát di sản CyArk / Open Heritage 3D.",
    provenanceNotes: "Dữ liệu hình ảnh đo vẽ khảo sát của CyArk và Trung tâm Bảo tồn Di tích Cố đô Huế. Xử lý quang trắc bởi matousekfoto.",
  },
  "SF-011": {
    id: "SF-011",
    title: "Stele Building (CyArk Dataset)",
    siteName: "Bi Đình — Lăng Tự Đức",
    creatorName: "Vasilis Haroupas",
    creatorUrl: "https://sketchfab.com/haroupas",
    modelUid: "b5d78ecd5e62483192d7ccd193bc063b",
    modelUrl: "https://sketchfab.com/3d-models/tu-ducs-tomb-stele-building-cyark-dataset-b5d78ecd5e62483192d7ccd193bc063b",
    license: "CC BY 4.0",
    noai: false,
    doi: "10.26301/n06n-qa49",
    doiUrl: "https://doi.org/10.26301/n06n-qa49",
    thumbnailUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Stele_Pavilion_Tu_Duc_Tomb.jpg/1280px-Stele_Pavilion_Tu_Duc_Tomb.jpg",
    description: "Quét 3D nhà bia Khiêm Cung Ký tại Lăng Tự Đức, tấm bia đá nặng 20 tấn khắc bài văn tự sự của vua Tự Đức.",
    provenanceNotes: "Số hóa chi tiết công trình Bi Đình dựa trên bộ dữ liệu đo vẽ CyArk. Cấp phép CC BY bởi Vasilis Haroupas.",
  },
  "SF-016": {
    id: "SF-016",
    title: "An Dinh Palace - Open Heritage 3D",
    siteName: "Cung An Định",
    creatorName: "Alexei MKLT",
    creatorUrl: "https://sketchfab.com/alexei.mklt",
    modelUid: "b6143a3e8ff1446aa0c6d5694d08f9e7",
    modelUrl: "https://sketchfab.com/3d-models/an-dinh-palace-open-heritage-3d-b6143a3e8ff1446aa0c6d5694d08f9e7",
    license: "CC BY 4.0",
    noai: false,
    doi: "10.26301/4z5b-vz23",
    doiUrl: "https://doi.org/10.26301/4z5b-vz23",
    thumbnailUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/An_Dinh_Palace_Hue_Vietnam.jpg/1280px-An_Dinh_Palace_Hue_Vietnam.jpg",
    description: "Lưới đa giác tối ưu hóa công trình Khải Tường Lâu tại Cung An Định, di tích kết hợp hài hòa phong cách kiến trúc Pháp - Việt thời Nguyễn.",
    provenanceNotes: "Khảo sát Photogrammetry & LiDAR thực hiện bởi CyArk và HMCC (DOI: 10.26301/4z5b-vz23). Decimated mesh bởi Alexei MKLT.",
  },
  "SF-010": {
    id: "SF-010",
    title: "Tomb of Tu Duc",
    siteName: "Lăng Tự Đức",
    creatorName: "Agisoft",
    creatorUrl: "https://sketchfab.com/Agisoft",
    modelUid: "978f8e7afd9a4aebb738339c9f0087a0",
    modelUrl: "https://sketchfab.com/3d-models/tomb-of-tu-duc-978f8e7afd9a4aebb738339c9f0087a0",
    license: "CC BY-NC-SA 4.0",
    noai: false,
    doi: "10.26301/n06n-qa49",
    doiUrl: "https://doi.org/10.26301/n06n-qa49",
    thumbnailUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Khiem_Tomb_Hue_Vietnam.jpg/1280px-Khiem_Tomb_Hue_Vietnam.jpg",
    description: "Mô hình quang trắc Lăng Tự Đức xử lý bởi Agisoft từ bộ dữ liệu CyArk. Giới hạn phi thương mại (CC BY-NC-SA).",
    provenanceNotes: "Bị chặn không nhúng thương mại theo ADR 05 và chính sách LƯU NIÊN. Chỉ phục vụ tra cứu học thuật.",
  },
  "SF-017": {
    id: "SF-017",
    title: "An Dinh Palace photogrammetry + lidar",
    siteName: "Cung An Định",
    creatorName: "Miguel Bandera",
    creatorUrl: "https://sketchfab.com/miguelbandera",
    modelUid: "dca05e147d79420eb3696eefcf8e1f19",
    modelUrl: "https://sketchfab.com/3d-models/an-dinh-palace-photogrammetry-lidar-dca05e147d79420eb3696eefcf8e1f19",
    license: "CC BY-NC-SA / NoAI",
    noai: true,
    doi: "10.26301/4z5b-vz23",
    doiUrl: "https://doi.org/10.26301/4z5b-vz23",
    thumbnailUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/An_Dinh_Palace_Hue_Vietnam.jpg/1280px-An_Dinh_Palace_Hue_Vietnam.jpg",
    description: "Khảo sát quang trắc kết hợp LiDAR công trình Cung An Định. Mang nhãn NoAI và CC BY-NC-SA.",
    provenanceNotes: "Bị chặn không nhúng thương mại và cấm thu thập huấn luyện AI per NoAI / CC BY-NC-SA restrictions.",
  },
  "SF-020": {
    id: "SF-020",
    title: "Đại nội Huế Văn Hóa Việt Nam",
    siteName: "Đại Nội — Kinh thành Huế",
    creatorName: "nguyenduc0",
    creatorUrl: "https://sketchfab.com/nguyenduc0",
    modelUid: "84a8ab573293497ab0d4f97b4650bb55",
    modelUrl: "https://sketchfab.com/3d-models/ai-noi-hue-van-hoa-viet-nam-84a8ab573293497ab0d4f97b4650bb55",
    license: "NOT STATED",
    noai: false,
    doi: "",
    doiUrl: "",
    thumbnailUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Ngo_Mon_Gate_Imperial_City_Hue.jpg/1280px-Ngo_Mon_Gate_Imperial_City_Hue.jpg",
    description: "Mô hình kiến trúc mang tính tưởng tượng và biểu tượng, không bảo đảm tính chuẩn xác lịch sử.",
    provenanceNotes: "BỊ TỪ CHỐI VĨNH VIỄN: Negative-test guardrail per Master Spec V2-C.2. Không được phép nhúng hoặc liên kết như tư liệu di tích.",
  },
};

export interface SketchfabExhibitProps extends React.HTMLAttributes<HTMLDivElement> {
  modelId?: string;
  modelUid?: string;
  modelTitle?: string;
  siteName?: string;
  creatorName?: string;
  creatorUrl?: string;
  thumbnailUrl?: string;
  licenseText?: string;
  doi?: string;
  doiUrl?: string;
  modelUrl?: string;
  noai?: boolean;
  className?: string;
  onActivate?: () => void;
  onDismiss?: () => void;
}

/**
 * Checks client-side WebGL support without throwing errors.
 */
function checkWebGLSupport(): boolean {
  if (typeof window === "undefined") return true;
  try {
    const canvas = document.createElement("canvas");
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext("webgl2") || canvas.getContext("webgl"))
    );
  } catch {
    return false;
  }
}

/**
 * Validates that a string is a valid 32-character hexadecimal UID.
 */
export function isValidSketchfabUid(uid?: string | null): boolean {
  if (!uid) return false;
  return /^[0-9a-f]{32}$/i.test(uid.trim());
}

export function SketchfabExhibit({
  modelId,
  modelUid: propModelUid,
  modelTitle: propModelTitle,
  siteName: propSiteName,
  creatorName: propCreatorName,
  creatorUrl: propCreatorUrl,
  thumbnailUrl: propThumbnailUrl,
  licenseText: propLicenseText,
  doi: propDoi,
  doiUrl: propDoiUrl,
  modelUrl: propModelUrl,
  noai: propNoai,
  className,
  onActivate,
  onDismiss,
  ...props
}: SketchfabExhibitProps) {
  const [isActive, setIsActive] = React.useState(false);
  const [webglError, setWebglError] = React.useState(false);

  // Match curated record if modelId is known
  const curated = modelId ? CURATED_MODELS[modelId] : undefined;

  const resolvedModelId = modelId || (curated ? curated.id : undefined);
  const resolvedModelUid = (propModelUid || curated?.modelUid || "").toLowerCase().trim();
  const resolvedTitle = propModelTitle || curated?.title || "Mô hình 3D Di sản Huế";
  const resolvedSiteName = propSiteName || curated?.siteName || "Quần thể Di tích Huế";
  const resolvedCreatorName = propCreatorName || curated?.creatorName || "Tác giả bên thứ ba";
  const resolvedCreatorUrl = propCreatorUrl || curated?.creatorUrl || "https://sketchfab.com";
  const resolvedThumbnailUrl = propThumbnailUrl || curated?.thumbnailUrl || "";
  const resolvedLicense = propLicenseText || curated?.license || "CC BY 4.0";
  const resolvedNoAi = propNoai !== undefined ? propNoai : curated?.noai || false;
  const resolvedDoi = propDoi || curated?.doi;
  const resolvedDoiUrl = propDoiUrl || curated?.doiUrl;
  const resolvedModelUrl =
    propModelUrl || curated?.modelUrl || (resolvedModelUid ? `https://sketchfab.com/models/${resolvedModelUid}` : undefined);

  // =========================================================================
  // NEGATIVE GUARDRAIL: REJECT SF-020 PERMANENTLY
  // =========================================================================
  const isRejectedModel =
    resolvedModelId === REJECTED_SKETCHFAB_MODEL ||
    resolvedModelUid === REJECTED_SKETCHFAB_UID ||
    (resolvedTitle && resolvedTitle.toLowerCase().includes("ai-noi-hue-van-hoa-viet-nam"));

  if (isRejectedModel) {
    return (
      <ThreeDFallback
        modelId="SF-020"
        modelTitle="Đại nội Huế Văn Hóa Việt Nam (Mô hình bị từ chối)"
        siteName="Đại Nội — Kinh thành Huế"
        reason="rejected_accuracy"
        reasonDetails="Mô hình SF-020 bị loại trừ vĩnh viễn: Tác giả xác nhận chi tiết kiến trúc mang tính tưởng tượng và không bảo đảm tính chuẩn xác lịch sử theo quy chuẩn di sản LƯU NIÊN."
        licenseTier="rejected_inaccurate"
        className={className}
      />
    );
  }

  // =========================================================================
  // RESTRICTION GUARDRAILS: BLOCK SF-010 & SF-017 (CC BY-NC-SA / NoAI)
  // =========================================================================
  if (resolvedModelId === "SF-010" || resolvedModelUid === "978f8e7afd9a4aebb738339c9f0087a0") {
    return (
      <ThreeDFallback
        modelId="SF-010"
        modelTitle={resolvedTitle}
        siteName="Lăng Tự Đức"
        reason="blocked_nc"
        reasonDetails="Mô hình được cấp phép phi thương mại (CC BY-NC-SA). Excluded from commercial deployment per ADR 05. Tra cứu trực tiếp trên Sketchfab."
        sketchfabUrl="https://sketchfab.com/3d-models/tomb-of-tu-duc-978f8e7afd9a4aebb738339c9f0087a0"
        licenseText="CC BY-NC-SA 4.0"
        licenseTier="blocked_nc"
        className={className}
      />
    );
  }

  if (resolvedModelId === "SF-017" || resolvedModelUid === "dca05e147d79420eb3696eefcf8e1f19" || resolvedNoAi) {
    return (
      <ThreeDFallback
        modelId="SF-017"
        modelTitle={resolvedTitle}
        siteName="Cung An Định"
        reason="blocked_noai"
        reasonDetails="Mô hình mang nhãn NoAI và CC BY-NC-SA. Nghiêm cấm thu thập làm dữ liệu huấn luyện AI và không nhúng thương mại."
        sketchfabUrl="https://sketchfab.com/3d-models/an-dinh-palace-photogrammetry-lidar-dca05e147d79420eb3696eefcf8e1f19"
        licenseText="CC BY-NC-SA / NoAI"
        licenseTier="blocked_noai"
        noai={true}
        className={className}
      />
    );
  }

  // =========================================================================
  // VALIDATION: UID INTEGRITY
  // =========================================================================
  if (!isValidSketchfabUid(resolvedModelUid)) {
    return (
      <ThreeDFallback
        modelId={resolvedModelId}
        modelTitle={resolvedTitle}
        siteName={resolvedSiteName}
        reason="model_missing"
        reasonDetails="Mã định danh mô hình Sketchfab không hợp lệ hoặc đang chờ thẩm định."
        className={className}
      />
    );
  }

  // =========================================================================
  // HARDWARE CHECK: WEBGL DEGRADATION
  // =========================================================================
  if (webglError) {
    return (
      <ThreeDFallback
        modelId={resolvedModelId}
        modelTitle={resolvedTitle}
        siteName={resolvedSiteName}
        reason="webgl_unsupported"
        onRetryWebGL={() => {
          setWebglError(false);
          setIsActive(false);
        }}
        sketchfabUrl={resolvedModelUrl}
        className={className}
      />
    );
  }

  // Handle User Launch Click
  const handleLaunch3D = () => {
    if (!checkWebGLSupport()) {
      setWebglError(true);
      return;
    }
    setIsActive(true);
    if (onActivate) onActivate();
  };

  // Handle Dismiss / Stop Click: Unmounts iframe immediately to free GPU memory
  const handleDismiss3D = () => {
    setIsActive(false);
    if (onDismiss) onDismiss();
  };

  // Safe Sandboxed Embed Endpoint Construction
  const embedSrc = `https://sketchfab.com/models/${resolvedModelUid}/embed?autostart=1&ui_controls=1&ui_infos=0&ui_watermark=1`;

  return (
    <div
      role="region"
      aria-label={`Trình xem mô hình 3D tương tác: ${resolvedTitle}`}
      className={cn(
        "group relative flex flex-col w-full rounded-2xl border border-border/80 bg-card overflow-hidden shadow-sm transition-all",
        className
      )}
      {...props}
    >
      {/* 16:9 Aspect Ratio Display Stage */}
      <div className="relative w-full aspect-video bg-neutral-950 overflow-hidden">
        {isActive ? (
          /* ================= ACTIVE STATE: IFRAME MOUNTED ================= */
          <div className="relative w-full h-full">
            <iframe
              title={`${resolvedTitle} — 3D Heritage Scan`}
              src={embedSrc}
              loading="lazy"
              allow="fullscreen; xr-spatial-tracking"
              sandbox="allow-scripts allow-same-origin allow-popups"
              referrerPolicy="origin"
              className="w-full h-full border-0 rounded-t-2xl"
            />

            {/* Floating Top Control Bar with GPU Release / Dismiss Button */}
            <div className="absolute top-3 right-3 flex items-center gap-2 z-20 pointer-events-auto">
              {resolvedModelUrl && (
                <a
                  href={resolvedModelUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-black/75 hover:bg-black/90 text-white/90 border border-white/20 backdrop-blur-md transition-colors"
                  title="Mở toàn màn hình trên Sketchfab"
                >
                  <Maximize2 className="size-3.5" aria-hidden="true" />
                  <span className="hidden sm:inline">Mở ngoài</span>
                </a>
              )}

              {/* Stop / Dismiss Button: Immediately unmounts iframe to free GPU resources */}
              <button
                type="button"
                onClick={handleDismiss3D}
                aria-label="Đóng trình xem 3D và giải phóng bộ nhớ GPU"
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-rose-600/90 hover:bg-rose-700 text-white border border-rose-400/40 shadow-lg backdrop-blur-md transition-all active:scale-95"
              >
                <Square className="size-3 fill-current" aria-hidden="true" />
                <span>Dừng mô hình (Giải phóng GPU)</span>
              </button>
            </div>
          </div>
        ) : (
          /* ================= IDLE STATE: PREVIEW CARD ================= */
          <div className="relative w-full h-full flex items-center justify-center">
            {resolvedThumbnailUrl ? (
              <img
                src={resolvedThumbnailUrl}
                alt={`Mô hình 3D ${resolvedTitle}`}
                loading="lazy"
                className="absolute inset-0 w-full h-full object-cover brightness-[0.78] transition-transform duration-700 group-hover:scale-105"
              />
            ) : (
              <div className="absolute inset-0 bg-gradient-to-br from-neutral-900 via-neutral-950 to-neutral-900" />
            )}

            {/* Dark vignette overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/40 to-black/30 pointer-events-none" />

            {/* Top Bar: Site Name & License Badge */}
            <div className="absolute top-3 left-3 right-3 flex items-center justify-between gap-2 z-10 pointer-events-none">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold tracking-wide uppercase bg-black/60 text-white border border-white/20 backdrop-blur-md">
                  <Box className="size-3.5 text-amber-400" aria-hidden="true" />
                  <span>Mô hình 3D tương tác</span>
                </span>

                <LicenseBadge
                  tier="approved_cc_by"
                  licenseText={resolvedLicense}
                  size="sm"
                  className="backdrop-blur-md bg-opacity-90 dark:bg-opacity-90"
                />
              </div>

              {resolvedModelId && (
                <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-black/70 text-emerald-300 border border-emerald-400/30">
                  {resolvedModelId}
                </span>
              )}
            </div>

            {/* Center Action: "Xem mô hình 3D tương tác" Button */}
            <div className="relative z-10 flex flex-col items-center justify-center p-4 text-center max-w-md mx-auto">
              <button
                type="button"
                onClick={handleLaunch3D}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm bg-gradient-to-r from-amber-500 via-primary to-emerald-600 text-white shadow-xl hover:brightness-110 active:scale-95 transition-all duration-200 border border-white/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
                aria-label={`Xem mô hình 3D tương tác ${resolvedTitle}`}
              >
                <Box className="size-4 animate-pulse" aria-hidden="true" />
                <span>Xem mô hình 3D tương tác</span>
              </button>

              <p className="text-[11px] text-white/80 mt-2.5 tracking-wide">
                Khởi tạo WebGL khi nhấn • Tiết kiệm bộ nhớ GPU & pin thiết bị
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Exhibit Details & Metadata Bar */}
      <div className="p-4 bg-card flex flex-col gap-2.5 border-t border-border/60">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="text-[11px] font-semibold text-primary uppercase tracking-wider">
                {resolvedSiteName}
              </span>
              <LicenseBadge
                tier="approved_cc_by"
                licenseText={resolvedLicense}
                size="sm"
              />
            </div>
            <h3 className="text-base font-semibold text-foreground leading-snug">
              {resolvedTitle}
            </h3>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Tác giả mô hình:</span>
            <a
              href={resolvedCreatorUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs font-semibold text-foreground hover:text-primary transition-colors focus-visible:underline"
            >
              <span>{resolvedCreatorName}</span>
              <ExternalLink className="size-3 text-muted-foreground" aria-hidden="true" />
            </a>
          </div>
        </div>

        {/* Dataset Provenance & DOI Acknowledgement */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-border/40 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5 flex-wrap">
            <ShieldCheck className="size-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" aria-hidden="true" />
            <span>Nguồn dữ liệu:</span>
            {resolvedDoiUrl ? (
              <a
                href={resolvedDoiUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-foreground hover:underline inline-flex items-center gap-1"
              >
                <span>CyArk / Open Heritage 3D (DOI: {resolvedDoi})</span>
                <ExternalLink className="size-2.5" aria-hidden="true" />
              </a>
            ) : (
              <span className="font-medium text-foreground">Open Heritage 3D / CyArk</span>
            )}
          </div>

          {resolvedModelUrl && (
            <a
              href={resolvedModelUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-primary hover:underline ml-auto"
            >
              <span>Xem trang Sketchfab gốc</span>
              <ExternalLink className="size-3" aria-hidden="true" />
            </a>
          )}
        </div>

        {/* Legal & Educational Disclosure */}
        <div className="flex items-start gap-1.5 p-2 rounded-lg bg-muted/40 text-[11px] text-muted-foreground leading-relaxed">
          <Sparkles className="size-3 text-amber-500 shrink-0 mt-0.5" aria-hidden="true" />
          <p>
            Mô hình được nhúng qua API Sketchfab theo giấy phép Creative Commons. Không lưu trữ tệp nhị phân trên máy chủ dự án. Mọi quyền tác giả thuộc về người tạo mô hình và các đơn vị khảo sát đo đạc.
          </p>
        </div>
      </div>
    </div>
  );
}

export default SketchfabExhibit;
