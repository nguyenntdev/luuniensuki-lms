"use client";

import React, { useState } from "react";
import Image from "next/image";
import {
  Camera,
  Maximize2,
  ZoomIn,
  Sparkles,
  Shield,
  Layers,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  getHeritageImagesBySite,
  HERITAGE_IMAGE_TYPES,
  type HeritageImage,
} from "@/lib/imperial/heritage-images";
import { MissingImageNotice } from "./MissingImageNotice";
import { ImageLightboxModal } from "./ImageLightboxModal";
import { StopHotspotOverlay } from "./StopHotspotOverlay";

interface StopImageGalleryProps {
  monumentSlug: string;
  monumentNameVi: string;
  onOpenReportModal?: () => void;
  className?: string;
}

export function StopImageGallery({
  monumentSlug,
  monumentNameVi,
  onOpenReportModal,
  className = "",
}: StopImageGalleryProps) {
  const images = getHeritageImagesBySite(monumentSlug);
  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const [isLightboxOpen, setIsLightboxOpen] = useState(false);
  const [showHotspots, setShowHotspots] = useState(false);

  // If no verified photos exist for this monument (e.g. Điện Cần Chánh), render MissingImageNotice
  if (images.length === 0) {
    return (
      <div className={className}>
        <MissingImageNotice
          monumentSlug={monumentSlug}
          monumentNameVi={monumentNameVi}
          onOpenReportModal={onOpenReportModal}
        />
      </div>
    );
  }

  const currentImage = images[activeImageIndex] || images[0];
  const typeMeta = HERITAGE_IMAGE_TYPES[currentImage.imageType];

  return (
    <div className={cn("space-y-4", className)}>
      {/* Gallery Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-1">
        <div className="flex items-center gap-2">
          <Camera className="h-4 w-4 text-primary" />
          <span className="font-serif text-sm font-bold text-foreground">
            Ảnh hiện trạng & Tư liệu kiến trúc ({images.length} tư liệu)
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Architectural Hotspots trigger (for Ngọ Môn & Thái Hòa) */}
          <StopHotspotOverlay
            monumentSlug={monumentSlug}
            isVisible={showHotspots}
            onToggleVisible={() => setShowHotspots((prev) => !prev)}
          />

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setIsLightboxOpen(true)}
            className="h-8 px-2.5 text-xs font-medium gap-1 rounded-xl border-border/80 hover:bg-secondary"
          >
            <Maximize2 className="h-3.5 w-3.5 text-primary" />
            <span className="hidden sm:inline">Phóng to chi tiết</span>
          </Button>
        </div>
      </div>

      {/* Main Image Stage */}
      <div className="relative aspect-[16/10] w-full overflow-hidden rounded-2xl border-2 border-border/80 bg-neutral-950 shadow-md group">
        <Image
          src={currentImage.src}
          alt={currentImage.alt || currentImage.title}
          fill
          className="object-cover group-hover:scale-[1.02] transition-transform duration-500"
          sizes="(max-width: 1024px) 100vw, 55vw"
          priority
        />

        {/* Gradient shadow overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent pointer-events-none" />

        {/* Top Badges */}
        <div className="absolute top-3 left-3 z-10 flex items-center gap-2">
          <span
            className={cn(
              "rounded-lg px-2.5 py-1 text-[10px] font-bold shadow-md backdrop-blur-md border",
              typeMeta?.badgeClass || "bg-black/60 text-white",
            )}
          >
            {typeMeta?.label || "Hiện trạng gốc"}
          </span>

          <span className="rounded-lg bg-black/70 backdrop-blur-md px-2 py-1 text-[10px] font-mono text-white/90 shadow border border-white/10">
            {activeImageIndex + 1} / {images.length}
          </span>
        </div>

        {/* Bottom Caption Overlay */}
        <div className="absolute bottom-3 left-3 right-3 text-white pointer-events-none z-10 space-y-1">
          <h4 className="font-serif text-sm sm:text-base font-bold text-white line-clamp-1 drop-shadow-md">
            {currentImage.title}
          </h4>
          <p className="text-xs text-white/80 line-clamp-2 drop-shadow leading-relaxed max-w-xl">
            {currentImage.caption}
          </p>
          <div className="flex items-center justify-between text-[10px] text-white/60 pt-1 border-t border-white/20">
            <span>Nguồn: {currentImage.creditLine}</span>
            <span className="underline decoration-white/40">Bấm ảnh để xem toàn màn hình</span>
          </div>
        </div>

        {/* Click-to-open lightbox button overlay */}
        <button
          type="button"
          onClick={() => setIsLightboxOpen(true)}
          className="absolute inset-0 w-full h-full cursor-zoom-in z-0 focus:outline-none"
          aria-label={`Mở cửa sổ phóng to ảnh: ${currentImage.title}`}
        />
      </div>

      {/* Thumbnail Strip (if multiple photos available) */}
      {images.length > 1 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1.5 scrollbar-thin">
          {images.map((img, idx) => {
            const isThumbActive = idx === activeImageIndex;
            return (
              <button
                key={img.id}
                type="button"
                onClick={() => setActiveImageIndex(idx)}
                className={cn(
                  "relative aspect-[16/10] w-20 sm:w-24 shrink-0 overflow-hidden rounded-xl border-2 transition-all duration-200 select-none",
                  isThumbActive
                    ? "border-primary ring-2 ring-primary/40 scale-105 shadow-sm"
                    : "border-border/60 opacity-70 hover:opacity-100 hover:border-border",
                )}
                title={img.title}
              >
                <Image
                  src={img.src}
                  alt={img.alt || img.title}
                  fill
                  className="object-cover"
                  sizes="100px"
                />
                {isThumbActive && (
                  <div className="absolute inset-0 bg-primary/10 pointer-events-none" />
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Lightbox Modal */}
      <ImageLightboxModal
        images={images}
        initialIndex={activeImageIndex}
        isOpen={isLightboxOpen}
        onClose={() => setIsLightboxOpen(false)}
      />
    </div>
  );
}
