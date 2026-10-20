"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import Image from "next/image";
import {
  Compass,
  Expand,
  Eye,
  Info,
  Maximize2,
  Minimize2,
  Minus,
  Move,
  Plus,
  RotateCcw,
  Sparkles,
  Layers,
  HelpCircle,
  ExternalLink,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { ArtDetailModal } from "../art-detail/ArtDetailModal";
import type {
  ImperialLearningMedia,
  ImperialMediaHotspot,
  ImperialArtDetail,
} from "@/lib/imperial/v51-types";

interface MediaHotspotViewerProps {
  media: ImperialLearningMedia;
  hotspots?: ImperialMediaHotspot[];
  availableMediaList?: ImperialLearningMedia[];
  onSelectMedia?: (media: ImperialLearningMedia) => void;
  onHotspotClick?: (hotspot: ImperialMediaHotspot) => void;
  className?: string;
}

export function MediaHotspotViewer({
  media,
  hotspots: propHotspots,
  availableMediaList = [],
  onSelectMedia,
  onHotspotClick,
  className = "",
}: MediaHotspotViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  // Active hotspots list
  const hotspots = propHotspots || media.hotspots || [];

  // Pan & Zoom state
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isFullscreen, setIsFullscreen] = useState(false);

  // 360 mode state
  const isPano = media.kind === "panorama360";
  const [viewMode, setViewMode] = useState<"2d" | "360">(isPano ? "360" : "2d");
  const [panoYaw, setPanoYaw] = useState(0); // 0 to 360 degrees

  // Selected hotspot for Art Detail Modal
  const [activeHotspot, setActiveHotspot] = useState<ImperialMediaHotspot | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeDetailSlug, setActiveDetailSlug] = useState<string | null>(null);

  // Sync mode with media kind
  useEffect(() => {
    setViewMode(media.kind === "panorama360" ? "360" : "2d");
    setScale(1);
    setPosition({ x: 0, y: 0 });
  }, [media]);

  // Zoom handlers
  const handleZoomIn = () => setScale((s) => Math.min(s + 0.35, 4));
  const handleZoomOut = () => setScale((s) => Math.max(s - 0.35, 1));
  const handleReset = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
    setPanoYaw(0);
  };

  // Mouse wheel zoom
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    if (e.deltaY < 0) {
      setScale((s) => Math.min(s + 0.15, 4));
    } else {
      setScale((s) => {
        const next = Math.max(s - 0.15, 1);
        if (next === 1) setPosition({ x: 0, y: 0 });
        return next;
      });
    }
  };

  // Drag pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (scale <= 1 && viewMode !== "360") return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;

    if (viewMode === "360") {
      // In 360 mode, dragging horizontally rotates yaw
      const deltaX = e.movementX;
      setPanoYaw((prev) => (prev - deltaX * 0.3 + 360) % 360);
    }

    if (scale > 1) {
      const maxX = (scale - 1) * 300;
      const maxY = (scale - 1) * 200;
      const newX = Math.max(-maxX, Math.min(maxX, e.clientX - dragStart.x));
      const newY = Math.max(-maxY, Math.min(maxY, e.clientY - dragStart.y));
      setPosition({ x: newX, y: newY });
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  // Fullscreen toggle
  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  // Hotspot click handler
  const handleHotspotClick = (hotspot: ImperialMediaHotspot) => {
    setActiveHotspot(hotspot);
    if (hotspot.art_detail_slug) {
      setActiveDetailSlug(hotspot.art_detail_slug);
    } else if (hotspot.detail_id) {
      setActiveDetailSlug(hotspot.detail_id);
    } else {
      setActiveDetailSlug(null);
    }
    setIsModalOpen(true);
    onHotspotClick?.(hotspot);
  };

  // Compass heading direction for 360 mode
  const getCompassDirection = (deg: number) => {
    const directions = ["Bắc (N)", "Đông Bắc (NE)", "Đông (E)", "Đông Nam (SE)", "Nam (S)", "Tây Nam (SW)", "Tây (W)", "Tây Bắc (NW)"];
    const idx = Math.round(deg / 45) % 8;
    return directions[idx];
  };

  return (
    <div
      ref={containerRef}
      className={`flex flex-col bg-card rounded-xl border border-border/70 overflow-hidden shadow-sm ${className}`}
    >
      {/* Top Media Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 border-b border-border/60 bg-muted/40">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs bg-background">
            {media.kind === "panorama360" ? "Toàn cảnh 360°" : media.kind === "model3d" ? "Mô hình 3D" : "Ảnh 2D độ phân giải cao"}
          </Badge>
          <span className="font-semibold text-sm text-foreground truncate max-w-[240px] sm:max-w-md">
            {media.title_vi}
          </span>
        </div>

        {/* Media Switcher & Mode Selector */}
        <div className="flex items-center gap-2">
          {availableMediaList.length > 1 && (
            <div className="flex items-center gap-1 bg-background p-1 rounded-md border border-border/60">
              {availableMediaList.map((item) => (
                <Button
                  key={item.id}
                  size="sm"
                  variant={item.id === media.id ? "secondary" : "ghost"}
                  className="h-7 text-xs px-2"
                  onClick={() => onSelectMedia?.(item)}
                >
                  {item.kind === "panorama360" ? "360°" : "2D"}
                </Button>
              ))}
            </div>
          )}

          {isPano && (
            <div className="flex items-center gap-1 bg-background p-0.5 rounded-md border border-border/60">
              <Button
                size="sm"
                variant={viewMode === "360" ? "default" : "ghost"}
                className="h-7 text-xs px-2"
                onClick={() => setViewMode("360")}
              >
                <Compass className="w-3.5 h-3.5 mr-1" />
                360°
              </Button>
              <Button
                size="sm"
                variant={viewMode === "2d" ? "default" : "ghost"}
                className="h-7 text-xs px-2"
                onClick={() => setViewMode("2d")}
              >
                Trải phẳng
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Main Interactive Canvas / Image Viewer */}
      <div
        className="relative w-full h-[420px] sm:h-[540px] bg-black select-none overflow-hidden cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        {/* Transform Container */}
        <div
          className="relative w-full h-full flex items-center justify-center transition-transform duration-75"
          style={{
            transform: `translate3d(${position.x}px, ${position.y}px, 0) scale(${scale})`,
            transformOrigin: "center center",
          }}
        >
          {/* Media Image Layer */}
          <img
            ref={imageRef}
            src={media.media_url}
            alt={media.alt_text || media.title_vi}
            className={`w-full h-full object-contain pointer-events-none ${
              viewMode === "360" ? "opacity-95" : ""
            }`}
            style={
              viewMode === "360"
                ? {
                    // Panoramic offset simulation based on yaw
                    objectPosition: `${(panoYaw / 360) * 100}% 50%`,
                  }
                : undefined
            }
          />

          {/* Hotspot Pins Anchored at UV coordinates */}
          {hotspots.map((hotspot) => {
            // Hotspot coordinates (0..1) converted to percentage
            let uPos = hotspot.u * 100;
            const vPos = hotspot.v * 100;

            // In 360 mode, adjust uPos by panoYaw rotation
            if (viewMode === "360") {
              const yawOffset = (panoYaw / 360) * 100;
              uPos = (uPos - yawOffset + 100) % 100;
            }

            return (
              <TooltipProvider key={hotspot.id} delayDuration={100}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleHotspotClick(hotspot);
                      }}
                      className="absolute z-20 -translate-x-1/2 -translate-y-1/2 group focus:outline-none"
                      style={{
                        left: `${uPos}%`,
                        top: `${vPos}%`,
                      }}
                      aria-label={`Điểm quan sát: ${hotspot.title}`}
                    >
                      {/* Outer Pulse Ring */}
                      <span className="absolute -inset-2 rounded-full bg-amber-400/40 animate-ping duration-1000 group-hover:bg-amber-300/60" />

                      {/* Main Icon Button */}
                      <span className="relative flex items-center justify-center w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-amber-500 text-slate-950 font-bold shadow-lg border-2 border-white ring-2 ring-black/40 hover:scale-110 transition-transform">
                        <Sparkles className="w-3.5 h-3.5 text-slate-950" />
                      </span>
                    </button>
                  </TooltipTrigger>
                  <TooltipContent
                    side="top"
                    sideOffset={8}
                    className="bg-card text-foreground border border-border shadow-xl p-2.5 max-w-xs"
                  >
                    <div className="space-y-1">
                      <div className="font-semibold text-xs flex items-center gap-1 text-primary">
                        <Eye className="w-3 h-3" />
                        {hotspot.title}
                      </div>
                      {hotspot.description && (
                        <p className="text-[11px] text-muted-foreground line-clamp-2">
                          {hotspot.description}
                        </p>
                      )}
                      <div className="text-[10px] text-amber-600 dark:text-amber-400 font-medium pt-1">
                        Nhấn để xem câu chuyện & điển tích →
                      </div>
                    </div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            );
          })}
        </div>

        {/* Orientation Indicator (for 360 mode) */}
        {viewMode === "360" && (
          <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-md text-white text-xs px-3 py-1.5 rounded-full border border-white/20 flex items-center gap-2">
            <Compass
              className="w-4 h-4 text-amber-400 transition-transform"
              style={{ transform: `rotate(${-panoYaw}deg)` }}
            />
            <span>Hướng: {getCompassDirection(panoYaw)}</span>
            <span className="text-white/60">({Math.round(panoYaw)}°)</span>
          </div>
        )}

        {/* Floating Controls Overlay (Zoom, Pan Reset, Fullscreen) */}
        <div className="absolute bottom-4 right-4 flex items-center gap-1.5 bg-black/70 backdrop-blur-md p-1.5 rounded-lg border border-white/15 text-white">
          <Button
            size="icon"
            variant="ghost"
            onClick={handleZoomIn}
            disabled={scale >= 4}
            className="w-8 h-8 text-white hover:bg-white/20"
            title="Phóng to"
          >
            <Plus className="w-4 h-4" />
          </Button>

          <Button
            size="icon"
            variant="ghost"
            onClick={handleZoomOut}
            disabled={scale <= 1}
            className="w-8 h-8 text-white hover:bg-white/20"
            title="Thu nhỏ"
          >
            <Minus className="w-4 h-4" />
          </Button>

          <Button
            size="icon"
            variant="ghost"
            onClick={handleReset}
            className="w-8 h-8 text-white hover:bg-white/20 text-xs"
            title="Đặt lại khung nhìn"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </Button>

          <div className="w-[1px] h-4 bg-white/20 mx-0.5" />

          <Button
            size="icon"
            variant="ghost"
            onClick={toggleFullscreen}
            className="w-8 h-8 text-white hover:bg-white/20"
            title={isFullscreen ? "Thoát toàn màn hình" : "Toàn màn hình"}
          >
            {isFullscreen ? (
              <Minimize2 className="w-4 h-4" />
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </Button>
        </div>

        {/* Drag Helper Tip */}
        <div className="absolute bottom-4 left-4 hidden sm:flex items-center gap-1.5 bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-md text-[11px] text-white/80 border border-white/10 pointer-events-none">
          <Move className="w-3 h-3 text-amber-400" />
          <span>Kéo chuột để di chuyển góc nhìn · Cuộn chuột để phóng to/thu nhỏ</span>
        </div>
      </div>

      {/* Accessible Text Fallback List of Hotspots */}
      <section
        aria-label="Danh sách điểm quan sát mỹ thuật"
        className="p-4 sm:p-5 border-t border-border/60 bg-muted/20 space-y-3"
      >
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-xs sm:text-sm text-foreground uppercase tracking-wider flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-primary" />
            Danh mục điểm quan sát mỹ thuật trên ảnh ({hotspots.length})
          </h3>
          <span className="text-[11px] text-muted-foreground hidden sm:inline">
            Hỗ trợ người dùng khiếm thị & truy cập nhanh
          </span>
        </div>

        {hotspots.length === 0 ? (
          <p className="text-xs text-muted-foreground italic">
            Chưa có điểm quan sát nào được ghim trên hình ảnh này.
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {hotspots.map((hotspot, idx) => (
              <div
                key={hotspot.id}
                className="flex items-start justify-between gap-3 p-3 rounded-lg border border-border/50 bg-card hover:bg-accent/40 transition-colors"
              >
                <div className="space-y-1 text-xs">
                  <div className="font-semibold text-foreground flex items-center gap-1.5">
                    <span className="w-5 h-5 rounded-full bg-primary/10 text-primary flex items-center justify-center text-[10px] font-bold">
                      {idx + 1}
                    </span>
                    <span>{hotspot.title}</span>
                  </div>
                  {hotspot.description && (
                    <p className="text-muted-foreground text-[11px] line-clamp-2 pl-6">
                      {hotspot.description}
                    </p>
                  )}
                  <div className="text-[10px] text-muted-foreground pl-6">
                    Tọa độ UV: ({Math.round(hotspot.u * 100)}%, {Math.round(hotspot.v * 100)}%)
                  </div>
                </div>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleHotspotClick(hotspot)}
                  className="shrink-0 text-xs h-7 gap-1"
                >
                  <ExternalLink className="w-3 h-3" />
                  Khảo cứu
                </Button>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Art Detail Story Drawer/Dialog */}
      <ArtDetailModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        artDetail={activeHotspot?.art_detail || null}
        detailSlug={activeDetailSlug}
        variant="dialog"
      />
    </div>
  );
}
