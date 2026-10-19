"use client";

import * as React from "react";
import {
  Camera,
  ExternalLink,
  RotateCcw,
  AlertTriangle,
  Ban,
  XCircle,
  FileText,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { LicenseBadge, type LicenseBadgeTier } from "./LicenseBadge";

export type FallbackReason =
  | "model_missing"
  | "blocked_nc"
  | "blocked_noai"
  | "rejected_accuracy"
  | "webgl_unsupported"
  | "data_saver"
  | "needs_rights_review"
  | "custom";

export interface ThreeDFallbackProps extends React.HTMLAttributes<HTMLDivElement> {
  modelId?: string;
  modelTitle?: string;
  siteName?: string;
  reason?: FallbackReason;
  reasonDetails?: string;
  imageUrl?: string;
  imageAlt?: string;
  photographer?: string;
  photoDate?: string;
  archiveSource?: string;
  caption?: string;
  outboundCitationUrl?: string;
  outboundCitationLabel?: string;
  sketchfabUrl?: string;
  licenseText?: string;
  licenseTier?: LicenseBadgeTier;
  noai?: boolean;
  onRetryWebGL?: () => void;
  className?: string;
}

interface CuratedHeritageVisual {
  defaultImageUrl: string;
  alt: string;
  photographer: string;
  photoDate: string;
  archiveSource: string;
  citationUrl: string;
  citationLabel: string;
}

const CURATED_VISUALS: Record<string, CuratedHeritageVisual> = {
  "SF-009": {
    defaultImageUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Khiem_Tomb_Hue_Vietnam.jpg/1280px-Khiem_Tomb_Hue_Vietnam.jpg",
    alt: "Quần thể Lăng Tự Đức (Khiêm Lăng) — Khu vực hồ Lưu Khiêm và Xung Khiêm Tạ",
    photographer: "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC) & CyArk",
    photoDate: "2018–2024",
    archiveSource: "Open Heritage 3D / HMCC Survey Archive",
    citationUrl: "https://doi.org/10.26301/n06n-qa49",
    citationLabel: "Bộ tư liệu số hóa Open Heritage 3D (DOI: 10.26301/n06n-qa49)",
  },
  "SF-010": {
    defaultImageUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Khiem_Tomb_Hue_Vietnam.jpg/1280px-Khiem_Tomb_Hue_Vietnam.jpg",
    alt: "Khu lăng mộ Hoàng đế Tự Đức — Tư liệu ảnh chụp khảo sát quang trắc",
    photographer: "CyArk & Agisoft Research Dataset",
    photoDate: "2018",
    archiveSource: "CyArk Cultural Heritage Open Data",
    citationUrl: "https://doi.org/10.26301/n06n-qa49",
    citationLabel: "Khảo sát quang trắc CyArk (CC BY-NC-SA 4.0)",
  },
  "SF-011": {
    defaultImageUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Stele_Pavilion_Tu_Duc_Tomb.jpg/1280px-Stele_Pavilion_Tu_Duc_Tomb.jpg",
    alt: "Bi Đình (Nhà bia Khiêm Cung Ký) — Lăng Tự Đức, Huế",
    photographer: "Vasilis Haroupas / CyArk Open Survey",
    photoDate: "2019",
    archiveSource: "Open Heritage 3D Architectural Photogrammetry",
    citationUrl: "https://doi.org/10.26301/n06n-qa49",
    citationLabel: "Dữ liệu bia đá Khiêm Cung Ký (DOI: 10.26301/n06n-qa49)",
  },
  "SF-016": {
    defaultImageUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/An_Dinh_Palace_Hue_Vietnam.jpg/1280px-An_Dinh_Palace_Hue_Vietnam.jpg",
    alt: "Cung An Định — Khải Tường Lâu, kiến trúc kết hợp Á - Âu thời Khải Định",
    photographer: "Alexei MKLT / CyArk / HMCC",
    photoDate: "2020",
    archiveSource: "Open Heritage 3D Repository (DOI: 10.26301/4z5b-vz23)",
    citationUrl: "https://doi.org/10.26301/4z5b-vz23",
    citationLabel: "Bộ tư liệu quét Cung An Định (DOI: 10.26301/4z5b-vz23)",
  },
  "SF-017": {
    defaultImageUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/An_Dinh_Palace_Hue_Vietnam.jpg/1280px-An_Dinh_Palace_Hue_Vietnam.jpg",
    alt: "Cung An Định — Toàn cảnh kiến trúc mặt chính Khải Tường Lâu",
    photographer: "Miguel Bandera Photogrammetry Survey",
    photoDate: "2021",
    archiveSource: "Tư liệu nghiên cứu cá nhân (NoAI & CC BY-NC-SA)",
    citationUrl: "https://doi.org/10.26301/4z5b-vz23",
    citationLabel: "Khảo sát LiDAR & Ảnh chụp Cung An Định (Tham chiếu nghiên cứu)",
  },
  "SF-020": {
    defaultImageUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Ngo_Mon_Gate_Imperial_City_Hue.jpg/1280px-Ngo_Mon_Gate_Imperial_City_Hue.jpg",
    alt: "Kinh thành Huế — Cổng Ngọ Môn và Đại Nội nhìn từ Kỳ Đài",
    photographer: "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
    photoDate: "2022",
    archiveSource: "Hồ sơ khoa học Di tích Cố đô Huế (UNESCO Inscription 678)",
    citationUrl: "https://whc.unesco.org/en/list/678",
    citationLabel: "Hồ sơ Quần thể Di tích Cố đô Huế — UNESCO World Heritage List 678",
  },
};

const DEFAULT_FALLBACK: CuratedHeritageVisual = {
  defaultImageUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Ngo_Mon_Gate_Imperial_City_Hue.jpg/1280px-Ngo_Mon_Gate_Imperial_City_Hue.jpg",
  alt: "Di tích lịch sử văn hóa Cố đô Huế — Ảnh chụp tư liệu lưu trữ",
  photographer: "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
  photoDate: "2023",
  archiveSource: "Kho tư liệu số hóa di sản Lưu Niên",
  citationUrl: "https://whc.unesco.org/en/list/678",
  citationLabel: "Hồ sơ tư liệu Quần thể Di tích Cố đô Huế (UNESCO 678)",
};

interface ReasonMeta {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string; "aria-hidden"?: boolean | "true" | "false" }>;
  tone: "warning" | "destructive" | "neutral" | "info";
  suggestExternal: boolean;
}

