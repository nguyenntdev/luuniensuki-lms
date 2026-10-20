"use client";

import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import Image from "next/image";
import {
  Eye,
  EyeOff,
  Maximize2,
  Minus,
  Plus,
  RotateCcw,
  ZoomIn,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  calculateFitTransform,
  clampPan,
  clampZoom,
  DEFAULT_ZOOM,
  MAX_ZOOM,
  MIN_ZOOM,
} from "@/lib/imperial/coordinate-utils";
import type {
  ImperialMapAnnotation,
  ViewportTransform,
} from "@/lib/imperial/map-types";
import {
  announceMapNavigation,
  announceMarkerSelection,
} from "@/lib/imperial/a11y-utils";
import { MonumentMarker } from "./MonumentMarker";
import { cn } from "@/lib/utils";

export interface AerialMapViewerProps {
  mapImage: {
    url: string;
    width: number;
    height: number;
    credit?: string;
    title_vi?: string;
  };
  annotations: ImperialMapAnnotation[];
  selectedAnnotationId?: string | null;
  activeZoneSlug?: string | null;
  onSelectAnnotation?: (annotation: ImperialMapAnnotation | null) => void;
  className?: string;
  focusAnnotationId?: string | null;
}

export function AerialMapViewer({
  mapImage,
  annotations,
  selectedAnnotationId,
  activeZoneSlug,
  onSelectAnnotation,
  className,
  focusAnnotationId,
}: AerialMapViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  const intrinsicWidth = mapImage.width || 4096;
  const intrinsicHeight = mapImage.height || 3072;

  // Viewport transform state
  const [transform, setTransform] = useState<ViewportTransform>({
    scale: DEFAULT_ZOOM,
    translateX: 0,
    translateY: 0,
    fittedWidth: intrinsicWidth,
    fittedHeight: intrinsicHeight,
  });

  const [showLabels, setShowLabels] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [isImageLoaded, setIsImageLoaded] = useState(false);

  // Dragging and touch references
  const dragRef = useRef<{
    startX: number;
    startY: number;
    startTx: number;
    startTy: number;
  }>({ startX: 0, startY: 0, startTx: 0, startTy: 0 });

  const touchRef = useRef<{
    initialDistance: number;
    initialScale: number;
    midpointX: number;
    midpointY: number;
  }>({ initialDistance: 0, initialScale: 1, midpointX: 0, midpointY: 0 });

  /**
   * Fits the image cleanly inside the viewport container.
   */
  const handleFitToScreen = useCallback(() => {
    if (!containerRef.current) return;
    const { clientWidth, clientHeight } = containerRef.current;
    if (clientWidth <= 0 || clientHeight <= 0) return;

    const fit = calculateFitTransform(
      clientWidth,
      clientHeight,
      intrinsicWidth,
      intrinsicHeight,
    );

    setTransform({
      scale: 1,
      translateX: fit.offsetX ?? 0,
      translateY: fit.offsetY ?? 0,
      fittedWidth: fit.fittedWidth ?? clientWidth,
      fittedHeight: fit.fittedHeight ?? clientHeight,
    });
  }, [intrinsicWidth, intrinsicHeight]);

  /**
   * Resets zoom to 1:1 scale relative to intrinsic resolution.
   */
  const handleScale1To1 = useCallback(() => {
    if (!containerRef.current) return;
    const { clientWidth, clientHeight } = containerRef.current;

    const targetTx = (clientWidth - intrinsicWidth) / 2;
    const targetTy = (clientHeight - intrinsicHeight) / 2;

    setTransform({
      scale: 1,
      translateX: targetTx,
      translateY: targetTy,
      fittedWidth: intrinsicWidth,
      fittedHeight: intrinsicHeight,
    });
  }, [intrinsicWidth, intrinsicHeight]);

  // Initial fit on mount or resize
  useEffect(() => {
    handleFitToScreen();

    const handleResize = () => {
      handleFitToScreen();
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [handleFitToScreen]);

  /**
   * Smoothly pans the camera to center a target marker.
   */
  const focusOnAnnotation = useCallback(
    (anno: ImperialMapAnnotation) => {
      if (!containerRef.current) return;
      const { clientWidth, clientHeight } = containerRef.current;
      const wfit = transform.fittedWidth ?? intrinsicWidth;
      const hfit = transform.fittedHeight ?? intrinsicHeight;

      const targetScale = Math.max(transform.scale, 1.4);
      const markerX = anno.u * wfit;
      const markerY = anno.v * hfit;

      const targetTx = clientWidth / 2 - markerX * targetScale;
      const targetTy = clientHeight / 2 - markerY * targetScale;

      setTransform((prev) => ({
        ...prev,
        scale: targetScale,
        translateX: targetTx,
        translateY: targetTy,
      }));
    },
    [transform.fittedWidth, transform.fittedHeight, transform.scale, intrinsicWidth, intrinsicHeight],
  );

  // Trigger focus when focusAnnotationId prop changes
  useEffect(() => {
    if (!focusAnnotationId) return;
    const target = annotations.find((a) => a.id === focusAnnotationId);
    if (target) {
      focusOnAnnotation(target);
    }
  }, [focusAnnotationId, annotations, focusOnAnnotation]);

  /**
   * Zooms toward a specific screen anchor point.
   */
  const zoomAtPoint = useCallback(
    (screenX: number, screenY: number, factor: number) => {
      setTransform((prev) => {
        const newScale = clampZoom(prev.scale * factor, MIN_ZOOM, MAX_ZOOM);
        if (newScale === prev.scale) return prev;

        const qx = (screenX - prev.translateX) / prev.scale;
        const qy = (screenY - prev.translateY) / prev.scale;

        const rawTx = screenX - qx * newScale;
        const rawTy = screenY - qy * newScale;

        return {
          ...prev,
          scale: newScale,
          translateX: rawTx,
          translateY: rawTy,
        };
      });
    },
    [],
  );

  /**
   * Mouse Wheel: zoom centered at mouse cursor.
   */
  const handleWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const screenX = e.clientX - rect.left;
    const screenY = e.clientY - rect.top;

    const factor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
    zoomAtPoint(screenX, screenY, factor);
  };

  /**
   * Mouse Pointer Down: start panning.
   */
  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    // Only drag with left mouse button or touch
    if (e.button !== 0) return;
    setIsDragging(true);
    dragRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      startTx: transform.translateX,
      startTy: transform.translateY,
    };
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  };

  /**
   * Mouse Pointer Move: pan transformed plane.
   */
  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    const dx = e.clientX - dragRef.current.startX;
    const dy = e.clientY - dragRef.current.startY;

    setTransform((prev) => ({
      ...prev,
      translateX: dragRef.current.startTx + dx,
      translateY: dragRef.current.startTy + dy,
    }));
  };

  /**
   * Mouse Pointer Up / Cancel.
   */
  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (isDragging) {
      setIsDragging(false);
      try {
        (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
      } catch {
        // Ignored if pointer capture already ended
      }
    }
  };

  /**
   * Double-click to zoom in towards cursor.
   */
  const handleDoubleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const screenX = e.clientX - rect.left;
    const screenY = e.clientY - rect.top;
    zoomAtPoint(screenX, screenY, 1.4);
  };

  /**
   * Touch Events: Pinch-to-zoom support.
   */
  const handleTouchStart = (e: React.TouchEvent<HTMLDivElement>) => {
    if (e.touches.length === 2 && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const t1 = e.touches[0];
      const t2 = e.touches[1];
      const dist = Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY);

      touchRef.current = {
        initialDistance: dist,
        initialScale: transform.scale,
        midpointX: (t1.clientX + t2.clientX) / 2 - rect.left,
        midpointY: (t1.clientY + t2.clientY) / 2 - rect.top,
      };
    }
  };

  const handleTouchMove = (e: React.TouchEvent<HTMLDivElement>) => {
    if (e.touches.length === 2) {
      e.preventDefault();
      const t1 = e.touches[0];
      const t2 = e.touches[1];
      const dist = Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY);

      if (touchRef.current.initialDistance > 0) {
        const factor = dist / touchRef.current.initialDistance;
        const newScale = clampZoom(
          touchRef.current.initialScale * factor,
          MIN_ZOOM,
          MAX_ZOOM,
        );

        setTransform((prev) => {
          const mx = touchRef.current.midpointX;
          const my = touchRef.current.midpointY;
          const qx = (mx - prev.translateX) / prev.scale;
          const qy = (my - prev.translateY) / prev.scale;

          return {
            ...prev,
            scale: newScale,
            translateX: mx - qx * newScale,
            translateY: my - qy * newScale,
          };
        });
      }
    }
  };

  /**
   * Keyboard Navigation: Arrow keys pan, +/- zoom, 0 fit.
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const panStep = 60;
    if (e.key === "ArrowLeft") {
      setTransform((prev) => ({ ...prev, translateX: prev.translateX + panStep }));
    } else if (e.key === "ArrowRight") {
      setTransform((prev) => ({ ...prev, translateX: prev.translateX - panStep }));
    } else if (e.key === "ArrowUp") {
      setTransform((prev) => ({ ...prev, translateY: prev.translateY + panStep }));
    } else if (e.key === "ArrowDown") {
      setTransform((prev) => ({ ...prev, translateY: prev.translateY - panStep }));
    } else if (e.key === "+" || e.key === "=") {
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current;
        zoomAtPoint(clientWidth / 2, clientHeight / 2, 1.25);
      }
    } else if (e.key === "-") {
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current;
        zoomAtPoint(clientWidth / 2, clientHeight / 2, 1 / 1.25);
      }
    } else if (e.key === "0") {
      handleFitToScreen();
    }
  };

  const imageWidth = transform.fittedWidth || intrinsicWidth;
  const imageHeight = transform.fittedHeight || intrinsicHeight;

  return (
    <div
      ref={containerRef}
      role="region"
      aria-label="Khung nhìn bản đồ không ảnh Đại Nội"
      tabIndex={0}
      onWheel={handleWheel}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      onDoubleClick={handleDoubleClick}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onKeyDown={handleKeyDown}
      className={cn(
        "relative w-full h-full overflow-hidden select-none bg-stone-950 focus:outline-none",
        isDragging ? "cursor-grabbing" : "cursor-grab",
        className,
      )}
    >
      {/* Transform Plane (Pan & Zoom Layer) */}
      <div
        className="absolute origin-top-left transition-transform duration-75 ease-out will-change-transform"
        style={{
          transform: `translate3d(${transform.translateX}px, ${transform.translateY}px, 0) scale(${transform.scale})`,
          width: `${imageWidth}px`,
          height: `${imageHeight}px`,
        }}
      >
        {/* Orthomosaic Aerial Image */}
        <img
          src={mapImage.url}
          alt={mapImage.title_vi || "Bản đồ không ảnh Đại Nội Huế"}
          width={intrinsicWidth}
          height={intrinsicHeight}
          draggable={false}
          onLoad={() => setIsImageLoaded(true)}
          className={cn(
            "w-full h-full object-contain pointer-events-none transition-opacity duration-300 drop-shadow-2xl",
            isImageLoaded ? "opacity-100" : "opacity-90",
          )}
        />

        {/* Marker Overlay Plane Anchored with Normalized UV Coordinates */}
        <div className="absolute inset-0 pointer-events-none">
          {annotations.map((annotation) => {
            const isSelected = selectedAnnotationId === annotation.id;
            const isDimmed =
              Boolean(activeZoneSlug) &&
              annotation.site?.zone_slug !== activeZoneSlug;

            return (
              <MonumentMarker
                key={annotation.id}
                annotation={annotation}
                isSelected={isSelected}
                isDimmed={isDimmed}
                showLabel={showLabels}
                scale={transform.scale}
                onClick={(anno) => {
                  onSelectAnnotation?.(anno);
                  focusOnAnnotation(anno);
                  if (anno.site) {
                    announceMarkerSelection({
                      name_vi: anno.site.name_vi,
                      name_han_nom:
                        anno.site.name_han_nom || anno.site.chinese_name || undefined,
                      zone_name: (anno.site as any).zone_name || (anno.site as any).zone_slug,
                      condition: anno.site.condition,
                    });
                  }
                }}
              />
            );
          })}
        </div>
      </div>

      {/* Floating Viewport Controls Toolbar */}
      <div
        aria-label="Công cụ điều khiển bản đồ"
        className="absolute bottom-6 right-6 z-30 flex flex-col items-center gap-1.5 p-1.5 rounded-2xl bg-card/90 backdrop-blur-xl border border-border/80 shadow-2xl"
      >
        {/* Zoom In */}
        <Button
          type="button"
          size="icon-xs"
          variant="ghost"
          aria-label="Phóng to bản đồ (+)"
          onClick={() => {
            if (containerRef.current) {
              const { clientWidth, clientHeight } = containerRef.current;
              zoomAtPoint(clientWidth / 2, clientHeight / 2, 1.25);
              announceMapNavigation("zoom_in", {
                scale: transform.scale * 1.25,
              });
            }
          }}
          className="rounded-xl hover:bg-secondary text-foreground"
        >
          <Plus className="w-4 h-4" />
        </Button>

        {/* Zoom Out */}
        <Button
          type="button"
          size="icon-xs"
          variant="ghost"
          aria-label="Thu nhỏ bản đồ (-)"
          onClick={() => {
            if (containerRef.current) {
              const { clientWidth, clientHeight } = containerRef.current;
              zoomAtPoint(clientWidth / 2, clientHeight / 2, 1 / 1.25);
              announceMapNavigation("zoom_out", {
                scale: transform.scale / 1.25,
              });
            }
          }}
          className="rounded-xl hover:bg-secondary text-foreground"
        >
          <Minus className="w-4 h-4" />
        </Button>

        <div className="w-4 h-px bg-border/80 my-0.5" />

        {/* Fit to Screen */}
        <Button
          type="button"
          size="icon-xs"
          variant="ghost"
          aria-label="Vừa vặn khung nhìn (0)"
          onClick={() => {
            handleFitToScreen();
            announceMapNavigation("fit");
          }}
          className="rounded-xl hover:bg-secondary text-foreground"
          title="Vừa vặn khung nhìn"
        >
          <Maximize2 className="w-3.5 h-3.5" />
        </Button>

        {/* 1:1 Scale */}
        <Button
          type="button"
          size="icon-xs"
          variant="ghost"
          aria-label="Tỷ lệ gốc 1:1"
          onClick={() => {
            handleScale1To1();
            announceMapNavigation("scale_1to1");
          }}
          className="rounded-xl hover:bg-secondary text-foreground text-[10px] font-bold"
          title="Tỷ lệ gốc 1:1"
        >
          1:1
        </Button>

        {/* Toggle Labels */}
        <Button
          type="button"
          size="icon-xs"
          variant="ghost"
          aria-label={showLabels ? "Ẩn nhãn tên" : "Hiện nhãn tên"}
          onClick={() => {
            setShowLabels((prev) => {
              const next = !prev;
              announceMapNavigation("toggle_labels");
              return next;
            });
          }}
          className={cn(
            "rounded-xl hover:bg-secondary",
            showLabels ? "text-primary" : "text-muted-foreground",
          )}
          title={showLabels ? "Ẩn nhãn tên" : "Hiện nhãn tên"}
        >
          {showLabels ? (
            <Eye className="w-3.5 h-3.5" />
          ) : (
            <EyeOff className="w-3.5 h-3.5" />
          )}
        </Button>
      </div>

      {/* Credit & Scale Readout Watermark */}
      <div className="absolute bottom-6 left-6 z-20 pointer-events-none flex flex-col gap-1 text-[11px] text-muted-foreground/80 drop-shadow-md">
        <span className="font-medium text-foreground/90">
          {mapImage.title_vi || "Bản đồ không ảnh Đại Nội Huế"}
        </span>
        <span className="text-[10px] text-muted-foreground">
          {mapImage.credit || "Dự án Lưu Niên — Bản đồ học tập di sản số"} • Tỷ lệ:{" "}
          {Math.round(transform.scale * 100)}%
        </span>
      </div>
    </div>
  );
}
