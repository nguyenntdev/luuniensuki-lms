"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  Camera,
  Compass,
  MapPin,
  Calendar,
  Crown,
  CheckCircle2,
  AlertTriangle,
  Hammer,
  HelpCircle,
  Layers,
  ChevronRight,
  Headphones,
  Play,
  Pause,
  Volume2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ImperialMapAnnotation, ImperialSite, ImperialZone } from "@/lib/imperial/map-types";
import { useAudioPlayerStore } from "@/stores/imperialAudioStore";
import { getPrimaryHeritageImage, HERITAGE_IMAGE_TYPES } from "@/lib/imperial/heritage-images";

interface MonumentHeroProps {
  site: ImperialSite;
  zone?: ImperialZone | null;
  annotation?: ImperialMapAnnotation | null;
}

export function getConditionBadge(condition: string) {
  switch (condition) {
    case "extant":
      return {
        label: "Còn nguyên vẹn",
        variant: "default" as const,
        icon: CheckCircle2,
        className: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/30",
      };
    case "restored":
    case "reconstructed":
      return {
        label: "Đã phục hồi hoàn chỉnh",
        variant: "secondary" as const,
        icon: Hammer,
        className: "bg-sky-500/15 text-sky-700 dark:text-sky-400 border-sky-500/30",
      };
    case "ruin":
    case "archaeological":
      return {
        label: "Dấu tích khảo cổ / Phế tích",
        variant: "destructive" as const,
        icon: AlertTriangle,
        className: "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30",
      };
    case "altered":
    case "lost":
      return {
        label: "Biến đổi qua thời gian",
        variant: "outline" as const,
        icon: Layers,
        className: "bg-purple-500/15 text-purple-700 dark:text-purple-400 border-purple-500/30",
      };
    default:
      return {
        label: "Đang khảo cứu",
        variant: "outline" as const,
        icon: HelpCircle,
        className: "bg-muted text-muted-foreground border-border",
      };
  }
}