const REASON_CONFIGS: Record<FallbackReason, ReasonMeta> = {
  blocked_nc: {
    title: "Mô hình giới hạn phi thương mại (CC BY-NC-SA)",
    description:
      "Mô hình 3D được cấp phép phi thương mại. Theo chính sách LƯU NIÊN, nội dung này không nhúng trong luồng dịch vụ thương mại, ưu tiên ảnh chụp thực địa và liên kết tra cứu.",
    icon: AlertTriangle,
    tone: "warning",
    suggestExternal: true,
  },
  blocked_noai: {
    title: "Mô hình bảo vệ bản quyền NoAI (Không cấp phép AI)",
    description:
      "Mô hình mang nhãn NoAI và giấy phép phi thương mại. Nghiêm cấm thu thập làm dữ liệu huấn luyện AI và không nhúng trực tiếp. Bạn có thể tra cứu trực tiếp tại nền tảng gốc.",
    icon: Ban,
    tone: "warning",
    suggestExternal: true,
  },
  rejected_accuracy: {
    title: "Mô hình không bảo đảm tính xác thực lịch sử (SF-020)",
    description:
      "Mô hình này bị loại trừ vĩnh viễn khỏi danh mục hiển thị do cấu trúc kiến trúc suy đoán/tưởng tượng, không có căn cứ khảo cổ học. LƯU NIÊN áp dụng ảnh tư liệu kiểm chứng học thuật.",
    icon: XCircle,
    tone: "destructive",
    suggestExternal: false,
  },
  webgl_unsupported: {
    title: "Thiết bị không hỗ trợ hoặc mất bối cảnh WebGL",
    description:
      "Trình duyệt hoặc phần cứng đồ họa không hỗ trợ WebGL 2.0 hoặc đã bật chế độ tiết kiệm dữ liệu. Đang hiển thị bản chụp tư liệu lưu trữ độ phân giải cao.",
    icon: Info,
    tone: "info",
    suggestExternal: true,
  },
  data_saver: {
    title: "Đã bật chế độ tiết kiệm dữ liệu",
    description:
      "Để giảm thiểu băng thông mạng di động và tiết kiệm tài nguyên pin, trình xem 3D tạm dừng và hiển thị ảnh tĩnh tối ưu.",
    icon: Info,
    tone: "neutral",
    suggestExternal: true,
  },
  needs_rights_review: {
    title: "Đang tiến hành thủ tục xác thực bản quyền",
    description:
      "Mô hình 3D đang chờ cấp phép chính thức từ tác giả hoặc cơ quan chủ quản. Hiển thị ảnh tư liệu khảo sát có bản quyền để đảm bảo tính pháp lý.",
    icon: Info,
    tone: "neutral",
    suggestExternal: true,
  },
  model_missing: {
    title: "Chưa có mô hình 3D số hóa đạt chuẩn",
    description:
      "Địa danh này hiện chưa có mô hình quét 3D laser hoặc quang trắc đạt tiêu chuẩn thẩm định. Mời bạn xem ảnh chụp tư liệu khảo sát thực địa.",
    icon: Camera,
    tone: "neutral",
    suggestExternal: false,
  },
  custom: {
    title: "Chế độ xem tư liệu 2D thay thế",
    description: "Đang hiển thị ảnh chụp tư liệu thực địa có kiểm chứng nguồn gốc.",
    icon: FileText,
    tone: "neutral",
    suggestExternal: true,
  },
};

