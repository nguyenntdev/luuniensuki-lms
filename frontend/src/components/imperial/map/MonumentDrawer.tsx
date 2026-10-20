"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowRight,
  BookOpen,
  Calendar,
  Camera,
  Compass,
  Crown,
  FileText,
  Headphones,
  HelpCircle,
  Landmark,
  Pause,
  Play,
  ShieldCheck,
  Sparkles,
  Volume2,
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import type { ImperialMapAnnotation, ImperialSite } from "@/lib/imperial/map-types";
import { useAudioPlayerStore } from "@/stores/imperialAudioStore";
import { getPrimaryHeritageImage, HERITAGE_IMAGE_TYPES } from "@/lib/imperial/heritage-images";

export interface MonumentDrawerProps {
  annotation: ImperialMapAnnotation | null;
  siteDetail?: ImperialSite | null;
  isOpen: boolean;
  onClose: () => void;
}

export function MonumentDrawer({
  annotation,
  siteDetail,
  isOpen,
  onClose,
}: MonumentDrawerProps) {
  const [isMobile, setIsMobile] = useState(false);

  const currentTrack = useAudioPlayerStore((s) => s.currentTrack);
  const isPlaying = useAudioPlayerStore((s) => s.isPlaying);
  const playSite = useAudioPlayerStore((s) => s.playSite);
  const togglePlayPause = useAudioPlayerStore((s) => s.togglePlayPause);
  const setMinimized = useAudioPlayerStore((s) => s.setMinimized);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  if (!annotation) return null;

  const site = (siteDetail || annotation.site) as any;
  const slug = site?.slug || annotation.site_id;
  const heritageImage = slug ? getPrimaryHeritageImage(slug) : null;
  const nameVi = site?.name_vi || annotation.label || "Công trình";
  const hanNom = site?.name_han_nom || site?.chinese_name;
  const zoneSlug = site?.zone_slug || undefined;

  const isCurrentSiteActive = currentTrack?.siteSlug === slug;
  const isAudioPlaying = isCurrentSiteActive && isPlaying;

  const handleAudioClick = () => {
    if (isCurrentSiteActive) {
      togglePlayPause();
    } else if (slug) {
      playSite(slug, true);
      setMinimized(false);
    }
  };

  const getZoneTitle = (zone?: string) => {
    switch (zone) {
      case "central-ceremonial-axis":
        return "Trục trung tâm (Chính đạo)";
      case "ancestral-worship-space":
        return "Không gian thờ tự (Tổ miếu)";
      case "purple-forbidden-city":
        return "Tử Cấm Thành (Cấm địa)";
      case "royal-living-gardens":
        return "Không gian sinh hoạt (Cung viên)";
      default:
        return "Đại Nội Huế";
    }
  };

  const getConditionBadge = (condition?: string) => {
    switch (condition) {
      case "extant":
        return {
          label: "Bảo tồn nguyên vẹn",
          className: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
        };
      case "ruin":
        return {
          label: "Phế tích / Nền móng khảo cổ",
          className: "bg-amber-500/15 text-amber-400 border-amber-500/30",
        };
      case "reconstructed":
        return {
          label: "Đã phục dựng hoàn chỉnh",
          className: "bg-sky-500/15 text-sky-400 border-sky-500/30",
        };
      default:
        return {
          label: "Di tích di sản",
          className: "bg-stone-500/15 text-stone-300 border-stone-500/30",
        };
    }
  };

  const conditionMeta = getConditionBadge(site?.condition);

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent
        side={isMobile ? "bottom" : "right"}
        className={cn(
          "bg-card/95 backdrop-blur-2xl border-border/70 p-6 shadow-2xl flex flex-col overflow-y-auto no-scrollbar",
          isMobile
            ? "max-h-[85vh] rounded-t-3xl border-t"
            : "w-full sm:max-w-lg border-l",
        )}
      >
        <SheetHeader className="space-y-2 text-left">
          {/* Spatial Zone & Verification Badges */}
          <div className="flex flex-wrap items-center gap-2">
            <Badge
              variant="outline"
              className="bg-primary/10 text-primary border-primary/30 text-xs px-2.5 py-0.5 font-medium"
            >
              <Compass className="w-3 h-3 mr-1 inline-block" />
              {getZoneTitle(zoneSlug)}
            </Badge>

            <Badge
              variant="outline"
              className={cn("text-xs px-2.5 py-0.5 font-medium", conditionMeta.className)}
            >
              {conditionMeta.label}
            </Badge>
          </div>

          {/* Monument Title */}
          <div className="pt-1">
            <SheetTitle className="text-2xl font-bold font-serif tracking-tight text-foreground">
              {nameVi}
            </SheetTitle>
            <SheetDescription className="text-xs text-muted-foreground mt-0.5">
              Tọa độ chuẩn hóa UV: [{annotation.u.toFixed(4)}, {annotation.v.toFixed(4)}]
            </SheetDescription>
          </div>
        </SheetHeader>

        <Separator className="my-4 bg-border/60" />

        {/* Content Body */}
        <div className="flex-1 space-y-5 text-sm">
          {/* Monument Featured Photograph (Spec Patch V2.2) */}
          {heritageImage ? (
            <div className="relative aspect-[16/10] w-full overflow-hidden rounded-xl border border-border/70 shadow-sm bg-neutral-950 group">
              <Image
                src={heritageImage.src}
                alt={heritageImage.alt || nameVi}
                fill
                className="object-cover group-hover:scale-105 transition-transform duration-500"
                sizes="(max-width: 640px) 100vw, 450px"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent pointer-events-none" />
              <div className="absolute top-2.5 left-2.5">
                <span className="rounded-md bg-black/75 backdrop-blur-md px-2 py-0.5 text-[10px] font-medium text-white shadow border border-white/10">
                  {HERITAGE_IMAGE_TYPES[heritageImage.imageType]?.label || "Hiện trạng"}
                </span>
              </div>
              <div className="absolute bottom-2 left-3 right-3 text-white pointer-events-none">
                <p className="text-[11px] font-medium text-white/95 line-clamp-1 drop-shadow">
                  {heritageImage.title}
                </p>
                <p className="text-[9px] text-white/70 truncate">
                  Nguồn: {heritageImage.creditLine}
                </p>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-secondary/30 border border-dashed border-border/60 text-xs text-muted-foreground">
              <HelpCircle className="w-3.5 h-3.5 opacity-60 shrink-0" />
              <span>Chưa có ảnh chụp thực tế đã xác minh cho di tích này</span>
            </div>
          )}

          {/* Historical Period / Reign */}
          {(site?.construction_year || site?.reign) && (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-secondary/50 border border-border/50 text-xs text-foreground/90">
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500 shrink-0">
                <Calendar className="w-4 h-4" />
              </div>
              <div>
                <span className="font-semibold block text-foreground">
                  Niên đại & Triều đại
                </span>
                <span className="text-muted-foreground">
                  {site.construction_year ? `Năm khởi dựng: ${site.construction_year}` : ""}
                  {site.reign ? ` — Triều vua ${site.reign}` : ""}
                </span>
              </div>
            </div>
          )}

          {/* Summary */}
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-primary" />
              Tóm lược lịch sử kiến trúc
            </h4>
            <p className="text-foreground/90 leading-relaxed text-sm bg-background/50 p-3.5 rounded-xl border border-border/50">
              {site?.historical_summary ||
                site?.description_vi ||
                "Công trình di sản quan trọng thuộc Quần thể Di tích Cố đô Huế, được ghi danh Di sản Văn hóa Thế giới UNESCO."}
            </p>
          </div>

          {/* Guiding Question / Pedagogical Inquiry */}
          {(site?.guiding_inquiry_question || site?.guiding_question) && (
            <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/30 text-amber-200 space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs font-bold text-amber-400">
                <HelpCircle className="w-3.5 h-3.5" />
                <span>Câu hỏi định hướng khám phá</span>
              </div>
              <p className="text-xs leading-relaxed italic text-amber-100/90 font-serif">
                &ldquo;{site.guiding_inquiry_question || site.guiding_question}&rdquo;
              </p>
            </div>
          )}

          {/* Archival Evidence Snippet */}
          {site?.primary_sources && site.primary_sources.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                Nguồn sử liệu chính biên
              </h4>
              <div className="text-xs bg-secondary/40 p-3 rounded-xl border border-border/50 space-y-1">
                <div className="font-semibold text-foreground">
                  {site.primary_sources[0].source_title}
                  {site.primary_sources[0].volume_or_chapter && (
                    <span className="text-muted-foreground font-normal">
                      {" "}
                      ({site.primary_sources[0].volume_or_chapter})
                    </span>
                  )}
                </div>
                {site.primary_sources[0].citation && (
                  <p className="text-muted-foreground italic line-clamp-2">
                    &ldquo;{site.primary_sources[0].citation}&rdquo;
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

          {/* Action Footer */}
        <div className="pt-5 mt-auto border-t border-border/60 flex flex-col sm:flex-row items-center gap-2.5">
          <Button
            type="button"
            variant="outline"
            onClick={handleAudioClick}
            className={cn(
              "w-full sm:w-auto px-4 py-2 text-xs font-semibold flex items-center justify-center gap-2 border transition-all",
              isAudioPlaying
                ? "bg-primary text-primary-foreground border-primary hover:bg-primary/90"
                : "bg-secondary/60 hover:bg-secondary text-foreground border-border/80 hover:border-primary/50",
            )}
          >
            <Headphones className={cn("w-4 h-4", isAudioPlaying && "animate-bounce text-primary-foreground")} />
            <span>
              {isAudioPlaying
                ? "Đang nghe thuyết minh"
                : isCurrentSiteActive
                ? "Tiếp tục thuyết minh"
                : "Nghe thuyết minh di sản"}
            </span>
            {isAudioPlaying ? (
              <Pause className="w-3.5 h-3.5 fill-current ml-0.5" />
            ) : (
              <Play className="w-3.5 h-3.5 fill-current ml-0.5" />
            )}
          </Button>

          <Button
            asChild
            className="w-full flex-1 bg-gradient-to-r from-primary via-amber-500 to-amber-600 hover:brightness-110 text-primary-foreground font-semibold shadow-lg text-xs tracking-wider"
          >
            <Link href={`/dai-noi/cong-trinh/${slug}`}>
              Xem hồ sơ công trình & tư liệu
              <ArrowRight className="w-4 h-4 ml-1.5" />
            </Link>
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