export default function MonumentHero({
  site,
  zone,
  annotation,
}: MonumentHeroProps) {
  const cond = getConditionBadge(site.condition);
  const CondIcon = cond.icon;

  const currentTrack = useAudioPlayerStore((s) => s.currentTrack);
  const isPlaying = useAudioPlayerStore((s) => s.isPlaying);
  const playSite = useAudioPlayerStore((s) => s.playSite);
  const togglePlayPause = useAudioPlayerStore((s) => s.togglePlayPause);
  const setMinimized = useAudioPlayerStore((s) => s.setMinimized);

  const isCurrentSiteActive = currentTrack?.siteSlug === site.slug;
  const isAudioPlaying = isCurrentSiteActive && isPlaying;

  const handleAudioClick = () => {
    if (isCurrentSiteActive) {
      togglePlayPause();
    } else {
      playSite(site.slug, true);
      setMinimized(false);
    }
  };

  const u = annotation?.u ?? 0.5;
  const v = annotation?.v ?? 0.5;

  const heritageImage = getPrimaryHeritageImage(site.slug);
  const [viewMode, setViewMode] = useState<"photo" | "aerial">(
    heritageImage ? "photo" : "aerial",
  );

  return (
    <div className="relative overflow-hidden rounded-2xl border border-border/70 bg-gradient-to-b from-card/90 to-background p-6 shadow-sm md:p-8">
      {/* Breadcrumb path */}
      <nav aria-label="Đường dẫn di tích" className="mb-4 flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
        <Link
          href="/dai-noi"
          className="hover:text-foreground transition-colors"
        >
          Đại Nội Huế
        </Link>
        <ChevronRight className="h-3 w-3 opacity-60" />
        <Link
          href={`/dai-noi?zone=${zone?.slug || site.zone_slug || ""}`}
          className="hover:text-foreground transition-colors font-medium text-foreground/80"
        >
          {zone?.title_vi || "Khu vực Hoàng Thành"}
        </Link>
        <ChevronRight className="h-3 w-3 opacity-60" />
        <span className="font-semibold text-primary truncate max-w-[200px]">
          {site.name_vi}
        </span>
      </nav>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 lg:gap-8 items-start">
        {/* Left column: Identification & Names */}
        <div className="lg:col-span-8 space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${cond.className}`}
            >
              <CondIcon className="h-3.5 w-3.5" />
              {cond.label}
            </span>

            {site.learning_level && (
              <Badge variant="outline" className="text-xs font-mono font-medium tracking-wide">
                {site.learning_level === "L2_LEARNING_READY" || site.learning_level === "L2_ANALYZED"
                  ? "L2 • Đã thẩm định học tập"
                  : "L1 • Tư liệu kiểm chứng"}
              </Badge>
            )}

            {zone?.title_vi && (
              <Badge variant="secondary" className="text-xs">
                {zone.title_vi}
              </Badge>
            )}
          </div>

          <div className="space-y-1">
            <div className="flex flex-wrap items-baseline gap-3">
              <h1 className="font-display text-3xl font-extrabold tracking-tight text-foreground md:text-4xl">
                {site.name_vi}
              </h1>
            </div>

            {site.name_en && (
              <p className="text-sm font-medium text-muted-foreground italic">
                {site.name_en}
              </p>
            )}

            {site.alternative_names && site.alternative_names.length > 0 && (
              <p className="text-xs text-muted-foreground">
                <span className="font-semibold">Tên gọi khác:</span>{" "}
                {site.alternative_names.join(", ")}
              </p>
            )}
          </div>

          {/* Quick meta row */}
          <div className="flex flex-wrap items-center gap-y-2 gap-x-6 pt-2 text-xs text-muted-foreground border-t border-border/50">
            {site.construction_year && (
              <div className="flex items-center gap-1.5">
                <Calendar className="h-4 w-4 text-primary shrink-0" />
                <span>
                  Khởi dựng: <strong className="text-foreground">{site.construction_year}</strong>
                </span>
              </div>
            )}
            {site.reign && (
              <div className="flex items-center gap-1.5">
                <Crown className="h-4 w-4 text-primary shrink-0" />
                <span>
                  Niên hiệu: <strong className="text-foreground">{site.reign}</strong>
                </span>
              </div>
            )}
            <div className="flex items-center gap-1.5">
              <Compass className="h-4 w-4 text-primary shrink-0" />
              <span>
                Trục: <strong className="text-foreground">{zone?.title_vi || "Nội thành"}</strong>
              </span>
            </div>
            {annotation && (
              <div className="flex items-center gap-1.5 font-mono text-[11px]">
                <MapPin className="h-3.5 w-3.5 text-primary shrink-0" />
                <span>UV: ({annotation.u.toFixed(4)}, {annotation.v.toFixed(4)})</span>
              </div>
            )}
          </div>

          {/* Heritage Audio Guide Player Trigger Button */}
          <div className="pt-1">
            <Button
              type="button"
              onClick={handleAudioClick}
              variant={isAudioPlaying ? "default" : "outline"}
              className={cn(
                "h-9 px-3.5 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-sm",
                isAudioPlaying
                  ? "bg-primary text-primary-foreground shadow-primary/25 hover:bg-primary/90"
                  : "bg-secondary/70 hover:bg-secondary text-foreground border-border/80 hover:border-primary/50",
              )}
            >
              <Headphones className={cn("h-4 w-4", isAudioPlaying ? "animate-bounce" : "text-primary")} />
              <span>
                {isAudioPlaying
                  ? "Đang phát thuyết minh di tích"
                  : isCurrentSiteActive
                  ? "Tiếp tục nghe thuyết minh"
                  : "Nghe thuyết minh âm thanh di sản"}
              </span>
              {isAudioPlaying ? (
                <Pause className="h-3.5 w-3.5 fill-current ml-1" />
              ) : (
                <Play className="h-3.5 w-3.5 fill-current ml-1" />
              )}
            </Button>
          </div>

          {site.condition_description_vi && (
            <div className="rounded-lg bg-secondary/50 p-3 text-xs leading-relaxed text-secondary-foreground">
              <span className="font-semibold text-foreground">Hiện trạng bảo tồn:</span>{" "}
              {site.condition_description_vi}
            </div>
          )}
        </div>

        {/* Right column: Photo / Mini Aerial Map Locator Preview */}
        <div className="lg:col-span-4 flex flex-col items-center">
          {heritageImage && (
            <div className="flex items-center gap-1 p-1 mb-2 rounded-lg bg-secondary/60 border border-border/60 text-xs">
              <button
                type="button"
                onClick={() => setViewMode("photo")}
                className={cn(
                  "flex items-center gap-1.5 px-2.5 py-1 rounded-md font-medium transition-all",
                  viewMode === "photo"
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                <Camera className="h-3 w-3" />
                Ảnh chụp thực tế
              </button>
              <button
                type="button"
                onClick={() => setViewMode("aerial")}
                className={cn(
                  "flex items-center gap-1.5 px-2.5 py-1 rounded-md font-medium transition-all",
                  viewMode === "aerial"
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                <MapPin className="h-3 w-3" />
                Định vị không ảnh
              </button>
            </div>
          )}

          {viewMode === "photo" && heritageImage ? (
            <div className="relative w-full max-w-[280px] aspect-[4/3] rounded-xl overflow-hidden border-2 border-primary/30 shadow-md group bg-neutral-900">
              <Image
                src={heritageImage.src}
                alt={heritageImage.alt || site.name_vi}
                fill
                className="object-cover group-hover:scale-105 transition-transform duration-500"
                sizes="(max-width: 768px) 100vw, 300px"
                priority
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-transparent to-black/20 pointer-events-none" />
              <div className="absolute top-2 left-2">
                <span className="rounded bg-black/70 backdrop-blur-md px-2 py-0.5 text-[9px] font-medium text-white shadow border border-white/10">
                  {HERITAGE_IMAGE_TYPES[heritageImage.imageType]?.label || "Hiện trạng"}
                </span>
              </div>
              <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between text-[10px] text-white/95 bg-black/65 backdrop-blur-md px-2.5 py-1 rounded-md">
                <span className="truncate max-w-[170px] drop-shadow">
                  {heritageImage.title}
                </span>
                <a
                  href="#imagery-heading"
                  className="text-primary-foreground font-semibold hover:underline shrink-0"
                >
                  Xem thêm
                </a>
              </div>
            </div>
          ) : (
            <div className="relative w-full max-w-[280px] aspect-[4/3] rounded-xl overflow-hidden border-2 border-primary/30 shadow-md group bg-neutral-900">
              {/* Background aerial image preview */}
              <Image
                src="/assets/imperial/maps/dai-noi-aerial-v1.webp"
                alt="Bản đồ định vị công trình trên không ảnh Đại Nội"
                fill
                className="object-cover opacity-85 group-hover:scale-105 transition-transform duration-500"
                sizes="(max-width: 768px) 100vw, 300px"
              />
              {/* Dark gradient vignette */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20 pointer-events-none" />

              {/* Glowing UV Target Locator Pin */}
              <div
                className="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-none z-10 flex flex-col items-center"
                style={{
                  left: `${u * 100}%`,
                  top: `${v * 100}%`,
                }}
              >
                <span className="relative flex h-5 w-5 items-center justify-center">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-red-600 border-2 border-white shadow-lg" />
                </span>
              </div>

              {/* Locator caption */}
              <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between text-[10px] text-white/90 bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-md">
                <span className="flex items-center gap-1 font-medium truncate">
                  <MapPin className="h-3 w-3 text-red-400 shrink-0" />
                  Vị trí trên không ảnh
                </span>
                <Link
                  href={`/dai-noi?focus=${site.slug}`}
                  className="text-primary-foreground font-semibold hover:underline"
                >
                  Mở bản đồ
                </Link>
              </div>
            </div>
          )}

          <p className="mt-1.5 text-[11px] text-muted-foreground text-center">
            {viewMode === "photo" && heritageImage
              ? `Nguồn: ${heritageImage.creditLine}`
              : `Tọa độ chuẩn hóa UV: [${u.toFixed(4)}, ${v.toFixed(4)}]`}
          </p>
        </div>
      </div>
    </div>
  );
}