export function ThreeDFallback({
  modelId,
  modelTitle,
  siteName,
  reason = "model_missing",
  reasonDetails,
  imageUrl,
  imageAlt,
  photographer,
  photoDate,
  archiveSource,
  caption,
  outboundCitationUrl,
  outboundCitationLabel,
  sketchfabUrl,
  licenseText,
  licenseTier,
  noai,
  onRetryWebGL,
  className,
  ...props
}: ThreeDFallbackProps) {
  // Infer reason if SF-020 or SF-010 or SF-017 passed
  let effectiveReason = reason;
  if (modelId === "SF-020") {
    effectiveReason = "rejected_accuracy";
  } else if (modelId === "SF-017") {
    effectiveReason = "blocked_noai";
  } else if (modelId === "SF-010") {
    effectiveReason = "blocked_nc";
  }

  const curated = (modelId && CURATED_VISUALS[modelId]) || DEFAULT_FALLBACK;
  const resolvedImageUrl = imageUrl || curated.defaultImageUrl;
  const resolvedAlt = imageAlt || (modelTitle ? `Ảnh chụp tư liệu: ${modelTitle}` : curated.alt);
  const resolvedPhotographer = photographer || curated.photographer;
  const resolvedPhotoDate = photoDate || curated.photoDate;
  const resolvedArchiveSource = archiveSource || curated.archiveSource;
  const resolvedCitationUrl = outboundCitationUrl || curated.citationUrl;
  const resolvedCitationLabel = outboundCitationLabel || curated.citationLabel;

  const reasonMeta = REASON_CONFIGS[effectiveReason] || REASON_CONFIGS.custom;
  const ReasonIcon = reasonMeta.icon;

  // Determine badge tier
  let resolvedBadgeTier = licenseTier;
  if (!resolvedBadgeTier) {
    if (effectiveReason === "rejected_accuracy" || modelId === "SF-020") {
      resolvedBadgeTier = "rejected_inaccurate";
    } else if (effectiveReason === "blocked_noai" || noai) {
      resolvedBadgeTier = "blocked_noai";
    } else if (effectiveReason === "blocked_nc") {
      resolvedBadgeTier = "blocked_nc";
    } else if (effectiveReason === "needs_rights_review") {
      resolvedBadgeTier = "review_pending";
    } else {
      resolvedBadgeTier = "institutional_record";
    }
  }

  return (
    <figure
      role="region"
      aria-label={`Bản chụp tư liệu 2D thay thế: ${modelTitle || siteName || "Di tích Huế"}`}
      className={cn(
        "group relative flex flex-col w-full rounded-2xl border border-border/70 bg-card overflow-hidden shadow-sm transition-all",
        className
      )}
      {...props}
    >
      {/* 16:9 Photographic Stage */}
      <div className="relative w-full aspect-video bg-neutral-900/95 overflow-hidden">
        <img
          src={resolvedImageUrl}
          alt={resolvedAlt}
          loading="lazy"
          className="w-full h-full object-cover transition-transform duration-500 ease-out group-hover:scale-[1.01]"
        />

        {/* Ambient Dark Gradient for Caption Readability */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/25 to-black/35 pointer-events-none" />

        {/* Top Floating Badge Bar */}
        <div className="absolute top-3 left-3 right-3 flex items-center justify-between gap-2 z-10">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold tracking-wide uppercase bg-black/60 text-white/95 border border-white/20 backdrop-blur-md">
              <Camera className="size-3 text-amber-400" aria-hidden="true" />
              <span>Ảnh tư liệu 2D</span>
            </span>

            <LicenseBadge
              tier={resolvedBadgeTier}
              licenseText={licenseText}
              noai={noai}
              size="sm"
              className="backdrop-blur-md bg-opacity-90 dark:bg-opacity-90"
            />
          </div>

          {modelId && (
            <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-black/65 text-amber-300 border border-amber-400/30">
              {modelId}
            </span>
          )}
        </div>

        {/* Overlay Notice Banner */}
        <div className="absolute bottom-3 left-3 right-3 z-10 flex flex-col gap-1.5 p-3 rounded-xl bg-black/75 border border-white/15 text-white backdrop-blur-md">
          <div className="flex items-start gap-2">
            <ReasonIcon
              className={cn(
                "size-4 shrink-0 mt-0.5",
                reasonMeta.tone === "destructive" && "text-rose-400",
                reasonMeta.tone === "warning" && "text-amber-400",
                reasonMeta.tone === "info" && "text-sky-400",
                reasonMeta.tone === "neutral" && "text-emerald-400"
              )}
              aria-hidden="true"
            />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold leading-tight text-white/95">
                {reasonMeta.title}
              </p>
              <p className="text-[11px] text-white/75 mt-0.5 leading-relaxed line-clamp-2">
                {reasonDetails || reasonMeta.description}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Metadata & Outbound Citation Footer */}
      <figcaption className="p-3.5 sm:p-4 bg-card flex flex-col gap-2.5 border-t border-border/50">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
          <div className="flex flex-col gap-0.5">
            {siteName && (
              <span className="text-[11px] font-semibold text-primary uppercase tracking-wider">
                {siteName}
              </span>
            )}
            <h4 className="font-semibold text-foreground text-sm leading-snug">
              {modelTitle || resolvedAlt}
            </h4>
            {caption && (
              <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                {caption}
              </p>
            )}
          </div>
        </div>

        {/* Provenance Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2 border-t border-border/40 text-[11px] text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <span className="font-medium text-foreground">Tác giả ảnh:</span>
            <span className="truncate">{resolvedPhotographer} ({resolvedPhotoDate})</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="font-medium text-foreground">Lưu trữ:</span>
            <span className="truncate">{resolvedArchiveSource}</span>
          </div>
        </div>

        {/* Actions & Links Bar */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-border/40">
          {/* Outbound Citation Link */}
          {resolvedCitationUrl && (
            <a
              href={resolvedCitationUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded"
              aria-label={`Xem tư liệu đối chiếu: ${resolvedCitationLabel}`}
            >
              <FileText className="size-3.5 text-primary shrink-0" aria-hidden="true" />
              <span className="truncate max-w-[280px] sm:max-w-[360px]">
                {resolvedCitationLabel}
              </span>
              <ExternalLink className="size-3 text-muted-foreground shrink-0" aria-hidden="true" />
            </a>
          )}

          <div className="flex items-center gap-2 ml-auto">
            {/* Retry WebGL button if failed context */}
            {effectiveReason === "webgl_unsupported" && onRetryWebGL && (
              <button
                type="button"
                onClick={onRetryWebGL}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border bg-secondary hover:bg-secondary/80 text-foreground transition-colors"
              >
                <RotateCcw className="size-3" aria-hidden="true" />
                <span>Thử lại WebGL</span>
              </button>
            )}

            {/* Outbound Sketchfab exploration link (ONLY if not permanently rejected SF-020) */}
            {sketchfabUrl && effectiveReason !== "rejected_accuracy" && reasonMeta.suggestExternal && (
              <a
                href={sketchfabUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border/80 bg-background hover:bg-muted text-foreground transition-colors"
                title="Chuyển tiếp đến nền tảng ngoài — Bản quyền thuộc về tác giả gốc"
              >
                <span>Xem trên Sketchfab</span>
                <ExternalLink className="size-3 text-muted-foreground" aria-hidden="true" />
              </a>
            )}
          </div>
        </div>
      </figcaption>
    </figure>
  );
}

export default ThreeDFallback;
