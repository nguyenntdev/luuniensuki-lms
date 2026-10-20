"use client";

import React, { useState, useEffect, useCallback } from "react";
import Image from "next/image";
import {
  X,
  ZoomIn,
  ZoomOut,
  Maximize2,
  ChevronLeft,
  ChevronRight,
  Shield,
  Info,
  Calendar,
  RotateCcw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  HERITAGE_IMAGE_TYPES,
  type HeritageImage,
} from "@/lib/imperial/heritage-images";

interface ImageLightboxModalProps {
  images: HeritageImage[];
  initialIndex?: number;
  isOpen: boolean;
  onClose: () => void;
}

export function ImageLightboxModal({
  images,
  initialIndex = 0,
  isOpen,
  onClose,
}: ImageLightboxModalProps) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [zoomLevel, setZoomLevel] = useState(1);

  useEffect(() => {
    setCurrentIndex(initialIndex);
    setZoomLevel(1);
  }, [initialIndex, isOpen]);

  const currentImage = images[currentIndex] || images[0];

  const handleNext = useCallback(() => {
    setCurrentIndex((prev) => (prev + 1) % images.length);
    setZoomLevel(1);
  }, [images.length]);

  const handlePrev = useCallback(() => {
    setCurrentIndex((prev) => (prev - 1 + images.length) % images.length);
    setZoomLevel(1);
  }, [images.length]);

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight") handleNext();
      if (e.key === "ArrowLeft") handlePrev();
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, handleNext, handlePrev, onClose]);

  if (!isOpen || !currentImage) return null;

  const typeMeta = HERITAGE_IMAGE_TYPES[currentImage.imageType];

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Cửa sổ phóng to khảo cứu ảnh di sản"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/92 backdrop-blur-md p-3 sm:p-6 animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="relative flex flex-col w-full max-w-5xl h-[92vh] rounded-3xl bg-card border border-border/70 shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Lightbox Topbar */}
        <div className="flex items-center justify-between border-b border-border/70 px-5 py-3.5 bg-secondary/30">
          <div className="flex items-center gap-2.5 min-w-0">
            <span
              className={cn(
                "rounded-md px-2 py-0.5 text-[10px] font-bold border",
                typeMeta?.badgeClass || "bg-black/40 text-white",
              )}
            >
              {typeMeta?.label || "Hiện trạng"}
            </span>
            <span className="font-mono text-xs text-muted-foreground truncate">
              {currentIndex + 1} / {images.length}
            </span>
            <span className="text-muted-foreground/40 hidden sm:inline">•</span>
            <span className="font-serif text-xs font-bold text-foreground truncate max-w-md hidden sm:inline">
              {currentImage.title}
            </span>
          </div>

          {/* Action Toolbar */}
          <div className="flex items-center gap-1.5 shrink-0">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              onClick={() => setZoomLevel((z) => Math.min(z + 0.5, 3))}
              title="Phóng to"
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              onClick={() => setZoomLevel((z) => Math.max(z - 0.5, 1))}
              title="Thu nhỏ"
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
            {zoomLevel > 1 && (
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-muted-foreground hover:text-foreground"
                onClick={() => setZoomLevel(1)}
                title="Đặt lại kích thước gốc"
              >
                <RotateCcw className="h-3.5 w-3.5" />
              </Button>
            )}
            <div className="h-4 w-px bg-border/60 mx-1" />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              onClick={onClose}
              title="Đóng cửa sổ (ESC)"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
        </div>

        {/* Lightbox Main Stage Container */}
        <div className="relative flex-1 bg-neutral-950 flex items-center justify-center overflow-hidden select-none">
          {/* Zoomable Image Wrapper */}
          <div
            className="relative w-full h-full flex items-center justify-center p-4 transition-transform duration-200"
            style={{ transform: `scale(${zoomLevel})` }}
          >
            <Image
              src={currentImage.src}
              alt={currentImage.alt || currentImage.title}
              fill
              className="object-contain"
              sizes="(max-width: 1280px) 100vw, 1200px"
              priority
            />
          </div>

          {/* Navigation Arrows */}
          {images.length > 1 && (
            <>
              <button
                type="button"
                onClick={handlePrev}
                className="absolute left-3 top-1/2 -translate-y-1/2 flex h-10 w-10 items-center justify-center rounded-full bg-black/60 text-white hover:bg-primary transition-all border border-white/20 shadow-lg"
                title="Ảnh trước (Mũi tên trái)"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <button
                type="button"
                onClick={handleNext}
                className="absolute right-3 top-1/2 -translate-y-1/2 flex h-10 w-10 items-center justify-center rounded-full bg-black/60 text-white hover:bg-primary transition-all border border-white/20 shadow-lg"
                title="Ảnh kế tiếp (Mũi tên phải)"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            </>
          )}

          {/* Zoom Indicator Badge */}
          {zoomLevel > 1 && (
            <div className="absolute bottom-3 right-3 rounded-md bg-black/75 px-2 py-1 font-mono text-[11px] text-white backdrop-blur-md">
              Zoom: {Math.round(zoomLevel * 100)}%
            </div>
          )}
        </div>

        {/* Lightbox Footer & Historical Metadata */}
        <div className="border-t border-border/70 p-4 sm:p-5 bg-card space-y-2.5 max-h-48 overflow-y-auto">
          <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
            <h3 className="font-serif text-base font-bold text-foreground">
              {currentImage.title}
            </h3>
            <span className="text-[11px] font-mono text-muted-foreground shrink-0">
              Góc chụp: {currentImage.viewpoint === "front" ? "Chính diện" : currentImage.viewpoint === "oblique" ? "Góc nghiêng" : "Chi tiết"}
            </span>
          </div>

          <p className="text-xs text-muted-foreground leading-relaxed">
            {currentImage.caption}
          </p>

          <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-border/50 text-[11px] text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <Shield className="h-3.5 w-3.5 text-primary" />
              <span>Nguồn & Bản quyền: <strong>{currentImage.creditLine}</strong></span>
            </div>
            {currentImage.editDisclosure && (
              <span className="text-amber-600 dark:text-amber-400 font-medium">
                Ghi chú xử lý: {currentImage.editDisclosure}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
